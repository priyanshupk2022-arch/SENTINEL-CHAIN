"""Comprehensive Soak, Reliability, Streaming, and Data Plane Gate Test Suite (Gates 2, 6, 7, 10)."""
import asyncio
import time
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.database import db, DEFAULT_DEFAULT_ORG_ID
from app.security.api_key import generate_api_key, invalidate_key_cache
from app.billing.service import billing_service
import json

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    db._init_db()

@pytest.mark.asyncio
async def test_atomic_quota_database_enforcement():
    """Verifies that atomic_increment_quota enforces hard database limits (Gate 7)."""
    t_now = int(time.time() * 1000)
    user = await db.create_user(
        email=f"quota_atomic_{t_now}@testcorp.io",
        hashed_password="hashed_atomic_pw",
        full_name="Quota Atomic Officer",
        role="OWNER"
    )
    org = await db.create_organization(
        name="Atomic Quota Corp",
        slug=f"atomic-quota-{t_now}",
        owner_user_id=user["id"],
        tier="free"
    )
    # Organization is created with free tier limit (1,000 requests)
    # Manually set current_period_requests to 999 to test the boundary
    with db._get_raw_connection() as conn:
        conn.execute("UPDATE organizations SET current_period_requests = 999 WHERE id = ?", (org["id"],))
        conn.commit()

    # 1. 1000th request should succeed atomically
    success_1000 = await db.atomic_increment_quota(org["id"])
    assert success_1000 is True

    # 2. 1001st request must FAIL atomically at the SQL level (0 rows updated)
    success_1001 = await db.atomic_increment_quota(org["id"])
    assert success_1001 is False

@pytest.mark.asyncio
async def test_streaming_correctness_and_done_sentinel():
    """Verifies that reverse proxy streaming produces valid SSE chunks and ends with [DONE] (Gate 2)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        raw_key, prefix, key_hash = generate_api_key("Streaming Test Key")
        await db.create_api_key(DEFAULT_DEFAULT_ORG_ID, "Streaming Test Key", prefix, key_hash)
        invalidate_key_cache()

        headers = {"Authorization": f"Bearer {raw_key}"}
        res = await ac.post("/v1/chat/completions", json={
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Tell me about quantum computing."}],
            "stream": True
        }, headers=headers)

        assert res.status_code == 200
        assert "text/event-stream" in res.headers.get("content-type", "")
        body_text = res.text
        assert "data: " in body_text
        assert "data: [DONE]" in body_text

@pytest.mark.asyncio
async def test_high_concurrency_soak_and_zero_lock_contention():
    """Runs 60 concurrent requests simulating burst traffic with zero SQLite lock errors (Gate 10)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        raw_key, prefix, key_hash = generate_api_key("Soak Stress Key")
        await db.create_api_key(DEFAULT_DEFAULT_ORG_ID, "Soak Stress Key", prefix, key_hash)
        invalidate_key_cache()

        headers = {"Authorization": f"Bearer {raw_key}"}
        
        async def single_call(i):
            return await ac.post("/v1/chat/completions", json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": f"Concurrent safe query #{i}"}]
            }, headers=headers)

        t0 = time.perf_counter()
        results = await asyncio.gather(*(single_call(i) for i in range(60)))
        t1 = time.perf_counter()

        # All 60 requests must succeed with HTTP 200
        for r in results:
            assert r.status_code == 200

        total_time = t1 - t0
        assert total_time < 3.0, f"60 concurrent requests took {total_time:.2f}s (exceeds 3.0s soak threshold)"

@pytest.mark.asyncio
async def test_billing_webhook_replay_and_cancellation_downgrade():
    """Verifies server-authoritative entitlement downgrade on cancellation and duplicate webhook idempotency (Gate 6)."""
    t_now = int(time.time() * 1000)
    user = await db.create_user(
        email=f"billing_soak_{t_now}@testcorp.io",
        hashed_password="hashed_billing_pw",
        full_name="Billing Soak Officer",
        role="OWNER"
    )
    org = await db.create_organization(
        name="Billing Soak Corp",
        slug=f"billing-soak-{t_now}",
        owner_user_id=user["id"],
        tier="pro"
    )

    # 1. Simulate Stripe customer.subscription.deleted event
    event_payload = {
        "id": f"evt_test_{t_now}",
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": f"sub_stripe_{t_now}",
                "customer": f"cus_stripe_{t_now}",
                "status": "canceled",
                "metadata": {"organization_id": org["id"]}
            }
        }
    }

    # Handle cancellation webhook
    payload_bytes = json.dumps(event_payload).encode("utf-8")
    res = await billing_service.handle_webhook(payload_bytes=payload_bytes, signature_header="")
    assert res.get("received") is True or res.get("status") in ("canceled", "downgraded_to_free")

    # Verify organization tier was downgraded to free
    updated_org = await db.get_organization(org["id"])
    assert updated_org["tier"] == "free"
    assert updated_org["max_monthly_requests"] == 1000

    # 2. Replay duplicate webhook -> Must succeed idempotently without error
    replay_res = await billing_service.handle_webhook(payload_bytes=payload_bytes, signature_header="")
    assert replay_res.get("received") is True or replay_res.get("status") in ("canceled", "downgraded_to_free")

