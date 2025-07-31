from unittest.mock import patch

import pytest
from amazon_monitor.security.encryption import Encryption
from cryptography.fernet import Fernet


class TestPasswordEncryption:

    @pytest.fixture(scope="session")
    def test_key(self):
        """Create a consistent test key for the entire test session."""
        return Fernet.generate_key()

    @pytest.fixture
    def mock_keyring(self):
        """Mock keyring for testing."""
        with patch('keyring.get_password') as mock_get:
            with patch('keyring.set_password') as mock_set:
                with patch('keyring.delete_password') as mock_delete:
                    yield {
                        'get': mock_get,
                        'set': mock_set,
                        'delete': mock_delete
                    }

    @pytest.fixture
    def encryption(self, mock_keyring):
        """Fixture to create Encryption instance with mocked keyring."""
        # Setup mock to return None initially (no existing key)
        mock_keyring['get'].return_value = None
        return Encryption()

    def test_encrypt_decrypt_cycle(self, encryption):
        """Test encrypting and decrypting a password."""
        original_password = "test_password_123"
        encrypted = encryption.encrypt(original_password)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == original_password
        assert encrypted != original_password
        assert encryption.is_encrypted(encrypted) is True

    def test_is_encrypted_detection(self, encryption):
        """Test detecting encrypted vs. plain passwords."""
        plain_password = "plaintext123"
        encrypted_password = encryption.encrypt(plain_password)

        assert encryption.is_encrypted(plain_password) is False
        assert encryption.is_encrypted(encrypted_password) is True

    def test_password_manager(self, encryption):
        """Test PasswordManager functionality."""
        plain_password = "test123"
        encrypted = encryption.encrypt(plain_password)

        # Test getting password from encrypted input
        result_encrypted = encryption.get_password(encrypted)
        assert result_encrypted == plain_password

        # Test getting password from plain input
        result_plain = encryption.get_password(plain_password)
        assert result_plain == plain_password

    def test_get_plain_password(self, encryption):
        """Test get_password method."""
        plain_password = "test123"

        # Test with a plain password
        result = encryption.get_password(plain_password)
        assert result == plain_password

        # Test with encrypted password
        encrypted = encryption.encrypt(plain_password)
        result = encryption.get_password(encrypted)
        assert result == plain_password

    def test_decrypt_with_wrong_key(self, encryption, mock_keyring):
        """Test that the wrong key fails gracefully."""
        # Encrypt with the current key
        original_password = "test123"
        encrypted = encryption.encrypt(original_password)

        # Replace the key with a new one
        new_key = encryption._generate_key()
        mock_keyring['get'].return_value = new_key.decode()

        # Force reinitialization of Fernet instance
        encryption._fernet = None

        # Try to decrypt with the new key
        with pytest.raises(Exception):
            encryption.decrypt(encrypted)

    @pytest.mark.usefixtures("mock_keyring")
    def test_key_rotation(self, encryption, mock_keyring):
        """Test that key rotation works correctly."""
        test_data = "test_password"

        # Encrypt with initial key
        initial_encrypted = encryption.encrypt(test_data)

        # Verify we can decrypt with initial key
        assert encryption.decrypt(initial_encrypted) == test_data

        # Store initial Fernet instance for comparison
        initial_fernet = encryption._fernet

        # Perform key rotation
        encryption.rotate_key()

        # Verify rotation occurred
        assert mock_keyring['set'].called
        assert encryption._fernet is not initial_fernet

        # Verify new encryption works
        new_encrypted = encryption.encrypt(test_data)
        assert new_encrypted != initial_encrypted
        assert encryption.decrypt(new_encrypted) == test_data