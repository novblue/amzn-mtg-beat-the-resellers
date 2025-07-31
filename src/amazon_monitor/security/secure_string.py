import ctypes
import mmap
import resource
import secrets
import warnings


class SecureString:
    """Secure string implementation for handling sensitive data in memory."""

    def __init__(self, secret: str):
        self._length = len(secret)
        self._buffer = ctypes.create_string_buffer(secret.encode())

        # Lock memory if supported
        if hasattr(mmap, 'mlock'):
            try:
                mmap.mlock(self._buffer)
            except OSError as e:
                warnings.warn(f"Could not lock memory: {e}")

        # Disable core dumps
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    def __del__(self):
        self._secure_wipe()

    def _secure_wipe(self):
        if hasattr(self, '_buffer'):
            random_bytes = secrets.token_bytes(self._length)
            ctypes.memmove(self._buffer, random_bytes, self._length)
            ctypes.memset(self._buffer, 0, self._length)

    def use_secret(self, func):
        try:
            temp = self._buffer.raw[:self._length].decode()
            return func(temp)
        finally:
            del temp
