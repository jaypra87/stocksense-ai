"""Field-level encryption for email addresses.

Why app-level encryption on top of the provider's disk encryption: disk
encryption protects against someone walking off with the storage, not against
a leaked connection string or a SQL dump. With this, a copy of the `users`
table holds ciphertext and keyed hashes, never addresses.

Two columns per email:

- `email`      — AES-256-GCM ciphertext, base64, random 96-bit nonce per row.
                 Decryptable, so the app can still display the address.
- `email_hash` — HMAC-SHA256 of the normalised address. Deterministic, so it
                 can carry the unique index and answer "is this email taken?"
                 without decrypting every row. Keyed, so an attacker with the
                 dump cannot confirm guesses by hashing candidate addresses.

Both use the one key from EMAIL_ENCRYPTION_KEY, domain-separated by HKDF so
the HMAC key and the cipher key are independent. Rotating the key means
re-encrypting every row; the migration that introduced this is the template.
"""

import base64
import hmac
import os
from functools import lru_cache
from hashlib import sha256

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.core.config import get_settings

# Development-only key. Public by definition — it is in the repo — so anything
# encrypted with it is as good as plaintext. Production refuses to boot without
# its own (see Settings._require_email_key_in_prod).
_DEV_KEY_HEX = "6465762d6f6e6c792d6b65792d646f2d6e6f742d7573652d696e2d70726f6421"

_VERSION = b"v1"  # prefix on ciphertexts, so a future key/algorithm can coexist


def _master_key() -> bytes:
    key_hex = get_settings().email_encryption_key or _DEV_KEY_HEX
    return bytes.fromhex(key_hex)


@lru_cache(maxsize=1)
def _derived() -> tuple[bytes, bytes]:
    master = _master_key()

    def derive(info: bytes) -> bytes:
        return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info).derive(master)

    return derive(b"stocksense/email/aes-gcm"), derive(b"stocksense/email/hmac")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_email(email: str) -> str:
    """Deterministic keyed hash for lookups and the uniqueness constraint."""
    _, mac_key = _derived()
    return hmac.new(mac_key, normalize_email(email).encode(), sha256).hexdigest()


def encrypt_email(email: str) -> str:
    enc_key, _ = _derived()
    nonce = os.urandom(12)
    ciphertext = AESGCM(enc_key).encrypt(nonce, normalize_email(email).encode(), _VERSION)
    return base64.b64encode(_VERSION + b":" + nonce + ciphertext).decode()


def decrypt_email(blob: str) -> str:
    enc_key, _ = _derived()
    raw = base64.b64decode(blob)
    version, _, rest = raw.partition(b":")
    if version != _VERSION:
        raise ValueError(f"unknown email ciphertext version {version!r}")
    nonce, ciphertext = rest[:12], rest[12:]
    return AESGCM(enc_key).decrypt(nonce, ciphertext, _VERSION).decode()


def is_encrypted(value: str) -> bool:
    """True for values produced by encrypt_email (used by the data migration)."""
    try:
        return base64.b64decode(value, validate=True).startswith(_VERSION + b":")
    except Exception:  # noqa: BLE001 — any decode failure means "not ours"
        return False
