import sys
from pathlib import Path
from unittest.mock import patch, Mock

import pytest
from amazon_monitor.config.settings import Config
from cryptography.fernet import Fernet

# Add src to the Python path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

@pytest.fixture
def test_key():
    """Generate a consistent test key."""
    return Fernet.generate_key()

@pytest.fixture
def mock_keyring(test_key):
    """Mock keyring for testing."""
    with patch('keyring.get_password') as mock_get:
        with patch('keyring.set_password') as mock_set:
            with patch('keyring.delete_password') as mock_delete:
                mock_get.return_value = test_key.decode()
                yield {
                    'get': mock_get,
                    'set': mock_set,
                    'delete': mock_delete
                }

@pytest.fixture
def encrypted_password(mock_keyring):
    """Fixture to provide an encrypted test password."""
    from amazon_monitor.security.encryption import Encryption
    encryption = Encryption()
    return encryption.encrypt("testpassword")

@pytest.fixture
def config(encrypted_password):
    """Fixture to provide test configuration."""
    return Config(
        email="test@example.com",
        password_encrypted=encrypted_password,
        product_url="https://www.amazon.com/dp/B123456789",
        refresh_interval=60,
        headless=True,
        cookie_file="test_cookies.json",
        enable_anti_detection=False,
        randomize_user_agent=False,
        randomize_window_size=False,
        random_delays=False,
        stealth_mode=False
    )

@pytest.fixture
def mock_driver():
    driver = Mock()
    driver.page_source = "test page"
    driver.current_url = "https://amazon.com"
    return driver

@pytest.fixture
def mock_browser_manager(mock_driver):
    manager = Mock()
    manager.get_driver.return_value = mock_driver
    return manager