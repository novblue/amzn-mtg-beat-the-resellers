"""Amazon Pre-order Monitor - A human-like bot for monitoring Amazon pre-orders."""

__version__ = "0.1.0"
__author__ = "Alexander Hinton"

from .amazon.auth import AmazonAuth
from .amazon.checkout import CheckoutHandler
from .amazon.product import ProductChecker
from .config.settings import Config
from .core.monitor import PreorderMonitor, BrowserManager

__all__ = [
    "Config",
    "PreorderMonitor",
    "BrowserManager",
    "AmazonAuth",
    "ProductChecker",
    "CheckoutHandler"
]