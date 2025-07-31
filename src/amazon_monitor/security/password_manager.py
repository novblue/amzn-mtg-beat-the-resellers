from .encryption import Encryption
from .secure_string import SecureString


class PasswordManager:
    """Manages secure password operations."""

    def __init__(self):
        self._decrypted = None
        self._encryption = Encryption()

    def decrypt_password(self, encrypted_password: str) -> SecureString:
        decrypted = self._encryption.decrypt(encrypted_password)
        secure = SecureString(decrypted)
        del decrypted
        return secure

