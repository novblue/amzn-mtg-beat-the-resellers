import json
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

from amazon_monitor.utils.cookies import CookieManager


class TestCookieManager:
    def test_save_cookies_success(self):
        """Test successful cookie saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cookie_file = Path(temp_dir) / "test_cookies.json"
            manager = CookieManager(str(cookie_file))

            mock_driver = Mock()
            test_cookies = [
                {'name': 'session_id', 'value': 'abc123', 'domain': '.amazon.com'},
                {'name': 'user_pref', 'value': 'en-US', 'domain': '.amazon.com'}
            ]
            mock_driver.get_cookies.return_value = test_cookies

            result = manager.save_cookies(mock_driver)

            assert result is True
            assert cookie_file.exists()

            # Verify file contents
            with open(cookie_file, 'r') as f:
                saved_cookies = json.load(f)
            assert saved_cookies == test_cookies

    def test_load_cookies_success(self):
        """Test successful cookie loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cookie_file = Path(temp_dir) / "test_cookies.json"
            manager = CookieManager(str(cookie_file))

            test_cookies = [
                {'name': 'session_id', 'value': 'abc123', 'domain': '.amazon.com'},
                {'name': 'user_pref', 'value': 'en-US', 'domain': '.amazon.com'}
            ]

            # Create cookie file
            with open(cookie_file, 'w') as f:
                json.dump(test_cookies, f)

            mock_driver = Mock()
            result = manager.load_cookies(mock_driver)

            assert result is True
            assert mock_driver.add_cookie.call_count == 2

    def test_load_cookies_file_not_exists(self):
        """Test loading cookies when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cookie_file = Path(temp_dir) / "nonexistent.json"
            manager = CookieManager(str(cookie_file))

            mock_driver = Mock()
            result = manager.load_cookies(mock_driver)

            assert result is False
            mock_driver.add_cookie.assert_not_called()

    def test_clear_cookies(self):
        """Test clearing cookies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cookie_file = Path(temp_dir) / "test_cookies.json"
            manager = CookieManager(str(cookie_file))

            # Create a cookie file
            cookie_file.write_text('[]')
            assert cookie_file.exists()

            result = manager.clear_cookies()

            assert result is True
            assert not cookie_file.exists()

    def test_get_cookie_count(self):
        """Test getting cookie count."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cookie_file = Path(temp_dir) / "test_cookies.json"
            manager = CookieManager(str(cookie_file))

            # No file
            assert manager.get_cookie_count() == 0

            # File with cookies
            test_cookies = [{'name': 'test1'}, {'name': 'test2'}]
            with open(cookie_file, 'w') as f:
                json.dump(test_cookies, f)

            assert manager.get_cookie_count() == 2

    def test_has_valid_cookies(self):
        """Test checking for valid cookies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cookie_file = Path(temp_dir) / "test_cookies.json"
            manager = CookieManager(str(cookie_file))

            # No cookies
            assert manager.has_valid_cookies() is False

            # With cookies
            with open(cookie_file, 'w') as f:
                json.dump([{'name': 'test'}], f)

            assert manager.has_valid_cookies() is True