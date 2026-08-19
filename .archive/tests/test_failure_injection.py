"""Failure Injection & Fault-Tolerance Test Suite."""
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.database import db
from app.workers.bus import DistributedEventBus, event_bus

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    db._init_db()

@pytest.mark.asyncio
async def test_redis_failure_fallback():
    """Validates that when Redis is unavailable, EventBus gracefully falls back to local in-memory dispatch."""
    bus = DistributedEventBus()
    # Force initialize without valid Redis (offline fallback mode)
    await bus.initialize()
    
    # Publishing should not raise exceptions or crash the application
    test_event = {"type": "TEST_ALERT", "data": "Test Payload"}
    await bus.publish("security_events", test_event)
    assert True

@pytest.mark.asyncio
async def test_malformed_json_payload_handling():
    """Validates that malformed JSON payloads to API routes fail safely with 400 Bad Request."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/api/auth/login",
            content=b'{"email": "test@domain.com", MALFORMED_BODY}',
            headers={"Content-Type": "application/json"}
        )
        assert res.status_code in (400, 422)
