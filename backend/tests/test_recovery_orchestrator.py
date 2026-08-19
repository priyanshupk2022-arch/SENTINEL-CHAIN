import pytest
import os
import tempfile
from unittest.mock import AsyncMock, patch
from backend.app.storage.db import DatabaseManager
from backend.app.models.domain import ScraperJobState, EvidenceBundle
from backend.app.models.repair_proposal import RepairProposal
from backend.app.engine.cli_runner import CliExecutionResult
from backend.app.engine.recovery_orchestrator import RecoveryOrchestrator

@pytest.mark.asyncio
async def test_recovery_orchestrator_full_loop():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db = DatabaseManager(db_path=db_path)
        await db.initialize()

        orchestrator = RecoveryOrchestrator(db=db)

        # Mock CLI runner, evidence collector, diagnoser
        # 1. First run returns empty (simulating failure)
        # 2. Heal returns awaiting_approval
        # 3. Approve returns success
        # 4. Re-run returns populated CVE data
        orchestrator.cli_runner.run_scraper = AsyncMock(side_effect=[
            CliExecutionResult(
                command=["bdata", "run"],
                exit_code=0,
                stdout="[]",
                stderr="",
                duration_ms=100.0,
                parsed_json=[]
            ),
            CliExecutionResult(
                command=["bdata", "run"],
                exit_code=0,
                stdout='[{"cve_id": "CVE-2026-4401", "title": "OpenSSL ASN.1 Parsing Overflow", "severity": "CRITICAL"}]',
                stderr="",
                duration_ms=100.0,
                parsed_json=[{"cve_id": "CVE-2026-4401", "title": "OpenSSL ASN.1 Parsing Overflow", "severity": "CRITICAL"}]
            )
        ])

        orchestrator.cli_runner.heal_scraper = AsyncMock(return_value=CliExecutionResult(
            command=["bdata", "heal"],
            exit_code=0,
            stdout='{"status": "awaiting_approval", "preview_result": [{"cve_id": "CVE-2026-4401"}]}',
            stderr="",
            duration_ms=250.0,
            parsed_json={"status": "awaiting_approval"}
        ))

        orchestrator.cli_runner.approve_scraper = AsyncMock(return_value=CliExecutionResult(
            command=["bdata", "approve"],
            exit_code=0,
            stdout='{"status": "done"}',
            stderr="",
            duration_ms=150.0,
            parsed_json={"status": "done"}
        ))

        orchestrator.evidence_collector.collect_from_url = AsyncMock(return_value=EvidenceBundle(
            target_url="http://127.0.0.1:8000/api/proxy/target",
            error_message="Empty results",
            status_code=200,
            pruned_dom="<div class='vulnerability-badge'>CVE-2026-4401</div>",
            aom_tree="[span] (label='CVE-2026-4401')",
            screenshot_b64=None
        ))

        orchestrator.diagnoser.diagnose_and_propose = AsyncMock(return_value=RepairProposal(
            diagnosis="Class cve-id changed to vulnerability-badge",
            target_field="cve_id",
            evidence="Found vulnerability-badge element",
            proposed_selector=".vulnerability-badge",
            repair_prompt="Extract CVE from .vulnerability-badge",
            confidence=0.95,
            expected_output="CVE-2026-4401"
        ))

        # Execute recovery cycle
        result = await orchestrator.execute_scraper_cycle(
            collector_id="c_sentinel_cve_threats",
            target_url="http://127.0.0.1:8000/api/proxy/target",
            auto_heal=True
        )

        assert result["final_state"] == ScraperJobState.HEALTHY
        assert result["recovered"] is True
        assert len(result["extracted_records"]) == 1
        assert result["extracted_records"][0]["cve_id"] == "CVE-2026-4401"

        # Verify threat record saved in DB
        threats = await db.get_recent_threats(limit=10)
        assert len(threats) >= 1
        assert threats[0]["cve_id"] == "CVE-2026-4401"

        await db.close()
    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass
