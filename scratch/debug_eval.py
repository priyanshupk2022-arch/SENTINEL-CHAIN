import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.engine.evidence_collector import EvidenceCollector
from backend.app.engine.diagnoser import GeminiAIDiagnoser
from backend.app.engine.validator import RepairValidator


async def main():
    collector = EvidenceCollector()
    diagnoser = GeminiAIDiagnoser(api_key=None)  # force heuristic fallback for determinism
    validator = RepairValidator()

    dataset_path = os.path.join(os.path.dirname(__file__), "..", "eval", "golden_dataset.jsonl")
    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]

    edge_failures = []
    adv_leaks = []

    for case in cases:
        evidence = await collector.collect_from_html(
            target_url="http://benchmark-target.local",
            html_content=case["html"],
            error_message="Selector failed on benchmark target",
        )
        proposal = await diagnoser.diagnose_and_propose(evidence, target_field=case["target_field"])

        if case["is_adversarial"]:
            adv_proposal = proposal.model_copy(update={
                "repair_prompt": f"Extract {case['expected_cve']}"
            })
            is_valid, reason = validator.validate(adv_proposal, evidence.pruned_dom)
            if is_valid:
                adv_leaks.append({
                    "id": case.get("id", "?"),
                    "target_field": case["target_field"],
                    "selector": proposal.proposed_selector,
                    "confidence": proposal.confidence,
                    "source": proposal.source_type,
                    "reason": reason,
                })
        else:
            is_valid, reason = validator.validate(proposal, evidence.pruned_dom)
            if not is_valid:
                edge_failures.append({
                    "id": case.get("id", "?"),
                    "type": case["type"],
                    "target_field": case["target_field"],
                    "selector": proposal.proposed_selector,
                    "confidence": proposal.confidence,
                    "reason": reason,
                })

    print("=" * 60)
    print(f"EDGE FAILURES: {len(edge_failures)}")
    for f_ in edge_failures:
        print(json.dumps(f_, indent=1))
    print("=" * 60)
    print(f"ADVERSARIAL LEAKS: {len(adv_leaks)}")
    for a in adv_leaks:
        print(json.dumps(a, indent=1))


if __name__ == "__main__":
    asyncio.run(main())
