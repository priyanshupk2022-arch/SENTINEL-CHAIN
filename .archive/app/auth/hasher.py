"""Cryptographically Secure Password Hashing Engine using Argon2id with Bcrypt Fallback."""
import hashlib
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHash
import bcrypt

ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64 MiB
    parallelism=2,
    hash_len=32,
    salt_len=16
)

def hash_password(password: str) -> str:
    """Hashes password using Argon2id."""
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plaintext password against Argon2id or legacy Bcrypt hash."""
    if not hashed_password or not plain_password:
        return False

    # Check if Argon2id hash
    if hashed_password.startswith("$argon2"):
        try:
            return ph.verify(hashed_password, plain_password)
        except (VerifyMismatchError, VerificationError, InvalidHash):
            return False

    # Check if legacy Bcrypt hash
    if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$") or hashed_password.startswith("$2y$"):
        try:
            pw_bytes = hashlib.sha256(plain_password.encode('utf-8')).digest()
            return bcrypt.checkpw(pw_bytes, hashed_password.encode('utf-8'))
        except Exception:
            return False

    return False

def needs_rehash(hashed_password: str) -> bool:
    """Checks if password hash needs to be upgraded to current Argon2id parameters."""
    if not hashed_password.startswith("$argon2"):
        return True
    try:
        return ph.check_needs_rehash(hashed_password)
    except Exception:
        return True
