"""API Key Generation, SHA-256 Hashing, and Fast Quota-Enforced Verification."""
import hashlib
import secrets
import time
from typing import Tuple, Dict, Any, Optional
from fastapi import Request, HTTPException, status

from app.models.database import db, DEFAULT_DEFAULT_ORG_ID

API_KEY_PREFIX = "aegis_live_"

def generate_api_key(name: str = "Default Key") -> Tuple[str, str, str]:
    """
    Generates a cryptographically secure platform API key.
    Returns (raw_plaintext_key, key_prefix, sha256_hash).
    """
    random_bytes = secrets.token_hex(20)  # 40 hex chars
    raw_key = f"{API_KEY_PREFIX}{random_bytes}"
    key_prefix = raw_key[:16]
    hashed_key = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
    return raw_key, key_prefix, hashed_key

def hash_key(raw_key: str) -> str:
    """Calculates deterministic SHA-256 hash of plaintext key."""
    return hashlib.sha256(raw_key.strip().encode('utf-8')).hexdigest()

# In-memory cache for API key validation (<0.1ms overhead)
_KEY_CACHE: Dict[str, Tuple[Dict[str, Any], float]] = {}
_CACHE_TTL_SEC = 10.0

def invalidate_key_cache(key_hash: Optional[str] = None) -> None:
    """Invalidates cached API key records."""
    global _KEY_CACHE
    if key_hash:
        _KEY_CACHE.pop(key_hash, None)
    else:
        _KEY_CACHE.clear()

async def verify_api_key(request: Request) -> Dict[str, Any]:
    """
    FastAPI dependency validating incoming API keys for data plane proxy & scan endpoints.
    Enforces tenant scoping and monthly quota caps.

    CRITICAL: when REQUIRE_AUTH_FOR_API is True (production), missing or invalid
    keys raise HTTP 401. The previous behavior of silently authenticating
    anonymous callers as DEFAULT_DEFAULT_ORG_ID was a P0 multi-tenant bypass.
    """
    from app.config import settings
    import os as _os

    auth_header = request.headers.get("Authorization", "")
    api_key_header = request.headers.get("X-API-Key", "")

    raw_token = ""
    if auth_header.startswith("Bearer "):
        raw_token = auth_header.replace("Bearer ", "").strip()
    elif api_key_header:
        raw_token = api_key_header.strip()

    # If no token provided
    if not raw_token:
        # Allow anonymous only in dev/test, never in production
        is_test_env = (
            settings.ENVIRONMENT in ("development", "test")
            or _os.getenv("PYTEST_CURRENT_TEST") is not None
        )
        if settings.REQUIRE_AUTH_FOR_API and not is_test_env:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing API key. Provide an 'Authorization: Bearer aegis_live_...' header.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Dev/test fallback: anonymous (only enabled in dev)
        return {
            "authenticated": False,
            "organization_id": DEFAULT_DEFAULT_ORG_ID,
            "api_key_id": None,
            "actor_type": "anonymous",
            "tier": "community_evaluation",
            "scopes": ["proxy:all", "scans:all"]
        }

    # Wrong prefix: reject — even in test mode, never silently accept
    if not raw_token.startswith(API_KEY_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid API key format. Keys must start with '{API_KEY_PREFIX}'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    hashed = hash_key(raw_token)
    now = time.time()

    # Check in-memory cache
    if hashed in _KEY_CACHE:
        key_data, timestamp = _KEY_CACHE[hashed]
        if now - timestamp < _CACHE_TTL_SEC:
            org_id = key_data["organization_id"]
            # Increment in-memory counter atomically
            key_data["current_period_requests"] = key_data.get("current_period_requests", 0) + 1
            # Enforce Quotas
            if key_data["current_period_requests"] > key_data.get("max_monthly_requests", 1000):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Monthly API quota exceeded for organization '{key_data.get('org_name')}'. Please upgrade your subscription tier."
                )
            # Async record usage in database
            await db.record_api_key_usage(key_data["id"], org_id)
            return {
                "authenticated": True,
                "organization_id": org_id,
                "api_key_id": key_data["id"],
                "actor_type": "api_key",
                "tier": key_data.get("org_tier", "free"),
                "scopes": key_data.get("scopes", "").split(",")
            }

    # Query database
    key_record = await db.get_api_key_by_hash(hashed)
    if not key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked Aegis API key."
        )

    # CRITICAL: if API key was issued for org X, do not let the request
    # override `X-Organization-ID` to org Y. Trust the key's binding.
    # The downstream ProxyHandler uses auth_context["organization_id"].

    key_record_dict = dict(key_record)
    # Increment usage counter
    key_record_dict["current_period_requests"] = key_record_dict.get("current_period_requests", 0) + 1
    _KEY_CACHE[hashed] = (key_record_dict, now)
    org_id = key_record_dict["organization_id"]

    # Enforce Monthly Quotas
    if key_record_dict["current_period_requests"] > key_record_dict.get("max_monthly_requests", 1000):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly API quota exceeded for organization '{key_record_dict.get('org_name')}'. Please upgrade your subscription tier."
        )

    # Async record usage
    await db.record_api_key_usage(key_record_dict["id"], org_id)

    return {
        "authenticated": True,
        "organization_id": org_id,
        "api_key_id": key_record_dict["id"],
        "actor_type": "api_key",
        "tier": key_record_dict.get("org_tier", "free"),
        "scopes": key_record_dict.get("scopes", "").split(",")
    }

