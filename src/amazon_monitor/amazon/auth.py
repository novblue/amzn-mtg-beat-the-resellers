"""Amazon authentication and session management."""
import logging
import time
from typing import Optional

from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException, StaleElementReferenceException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..config.settings import Config
from ..exceptions import ElementNotFoundError
from ..security.password_manager import PasswordManager


class AmazonAuth:
    """Handles Amazon authentication and session validation."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.password_manager = PasswordManager()

    def login(self, driver) -> bool:
        """
        Perform login to an Amazon account.

        Args:
            driver: Selenium WebDriver instance

        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            self._navigate_to_login(driver)
            self._enter_credentials(driver)
            self._handle_security_checks(driver)
            return self._verify_login(driver)
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False

    def is_session_valid(self, driver) -> bool:
        """Check if the current Amazon session is still valid."""
        try:
            driver.get("https://www.amazon.com")
            time.sleep(2)

            # DEBUG: Log current URL and page title
            self.logger.info(f"Session check - URL: {driver.current_url}")
            self.logger.info(f"Session check - Title: {driver.title}")

            # DEBUG: Check if we're on a problem page
            page_source_lower = driver.page_source.lower()
            if "captcha" in page_source_lower:
                self.logger.warning("Session check - CAPTCHA page detected")
                return False
            if "unusual traffic" in page_source_lower:
                self.logger.warning("Session check - Unusual traffic page detected")
                return False

            # Check for positive indicators that we ARE logged in
            positive_indicators = [
                driver.find_elements(By.XPATH, "//span[contains(text(), 'Hello,')]"),
                driver.find_elements(By.XPATH, "//a[contains(@id, 'nav-link-accountList')]//span[contains(text(), 'Account')]"),
                driver.find_elements(By.ID, "nav-link-accountList-nav-line-1"),
                driver.find_elements(By.XPATH, "//a[contains(@href, '/gp/css/homepage')]"),
                driver.find_elements(By.XPATH, "//span[contains(text(), 'Account & Lists')]"),
                driver.find_elements(By.XPATH, "//a[contains(@href, '/gp/css/order-history')]")
            ]

            for elements in positive_indicators:
                if elements:
                    for element in elements:
                        text = element.text.strip()
                        if text and text.lower() != "hello, sign in":
                            self.logger.info(f"Session valid - found logged-in indicator: '{text}'")
                            return True

            # Check for explicit sign-in prompts
            sign_in_indicators = [
                "Hello, sign in",
                "Sign in",
                "Sign in to your account"
            ]

            page_source = driver.page_source.lower()
            for indicator in sign_in_indicators:
                if indicator.lower() in page_source:
                    self.logger.warning(f"Session expired - found sign-in prompt: '{indicator}'")
                    return False

            self.logger.warning("Session validity unclear, assuming logged out")
            return False

        except Exception as e:
            self.logger.error(f"Error checking session validity: {e}")
            return False

    def _navigate_to_login(self, driver):
        """Navigate to the Amazon sign-in page."""
        self.logger.info("Navigating to Amazon homepage...")
        driver.get("https://www.amazon.com")
        time.sleep(2)

        # Find and click a sign-in link
        selectors = [
            (By.ID, "nav-link-accountList"),
            (By.XPATH, "//a[contains(text(), 'Hello, sign in')]"),
            (By.XPATH, "//span[contains(text(), 'Account & Lists')]")
        ]

        sign_in_element = self._find_element_by_selectors(driver, selectors)
        if sign_in_element:
            self._click_element(driver, sign_in_element)
        else:
            self.logger.info("Sign-in link not found, navigating directly")
            driver.get("https://www.amazon.com/gp/sign-in.html")

        time.sleep(2)

    def _enter_credentials(self, driver):
        """Enter email and password credentials."""
        try:
            # Step 1: Find and fill the email field
            email_field = self._find_email_field(driver)
            email_field.clear()
            email_field.send_keys(self.config.email)

            # Step 2: Click continue
            self._click_continue_button(driver)

            # Step 3: Get secure password and fill password field
            def fill_password(password: str):
                password_field = self._find_password_field(driver)
                password_field.clear()
                password_field.send_keys(password)
                self._click_signin_button(driver)

            # Use secure password handling
            secure_password = self.password_manager.decrypt_password(self.config.password_encrypted)
            secure_password.use_secret(fill_password)


            # Step 4: Submit login
            self._click_signin_button(driver)

        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            raise

    def _find_email_field(self, driver):
        """Find the email field using fast detection."""
        self.logger.info("Looking for email field...")

        # Try quick selectors first (2 seconds each)
        quick_selectors = [
            (By.ID, "ap_email"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[type='text']:not([type='hidden'])")
        ]

        field = self._try_selectors(driver, quick_selectors, timeout=2)
        if field:
            return field

        # Fallback to comprehensive search
        self.logger.debug("Quick search failed, trying comprehensive search...")
        comprehensive_selectors = [
            (By.NAME, "email"),
            (By.XPATH, "//input[contains(@placeholder, 'email') or contains(@placeholder, 'mobile')]"),
            (By.CSS_SELECTOR, "input[autocomplete*='email']")
        ]

        field = self._try_selectors(driver, comprehensive_selectors, timeout=3)
        if field:
            return field

        raise ElementNotFoundError("Email field not found")

    @staticmethod
    def _find_password_field(driver):
        """Find the password field."""
        return WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "ap_password"))
        )

    @staticmethod
    def _click_continue_button(driver):
        """Click the Continue button."""
        continue_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.ID, "continue"))
        )
        continue_button.click()
        time.sleep(2)

    def _click_signin_button(self, driver):
        self.logger.info("Looking for sign-in button...")

        # More comprehensive selectors for the sign-in button
        selectors = [
            (By.ID, "signInSubmit"),
            (By.NAME, "signInSubmit"),
            (By.CSS_SELECTOR, "[type='submit']"),
            (By.XPATH, "//input[@type='submit']"),
            (By.XPATH, "//span[contains(text(), 'Sign-In')]"),
            (By.XPATH, "//input[contains(@value, 'Sign-In')]"),
            (By.XPATH, "//button[contains(text(), 'Sign-In')]")
        ]

        # Try each selector
        for by, selector in selectors:
            try:
                self.logger.debug(f"Trying selector: {by}={selector}")
                button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((by, selector))
                )
                self.logger.info(f"Found sign-in button using: {by}={selector}")
                button.click()
                return True
            except TimeoutException:
                continue
            except Exception as e:
                self.logger.debug(f"Error with selector {selector}: {str(e)}")
                continue

        # If we get here, log the page content for debugging
        self.logger.error("Could not find sign-in button. Current page content:")
        self._debug_available_fields(driver)
        raise ElementNotFoundError("Sign-in button not found")

    def _try_selectors(self, driver, selectors, timeout=3):
        """Try multiple selectors and return the first match."""
        for by, selector in selectors:
            try:
                field = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((by, selector))
                )
                self.logger.info(f"Found field: {selector}")
                return field
            except TimeoutException:
                continue
        return None

    def _find_field(self, driver, selectors, field_name, timeout=10):
        """Find a field using multiple selectors."""
        for by, selector in selectors:
            try:
                self.logger.debug(f"Trying {field_name} selector: {by}={selector}")
                field = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((by, selector))
                )
                self.logger.info(f"Found {field_name} using: {by}={selector}")
                return field
            except TimeoutException:
                continue

        # If no field found, debug what's available
        self.logger.error(f"No {field_name} found. Available fields:")
        self._debug_available_fields(driver)
        raise ElementNotFoundError(f"{field_name} not found")

    def _debug_available_fields(self, driver):
        """Debug helper to show all available input fields."""
        try:
            all_inputs = driver.find_elements(By.CSS_SELECTOR, "input:not([type='hidden']), button")
            for i, inp in enumerate(all_inputs[:10]):  # Show first 10
                try:
                    tag = inp.tag_name
                    inp_type = inp.get_attribute("type") or "text"
                    inp_id = inp.get_attribute("id") or "no-id"
                    inp_name = inp.get_attribute("name") or "no-name"
                    inp_value = inp.get_attribute("value") or "no-value"
                    inp_text = inp.text or "no-text"
                    self.logger.error(f"  {tag} {i}: type={inp_type}, id={inp_id}, name={inp_name}, value={inp_value}, text={inp_text}")
                except (StaleElementReferenceException, WebDriverException) as e:
                    self.logger.debug(f"Could not get attributes for element {i}: {e}")
        except (NoSuchElementException, WebDriverException) as e:
            self.logger.debug(f"Failed to get input fields: {e}")

    def _handle_security_checks(self, driver):
        """Handle CAPTCHA and other security verification."""
        time.sleep(5)  # Give page time to load
        page_source_lower = driver.page_source.lower()

        captcha_indicators = [
            "captcha",
            "enter the characters you see below",
            "enter the characters you see above",
            "type the characters you see in this image",
            "bot check",
            "sorry, we just need to make sure you're not a robot",
            "verify your identity",
            "enter the text you see above",
            "unusual activity"
        ]

        if any(indicator in page_source_lower for indicator in captcha_indicators):
            self.logger.warning("CAPTCHA detected!")
            print("\n🤖 CAPTCHA detected - solve it in the browser window")
            input("Press Enter when done... ")

        if ("additional security verification" in page_source_lower or
                "we need to verify your identity" in page_source_lower):
            self.logger.warning("Security verification required!")
            print("\n🔐 Security verification required - complete it in the browser")
            input("Press Enter when done... ")

    def _verify_login(self, driver) -> bool:
        """Verify that login was successful."""
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "nav-link-accountList"))
            )
            self.logger.info("Successfully logged in to Amazon")

            # Visit account page to strengthen session
            driver.get("https://www.amazon.com/gp/css/homepage.html")
            time.sleep(2)
            return True

        except TimeoutException:
            self.logger.error("Login verification failed")
            return False

    @staticmethod
    def _find_element_by_selectors(driver, selectors) -> Optional:
        """Find element using multiple selector strategies."""
        for by, selector in selectors:
            elements = driver.find_elements(by, selector)
            if elements:
                return elements[0]
        return None

    def _click_element(self, driver, element):
        """Click an element with basic error handling."""
        try:
            element.click()
        except Exception as e:
            self.logger.warning(f"Failed to click element: {e}")
            # Fallback to JavaScript click
            driver.execute_script("arguments[0].click();", element)