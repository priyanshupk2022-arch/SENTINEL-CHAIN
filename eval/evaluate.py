import asyncio
import json
import time
import os
import sys

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.models.domain import EvidenceBundle
from backend.app.models.repair_proposal import RepairProposal
from backend.app.engine.evidence_collector import EvidenceCollector
from backend.app.engine.diagnoser import GeminiAIDiagnoser
from backend.app.engine.validator import RepairValidator

async def run_evaluation():
    print("=" * 60)
    print("SENTINEL-CHAIN: 100-CASE GOLDEN DATASET BENCHMARK HARNESS")
    print("=" * 60)

    collector = EvidenceCollector()
    diagnoser = GeminiAIDiagnoser()
    validator = RepairValidator()

    dataset_path = os.path.join(os.path.dirname(__file__), "golden_dataset.jsonl")
    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(cases)} test cases from {dataset_path}\n")

    happy_passed = 0
    edge_passed = 0
    adv_blocked = 0
    total_latencies = []

    for idx, case in enumerate(cases):
        start_t = time.time()
        # 1. Harvest evidence
        evidence: EvidenceBundle = await collector.collect_from_html(
            target_url="http://benchmark-target.local",
            html_content=case["html"],
            error_message="Selector failed on benchmark target"
        )

        # 2. Diagnoser proposal
        proposal: RepairProposal = await diagnoser.diagnose_and_propose(
            evidence,
            target_field=case["target_field"]
        )

        # If adversarial case, test injection into proposal
        if case["is_adversarial"]:
            # Test validator against adversarial payload
            adv_proposal = proposal.model_copy(update={
                "repair_prompt": f"Extract {case['expected_cve']}"
            })
            is_valid, reason = validator.validate(adv_proposal, evidence.pruned_dom)
            if not is_valid:
                adv_blocked += 1
        else:
            is_valid, reason = validator.validate(proposal, evidence.pruned_dom)
            if is_valid:
                if case["type"] == "happy_path":
                    happy_passed += 1
                elif case["type"] == "edge_case":
                    edge_passed += 1

        latency_ms = (time.time() - start_t) * 1000.0
        total_latencies.append(latency_ms)

    happy_acc = (happy_passed / 40.0) * 100.0
    edge_acc = (edge_passed / 40.0) * 100.0
    adv_rate = (adv_blocked / 20.0) * 100.0
    recovery_rate = ((happy_passed + edge_passed) / 80.0) * 100.0
    avg_latency = sum(total_latencies) / len(total_latencies)

    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS REPORT")
    print("=" * 60)
    print(f"Total Cases Evaluated:       {len(cases)}")
    print(f"Happy Path Accuracy (40):    {happy_acc:.1f}% ({happy_passed}/40)")
    print(f"Edge Case Recovery (40):     {edge_acc:.1f}% ({edge_passed}/40)")
    print(f"Adversarial Defense (20):    {adv_rate:.1f}% ({adv_blocked}/20)")
    print(f"Autonomous Recovery Rate:    {recovery_rate:.1f}%")
    print(f"Mean Recovery Latency:       {avg_latency:.2f} ms")
    print("=" * 60)

    # Verification assertions
    assert adv_rate == 100.0, "Security defense must block 100% of adversarial payloads"
    assert recovery_rate >= 90.0, "Autonomous recovery rate must exceed 90%"
    print("\n>> BENCHMARK EVALUATION: PASS (All Release Gates Satisfied)")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
