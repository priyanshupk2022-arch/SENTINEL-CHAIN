import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.chaos.chaos_proxy import ChaosMode

@pytest.mark.asyncio
async def test_health_and_proxy_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res = await client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

        # 2. Chaos proxy target endpoint (clean by default)
        res_proxy = await client.get("/api/proxy/target")
        assert res_proxy.status_code == 200
        assert "CVE-2026-4401" in res_proxy.text

        # 3. Chaos mutation endpoint
        res_mutate = await client.post("/api/chaos/mutate", json={"mode": "table_to_cards"})
        assert res_mutate.status_code == 200
        assert res_mutate.json()["current_mode"] == "table_to_cards"

        # 4. Verify mutated proxy response
        res_mutated_target = await client.get("/api/proxy/target")
        assert "exploit-card" in res_mutated_target.text

        # 5. Threats endpoint
        res_threats = await client.get("/api/threats")
        assert res_threats.status_code == 200
        assert isinstance(res_threats.json(), list)
