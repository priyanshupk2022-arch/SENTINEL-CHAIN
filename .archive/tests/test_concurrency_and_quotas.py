"""Concurrency & High-Throughput Stress Test Suite."""
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.database import db

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    db._init_db()

@pytest.mark.asyncio
async def test_concurrent_api_key_and_proxy_traffic():
    """Validates that concurrent requests under load do not corrupt state or cause race conditions."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        t_now = int(asyncio.get_event_loop().time() * 1000)

        # 1. Register test tenant
        reg = await ac.post("/api/auth/register", json={
            "full_name": "Concurrent Load Tester",
            "organization_name": "Concurrency Corp",
            "email": f"load_{t_now}@load.com",
            "password": "Password123!"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create API key
        key_res = await ac.post("/api/api-keys", json={"name": "Concurrent Ingress Key"}, headers=headers)
        raw_key = key_res.json()["raw_api_key"]
        proxy_headers = {"Authorization": f"Bearer {raw_key}"}

        # 3. Fire 50 concurrent proxy requests
        async def send_proxy_request(idx: int):
            return await ac.post("/v1/chat/completions", json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": f"Request #{idx}: Security analysis query"}]
            }, headers=proxy_headers)

        tasks = [send_proxy_request(i) for i in range(50)]
        results = await asyncio.gather(*tasks)

        # All 50 concurrent requests must succeed (HTTP 200) without race errors
        assert len(results) == 50
        for r in results:
            assert r.status_code == 200

        # 4. Check that audit logs recorded all 50 events accurately
        stats = await ac.get("/api/stats", headers=headers)
        assert stats.status_code == 200
        assert stats.json()["total_requests"] >= 50
