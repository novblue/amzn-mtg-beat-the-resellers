"""Amazon product page interactions and availability checking."""

import logging
import random
import time
from typing import Tuple, Optional, Any

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from ..config.settings import Config
from ..exceptions import ElementClickError


class ProductChecker:
    """Handles product availability checking and page interactions."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def check_availability(self, driver) -> Tuple[bool, Optional[Any], Optional[str]]:
        """
        Check if the product is available for pre-order.

        Args:
            driver: Selenium WebDriver instance

        Returns:
            Tuple of (available, button_element, button_type)
            - available: True if product can be ordered
            - button_element: The clickable element to order
            - button_type: "direct" or "buying_options"
        """
        try:
            self.simulate_human_browsing(driver)
            self._navigate_to_product(driver)
            self.simulate_human_browsing(driver)

            # Check for direct pre-order buttons first
            available, button, button_type = self._check_direct_preorder_buttons(driver)
            if available:
                return available, button, button_type

            # Check for buying options buttons
            available, button, button_type = self._check_buying_options_buttons(driver)
            if available:
                return available, button, button_type

            # Check for unavailability messages
            if self._check_unavailability_messages(driver):
                return False, None, None

            self.logger.warning("Product availability status unclear, assuming unavailable")
            return False, None, None

        except Exception as e:
            self.logger.error(f"Error checking product availability: {e}")
            return False, None, None

    def simulate_human_browsing(self, driver):
        """Simulate human-like browsing behavior on the product page."""
        self._simulate_referrer_visit(driver)
        self._scroll_page(driver)
        self._check_images(driver)
        self._scroll_back_to_top(driver)

    def _navigate_to_product(self, driver):
        """Navigate to the actual product page."""
        self.logger.info(f"Navigating to product page: {self.config.product_url}")
        driver.get(self.config.product_url)
        time.sleep(self._random_delay(2, 4))

    def _simulate_referrer_visit(self, driver):
        """Simulate visiting a referrer page before going to product."""
        referrers = [
            "https://www.amazon.com",
            "https://www.amazon.com/gp/bestsellers",
            "https://www.google.com/search?q=amazon+products",
            None  # Sometimes come directly
        ]

        referrer = random.choice(referrers)
        if not referrer:
            return

        self.logger.info(f"Visiting referrer page: {referrer}")
        driver.get(referrer)
        time.sleep(self._random_delay(1, 3))

        # Sometimes simulate a search
        if "amazon.com" in referrer and random.random() < 0.3:
            self._simulate_product_search(driver)

    def _simulate_product_search(self, driver):
        """Simulate searching for the product on Amazon."""
        try:
            product_search = self._extract_product_name_from_url()
            self._perform_search(driver, product_search)

            if random.random() < 0.4:
                self._click_random_search_result(driver)
        except Exception as e:
            self.logger.warning(f"Error during search simulation: {e}")

    def _extract_product_name_from_url(self) -> str:
        """Extract a searchable product name from the URL."""
        product_parts = self.config.product_url.split('/')
        for part in product_parts:
            if len(part) > 5 and '-' in part:
                return part.replace('-', ' ')
        return "new products"

    def _perform_search(self, driver, search_term: str):
        """Perform a search using the search box."""
        try:
            search_box = driver.find_element(By.ID, "twotabsearchtextbox")
            search_box.clear()
            self._humanlike_typing(driver, search_box, search_term)
            search_box.send_keys(Keys.ENTER)
            time.sleep(self._random_delay(2, 4))
        except Exception as e:
            self.logger.warning(f"Error performing search: {e}")

    def _click_random_search_result(self, driver):
        """Click on a random search result and navigate back."""
        try:
            results = driver.find_elements(By.XPATH, "//a[contains(@class, 's-result-item')]")
            if not results:
                return

            max_results = min(5, len(results))
            random_result = random.choice(results[:max_results])
            self._humanlike_click(driver, random_result)
            time.sleep(self._random_delay(2, 4))

            driver.back()
            time.sleep(self._random_delay(1, 3))
        except Exception as e:
            self.logger.warning(f"Error clicking search result: {e}")

    def _scroll_page(self, driver):
        """Perform random scrolling to view product details."""
        try:
            # Initial scroll
            scroll_height = random.randint(300, 800)
            driver.execute_script(f"window.scrollBy(0, {scroll_height})")
            time.sleep(self._random_delay(1, 3))

            # Maybe scroll more
            if random.random() < 0.5:
                additional_scroll = random.randint(500, 1200)
                driver.execute_script(f"window.scrollBy(0, {additional_scroll})")
                time.sleep(self._random_delay(1, 2))
        except Exception as e:
            self.logger.warning(f"Error during scrolling: {e}")

    def _check_images(self, driver):
        """Sometimes check product images to simulate human behavior."""
        if random.random() >= 0.3:
            return

        try:
            image_elements = self._find_product_images(driver)
            if not image_elements:
                return

            self._humanlike_click(driver, image_elements[0])
            time.sleep(self._random_delay(1, 3))
            self._close_image_modal_if_opened(driver)
        except Exception as e:
            self.logger.warning(f"Error checking images: {e}")

    def _find_product_images(self, driver):
        """Find product image elements on the page."""
        image_elements = driver.find_elements(By.ID, "landingImage")
        if not image_elements:
            image_elements = driver.find_elements(By.XPATH, "//img[contains(@id, 'image')]")
        return image_elements

    def _close_image_modal_if_opened(self, driver):
        """Close image modal if it was opened."""
        try:
            close_buttons = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Close')]")
            if close_buttons:
                self._humanlike_click(driver, close_buttons[0])
                time.sleep(self._random_delay(0.5, 1))
        except Exception:
            pass

    def _scroll_back_to_top(self, driver):
        """Scroll back to the buy box area."""
        try:
            driver.execute_script("window.scrollTo(0, 0)")
            time.sleep(self._random_delay(1, 2))
        except Exception as e:
            self.logger.warning(f"Error scrolling to top: {e}")

    def _check_direct_preorder_buttons(self, driver) -> Tuple[bool, Optional[Any], Optional[str]]:
        """Check for direct pre-order buttons."""
        selectors = [
            (By.ID, "preorder-button"),
            (By.ID, "submit.preorder"),
            (By.ID, "submit.preorder-now"),
            (By.ID, "buy-now-button"),
            (By.ID, "add-to-cart-button"),
            (By.XPATH, "//input[contains(@value, 'Pre-order')]"),
            (By.XPATH, "//span[contains(text(), 'Pre-order')]"),
            (By.XPATH, "//a[contains(text(), 'Pre-order')]")
        ]

        for selector_type, selector in selectors:
            try:
                elements = driver.find_elements(selector_type, selector)
                if elements:
                    self.logger.info(f"Direct pre-order button found: {selector}")
                    return True, elements[0], "direct"
            except Exception as e:
                self.logger.warning(f"Error checking selector {selector}: {e}")

        return False, None, None

    def _check_buying_options_buttons(self, driver) -> Tuple[bool, Optional[Any], Optional[str]]:
        """Check for 'See all buying options' buttons."""
        selectors = [
            (By.ID, "buybox-see-all-buying-choices"),
            (By.ID, "buybox-see-all-buying-choices-announce"),
            (By.XPATH, "//span[contains(text(), 'See All Buying Options')]"),
            (By.XPATH, "//a[contains(text(), 'See All Buying Options')]")
        ]

        for selector_type, selector in selectors:
            try:
                elements = driver.find_elements(selector_type, selector)
                if elements:
                    self.logger.info(f"Buying options button found: {selector}")
                    return True, elements[0], "buying_options"
            except Exception as e:
                self.logger.warning(f"Error checking selector {selector}: {e}")

        return False, None, None

    def _check_unavailability_messages(self, driver) -> bool:
        """Check for unavailability messages on the page."""
        unavailable_texts = [
            "Currently unavailable",
            "Out of Stock",
            "Sign up to be notified when this item becomes available",
            "Temporarily out of stock"
        ]

        try:
            page_source = driver.page_source
            for text in unavailable_texts:
                if text in page_source:
                    self.logger.info(f"Product unavailable: '{text}' found on page")
                    return True
        except Exception as e:
            self.logger.warning(f"Error checking unavailability messages: {e}")

        return False

    @staticmethod
    def _random_delay(min_seconds: float, max_seconds: float) -> float:
        """Return a random delay between min and max seconds."""
        return random.uniform(min_seconds, max_seconds)

    def _humanlike_typing(self, element, text: str):
        """Type text in a human-like manner."""
        for char in text:
            element.send_keys(char)
            time.sleep(self._random_delay(0.05, 0.15))

    @staticmethod
    def _humanlike_click(driver, element):
        """Click an element in a human-like way."""
        regular_click_error = None
        js_click_error = None

        try:
            # Try regular click first
            element.click()
            return
        except Exception as e:
            regular_click_error = e

        # Fallback to JavaScript click
        try:
            driver.execute_script("arguments[0].click();", element)
            return
        except Exception as e:
            js_click_error = e

            # Both methods failed
        raise ElementClickError(
            f"Failed to click element using both regular click and JavaScript click. "
            f"Regular click error: {regular_click_error}. "
            f"JavaScript click error: {js_click_error}"
        )