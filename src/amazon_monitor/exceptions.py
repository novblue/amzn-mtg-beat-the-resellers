"""Custom exceptions for the Amazon MTG Order Monitor application."""


class AmazonMonitorError(Exception):
    """Base exception for all Amazon Monitor errors."""
    pass

class ElementClickError(Exception):
    """Raised when an element cannot be clicked using any available method."""
    pass

class ConfigurationError(AmazonMonitorError):
    """Raised when there's an issue with configuration settings."""
    pass


class AuthenticationError(AmazonMonitorError):
    """Raised when authentication with Amazon fails."""
    pass


class ProductNotFoundError(AmazonMonitorError):
    """Raised when a product cannot be found or accessed."""
    pass


class ProductUnavailableError(AmazonMonitorError):
    """Raised when a product is found but not available for purchase."""
    pass


class CheckoutError(AmazonMonitorError):
    """Raised when there's an error during the checkout process."""
    pass


class WebDriverError(AmazonMonitorError):
    """Raised when there's an issue with the WebDriver."""
    pass


class CookieError(AmazonMonitorError):
    """Raised when there's an issue with cookie management."""
    pass


class EncryptionError(AmazonMonitorError):
    """Raised when there's an issue with encryption/decryption operations."""
    pass


class DecryptionError(EncryptionError):
    """Raised when decryption fails."""
    pass


class ElementNotFoundError(AmazonMonitorError):
    """Raised when a required web element cannot be found."""
    pass


class MonitoringError(AmazonMonitorError):
    """Raised when there's an error during product monitoring."""
    pass