import os
import logging
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

def get_cipher():
    key = os.getenv("FTP_ENCRYPTION_KEY")
    if not key:
        return None
    try:
        return Fernet(key.encode('utf-8'))
    except Exception as e:
        logger.error(f"Invalid FTP_ENCRYPTION_KEY: {e}")
        return None

def encrypt_data(data: bytes) -> bytes:
    cipher = get_cipher()
    if not cipher:
        return data
    try:
        return cipher.encrypt(data)
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return data

def decrypt_data(data: bytes) -> bytes:
    cipher = get_cipher()
    if not cipher:
        return data
    try:
        return cipher.decrypt(data)
    except Exception as e:
        # If decryption fails, it might be an unencrypted file (backward compatibility)
        logger.warning(f"Decryption failed (fallback to plain): {e}")
        return data
