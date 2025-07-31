import pytest
from amazon_monitor.config.settings import Config
from amazon_monitor.core.monitor import PreorderMonitor, BrowserManager

class TestLoginFlow:
    @pytest.fixture(autouse=True)
    def setup(self, encrypted_password):
        """Set up test fixtures."""
        config = Config(
            email="test@example.com",
            password_encrypted=encrypted_password,  # Using an encrypted password
            product_url="https://www.amazon.com/dp/B123456789"
        )
        browser_manager = BrowserManager(config)
        self.monitor = PreorderMonitor(config, browser_manager)