import argparse
import logging
import sys

from amazon_monitor.exceptions import ConfigurationError

from .config.settings import Config, create_config_from_env
from .core.monitor import PreorderMonitor, BrowserManager


def create_config_from_args() -> Config:
    """Create configuration from command line arguments and environment."""
    parser = argparse.ArgumentParser(description="Amazon Pre-order Monitor")

    # Basic arguments
    parser.add_argument("--email", help="Amazon email address")
    parser.add_argument("--password-encrypted", help="Amazon encrypted password")  # Changed from --password
    parser.add_argument("--url", help="Product URL to monitor")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--cookie-file", default="amazon_cookies.json", help="Cookie file path")

    # Anti-detection flags
    parser.add_argument("--enable-anti-detection", action="store_true", help="Enable anti-detection measures")
    parser.add_argument("--randomize-user-agent", action="store_true", help="Randomize user agent")
    parser.add_argument("--randomize-window-size", action="store_true", help="Randomize window size")
    parser.add_argument("--random-delays", action="store_true", help="Add random delays")
    parser.add_argument("--stealth-mode", action="store_true", help="Enable stealth mode")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set the logging level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Get base config from the environment
    try:
        config = create_config_from_env()
    except (ValueError, KeyError, ConfigurationError):
        # If env config fails, create from CLI args
        config = Config(
            email=args.email or "",
            password_encrypted=args.password_encrypted or "",
            product_url=args.url or ""
        )

    # Override with CLI arguments if provided
    if args.email:
        config.email = args.email
    if args.password_encrypted:
        config.password_encrypted = args.password_encrypted
    if args.url:
        config.product_url = args.url
    if args.interval:
        config.refresh_interval = args.interval
    if args.headless:
        config.headless = args.headless
    if args.cookie_file:
        config.cookie_file = args.cookie_file

    # Anti-detection overrides
    if args.enable_anti_detection:
        config.enable_anti_detection = True
    if args.randomize_user_agent:
        config.randomize_user_agent = True
    if args.randomize_window_size:
        config.randomize_window_size = True
    if args.random_delays:
        config.random_delays = True
    if args.stealth_mode:
        config.stealth_mode = True

    return config

def main():
    """Main entry point for the Amazon Pre-order Monitor."""
    try:
        # Create configuration
        config = create_config_from_args()

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('amazon_monitor.log'),
                logging.StreamHandler()
            ]
        )

        logger = logging.getLogger(__name__)
        logger.info("Starting Amazon Pre-order Monitor...")
        logger.info(f"Product URL: {config.product_url}")
        logger.info(f"Check interval: {config.refresh_interval} seconds")
        logger.info(f"Headless mode: {config.headless}")

        # Create a browser manager and monitor
        browser_manager = BrowserManager(config)
        monitor = PreorderMonitor(config, browser_manager)

        # Start monitoring
        monitor.start()

    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Monitor error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()