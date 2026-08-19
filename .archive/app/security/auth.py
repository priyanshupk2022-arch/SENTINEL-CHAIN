"""JWT Authentication, Password Hashing & RBAC Enforcement Dependencies."""
import hashlib
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

import jwt
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.models.database import db, DEFAULT_DEFAULT_ORG_ID
from app.models.schemas import TokenData, UserOut
from app.auth.hasher import hash_password, verify_password

security_bearer = HTTPBearer(auto_error=False)

# ============================================================================
# JWT Token Generation & Verification (Authoritative Engine Integration)
# ============================================================================

from app.auth.tokens import create_access_token, create_refresh_token, decode_token

def decode_access_token(token: str) -> TokenData:
    """Decodes and validates an access JWT token with full claim verification."""
    payload = decode_token(token, expected_type="access")
    user_id: str = payload.get("sub")
    email: str = payload.get("email")
    role: str = str(payload.get("role", "member"))

    org_id: Optional[str] = payload.get("org_id")

    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims."
        )
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing tenant context."
        )
    return TokenData(user_id=user_id, email=email, role=role, organization_id=org_id)


# ============================================================================
# FastAPI Auth & RBAC Dependencies
# ============================================================================

ROLE_HIERARCHY: Dict[str, int] = {
    "OWNER": 5,
    "ADMIN": 4,
    "SECURITY_LEAD": 3,
    "AUDITOR": 2,
    "VIEWER": 1,
    "MEMBER": 1,
}

async def get_current_user_optional(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> Optional[Dict[str, Any]]:
    """Resolves authenticated user from Bearer header or session cookie without raising error."""
    token = None
    if auth and auth.credentials:
        token = auth.credentials
    elif "aegis_session" in request.cookies:
        token = request.cookies.get("aegis_session")

    if not token:
        return None

    try:
        token_data = decode_access_token(token)
        user = await db.get_user_by_id(token_data.user_id)
        if not user and token_data.user_id:
            user = {
                "id": token_data.user_id,
                "email": token_data.email,
                "role": token_data.role,
                "is_active": True,
                "active_token_org_id": token_data.organization_id
            }
        elif user:
            user = dict(user)
            user["role"] = token_data.role or user.get("role", "MEMBER")
            user["active_token_org_id"] = token_data.organization_id
        return user
    except Exception:
        return None

async def get_current_user(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> Dict[str, Any]:
    """Strictly enforces valid user authentication."""
    user = await get_current_user_optional(request, auth)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token or session cookie."
        )
    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been suspended."
        )
    return user

async def get_current_active_org(
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Resolves active organization context for the authenticated user."""
    requested_org_id = (
        request.headers.get("X-Organization-ID") or
        request.query_params.get("org_id") or
        request.cookies.get("aegis_active_org")
    )

    user_orgs = await db.get_user_organizations(user["id"])
    
    if not user_orgs:
        token_org_id = user.get("active_token_org_id")
        if token_org_id:
            org = await db.get_organization(token_org_id)
            if org:
                return org
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no organization memberships."
        )

    if requested_org_id:
        for org in user_orgs:
            if org["id"] == requested_org_id:
                return org
        token_org_id = user.get("active_token_org_id")
        if token_org_id and token_org_id == requested_org_id:
            org = await db.get_organization(token_org_id)
            if org:
                return org
        # Explicitly DENY unauthorized / manipulated tenant selection
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Caller does not have authorized membership in requested organization '{requested_org_id}'."
        )

    token_org_id = user.get("active_token_org_id")
    if token_org_id:
        for org in user_orgs:
            if org["id"] == token_org_id:
                return org

    return user_orgs[0]



def require_role(allowed_roles: List[str]):
    """RBAC Guard decorator/dependency enforcing user roles with role hierarchy."""
    async def _role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = str(user.get("role", "MEMBER")).upper()
        allowed_upper = [r.upper() for r in allowed_roles]
        
        # 1. Exact match or OWNER superuser bypass
        if user_role == "OWNER" or user_role in allowed_upper:
            return user

        # 2. Hierarchy comparison: if user rank is >= required minimum rank and OWNER is not explicitly exclusive
        user_rank = ROLE_HIERARCHY.get(user_role, 0)
        min_allowed_rank = min((ROLE_HIERARCHY.get(r, 99) for r in allowed_upper), default=99)
        if user_rank >= min_allowed_rank and allowed_upper != ["OWNER"]:
            return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Requires one of roles {allowed_roles}, but caller has role '{user_role}'."
        )
    return _role_checker

