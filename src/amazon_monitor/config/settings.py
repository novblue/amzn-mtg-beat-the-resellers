import os
from dataclasses import dataclass

from dotenv import load_dotenv

from ..exceptions import ConfigurationError


@dataclass
class Config:
    """Configuration settings for Amazon Pre-order Monitor."""

    # Required fields
    email: str
    password_encrypted: str = ""
    product_url: str = ""

    # Optional fields with defaults
    refresh_interval: int = 60
    headless: bool = False
    cookie_file: str = "amazon_cookies.json"

    # Anti-detection settings (off by default)
    enable_anti_detection: bool = False
    randomize_user_agent: bool = False
    randomize_window_size: bool = False
    random_delays: bool = False
    stealth_mode: bool = False

    def __post_init__(self):
        """Validate configuration after initialization.
        
        Raises:
            ConfigurationError: If any required configuration is missing or invalid.
        """
        if not self.email:
            raise ConfigurationError("Email is required")

        if not self.password_encrypted:
            raise ConfigurationError("Encrypted password is required")

        if not self.product_url:
            raise ConfigurationError("Product URL is required")

        if not self.product_url.startswith("https://www.amazon.com"):
            raise ConfigurationError("Invalid product URL - must be Amazon product page")

        if self.refresh_interval < 10:
            raise ConfigurationError("Refresh interval must be at least 10 seconds")

def create_config_from_env() -> Config:
    """Create configuration from environment variables."""
    load_dotenv()

    # Required fields
    email = os.getenv("AMAZON_EMAIL")
    password_encrypted = os.getenv("AMAZON_PASSWORD_ENCRYPTED", "")
    product_url = os.getenv("PRODUCT_URL")

    if not email or not product_url:
        raise ConfigurationError(
            "Missing required environment variables. "
            "Required: AMAZON_EMAIL, AMAZON_PASSWORD_ENCRYPTED, PRODUCT_URL"
        )

    # Optional fields with defaults
    refresh_interval = int(os.getenv("REFRESH_INTERVAL", "60"))
    headless = os.getenv("HEADLESS", "false").lower() == "true"
    cookie_file = os.getenv("COOKIE_FILE", "amazon_cookies.json")

    # Anti-detection flags (default: false)
    enable_anti_detection = os.getenv("ENABLE_ANTI_DETECTION", "false").lower() == "true"
    randomize_user_agent = os.getenv("RANDOMIZE_USER_AGENT", "false").lower() == "true"
    randomize_window_size = os.getenv("RANDOMIZE_WINDOW_SIZE", "false").lower() == "true"
    random_delays = os.getenv("RANDOM_DELAYS", "false").lower() == "true"
    stealth_mode = os.getenv("STEALTH_MODE", "false").lower() == "true"

    return Config(
        email=email,
        password_encrypted=password_encrypted,
        product_url=product_url,
        refresh_interval=refresh_interval,
        headless=headless,
        cookie_file=cookie_file,
        enable_anti_detection=enable_anti_detection,
        randomize_user_agent=randomize_user_agent,
        randomize_window_size=randomize_window_size,
        random_delays=random_delays,
        stealth_mode=stealth_mode
    )