# app/core/encryption.py
import base64
from cryptography.fernet import Fernet
from app.core.config import get_settings

settings = get_settings()


class EncryptionService:
    def __init__(self):
        key = settings.CAPTCHA_ENCRYPTION_KEY or ""
        # Ensure 32 bytes, pad if short
        key = (key + ("0" * 32))[:32]
        key_bytes = key.encode("utf-8")
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        self.cipher = Fernet(fernet_key)

    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()


encryption_service = EncryptionService()
