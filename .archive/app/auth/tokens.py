"""JWT Access & Refresh Token Engine with Rotation, Expiry and Revocation."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
import jwt
from fastapi import HTTPException, status

from app.config import settings

# In-memory revocation set for rotated/revoked refresh tokens.
# NOTE: replaced with persistent SQLite-backed store at app.security.token_revocation.
# This module imports and re-exports the persistent implementation so existing
# `from app.auth.tokens import _REVOKED_TOKENS, revoke_token, decode_token` callers
# continue to work and the revocation state survives restarts.
from app.security.token_revocation import (
    _REVOKED_TOKENS,
    revoke_token,
    is_revoked,
    persist_revocation,
)

from app.models.database import DEFAULT_DEFAULT_ORG_ID

def create_access_token(
    user_id: str,
    email: str,
    role: str,
    organization_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Generates signed short-lived JWT access token with proper issuer/audience."""
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "org_id": organization_id or DEFAULT_DEFAULT_ORG_ID,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "jti": secrets.token_hex(16)
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    user_id: str,
    organization_id: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Generates signed long-lived refresh token."""
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    jti = secrets.token_hex(16)
    payload = {
        "sub": user_id,
        "org_id": organization_id,
        "type": "refresh",
        "jti": jti,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """Decodes and validates token claims and checks revocation (with rotation)."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
            options={"verify_iss": True, "verify_aud": True}
        )
        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type: expected {expected_type} token."
            )
        jti = payload.get("jti")
        if jti and is_revoked(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked. Please log in again."
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please log in again."
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}"
        )

def revoke_token(token: str) -> None:
    """Adds token JTI to persistent revocation blacklist (survives restarts)."""
    from app.security.token_revocation import revoke_token as _persist_revoke
    _persist_revoke(token)

def generate_opaque_token() -> Tuple[str, str]:
    """
    Generates opaque token for password reset or email verification.
    Returns (raw_plaintext_token, sha256_hash).
    """
    raw = secrets.token_urlsafe(32)
    hashed = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    return raw, hashed
