from unittest.mock import patch

import pytest
from amazon_monitor.exceptions import ConfigurationError
from amazon_monitor.main import create_config_from_args


def test_create_config_from_env(encrypted_password):
    """Test config creation from environment variables."""
    # Mock load_dotenv to prevent loading real .env file
    with patch('amazon_monitor.config.settings.load_dotenv'):
        with patch.dict('os.environ', {
            'AMAZON_EMAIL': 'test@example.com',
            'AMAZON_PASSWORD_ENCRYPTED': encrypted_password,  # Changed from AMAZON_PASSWORD
            'PRODUCT_URL': 'https://www.amazon.com/dp/B123456789'
        }, clear=True):  # clear=True removes existing env vars
            with patch('sys.argv', ['amazon-monitor']):
                config = create_config_from_args()

                assert config.email == 'test@example.com'
                assert config.password_encrypted == encrypted_password  # Updated assertion
                assert config.product_url == 'https://www.amazon.com/dp/B123456789'

def test_main_error_handling():
    """Test main function error handling without actually running the monitor."""
    with patch('amazon_monitor.config.settings.load_dotenv'):
        with patch.dict('os.environ', {}, clear=True):
            with patch('sys.argv', ['amazon-monitor']):
                with patch('builtins.print'):
                    with pytest.raises(ConfigurationError,
                                       match="Email is required"):
                        create_config_from_args()
