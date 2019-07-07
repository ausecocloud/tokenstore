import base64
import binascii
import os

from cryptography.fernet import Fernet, MultiFernet, InvalidToken


class CryptoTool(object):

    def __init__(self, config):
        settings = config.registry.settings
        keys = [
            self._validate_key(key)
            for key in
            os.environ.get('TOKENSTORE_CRYPTOKEY', settings.get('tokenstore.cryptokey', '')).split(';')
            if key.strip()
        ]
        self.fernet = MultiFernet(
            Fernet(base64.urlsafe_b64encode(key)) for key in keys
        )

    def _validate_key(self, key):
        # key raw(32bytes), base64(44bytes), hex(64bytes)
        if isinstance(key, str):
            key = key.encode("ascii")
        if len(key) == 44:
            # base64 encoded
            try:
                key = base64.b64decode(key)
            except ValueError:
                pass
        elif len(key) == 64:
            try:
                return binascii.a2b_hex(key)
            except ValueError:
                pass
        if len(key) != 32:
            raise ValueError("Encryption keys must be be 32 bytes")
        return key

    def encrypt(self, data):
        # need binary / bytes to encrypt
        return self.fernet.encrypt(data.encode('utf-8'))

    # TODO: this may throw an InvalidToken Excetpnion?
    def decrypt(self, data):
        return self.fernet.decrypt(data).decode('utf-8')
