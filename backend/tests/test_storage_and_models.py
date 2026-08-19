import pytest
import pytest_asyncio
import os
import tempfile
from backend.app.config import get_settings
from backend.app.models.domain import ScraperJobState, ThreatRecord, EvidenceBundle, TelemetryEvent
from backend.app.models.repair_proposal import RepairProposal
from backend.app.storage.db import DatabaseManager

@pytest.mark.asyncio
async def test_domain_models():
    # 1. Test RepairProposal validation
    proposal = RepairProposal(
        diagnosis="Selector .cve-row broke due to table structure change",
        target_field="cve_id",
        evidence="Found table with class exploit-list",
        proposed_selector="table.exploit-list tr td:first-child",
        repair_prompt="Extract CVE identifier from the first column of exploit-list table",
        confidence=0.95,
        expected_output="CVE-2026-1234"
    )
    assert proposal.confidence >= 0.8
    assert "CVE identifier" in proposal.repair_prompt

    # 2. Test ThreatRecord
    threat = ThreatRecord(
        cve_id="CVE-2026-8888",
        title="Zero-day Remote Code Execution in Gateway",
        severity="CRITICAL",
        url="https://exploit-db.com/exploits/8888",
        source="Exploit-DB"
    )
    assert threat.cve_id == "CVE-2026-8888"
    assert threat.severity == "CRITICAL"

    # 3. Test EvidenceBundle
    evidence = EvidenceBundle(
        target_url="http://127.0.0.1:8000/api/proxy/target",
        error_message="Selector .cve-id matched 0 elements",
        status_code=200,
        pruned_dom="<div class='vulnerability-table'></div>",
        aom_tree="[table] row (cell 'CVE-2026-8888')",
        screenshot_b64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    assert evidence.status_code == 200
    assert "vulnerability-table" in evidence.pruned_dom

@pytest.mark.asyncio
async def test_database_manager_sqlite_wal():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db = DatabaseManager(db_path=db_path)
        await db.initialize()

        # Check WAL mode
        mode = await db.get_journal_mode()
        assert mode.upper() == "WAL"

        # Insert and retrieve ThreatRecord
        threat = ThreatRecord(
            cve_id="CVE-2026-9999",
            title="Kernel memory corruption vulnerability",
            severity="HIGH",
            url="https://exploit-db.com/exploits/9999",
            source="Exploit-DB",
            raw_payload={"author": "researcher", "type": "remote"}
        )
        saved = await db.save_threat_record(threat)
        assert saved is True

        records = await db.get_recent_threats(limit=10)
        assert len(records) >= 1
        assert records[0]["cve_id"] == "CVE-2026-9999"

        # Save and retrieve TelemetryEvent
        event = TelemetryEvent(
            node_id="detector",
            status="BROKEN",
            message="Zero fields extracted from target page",
            payload={"error": "SelectorNotFound"}
        )
        await db.save_telemetry_event(event)

        events = await db.get_recent_events(limit=10)
        assert len(events) >= 1
        assert events[0]["node_id"] == "detector"
        assert events[0]["status"] == "BROKEN"

        await db.close()
    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass
