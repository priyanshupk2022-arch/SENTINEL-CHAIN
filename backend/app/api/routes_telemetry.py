import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.app.telemetry.sse_hub import sse_hub
from backend.app.config import get_settings
from backend.app.storage.db import DatabaseManager

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])

@router.get("/events")
async def get_recent_telemetry_events(limit: int = 50):
    settings = get_settings()
    db = DatabaseManager(settings.DATABASE_PATH)
    return await db.get_recent_events(limit=limit)

@router.get("/stream")
async def stream_telemetry_sse():
    """Streams live DAG execution status updates, self-healing events, and threat alerts via SSE."""
    queue = sse_hub.subscribe()

    async def event_generator():
        try:
            # Send initial keepalive
            yield "data: {\"type\": \"connected\", \"message\": \"Sentinel-Chain Live SSE Connected\"}\n\n"
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield msg
                except asyncio.TimeoutError:
                    # Keepalive ping
                    yield ": keepalive\n\n"
        finally:
            sse_hub.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
