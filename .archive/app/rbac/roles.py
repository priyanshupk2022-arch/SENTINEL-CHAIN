"""Role-Based Access Control (RBAC) Permissions and Hierarchy."""
from enum import Enum
from typing import Set, Dict, List

class Role(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    SECURITY_LEAD = "SECURITY_LEAD"
    AUDITOR = "AUDITOR"
    VIEWER = "VIEWER"

class Permission(str, Enum):
    # Billing & Org Lifecycle
    BILLING_READ = "billing:read"
    BILLING_WRITE = "billing:write"
    ORG_DELETE = "org:delete"
    ORG_UPDATE = "org:update"
    ORG_MANAGE_MEMBERS = "org:manage_members"

    # API Keys & Auth
    API_KEYS_READ = "api_keys:read"
    API_KEYS_WRITE = "api_keys:write"
    API_KEYS_ROTATE = "api_keys:rotate"

    # Policies & Security Governance
    POLICIES_READ = "policies:read"
    POLICIES_WRITE = "policies:write"

    # Audit & Reporting
    AUDIT_READ = "audit:read"
    REPORTS_EXPORT = "reports:export"

    # Forensics & Proxy Scans
    SCANS_READ = "scans:read"
    SCANS_EXECUTE = "scans:execute"

    # Webhooks & Integrations
    WEBHOOKS_READ = "webhooks:read"
    WEBHOOKS_WRITE = "webhooks:write"

# Permissions matrix by Role
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.OWNER: {
        Permission.BILLING_READ, Permission.BILLING_WRITE,
        Permission.ORG_DELETE, Permission.ORG_UPDATE, Permission.ORG_MANAGE_MEMBERS,
        Permission.API_KEYS_READ, Permission.API_KEYS_WRITE, Permission.API_KEYS_ROTATE,
        Permission.POLICIES_READ, Permission.POLICIES_WRITE,
        Permission.AUDIT_READ, Permission.REPORTS_EXPORT,
        Permission.SCANS_READ, Permission.SCANS_EXECUTE,
        Permission.WEBHOOKS_READ, Permission.WEBHOOKS_WRITE
    },
    Role.ADMIN: {
        Permission.BILLING_READ,
        Permission.ORG_UPDATE, Permission.ORG_MANAGE_MEMBERS,
        Permission.API_KEYS_READ, Permission.API_KEYS_WRITE, Permission.API_KEYS_ROTATE,
        Permission.POLICIES_READ, Permission.POLICIES_WRITE,
        Permission.AUDIT_READ, Permission.REPORTS_EXPORT,
        Permission.SCANS_READ, Permission.SCANS_EXECUTE,
        Permission.WEBHOOKS_READ, Permission.WEBHOOKS_WRITE
    },
    Role.SECURITY_LEAD: {
        Permission.POLICIES_READ, Permission.POLICIES_WRITE,
        Permission.AUDIT_READ, Permission.REPORTS_EXPORT,
        Permission.SCANS_READ, Permission.SCANS_EXECUTE,
        Permission.WEBHOOKS_READ, Permission.WEBHOOKS_WRITE
    },
    Role.AUDITOR: {
        Permission.AUDIT_READ, Permission.REPORTS_EXPORT,
        Permission.POLICIES_READ, Permission.SCANS_READ
    },
    Role.VIEWER: {
        Permission.AUDIT_READ,
        Permission.POLICIES_READ,
        Permission.SCANS_READ
    }
}

def has_permission(role_str: str, permission: Permission) -> bool:
    """Checks if given role possesses the required permission."""
    try:
        role_enum = Role(role_str.upper())
        return permission in ROLE_PERMISSIONS.get(role_enum, set())
    except (ValueError, KeyError):
        # Default fallback for case-insensitivity
        for r, perms in ROLE_PERMISSIONS.items():
            if r.value.lower() == role_str.lower():
                return permission in perms
        return False
