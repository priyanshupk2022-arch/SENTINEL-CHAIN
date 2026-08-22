import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import get_settings
from backend.app.storage.db import DatabaseManager
from backend.app.engine.queue_manager import ScraperQueueManager
from backend.app.api.routes_proxy import router as proxy_router
from backend.app.api.routes_chaos import router as chaos_router
from backend.app.api.routes_scrapers import router as scraper_router
from backend.app.api.routes_threats import router as threats_router
from backend.app.api.routes_telemetry import router as telemetry_router
from backend.app.api.routes_targets import router as targets_router
from backend.app.api.routes_discovery import router as discovery_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sentinel.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Initializing Sentinel-Chain Backend & Storage...")
    db = DatabaseManager(settings.DATABASE_PATH)
    await db.initialize()

    queue_mgr = ScraperQueueManager()
    await queue_mgr.start()
    logger.info("Sentinel-Chain Backend is operational.")
    yield
    logger.info("Shutting down Sentinel-Chain background workers...")
    await queue_mgr.stop()
    await db.close()

app = FastAPI(
    title="SENTINEL-CHAIN: Autonomous Web Intelligence & Self-Healing Platform",
    description="Autonomous user-controlled web scraping, schema synthesis, and self-healing platform for Bright Data Scraper Studio",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    # Local dev surface only. Wildcard "*" is invalid together with credentials
    # and would let any origin drive mutating endpoints (heal/approve/chaos).
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(targets_router)
app.include_router(discovery_router)
app.include_router(proxy_router)
app.include_router(chaos_router)
app.include_router(scraper_router)
app.include_router(threats_router)
app.include_router(telemetry_router)

@app.get("/api/health")
async def health_check():
    settings = get_settings()
    return {
        "status": "healthy",
        "service": "SENTINEL-CHAIN",
        "version": "2.0.0",
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
