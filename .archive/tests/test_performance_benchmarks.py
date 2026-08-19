"""Empirical Performance Benchmarking & SLA Latency Breakdown Suite."""
import asyncio
import statistics
import time
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.database import db, DEFAULT_DEFAULT_ORG_ID
from app.forensics.sanitizer import sanitizer
from app.security.api_key import generate_api_key

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    db._init_db()

@pytest.mark.asyncio
async def test_forensic_and_gateway_latency_breakdown():
    """Measures precise latencies for T_forensics, T_auth, and T_total (P50, P95, P99)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create test API key
        raw_key, prefix, key_hash = generate_api_key("Perf Key")
        await db.create_api_key(DEFAULT_DEFAULT_ORG_ID, "Perf Key", prefix, key_hash)
        headers = {"Authorization": f"Bearer {raw_key}"}

        test_payload = "Client SSN 000-12-3456 and CC 4532-0151-1283-0366 requesting security posture evaluation."
        
        forensic_latencies = []
        total_latencies = []

        # Warm up
        for _ in range(5):
            sanitizer.scan_text(test_payload)

        # 100 benchmark iterations
        for i in range(100):
            # Measure isolated T_forensics
            t0 = time.perf_counter()
            report = sanitizer.scan_text(test_payload)
            t1 = time.perf_counter()
            forensic_latencies.append((t1 - t0) * 1000.0)

            # Measure full Gateway T_total
            t_gate_0 = time.perf_counter()
            res = await ac.post("/v1/chat/completions", json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": f"Iteration {i}: {test_payload}"}]
            }, headers=headers)
            t_gate_1 = time.perf_counter()
            assert res.status_code == 200
            total_latencies.append((t_gate_1 - t_gate_0) * 1000.0)

        # Calculate Percentiles
        forensic_latencies.sort()
        total_latencies.sort()

        p50_forensic = forensic_latencies[50]
        p95_forensic = forensic_latencies[95]
        p99_forensic = forensic_latencies[99]

        p50_total = total_latencies[50]
        p95_total = total_latencies[95]
        p99_total = total_latencies[99]

        print(f"\n[LATENCY BENCHMARKS]")
        print(f"T_forensics: P50={p50_forensic:.3f}ms, P95={p95_forensic:.3f}ms, P99={p99_forensic:.3f}ms")
        print(f"T_total:     P50={p50_total:.3f}ms, P95={p95_total:.3f}ms, P99={p99_total:.3f}ms")

        # Forensic SLA (<20ms) assertion
        assert p99_forensic < 20.0, f"P99 forensic overhead {p99_forensic}ms exceeded 20ms SLA!"
        assert p50_forensic < 5.0, f"P50 forensic overhead {p50_forensic}ms exceeded 5ms target!"
