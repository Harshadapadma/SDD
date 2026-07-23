import os
import base64
from django.conf import settings
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_fernet_instance = None

def get_fernet_key() -> bytes:
    """
    Derives a 32-byte Fernet key from settings.SECRET_KEY or FIELD_ENCRYPTION_KEY.
    """
    secret = getattr(settings, 'FIELD_ENCRYPTION_KEY', None) or settings.SECRET_KEY
    salt = b'negen_sdd_field_encryption_salt'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret.encode()))

def get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        _fernet_instance = Fernet(get_fernet_key())
    return _fernet_instance

def encrypt_val(val: str) -> str:
    """
    Encrypts a plaintext string value into an unreadable Fernet ciphertext string (gAAAAA...).
    If value is empty or already encrypted, returns as is.
    """
    if not val:
        return val
    if isinstance(val, str) and val.startswith("gAAAAA"):
        return val
    f = get_fernet()
    encrypted_bytes = f.encrypt(str(val).encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_val(val: str) -> str:
    """
    Decrypts a Fernet ciphertext string (gAAAAA...) into plaintext.
    If value is empty or not encrypted, returns original string safely.
    """
    if not val:
        return val
    if not (isinstance(val, str) and val.startswith("gAAAAA")):
        return val
    try:
        f = get_fernet()
        decrypted_bytes = f.decrypt(val.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception:
        return val
