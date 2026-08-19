"""Server-Side RBAC Guard Dependencies."""
from typing import List, Callable, Any, Dict
from fastapi import Depends, HTTPException, status

from app.rbac.roles import Permission, has_permission

def require_permission(permission: Permission):
    """FastAPI dependency enforcing specific RBAC permission."""
    def _permission_guard(auth_context: Dict[str, Any]) -> Dict[str, Any]:
        role = auth_context.get("role", "VIEWER")
        if not has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Role '{role}' lacks required permission '{permission.value}'."
            )
        return auth_context
    return _permission_guard
