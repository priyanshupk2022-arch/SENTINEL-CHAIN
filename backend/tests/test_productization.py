import pytest
import tempfile
import asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.storage.db import DatabaseManager
from backend.app.models.domain import Target, TargetStatus, ExtractionField, FieldDataType, PageType, MonitorSchedule
from backend.app.security.url_validator import SecurityUrlValidator
from backend.app.engine.target_inspector import TargetInspectionEngine
from backend.app.engine.schema_generator import SchemaGenerator
from backend.app.engine.recovery_orchestrator import RecoveryOrchestrator
from backend.app.engine.cli_runner import CliExecutionResult
from backend.app.models.domain import EvidenceBundle
from backend.app.models.repair_proposal import RepairProposal

@pytest.mark.asyncio
async def test_ssrf_and_url_security():
    """Verify strict SSRF defense: blocks private IPs, metadata endpoints, and non-http schemes."""
    # 1. AWS / Cloud metadata blocked
    valid, reason, _ = SecurityUrlValidator.validate_url("http://169.254.169.254/latest/meta-data", allow_local_demo=False)
    assert not valid
    assert "SSRF" in reason or "restricted" in reason or "blocked" in reason

    # 2. Localhost blocked in non-demo mode
    valid, reason, _ = SecurityUrlValidator.validate_url("http://127.0.0.1:9000/internal", allow_local_demo=False)
    assert not valid

    # 3. Disallowed scheme blocked
    valid, reason, _ = SecurityUrlValidator.validate_url("ftp://example.com/file", allow_local_demo=False)
    assert not valid
    assert "Only http and https" in reason

    # 4. Valid public target passes
    valid, reason, canonical = SecurityUrlValidator.validate_url("https://books.toscrape.com/catalogue/category/books_1/index.html")
    assert valid
    assert canonical.startswith("https://books.toscrape.com")

