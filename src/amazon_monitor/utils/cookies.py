"""Cookie management utilities for maintaining Amazon sessions."""

import json
import logging
from pathlib import Path
from typing import Optional


class CookieManager:
    """Manages browser cookies for session persistence."""

    def __init__(self, cookie_file: str):
        self.cookie_file = Path(cookie_file)
        self.logger = logging.getLogger(__name__)

    def save_cookies(self, driver) -> bool:
        """
        Save cookies from driver to file.

        Args:
            driver: Selenium WebDriver instance

        Returns:
            bool: True if cookies saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            self.cookie_file.parent.mkdir(parents=True, exist_ok=True)

            cookies = driver.get_cookies()
            with open(self.cookie_file, 'w') as f:
                json.dump(cookies, f, indent=2)

            self.logger.info(f"Saved {len(cookies)} cookies to {self.cookie_file}")
            return True

        except Exception as e:
            self.logger.warning(f"Error saving cookies: {e}")
            return False

    def load_cookies(self, driver) -> bool:
        """
        Load cookies from file into driver.

        Args:
            driver: Selenium WebDriver instance

        Returns:
            bool: True if cookies loaded successfully, False otherwise
        """
        try:
            if not self.cookie_file.exists():
                self.logger.info(f"Cookie file {self.cookie_file} does not exist")
                return False

            with open(self.cookie_file, 'r') as f:
                cookies = json.load(f)

            loaded_count = 0
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                    loaded_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to add cookie {cookie.get('name', 'unknown')}: {e}")

            self.logger.info(f"Loaded {loaded_count}/{len(cookies)} cookies from {self.cookie_file}")
            return loaded_count > 0

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in cookie file {self.cookie_file}: {e}")
            return False
        except Exception as e:
            self.logger.warning(f"Error loading cookies: {e}")
            return False

    def clear_cookies(self) -> bool:
        """
        Clear saved cookies by deleting the cookie file.

        Returns:
            bool: True if cookies cleared successfully, False otherwise
        """
        try:
            if self.cookie_file.exists():
                self.cookie_file.unlink()
                self.logger.info(f"Cleared cookies file {self.cookie_file}")
            return True
        except Exception as e:
            self.logger.warning(f"Error clearing cookies: {e}")
            return False

    def get_cookie_count(self) -> int:
        """
        Get the number of saved cookies.

        Returns:
            int: Number of cookies in the file, 0 if file doesn't exist or error
        """
        try:
            if not self.cookie_file.exists():
                return 0

            with open(self.cookie_file, 'r') as f:
                cookies = json.load(f)
            return len(cookies)

        except Exception:
            return 0

    def has_valid_cookies(self) -> bool:
        """
        Check if we have saved cookies that might be valid.

        Returns:
            bool: True if cookie file exists and contains cookies
        """
        return self.get_cookie_count() > 0

    def get_cookie_age_days(self) -> Optional[float]:
        """
        Get the age of the cookie file in days.

        Returns:
            Optional[float]: Age in days, None if file doesn't exist
        """
        try:
            if not self.cookie_file.exists():
                return None

            import time
            file_time = self.cookie_file.stat().st_mtime
            current_time = time.time()
            age_seconds = current_time - file_time
            return age_seconds / (24 * 60 * 60)  # Convert to days

        except Exception:
            return None