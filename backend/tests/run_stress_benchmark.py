import asyncio
import time
import uuid
from typing import List
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
import aiosqlite
import pytest

from backend.app.main import app
from backend.app.storage.db import DatabaseManager
from backend.app.config import get_settings
from backend.app.engine.queue_manager import ScraperQueueManager, QueueJobType
from backend.app.telemetry.sse_hub import sse_hub
from backend.app.models.domain import TelemetryEvent
from backend.app.engine.cli_runner import CliExecutionResult

async def run_queue_choke_stress():
    print("\n--- ATTACK 1: 50 Failing Scrapers Concurrency & Head-of-Line Blocking ---")
    queue_mgr = ScraperQueueManager()
    await queue_mgr.start()

    execution_times = []
    async def mock_failing_cycle(collector_id, target_url, auto_heal):
        start = time.time()
        await asyncio.sleep(0.05)
        duration = time.time() - start
        execution_times.append(duration)
        return {"collector_id": collector_id, "final_state": "BROKEN", "recovered": False}

    with patch("backend.app.api.routes_scrapers.orchestrator.execute_scraper_cycle", side_effect=mock_failing_cycle):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            t0 = time.time()
            tasks = [
                client.post("/api/scraper/trigger", json={
                    "collector_id": f"c_fail_{i}",
                    "target_url": "http://test/target",
                    "auto_heal": True
                })
                for i in range(50)
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            total_elapsed = time.time() - t0

    print(f"Total time for 50 serialized jobs (50ms each): {total_elapsed:.2f}s")
    print(f"Average time per job in single worker queue: {total_elapsed / 50.0:.3f}s")
    print(f"Head-of-Line penalty: Job 50 waited {total_elapsed:.2f}s despite arriving at t=0s!")
    await queue_mgr.stop()

async def run_sse_100_clients_stress():
    print("\n--- ATTACK 2: 100 Simultaneous SSE Stream Connections ---")
    client_queues = []
    for _ in range(100):
        q = sse_hub.subscribe()
        client_queues.append(q)

    print(f"Active SSE Subscribers: {len(sse_hub._subscribers)}")
    
    t0 = time.time()
    for i in range(50):
        event = TelemetryEvent(
            node_id="detector",
            status="THREAT_DETECTED",
            message=f"High frequency threat alert #{i}",
            payload={"index": i, "data": "A" * 1024}
        )
        await sse_hub.broadcast(event)
    broadcast_elapsed = time.time() - t0

    total_buffered_msgs = sum(q.qsize() for q in client_queues)
    print(f"Broadcasted 50 events to 100 subscribers in {broadcast_elapsed:.4f}s")
    print(f"Total buffered messages in memory: {total_buffered_msgs} items across 100 queues")
    
    for q in client_queues:
        sse_hub.unsubscribe(q)
    print(f"Subscribers after cleanup: {len(sse_hub._subscribers)}")

async def run_sqlite_wal_stress():
    print("\n--- ATTACK 3: SQLite WAL High Concurrency Under 100 Simultaneous Unpooled Writers ---")
    settings = get_settings()
    test_db_path = settings.DATABASE_PATH + ".stress.db"
    
    init_db = DatabaseManager(test_db_path)
    await init_db.initialize()
    journal_mode = await init_db.get_journal_mode()
    print(f"Database Journal Mode: {journal_mode}")
    await init_db.close()

    errors = []
    successes = []

    async def write_telemetry(idx):
        try:
            db = DatabaseManager(test_db_path)
            event = TelemetryEvent(
                node_id=f"node_{idx}",
                status="RUNNING",
                message=f"Concurrent stress message {idx}",
                payload={"iter": idx}
            )
            await db.save_telemetry_event(event)
            successes.append(idx)
        except Exception as e:
            errors.append((idx, str(e)))

    t0 = time.time()
    await asyncio.gather(*[write_telemetry(i) for i in range(100)], return_exceptions=True)
    elapsed = time.time() - t0

    print(f"100 Concurrent Unpooled Writes: {len(successes)} succeeded, {len(errors)} failed in {elapsed:.3f}s")
    if errors:
        print(f"Sample error: {errors[0]}")

async def main():
    await run_queue_choke_stress()
    await run_sse_100_clients_stress()
    await run_sqlite_wal_stress()

if __name__ == "__main__":
    asyncio.run(main())
