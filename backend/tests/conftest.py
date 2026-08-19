import pytest
import pytest_asyncio
from backend.app.engine.queue_manager import ScraperQueueManager, QueueJobType
from backend.app.chaos.chaos_proxy import ChaosProxyManager, ChaosMode
from backend.app.api.routes_scrapers import _orchestrator_job_handler

@pytest_asyncio.fixture(autouse=True)
async def cleanup_singletons():
    # Reset chaos mode to clean baseline
    chaos = ChaosProxyManager()
    chaos.set_mode(ChaosMode.CLEAN)

    # Ensure canonical handler is registered
    queue = ScraperQueueManager()
    queue.register_handler(QueueJobType.RUN_SCRAPER, _orchestrator_job_handler)

    yield

    # Clean up queue manager worker task if running
    if queue._running:
        await queue.stop()
    queue.register_handler(QueueJobType.RUN_SCRAPER, _orchestrator_job_handler)
