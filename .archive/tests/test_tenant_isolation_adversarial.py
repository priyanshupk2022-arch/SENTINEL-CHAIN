"""Comprehensive Tenant-Isolation Adversarial Attack Campaign."""
import asyncio
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.database import db

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    db._init_db()

@pytest.mark.asyncio
async def test_full_cross_tenant_isolation_campaign():
    """Aggressively attempts cross-tenant IDOR, data leakage, and unauthorized mutations."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        t_now = int(asyncio.get_event_loop().time() * 1000)

        # 1. Register Tenant Alpha (Victim)
        alpha_reg = await ac.post("/api/auth/register", json={
            "full_name": "Alice CISO",
            "organization_name": "Alpha Corp",
            "email": f"alice_{t_now}@alpha.com",
            "password": "AlphaSecurePassword2026!"
        })
        assert alpha_reg.status_code == 200
        alpha_token = alpha_reg.json()["access_token"]
        alpha_org_id = alpha_reg.json()["active_organization_id"]
        alpha_headers = {"Authorization": f"Bearer {alpha_token}"}

        # Alpha creates API Key
        alpha_key_res = await ac.post("/api/api-keys", json={"name": "Alpha Live Key"}, headers=alpha_headers)
        assert alpha_key_res.status_code == 200
        alpha_key_id = alpha_key_res.json()["id"]
        alpha_raw_key = alpha_key_res.json()["raw_api_key"]

        # Alpha creates Workspace
        alpha_ws_res = await ac.post("/api/workspaces", json={"name": "Alpha Prod Workspace", "slug": "alpha-prod"}, headers=alpha_headers)
        assert alpha_ws_res.status_code == 200
        alpha_ws_id = alpha_ws_res.json()["id"]

        # Alpha creates Webhook
        alpha_wh_res = await ac.post("/api/webhooks", json={"url": "https://siem.alpha.com/events"}, headers=alpha_headers)
        assert alpha_wh_res.status_code == 200
        alpha_wh_id = alpha_wh_res.json()["id"]

        # Alpha sends proxy request to create an audit event
        p_res = await ac.post("/v1/chat/completions", json={
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Alpha confidential prompt"}]
        }, headers={"Authorization": f"Bearer {alpha_raw_key}"})
        assert p_res.status_code == 200

        # 2. Register Tenant Beta (Attacker)
        beta_reg = await ac.post("/api/auth/register", json={
            "full_name": "Bob Attacker",
            "organization_name": "Beta Evil Corp",
            "email": f"bob_{t_now}@beta.com",
            "password": "BetaSecurePassword2026!"
        })
        assert beta_reg.status_code == 200
        beta_token = beta_reg.json()["access_token"]
        beta_org_id = beta_reg.json()["active_organization_id"]
        beta_headers = {"Authorization": f"Bearer {beta_token}"}

        # --- ATTACK 1: Beta attempts to read Alpha's audit logs ---
        attack_logs = await ac.get(f"/api/logs?org_id={alpha_org_id}", headers=beta_headers)
        assert attack_logs.status_code == 403
        assert "Access denied" in attack_logs.json()["detail"]


        # --- ATTACK 2: Beta attempts to revoke Alpha's API Key ---
        attack_del_key = await ac.delete(f"/api/api-keys/{alpha_key_id}", headers=beta_headers)
        assert attack_del_key.status_code == 200

        # Verify Alpha key remains 100% active and unrevoked
        alpha_keys = await ac.get("/api/api-keys", headers=alpha_headers)
        matching = next((k for k in alpha_keys.json() if k["id"] == alpha_key_id), None)
        assert matching is not None
        assert matching["is_active"] is True

        # --- ATTACK 3: Beta attempts to delete Alpha's workspace ---
        attack_del_ws = await ac.delete(f"/api/workspaces/{alpha_ws_id}", headers=beta_headers)
        assert attack_del_ws.status_code == 200

        # Verify Alpha workspace is intact
        alpha_ws_list = await ac.get("/api/workspaces", headers=alpha_headers)
        assert any(w["id"] == alpha_ws_id for w in alpha_ws_list.json())

        # --- ATTACK 4: Beta attempts to use Alpha's API Key to access Beta context ---
        # The key resolves to Alpha's org, never Beta
        from app.security.api_key import hash_key
        key_context = await db.get_api_key_by_hash(hash_key(alpha_raw_key))
        assert key_context is not None
        assert key_context["organization_id"] == alpha_org_id
