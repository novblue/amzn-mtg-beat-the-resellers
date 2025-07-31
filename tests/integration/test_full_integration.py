from unittest.mock import patch

import pytest
from amazon_monitor.config.settings import Config
from amazon_monitor.main import create_config_from_args


def test_create_config_from_env():
    """Test config creation from environment variables."""
    # Mock load_dotenv to prevent loading real .env file
    with patch('amazon_monitor.config.settings.load_dotenv'):
        with patch.dict('os.environ', {
            'AMAZON_EMAIL': 'test@example.com',
            'AMAZON_PASSWORD_ENCRYPTED': 'encrypted_password_string',  # Changed from AMAZON_PASSWORD
            'PRODUCT_URL': 'https://www.amazon.com/dp/B123456789'
        }, clear=True):  # clear=True removes existing env vars
            with patch('sys.argv', ['amazon-monitor']):
                config = create_config_from_args()

                assert config.email == 'test@example.com'
                assert config.password_encrypted == 'encrypted_password_string'  # Updated assertion
                assert config.product_url == 'https://www.amazon.com/dp/B123456789'

def test_create_config_from_cli_args(encrypted_password):
    """Test config creation from CLI arguments."""
    test_args = [
        'amazon-monitor',
        '--email', 'cli@example.com',
        '--password-encrypted', encrypted_password,  # Changed from --password
        '--url', 'https://www.amazon.com/dp/B987654321',
        '--headless',
        '--interval', '30'
    ]

    with patch('sys.argv', test_args):
        config = create_config_from_args()

        assert config.email == 'cli@example.com'
        assert config.password_encrypted == encrypted_password  # Changed assertion
        assert config.product_url == 'https://www.amazon.com/dp/B987654321'
        assert config.headless is True
        assert config.refresh_interval == 30

# tests/integration/test_full_integration.py
from amazon_monitor.exceptions import ConfigurationError

def test_config_validation_integration():
    """Test that config validation works end-to-end."""
    with pytest.raises(ConfigurationError, match="Invalid product URL - must be Amazon product page"):
        Config(
            email="test@example.com",
            password_encrypted="testpass",
            product_url="invalid-url"
        )

def test_main_error_handling():
    """Test main function error handling without actually running the monitor."""
    with patch('amazon_monitor.config.settings.load_dotenv'):
        with patch.dict('os.environ', {}, clear=True):
            with patch('sys.argv', ['amazon-monitor']):
                with patch('builtins.print'):
                    with pytest.raises(ConfigurationError,
                                       match="Email is required"):
                        create_config_from_args()


def test_browser_manager_integration():
    """Test BrowserManager creation and configuration."""
    from amazon_monitor.core.monitor import BrowserManager

    config = Config(
        email="test@example.com",
        password_encrypted="testpass",  # Changed from password to password_encrypted
        product_url="https://www.amazon.com/dp/B123456789",
        headless=True
    )

    # Just test that BrowserManager can be created without error
    browser_manager = BrowserManager(config)
    assert browser_manager.config == config
    assert browser_manager.driver is None

def test_monitor_initialization_integration():
    """Test PreorderMonitor initialization with real config."""
    from amazon_monitor.core.monitor import PreorderMonitor, BrowserManager

    config = Config(
        email="test@example.com",
        password_encrypted="testpass",  # Changed from password to password_encrypted
        product_url="https://www.amazon.com/dp/B123456789"
    )

    browser_manager = BrowserManager(config)
    monitor = PreorderMonitor(config, browser_manager)

    assert monitor.config == config
    assert monitor.browser_manager == browser_manager
    assert monitor.is_running is False
    assert monitor.auth is not None

def test_full_component_integration():
    """Test that all components can be instantiated together."""
    from amazon_monitor.core.monitor import PreorderMonitor, BrowserManager
    from amazon_monitor.amazon.auth import AmazonAuth
    from amazon_monitor.amazon.product import ProductChecker
    from amazon_monitor.amazon.checkout import CheckoutHandler
    from amazon_monitor.utils.cookies import CookieManager

    config = Config(
        email="test@example.com",
        password_encrypted="testpass",
        product_url="https://www.amazon.com/dp/B123456789"
    )

    # Test that all components can be created
    browser_manager = BrowserManager(config)
    monitor = PreorderMonitor(config, browser_manager)
    auth = AmazonAuth(config)
    product_checker = ProductChecker(config)
    checkout_handler = CheckoutHandler(config)
    cookie_manager = CookieManager(config.cookie_file)

    # Verify they're all properly initialized
    assert all([
        browser_manager, monitor, auth,
        product_checker, checkout_handler, cookie_manager
    ])