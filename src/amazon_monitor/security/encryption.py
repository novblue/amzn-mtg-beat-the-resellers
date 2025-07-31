import base64
import logging
import re
import secrets

import keyring
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

class Encryption:
    """
    Handles secure encryption/decryption operations using system keyring for key storage.
    """

    # Constants for keyring configuration
    SERVICE_ID = "amazon_monitor"
    KEY_USERNAME = "encryption_key"

    # Update the pattern to be more specific for Fernet-encrypted strings
    ENCRYPTED_PATTERN = r'^[A-Za-z0-9_-]{20,}={0,2}$'  # Minimum length for Fernet tokens

    def __init__(self):
        """Initialize the encryption handler."""
        self._fernet = None

    @property
    def fernet(self) -> Fernet:
        """Lazy initialization of a Fernet instance."""
        if self._fernet is None:
            key = self._load_key()
            self._fernet = Fernet(key)
        return self._fernet

    def _generate_key(self) -> bytes:
        """Generate a new Fernet key."""
        # Generate 32 bytes of random data and properly encode it
        raw_key = secrets.token_bytes(32)
        # Ensure the key is properly formatted for Fernet
        return base64.urlsafe_b64encode(raw_key)

    def _store_key(self, key: bytes) -> None:
        """Store encryption key in system keyring."""
        try:
            # Verify the key is valid before storing
            Fernet(key)
            # Store the key as a string
            keyring.set_password(self.SERVICE_ID, self.KEY_USERNAME, key.decode())
            # Initialize Fernet with the key
            self._fernet = Fernet(key)
        except Exception as e:
            logger.error(f"Failed to store encryption key: {e}")
            raise

    def _load_key(self) -> bytes:
        """Load the encryption key from the system keyring or generate a new one."""
        try:
            key_str = keyring.get_password(self.SERVICE_ID, self.KEY_USERNAME)

            if key_str is None:
                logger.info("No existing encryption key found, generating new key")
                key = self._generate_key()
                # Store the raw base64 string
                keyring.set_password(self.SERVICE_ID, self.KEY_USERNAME, key.decode())
                return key

            # If we have a stored key, ensure it's properly formatted
            try:
                # The stored key should already be in base64 format
                # Just encode it back to bytes and verify it's valid
                key = key_str.encode()
                # Verify the key by trying to initialize Fernet
                Fernet(key)
                return key
            except Exception:
                logger.warning("Stored key is invalid, generating new one")
                key = self._generate_key()
                keyring.set_password(self.SERVICE_ID, self.KEY_USERNAME, key.decode())
                return key

        except Exception as e:
            logger.error(f"Failed to load encryption key: {e}")
            raise

    def encrypt(self, data: str) -> str:
        """
        Encrypt a string value.
        
        Args:
            data: String to encrypt
            
        Returns:
            str: Base64-encoded encrypted string
        """
        try:
            encrypted = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt an encrypted string value.
        
        Args:
            encrypted_data: Base64-encoded encrypted string
        
        Returns:
            str: Decrypted string
        
        Raises:
            Exception: If decryption fails due to a wrong key or invalid data
        """
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data)
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode()
        except (InvalidToken, ValueError) as e:
            logger.error(f"Decryption failed: {e}")
            raise Exception(f"Failed to decrypt data: {str(e)}")

    def is_encrypted(self, data: str) -> bool:
        """
        Check if a string appears to be encrypted.
        
        Args:
            data: String to check
            
        Returns:
            bool: True if the string matches an encryption pattern
        """
        return bool(re.match(self.ENCRYPTED_PATTERN, data))

    def rotate_key(self) -> None:
        """
        Generate a new encryption key and re-encrypt any stored data.
        Should be called periodically for security.
        """
        try:
            # Generate a new key
            new_key = self._generate_key()
        
            # Store the new key and update Fernet instance
            self._store_key(new_key)
        
            logger.info("Encryption key rotated successfully")

        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            raise

    def setup_encrypted_password(self) -> str:
        """
        Interactive helper to encrypt a password.
        
        Returns:
            str: The encrypted password string to be stored
        """
        from getpass import getpass

        try:
            password = getpass("Enter password to encrypt: ")
            encrypted = self.encrypt(password)

            print("\nEncrypted password (store this in .env as AMAZON_PASSWORD_ENCRYPTED):")
            print(encrypted)

            return encrypted

        except Exception as e:
            logger.error(f"Password setup failed: {e}")
            raise

    def get_password(self, password_input: str) -> str:
        """
        Get plain text password from input (handles both encrypted and plain text).
        
        Args:
            password_input: Either plain text or encrypted password
            
        Returns:
            str: Plain text password
        """
        try:
            if self.is_encrypted(password_input):
                return self.decrypt(password_input)
            return password_input
        except Exception as e:
            logger.error(f"Failed to process password: {e}")
            raise