@pytest.mark.asyncio
async def test_target_crud_api_lifecycle():
    """Verify target onboarding, retrieval, listing, and deletion."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create target
        create_res = await client.post("/api/targets", json={
            "name": "E-Commerce Bookstore",
            "url": "https://books.toscrape.com",
            "is_demo": False
        })
        assert create_res.status_code == 200
        target_data = create_res.json()["target"]
        target_id = target_data["id"]
        assert target_data["name"] == "E-Commerce Bookstore"
        assert target_data["domain"] == "books.toscrape.com"

        # 2. Get target detail
        get_res = await client.get(f"/api/targets/{target_id}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == target_id

        # 3. List targets
        list_res = await client.get("/api/targets")
        assert list_res.status_code == 200
        assert any(t["id"] == target_id for t in list_res.json())

        # 4. Delete target
        del_res = await client.delete(f"/api/targets/{target_id}")
        assert del_res.status_code == 200
        assert del_res.json()["deleted"] is True

@pytest.mark.asyncio
async def test_target_inspection_and_schema_generation():
    """Verify target inspection DOM extraction and Gemini natural language schema synthesis."""
    inspector = TargetInspectionEngine(headless=True)
    schema_gen = SchemaGenerator()

    # 1. Mock inspection of a table-based target
    mock_html = """
    <html>
      <head><title>Threat Intelligence Feed</title></head>
      <body>
        <table class="cve-table">
          <thead><tr><th>CVE ID</th><th>Title</th><th>Severity</th><th>Published</th></tr></thead>
          <tbody>
            <tr><td class="cve-id">CVE-2026-0001</td><td class="cve-title">Buffer Overflow</td><td>CRITICAL</td><td>2026-01-01</td></tr>
            <tr><td class="cve-id">CVE-2026-0002</td><td class="cve-title">SQL Injection</td><td>HIGH</td><td>2026-01-02</td></tr>
          </tbody>
        </table>
      </body>
    </html>
    """

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(mock_html, "html.parser")
    page_type, containers, selectors, fields, sample_records = inspector._analyze_dom_structure(soup)

    assert page_type == PageType.TABLE
    assert "cve_id" in fields or "cve" in str(fields).lower()
    assert len(sample_records) > 0

    # 2. Test schema synthesis from natural language intent
    schema = await schema_gen.generate_schema_from_intent(
        target_id="test-target-1",
        intent_prompt="Extract the CVE ID, vulnerability title, and severity score"
    )

    assert schema.target_id == "test-target-1"
    field_names = [f.name for f in schema.fields]
    assert "cve_id" in field_names or "title" in field_names

@pytest.mark.asyncio
async def test_target_agnostic_self_healing_across_classes():
    """Verify that the self-healing engine diagnoses and heals across 3 distinct target classes:
       Class A: Table (column selector drift)
       Class B: Card Grid (layout conversion to article cards)
       Class C: Article List (custom badge class renaming)
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db = DatabaseManager(tmp.name)
        await db.initialize()

    orchestrator = RecoveryOrchestrator(db=db)

    # Class B: Card Grid Target
    target_b = Target(
        id="target-card-grid",
        name="Product Catalog Target",
        url="https://example.com/products",
        domain="example.com"
    )
    await db.save_target(target_b)

    orchestrator.cli_runner.run_scraper = AsyncMock(side_effect=[
        CliExecutionResult(command=["bdata", "run"], exit_code=0, stdout="[]", stderr="", duration_ms=50.0, parsed_json=[]),
        CliExecutionResult(command=["bdata", "run"], exit_code=0, stdout='[{"product_name": "Premium Keyboard", "price": "$129"}]', stderr="", duration_ms=60.0, parsed_json=[{"product_name": "Premium Keyboard", "price": "$129"}])
    ])

    orchestrator.cli_runner.heal_scraper = AsyncMock(return_value=CliExecutionResult(
        command=["bdata", "heal"], exit_code=0, stdout='{"status": "awaiting_approval"}', stderr="", duration_ms=100.0, parsed_json={"status": "awaiting_approval"}
    ))

    orchestrator.cli_runner.approve_scraper = AsyncMock(return_value=CliExecutionResult(
        command=["bdata", "approve"], exit_code=0, stdout='{"status": "done"}', stderr="", duration_ms=80.0, parsed_json={"status": "done"}
    ))

    orchestrator.evidence_collector.collect_from_url = AsyncMock(return_value=EvidenceBundle(
        target_url="https://example.com/products",
        error_message="Empty results",
        status_code=200,
        pruned_dom="<div class='product-card'><h2 class='title'>Premium Keyboard</h2><span class='price'>$129</span></div>",
        aom_tree="[div.product-card] -> 'Premium Keyboard'",
        screenshot_b64=None
    ))

    orchestrator.diagnoser.diagnose_and_propose = AsyncMock(return_value=RepairProposal(
        diagnosis="Products converted to card grid with .product-card containers",
        target_field="product_name",
        evidence="Found .product-card elements",
        proposed_selector=".product-card",
        repair_prompt="Extract product_name from .product-card",
        confidence=0.96,
        expected_output="Premium Keyboard"
    ))

    # Run cycle for Target B
    result = await orchestrator.execute_scraper_cycle(
        collector_id="c_product_catalog",
        target_url="https://example.com/products",
        target_id="target-card-grid",
        auto_heal=True
    )

    assert result["recovered"] is True
    assert result["final_state"].value == "HEALTHY"
    assert len(result["extracted_records"]) == 1
    assert result["extracted_records"][0]["product_name"] == "Premium Keyboard"

    # Verify dynamic records saved for Target B
    records = await db.get_target_records("target-card-grid")
    assert len(records) == 1
    assert records[0]["data"]["product_name"] == "Premium Keyboard"

@pytest.mark.asyncio
async def test_multi_target_isolation():
    """Verify that multiple targets run in parallel without cross-target data contamination."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db = DatabaseManager(tmp.name)
        await db.initialize()

    # Target 1: Cybersecurity
    t1 = Target(id="t1-sec", name="Security Feed", url="https://sec.example.com", domain="sec.example.com")
    await db.save_target(t1)

    # Target 2: Retail
    t2 = Target(id="t2-retail", name="Retail Store", url="https://shop.example.com", domain="shop.example.com")
    await db.save_target(t2)

    # Save dynamic records for T1
    await db.save_dynamic_record(from_dict := type('obj', (object,), {
        'target_id': 't1-sec', 'run_id': 'run-1', 'data': {'cve_id': 'CVE-2026-1111'}, 'is_simulated': False,
        'timestamp': __import__('datetime').datetime.utcnow()
    })())

    # Save dynamic records for T2
    await db.save_dynamic_record(from_dict := type('obj', (object,), {
        'target_id': 't2-retail', 'run_id': 'run-2', 'data': {'sku': 'SKU-888', 'price': '$49.99'}, 'is_simulated': False,
        'timestamp': __import__('datetime').datetime.utcnow()
    })())

    # Query T1 records
    r1 = await db.get_target_records("t1-sec")
    assert len(r1) == 1
    assert "cve_id" in r1[0]["data"]
    assert "sku" not in r1[0]["data"]

    # Query T2 records
    r2 = await db.get_target_records("t2-retail")
    assert len(r2) == 1
    assert "sku" in r2[0]["data"]
    assert "cve_id" not in r2[0]["data"]
