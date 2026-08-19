"""Distributed & In-Memory Pub/Sub Event Bus for Real-Time Telemetry & SSE Streaming."""
import asyncio
import json
from typing import Dict, Any, List, Optional
import redis.asyncio as aioredis

from app.config import settings

class DistributedEventBus:
    def __init__(self):
        self.redis_client = None
        self.in_memory_subscribers: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    async def initialize(self):
        if settings.REDIS_URL and settings.ENABLE_REDIS_BUS:
            try:
                self.redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                await self.redis_client.ping()
            except Exception:
                self.redis_client = None

    async def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=200)
        async with self._lock:
            self.in_memory_subscribers.append(q)
        return q

    async def unsubscribe(self, q: asyncio.Queue):
        async with self._lock:
            if q in self.in_memory_subscribers:
                self.in_memory_subscribers.remove(q)

    async def publish(self, channel: str, event_data: Dict[str, Any]):
        msg_str = json.dumps(event_data, default=str)
        if self.redis_client:
            try:
                await self.redis_client.publish(channel, msg_str)
            except Exception:
                pass

        # Broadcast to local in-memory listeners
        async with self._lock:
            dead_queues = []
            for q in self.in_memory_subscribers:
                try:
                    q.put_nowait(event_data)
                except asyncio.QueueFull:
                    dead_queues.append(q)
                except Exception:
                    dead_queues.append(q)
            for q in dead_queues:
                if q in self.in_memory_subscribers:
                    self.in_memory_subscribers.remove(q)

event_bus = DistributedEventBus()
