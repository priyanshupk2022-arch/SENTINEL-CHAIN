"""Comprehensive RBAC Permission Matrix Test Suite."""
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.database import db
from app.auth.tokens import create_access_token

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    db._init_db()

@pytest.mark.asyncio
async def test_rbac_permission_matrix():
    """Validates that each role adheres to the strict server-side authorization matrix."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        t_now = int(asyncio.get_event_loop().time() * 1000)

        # Create organization & Owner
        owner_reg = await ac.post("/api/auth/register", json={
            "full_name": "Org Owner",
            "organization_name": "RBAC Test Corp",
            "email": f"owner_{t_now}@rbac.com",
            "password": "OwnerPassword2026!"
        })
        assert owner_reg.status_code == 200
        org_id = owner_reg.json()["active_organization_id"]
        owner_id = owner_reg.json()["user"]["id"]

        # Helper to create tokens with specific role overrides
        def _get_token(user_id: str, email: str, role: str) -> str:
            return create_access_token(user_id=user_id, email=email, role=role, organization_id=org_id)

        viewer_token = _get_token("user-viewer-123", "viewer@rbac.com", "VIEWER")
        auditor_token = _get_token("user-auditor-123", "auditor@rbac.com", "AUDITOR")
        sec_lead_token = _get_token("user-seclead-123", "seclead@rbac.com", "SECURITY_LEAD")
        admin_token = _get_token("user-admin-123", "admin@rbac.com", "ADMIN")
        owner_token = owner_reg.json()["access_token"]

        # 1. Test Policy Mutation (`POST /api/policies/pol_prompt_inj`)
        # VIEWER & AUDITOR must be FORBIDDEN (403)
        res_v = await ac.post("/api/policies/pol_prompt_inj", json={"enabled": True}, headers={"Authorization": f"Bearer {viewer_token}"})
        assert res_v.status_code == 403

        res_a = await ac.post("/api/policies/pol_prompt_inj", json={"enabled": True}, headers={"Authorization": f"Bearer {auditor_token}"})
        assert res_a.status_code == 403

        # SECURITY_LEAD, ADMIN, OWNER must SUCCEED (200)
        res_sl = await ac.post("/api/policies/pol_prompt_inj", json={"enabled": True, "action": "BLOCK"}, headers={"Authorization": f"Bearer {sec_lead_token}"})
        assert res_sl.status_code == 200

        # 2. Test API Key Creation (`POST /api/api-keys`)
        # VIEWER & AUDITOR cannot create API Keys
        k_v = await ac.post("/api/api-keys", json={"name": "Viewer Key"}, headers={"Authorization": f"Bearer {viewer_token}"})
        assert k_v.status_code == 403

        k_a = await ac.post("/api/api-keys", json={"name": "Auditor Key"}, headers={"Authorization": f"Bearer {auditor_token}"})
        assert k_a.status_code == 403

        # 3. Test Team Member Invitation (`POST /api/invitations`)
        # VIEWER & AUDITOR cannot invite members
        inv_v = await ac.post("/api/invitations", json={"email": "newbie@rbac.com", "role": "viewer"}, headers={"Authorization": f"Bearer {viewer_token}"})
        assert inv_v.status_code == 403

        inv_owner = await ac.post("/api/invitations", json={"email": "newbie@rbac.com", "role": "viewer"}, headers={"Authorization": f"Bearer {owner_token}"})
        assert inv_owner.status_code == 200

        # 4. Test Audit Log Reading (`GET /api/logs`)
        # All roles (including VIEWER & AUDITOR) can read audit logs
        log_v = await ac.get("/api/logs", headers={"Authorization": f"Bearer {viewer_token}"})
        assert log_v.status_code == 200

        log_a = await ac.get("/api/logs", headers={"Authorization": f"Bearer {auditor_token}"})
        assert log_a.status_code == 200
