from unittest.mock import Mock, patch
from amazon_monitor.amazon.auth import AmazonAuth
from unittest.mock import Mock, patch

from amazon_monitor.amazon.auth import AmazonAuth


class TestAmazonAuth:
    def test_login_success(self, config, mock_driver):
        auth = AmazonAuth(config)

        with patch.object(auth, '_navigate_to_login'):
            with patch.object(auth, '_enter_credentials'):
                with patch.object(auth, '_handle_security_checks'):
                    with patch.object(auth, '_verify_login', return_value=True):
                        result = auth.login(mock_driver)

                        assert result is True

    def test_login_with_captcha_handling(self, config, mock_driver):
        auth = AmazonAuth(config)

        # Mock the page source to contain captcha
        mock_driver.page_source = "captcha detected"

        with patch.object(auth, '_navigate_to_login'):
            with patch.object(auth, '_enter_credentials'):
                with patch.object(auth, '_verify_login', return_value=True):
                    with patch('builtins.input', return_value=''):  # User solves captcha
                        result = auth.login(mock_driver)

                        assert result is True

    def test_session_validation_logged_in(self, config, mock_driver):
        auth = AmazonAuth(config)
        mock_element = Mock()
        mock_element.text = "Hello, TestUser"
        mock_driver.find_elements.return_value = [mock_element]

        result = auth.is_session_valid(mock_driver)

        assert result is True

    def test_session_validation_logged_out(self, config, mock_driver):
        auth = AmazonAuth(config)
        mock_driver.find_elements.return_value = []
        mock_driver.page_source = "Hello, sign in"

        result = auth.is_session_valid(mock_driver)

        assert result is False

    def test_login_failure(self, config, mock_driver):
        auth = AmazonAuth(config)

        with patch.object(auth, '_navigate_to_login'):
            with patch.object(auth, '_enter_credentials'):
                with patch.object(auth, '_handle_security_checks'):
                    with patch.object(auth, '_verify_login', return_value=False):
                        result = auth.login(mock_driver)

                        assert result is False

    def test_login_exception_handling(self, config, mock_driver):
        auth = AmazonAuth(config)

        with patch.object(auth, '_navigate_to_login', side_effect=Exception("Navigation failed")):
            result = auth.login(mock_driver)

            assert result is False