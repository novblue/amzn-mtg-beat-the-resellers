"""Amazon checkout and purchase handling."""

import logging
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..config.settings import Config


class CheckoutHandler:
    """Handles Amazon checkout and purchase process."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def attempt_purchase(self, driver, button, button_type: str) -> bool:
        """
        Attempt to purchase/pre-order the item.

        Args:
            driver: Selenium WebDriver instance
            button: The button element to click
            button_type: "direct" or "buying_options"

        Returns:
            bool: True if purchase successful, False otherwise
        """
        if not button or not button_type:
            self.logger.error("Invalid button or button_type provided")
            return False

        try:
            self.logger.info(f"Attempting purchase via {button_type} button")
            self._take_screenshot(driver, "purchase_attempt_start.png")

            if button_type == "buying_options":
                return self._handle_buying_options_flow(driver, button)
            else:
                return self._handle_direct_purchase_flow(driver, button)

        except Exception as e:
            self.logger.error(f"Error during purchase attempt: {e}")
            self._take_screenshot(driver, "purchase_error.png")
            return False

    def _handle_buying_options_flow(self, driver, button) -> bool:
        """Handle purchase through buying options modal."""
        try:
            # Click the "See All Buying Options" button
            self._scroll_to_element(driver, button)
            self._click_element(driver, button)
            self.logger.info("Clicked 'See All Buying Options' button")

            # Wait for buying options modal
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "aod-offer-list"))
            )

            # Look for purchase buttons in the modal
            purchase_buttons = self._find_purchase_buttons_in_modal(driver)

            if not purchase_buttons:
                self.logger.error("No purchase buttons found in buying options modal")
                self._take_screenshot(driver, "buying_options_modal_no_buttons.png")
                return False

            # Click the first available purchase button
            self._scroll_to_element(driver, purchase_buttons[0])
            self._click_element(driver, purchase_buttons[0])
            self.logger.info("Clicked purchase button in buying options modal")

            return self._complete_checkout_process(driver)

        except TimeoutException:
            self.logger.error("Timeout waiting for buying options modal")
            self._take_screenshot(driver, "buying_options_timeout.png")
            return False
        except Exception as e:
            self.logger.error(f"Error in buying options flow: {e}")
            return False

    def _handle_direct_purchase_flow(self, driver, button) -> bool:
        """Handle direct purchase button click."""
        try:
            button_id = self._get_element_identifier(button)

            self._scroll_to_element(driver, button)
            self._click_element(driver, button)
            self.logger.info(f"Clicked direct purchase button: {button_id}")

            return self._complete_checkout_process(driver)

        except Exception as e:
            self.logger.error(f"Error in direct purchase flow: {e}")
            return False

    def _complete_checkout_process(self, driver) -> bool:
        """Complete the checkout process after clicking purchase button."""
        try:
            # Try direct checkout first (one-click purchase)
            if self._attempt_direct_checkout(driver):
                return True

            # If not direct checkout, handle cart flow
            self.logger.info("Direct checkout not available, trying cart flow")
            return self._handle_cart_checkout_flow(driver)

        except Exception as e:
            self.logger.error(f"Error completing checkout: {e}")
            return False

    def _attempt_direct_checkout(self, driver) -> bool:
        """Attempt direct one-click checkout."""
        try:
            # Look for direct place order button
            place_order_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "submitOrderButtonId"))
            )

            self._take_screenshot(driver, "direct_checkout_page.png")

            # Final confirmation before placing order
            self.logger.info("Direct checkout available - placing order")
            place_order_button.click()

            # Wait a moment and verify success
            time.sleep(3)
            self._take_screenshot(driver, "order_confirmation.png")

            if self._verify_order_success(driver):
                self.logger.info("Order placed successfully via direct checkout!")
                return True
            else:
                self.logger.warning("Order placement unclear - may need manual verification")
                return False

        except TimeoutException:
            # Direct checkout not available
            return False
        except Exception as e:
            self.logger.error(f"Error in direct checkout: {e}")
            return False

    def _handle_cart_checkout_flow(self, driver) -> bool:
        """Handle checkout through shopping cart."""
        try:
            # Check if we're in cart or need to go to cart
            if not self._is_in_cart_flow(driver):
                self.logger.error("Not in cart flow and direct checkout failed")
                self._take_screenshot(driver, "unexpected_page_after_click.png")
                return False

            # Find and click proceed to checkout
            proceed_button = self._find_proceed_to_checkout_button(driver)
            if not proceed_button:
                self.logger.error("Could not find 'Proceed to checkout' button")
                self._take_screenshot(driver, "cart_no_proceed_button.png")
                return False

            self._scroll_to_element(driver, proceed_button)
            self._click_element(driver, proceed_button)
            self.logger.info("Clicked 'Proceed to checkout' button")

            # Wait for checkout page and place order
            place_order_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "submitOrderButtonId"))
            )

            self._take_screenshot(driver, "cart_checkout_page.png")
            place_order_button.click()

            # Verify order success
            time.sleep(3)
            self._take_screenshot(driver, "cart_order_confirmation.png")

            if self._verify_order_success(driver):
                self.logger.info("Order placed successfully via cart checkout!")
                return True
            else:
                self.logger.warning("Cart order placement unclear")
                return False

        except TimeoutException:
            self.logger.error("Timeout during cart checkout flow")
            self._take_screenshot(driver, "cart_checkout_timeout.png")
            return False
        except Exception as e:
            self.logger.error(f"Error in cart checkout flow: {e}")
            return False

    def _find_purchase_buttons_in_modal(self, driver):
        """Find purchase buttons in the buying options modal."""
        selectors = [
            "//input[contains(@name, 'submit.preOrder')]",
            "//span[contains(text(), 'Pre-order')]",
            "//input[contains(@name, 'submit.addToCart')]",
            "//span[contains(text(), 'Add to Cart')]",
            "//input[contains(@value, 'Buy now')]"
        ]

        for selector in selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    return elements
            except Exception:
                continue

        return []

    def _find_proceed_to_checkout_button(self, driver):
        """Find the proceed to checkout button."""
        selectors = [
            (By.ID, "sc-buy-box-ptc-button"),
            (By.XPATH, "//input[@name='proceedToRetailCheckout']"),
            (By.XPATH, "//span[contains(text(), 'Proceed to checkout')]"),
            (By.XPATH, "//a[contains(text(), 'Proceed to checkout')]")
        ]

        for by, selector in selectors:
            try:
                elements = driver.find_elements(by, selector)
                if elements:
                    return elements[0]
            except Exception:
                continue

        return None

    def _is_in_cart_flow(self, driver) -> bool:
        """Check if we're in the cart/checkout flow."""
        indicators = [
            "cart" in driver.current_url,
            "proceed-to-checkout" in driver.page_source.lower(),
            "shopping cart" in driver.page_source.lower(),
            "checkout" in driver.current_url
        ]

        return any(indicators)

    def _verify_order_success(self, driver) -> bool:
        """Verify that the order was placed successfully."""
        success_indicators = [
            "order placed" in driver.page_source.lower(),
            "thank you" in driver.page_source.lower(),
            "order confirmation" in driver.page_source.lower(),
            "your order" in driver.page_source.lower(),
            "/gp/css/order-history" in driver.current_url
        ]

        return any(success_indicators)

    def _scroll_to_element(self, driver, element):
        """Scroll element into view."""
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
        except Exception as e:
            self.logger.warning(f"Error scrolling to element: {e}")

    def _click_element(self, driver, element):
        """Click element with fallback strategies."""
        try:
            # Try regular click
            element.click()
        except Exception:
            try:
                # Try JavaScript click
                driver.execute_script("arguments[0].click();", element)
            except Exception as e:
                self.logger.error(f"Failed to click element: {e}")
                raise

    def _get_element_identifier(self, element) -> str:
        """Get a useful identifier for an element for logging."""
        try:
            element_id = element.get_attribute("id")
            if element_id:
                return f"ID: {element_id}"

            element_class = element.get_attribute("class")
            if element_class:
                return f"Class: {element_class}"

            return "Unknown element"
        except Exception:
            return "Element identifier unavailable"

    def _take_screenshot(self, driver, filename: str):
        """Take a screenshot for debugging."""
        try:
            driver.save_screenshot(filename)
            self.logger.info(f"Screenshot saved: {filename}")
        except Exception as e:
            self.logger.warning(f"Failed to save screenshot {filename}: {e}")