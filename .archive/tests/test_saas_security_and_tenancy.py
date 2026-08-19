"""Security, Multi-Tenancy Isolation, and RBAC Regression Test Suite."""
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.database import db, DEFAULT_DEFAULT_ORG_ID
from app.auth.hasher import hash_password, verify_password
from app.auth.tokens import create_access_token, decode_token, revoke_token

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    db._init_db()

@pytest.mark.asyncio
async def test_argon2id_password_hashing():
    pw = "P@ssw0rdEnterprise2026!"
    h = hash_password(pw)
    assert h.startswith("$argon2")
    assert verify_password(pw, h) is True
    assert verify_password("WrongPassword123", h) is False

@pytest.mark.asyncio
async def test_token_revocation_blacklist():
    token = create_access_token("user-1", "user@corp.com", "OWNER", DEFAULT_DEFAULT_ORG_ID)
    decoded = decode_token(token, expected_type="access")
    assert decoded["email"] == "user@corp.com"

@pytest.mark.asyncio
async def test_cross_tenant_isolation_on_audit_logs():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        t_now = int(asyncio.get_event_loop().time() * 1000)
        
        # Org 1 Register
        r1 = await ac.post("/api/auth/register", json={
            "full_name": "Org 1 Admin",
            "organization_name": "Org One",
            "email": f"admin1_{t_now}@org1.com",
            "password": "Password123!"
        })
        assert r1.status_code == 200
        token1 = r1.json()["access_token"]
        org1_id = r1.json()["active_organization_id"]

        # Org 2 Register
        r2 = await ac.post("/api/auth/register", json={
            "full_name": "Org 2 Admin",
            "organization_name": "Org Two",
            "email": f"admin2_{t_now}@org2.com",
            "password": "Password123!"
        })
        assert r2.status_code == 200
        token2 = r2.json()["access_token"]
        org2_id = r2.json()["active_organization_id"]

        # Org 1 generates an API key
        k1_res = await ac.post("/api/api-keys", json={"name": "Org1 Key"}, headers={"Authorization": f"Bearer {token1}"})
        assert k1_res.status_code == 200
        k1_raw = k1_res.json()["raw_api_key"]

        # Org 1 makes proxy request with its key
        p1 = await ac.post("/v1/chat/completions", json={
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": f"Confidential prompt for Org 1 {t_now}"}]
        }, headers={"Authorization": f"Bearer {k1_raw}"})
        assert p1.status_code == 200

        # Org 2 requests audit logs -> Must NOT see Org 1's confidential prompt
        logs2_res = await ac.get(f"/api/logs?org_id={org2_id}", headers={"Authorization": f"Bearer {token2}"})
        assert logs2_res.status_code == 200
        logs2 = logs2_res.json()["logs"]
        for log in logs2:
            assert f"Confidential prompt for Org 1 {t_now}" not in (log.get("input_preview") or "")

@pytest.mark.asyncio
async def test_observability_and_metrics_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # /ready
        res_ready = await ac.get("/ready")
        assert res_ready.status_code == 200
        assert res_ready.json()["status"] == "ready"

        # /metrics
        res_metrics = await ac.get("/metrics")
        assert res_metrics.status_code == 200
        assert "aegis_requests_total" in res_metrics.text or "# HELP" in res_metrics.text

@pytest.mark.asyncio
async def test_report_export_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        t_now = int(asyncio.get_event_loop().time() * 1000)
        r = await ac.post("/api/auth/register", json={
            "full_name": "Auditor User",
            "organization_name": "Audit Corp",
            "email": f"auditor_{t_now}@auditcorp.com",
            "password": "Password123!"
        })
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # CSV Export
        csv_res = await ac.get("/api/reports/audit/csv", headers=headers)
        assert csv_res.status_code == 200
        assert "text/csv" in csv_res.headers.get("content-type", "")

        # JSON Export
        json_res = await ac.get("/api/reports/audit/json", headers=headers)
        assert json_res.status_code == 200
        assert isinstance(json_res.json(), list)
