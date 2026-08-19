import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from backend.app.main import app
from backend.app.storage.db import DatabaseManager
from backend.app.config import get_settings
from backend.app.engine.queue_manager import ScraperQueueManager
from backend.app.chaos.chaos_proxy import ChaosMode
from backend.app.engine.cli_runner import CliExecutionResult
from backend.app.models.domain import ScraperJobState, EvidenceBundle
from backend.app.models.repair_proposal import RepairProposal

@pytest.mark.asyncio
async def test_full_e2e_self_healing_lifecycle():
    settings = get_settings()
    db = DatabaseManager(settings.DATABASE_PATH)
    await db.initialize()

    queue_mgr = ScraperQueueManager()
    await queue_mgr.start()

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Health check
            res_health = await client.get("/api/health")
            assert res_health.status_code == 200
            assert res_health.json()["status"] == "healthy"

            # 2. Mutate to class_renamed
            res_mutate = await client.post("/api/chaos/mutate", json={"mode": "class_renamed"})
            assert res_mutate.status_code == 200
            assert res_mutate.json()["current_mode"] == "class_renamed"

            # 3. Verify target markup is mutated
            res_target = await client.get("/api/proxy/target")
            assert res_target.status_code == 200
            assert "vulnerability-badge" in res_target.text

            # 4. Trigger Scraper cycle with auto_heal
            with patch("backend.app.api.routes_scrapers.orchestrator.cli_runner.run_scraper", new_callable=AsyncMock) as mock_run, \
                 patch("backend.app.api.routes_scrapers.orchestrator.cli_runner.heal_scraper", new_callable=AsyncMock) as mock_heal, \
                 patch("backend.app.api.routes_scrapers.orchestrator.cli_runner.approve_scraper", new_callable=AsyncMock) as mock_approve, \
                 patch("backend.app.api.routes_scrapers.orchestrator.evidence_collector.collect_from_url", new_callable=AsyncMock) as mock_evidence:

                # Mock first run failing (empty) and second run returning extracted CVE records
                mock_run.side_effect = [
                    CliExecutionResult(
                        command=["bdata", "run"],
                        exit_code=0,
                        stdout="[]",
                        stderr="",
                        duration_ms=80.0,
                        parsed_json=[]
                    ),
                    CliExecutionResult(
                        command=["bdata", "run"],
                        exit_code=0,
                        stdout='[{"cve_id": "CVE-2026-4401", "title": "OpenSSL ASN.1 Parsing Overflow", "severity": "CRITICAL", "source": "Exploit-DB"}]',
                        stderr="",
                        duration_ms=90.0,
                        parsed_json=[{"cve_id": "CVE-2026-4401", "title": "OpenSSL ASN.1 Parsing Overflow", "severity": "CRITICAL", "source": "Exploit-DB"}]
                    )
                ]

                mock_heal.return_value = CliExecutionResult(
                    command=["bdata", "heal"],
                    exit_code=0,
                    stdout='{"status": "awaiting_approval", "preview": [{"cve_id": "CVE-2026-4401"}]}',
                    stderr="",
                    duration_ms=200.0,
                    parsed_json={"status": "awaiting_approval"}
                )

                mock_approve.return_value = CliExecutionResult(
                    command=["bdata", "approve"],
                    exit_code=0,
                    stdout='{"status": "done"}',
                    stderr="",
                    duration_ms=100.0,
                    parsed_json={"status": "done"}
                )

                mock_evidence.return_value = EvidenceBundle(
                    target_url="http://test/api/proxy/target",
                    error_message="Empty results returned",
                    status_code=200,
                    pruned_dom="<table class='threat-data-grid'><tr><td class='vulnerability-badge'>CVE-2026-4401</td></tr></table>",
                    aom_tree="[table] -> [td.vulnerability-badge] -> 'CVE-2026-4401'",
                    screenshot_b64=None
                )

                # Trigger API
                res_trigger = await client.post("/api/scraper/trigger", json={
                    "collector_id": "c_sentinel_cve_threats",
                    "target_url": "http://test/api/proxy/target",
                    "auto_heal": True
                })

                assert res_trigger.status_code == 200
                data = res_trigger.json()
                assert data["status"] == "success"
                assert data["result"]["recovered"] is True
                assert data["result"]["final_state"] == "HEALTHY"
                assert len(data["result"]["extracted_records"]) == 1
                assert data["result"]["extracted_records"][0]["cve_id"] == "CVE-2026-4401"

            # 5. Verify Threat intelligence records in GET /api/threats
            res_threats = await client.get("/api/threats")
            assert res_threats.status_code == 200
            threats_list = res_threats.json()
            assert len(threats_list) >= 1
            assert any(t["cve_id"] == "CVE-2026-4401" for t in threats_list)
    finally:
        await queue_mgr.stop()
        await db.close()
