import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from backend.app.main import app
from backend.app.storage.db import DatabaseManager
from backend.app.config import get_settings
from backend.app.engine.queue_manager import ScraperQueueManager
from backend.app.chaos.chaos_proxy import ChaosProxyManager, ChaosMode
from backend.app.engine.cli_runner import CliExecutionResult
from backend.app.api.routes_scrapers import orchestrator

@pytest.mark.asyncio
async def test_concurrent_chaos_and_scraper_stress():
    settings = get_settings()
    db = DatabaseManager(settings.DATABASE_PATH)
    await db.initialize()

    queue_mgr = ScraperQueueManager()
    await queue_mgr.start()

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Stress test rapid chaos mode switching (20 rapid transitions)
            modes = [ChaosMode.CLEAN, ChaosMode.CLASS_RENAMED, ChaosMode.TABLE_TO_CARDS, ChaosMode.DEEP_NESTING]
            for i in range(20):
                target_mode = modes[i % len(modes)]
                res = await client.post("/api/chaos/mutate", json={"mode": target_mode.value})
                assert res.status_code == 200
                assert res.json()["current_mode"] == target_mode.value

            # 2. Concurrency stress: 10 simultaneous scraper requests
            with patch.object(orchestrator.cli_runner, "run_scraper", new_callable=AsyncMock) as mock_run:
                mock_run.return_value = CliExecutionResult(
                    command=["bdata", "run"],
                    exit_code=0,
                    stdout='[{"cve_id": "CVE-2026-9999", "title": "Stress Test Vuln", "severity": "HIGH"}]',
                    stderr="",
                    duration_ms=15.0,
                    parsed_json=[{"cve_id": "CVE-2026-9999", "title": "Stress Test Vuln", "severity": "HIGH"}]
                )

                async def trigger_one(idx):
                    return await client.post("/api/scraper/trigger", json={
                        "collector_id": f"c_stress_{idx}",
                        "target_url": "http://test/api/proxy/target",
                        "auto_heal": False
                    })

                tasks = [trigger_one(i) for i in range(10)]
                responses = await asyncio.gather(*tasks)

                for res in responses:
                    assert res.status_code == 200
                    assert res.json()["status"] == "success"
                    assert res.json()["result"]["final_state"] == "HEALTHY"

            # 3. Verify SQLite DB consistency under concurrent writes
            threats = await db.get_recent_threats(limit=50)
            assert len(threats) >= 1
    finally:
        await queue_mgr.stop()
        await db.close()
