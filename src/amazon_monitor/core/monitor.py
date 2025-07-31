"""Core monitoring functionality for Amazon Pre-order Monitor."""
import logging
import os
import random
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from ..amazon.auth import AmazonAuth
from ..amazon.checkout import CheckoutHandler
from ..amazon.product import ProductChecker
from ..config.settings import Config
from ..exceptions import WebDriverError


class PreorderMonitor:
    """Main pre-order monitoring class."""

    def __init__(self, config: Config, browser_manager=None):
        self.config = config
        self.browser_manager = browser_manager
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.auth = AmazonAuth(config)

        # Initialize the product checker and checkout handler
        self.product_checker = ProductChecker(config)
        self.checkout_handler = CheckoutHandler(config)

        # Monitoring state
        self.session_check_counter = 0
        self.check_count = 0

    def start(self):
        """Start the monitoring process."""
        self.logger.info("Starting Amazon pre-order monitor...")
        self.is_running = True

        try:
            self._monitoring_loop()
        except KeyboardInterrupt:
            self.logger.info("Monitor interrupted by user")
        except Exception as e:
            self.logger.error(f"Monitor error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stop the monitoring process."""
        self.logger.info("Stopping monitor...")
        self.is_running = False

        if self.browser_manager:
            self.browser_manager.cleanup()

    def _monitoring_loop(self) -> bool:
        """
        Main monitoring loop.

        Returns:
            bool: True if the product was successfully purchased, False otherwise
        """
        driver = self.browser_manager.get_driver()

        # Initialize session
        if not self._initialize_session(driver):
            self.logger.error("Failed to initialize session")
            return False

        self.logger.info(f"Starting to monitor: {self.config.product_url}")
        self.logger.info(f"Check interval: {self.config.refresh_interval} seconds")

        while self.is_running:
            # Calculate interval with randomization
            interval = self._calculate_interval()

            # Periodic session checks
            if self._should_check_session():
                if not self._handle_session_check(driver):
                    self.logger.error("Session check failed, stopping monitor")
                    return False

            # Random browsing behavior
            if self._should_do_random_browsing():
                self._handle_random_browsing(driver)

            # Check availability
            if self._check_availability(driver):
                if self._attempt_purchase(driver):
                    self.logger.info("Successfully purchased item!")
                    return True
                else:
                    self.logger.warning("Purchase attempt failed, continuing monitoring...")

            # Wait before next check
            self.logger.info(f"Item not available, checking again in {interval} seconds...")
            time.sleep(interval)

        return False

    def _initialize_session(self, driver) -> bool:
        """Initialize session with hybrid approach: quick check, then login if needed."""
        try:
            # First attempt: Quick session validation
            if self._quick_session_check(driver):
                self.logger.info("Existing session is valid")
                return True

            # Session invalid or uncertain - do fresh login
            self.logger.info("Session invalid or uncertain, performing fresh login...")
            success = self.auth.login(driver)

            if success:
                self.logger.info("Successfully logged into Amazon")
                return True
            else:
                self.logger.error("Login failed")
                return False

        except Exception as e:
            self.logger.error(f"Session initialization failed: {e}")
            return False

    def _quick_session_check(self, driver) -> bool:
        """
        Fast session validation with strict timeout and bot detection.
        Returns True only if we're definitely logged in, False otherwise.
        """
        try:
            self.logger.debug("Performing quick session check...")

            # Navigate with short timeout
            driver.set_page_load_timeout(15)
            driver.get("https://www.amazon.com")
            time.sleep(2)

            current_url = driver.current_url.lower()
            page_source_lower = driver.page_source.lower()

            # Check for bot detection first - immediate fail
            bot_detection_indicators = [
                "unusual traffic",
                "captcha",
                "enter the characters",
                "prove you're not a robot",
                "validatecaptcha",
                "robot_check",
                "sorry, something went wrong"
            ]

            for indicator in bot_detection_indicators:
                if indicator in page_source_lower or indicator in current_url:
                    self.logger.warning(f"Bot detection detected: {indicator}")
                    return False

            # Check for sign-in indicators - if found, we're not logged in
            if any(indicator in page_source_lower for indicator in [
                "hello, sign in",
                "sign in to your account",
                "/ap/signin"
            ]):
                self.logger.debug("Sign-in prompts found - not logged in")
                return False

            # Look for positive login indicators
            try:
                # Try to find account-related elements that only show when logged in
                account_element = driver.find_element(By.ID, "nav-link-accountList")
                account_text = account_element.text.strip()

                # If it contains a name or "Hello" but not "sign in", we're probably logged in
                if (account_text and
                        "sign in" not in account_text.lower() and
                        ("hello" in account_text.lower() or len(account_text.split()) > 1)):

                    self.logger.info(f"Session appears valid - found: '{account_text}'")
                    return True

            except Exception as e:
                self.logger.debug(f"Could not find account element: {e}")

            # If we can't determine clearly, err on the side of caution
            self.logger.debug("Session validity unclear - will attempt fresh login")
            return False

        except Exception as e:
            self.logger.debug(f"Quick session check failed: {e}")
            return False
        finally:
            # Reset page load timeout
            driver.set_page_load_timeout(30)


    def _calculate_interval(self) -> int:
        """Calculate a check interval with randomization."""
        if self.config.refresh_interval > 20:
            return self.config.refresh_interval + random.randint(-10, 10)
        return self.config.refresh_interval

    def _should_check_session(self) -> bool:
        """Determine if we should perform a session validity check."""
        self.session_check_counter += 1
        if self.session_check_counter >= random.randint(5, 10):
            self.session_check_counter = 0
            return True
        return False

    def _should_do_random_browsing(self) -> bool:
        """Determine if we should do random browsing."""
        self.check_count += 1
        return self.check_count % random.randint(8, 12) == 0

    def _handle_session_check(self, driver) -> bool:
        """Handle periodic session validity checks."""
        self.logger.info("Performing session validity check...")

        if self.auth.is_session_valid(driver):
            return True

        self.logger.warning("Session invalid, attempting to re-establish...")
        return self.auth.login(driver)

    def _handle_random_browsing(self, driver):
        """Perform random browsing to appear human-like."""
        random_pages = [
            "https://www.amazon.com/gp/bestsellers",
            "https://www.amazon.com/gp/new-releases",
            "https://www.amazon.com/gp/browse.html?node=16225016011",
        ]

        page = random.choice(random_pages)
        self.logger.info(f"Visiting random page: {page}")

        try:
            driver.get(page)
            time.sleep(random.uniform(3, 7))

            # Random scrolling
            for _ in range(random.randint(1, 3)):
                driver.execute_script("window.scrollBy(0, 500)")
                time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            self.logger.warning(f"Error during random browsing: {e}")

    def _check_availability(self, driver) -> bool:
        """Check if the product is available for pre-order."""
        available, _, button_type = self.product_checker.check_availability(driver)

        if available:
            self.logger.info(f"Product available via {button_type}!")
            return True

        return False

    def _attempt_purchase(self, driver) -> bool:
        """Attempt to purchase the item."""
        available, button, button_type = self.product_checker.check_availability(driver)

        if available:
            return self.checkout_handler.attempt_purchase(driver, button, button_type)

        return False


class BrowserManager:
    """Manages browser/WebDriver lifecycle."""

    def __init__(self, config: Config):
        self.config = config
        self.driver = None
        self.logger = logging.getLogger(__name__)

    def get_driver(self):
        """Get or create a WebDriver instance."""
        if self.driver is None:
            self.driver = self._create_driver()
        return self.driver

    def cleanup(self):
        """Clean up browser resources."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Browser closed")
            except Exception as e:
                self.logger.warning(f"Error closing browser: {e}")
            finally:
                self.driver = None

    def _create_driver(self):
        """Create and configure a WebDriver instance."""
        options = webdriver.ChromeOptions()

        # Basic options (always enabled)
        if self.config.headless:
            options.add_argument("--headless")

        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-notifications")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Anti-detection measures (configurable)
        if self.config.enable_anti_detection or self.config.stealth_mode:
            self.logger.info("Enabling anti-detection measures")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")

        # Randomized user agent
        if self.config.randomize_user_agent:
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            ]
            import random
            user_agent = random.choice(user_agents)
            options.add_argument(f"user-agent={user_agent}")
            self.logger.debug(f"Using randomized user agent: {user_agent}")

        # Randomized window size
        if self.config.randomize_window_size:
            import random
            width = random.randint(1200, 1920)
            height = random.randint(800, 1080)
            options.add_argument(f"--window-size={width},{height}")
            self.logger.debug(f"Using randomized window size: {width}x{height}")

        # Create driver with fallback strategy
        try:
            driver = webdriver.Chrome(options=options)
            self.logger.info("Using system ChromeDriver")
        except Exception as e1:
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                driver_path = ChromeDriverManager().install()
                if not os.access(driver_path, os.X_OK):
                    os.chmod(driver_path, 0o755)
                service = Service(driver_path)
                driver = webdriver.Chrome(service=service, options=options)
                self.logger.info("Using WebDriver Manager ChromeDriver")
            except Exception as e2:
                raise WebDriverError(f"Could not create WebDriver: {e1}, {e2}")

        # Inject anti-detection script if enabled
        if self.config.enable_anti_detection or self.config.stealth_mode:
            self._inject_anti_detection_script(driver)

        return driver

    @staticmethod
    def _inject_anti_detection_script(driver):
        """Inject JavaScript to prevent bot detection."""
        script = """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            window.chrome = {
                runtime: {}
            };
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": script})