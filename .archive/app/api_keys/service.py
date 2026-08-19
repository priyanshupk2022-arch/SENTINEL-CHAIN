"""Customer API Key Lifecycle & Rotation Engine."""
import hashlib
import secrets
import time
from typing import Tuple, Dict, Any, Optional

API_KEY_PREFIX = "aegis_live_"

class APIKeyService:
    @staticmethod
    def generate_api_key(name: str) -> Tuple[str, str, str]:
        """
        Generates platform API key in format `aegis_live_<40-hex-chars>`.
        Returns (raw_plaintext_key, key_prefix, sha256_hash).
        """
        random_bytes = secrets.token_hex(20)  # 40 hex chars
        raw_key = f"{API_KEY_PREFIX}{random_bytes}"
        key_prefix = raw_key[:16]
        hashed_key = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
        return raw_key, key_prefix, hashed_key

    @staticmethod
    def hash_key(raw_key: str) -> str:
        """Computes deterministic SHA-256 hash."""
        return hashlib.sha256(raw_key.strip().encode('utf-8')).hexdigest()

api_key_service = APIKeyService()
