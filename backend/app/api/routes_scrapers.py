from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from backend.app.config import get_settings
from backend.app.engine.queue_manager import ScraperQueueManager, QueueJobType
from backend.app.engine.recovery_orchestrator import RecoveryOrchestrator
from backend.app.telemetry.sse_hub import sse_hub

router = APIRouter(prefix="/api/scraper", tags=["Scraper"])
queue_manager = ScraperQueueManager()
orchestrator = RecoveryOrchestrator()

# Wire orchestrator telemetry to SSE hub
orchestrator.subscribe_telemetry(sse_hub.broadcast)

class ScraperTriggerRequest(BaseModel):
    collector_id: Optional[str] = Field(default="c_sentinel_cve_threats")
    target_url: Optional[str] = None
    auto_heal: bool = True

async def _orchestrator_job_handler(job):
    payload = job.payload
    collector_id = payload.get("collector_id", "c_sentinel_cve_threats")
    target_url = payload.get("target_url") or get_settings().TARGET_DEMO_URL
    auto_heal = payload.get("auto_heal", True)

    return await orchestrator.execute_scraper_cycle(
        collector_id=collector_id,
        target_url=target_url,
        auto_heal=auto_heal
    )

queue_manager.register_handler(QueueJobType.RUN_SCRAPER, _orchestrator_job_handler)

@router.post("/trigger")
async def trigger_scraper_run(req: ScraperTriggerRequest):
    settings = get_settings()
    target_url = req.target_url or settings.TARGET_DEMO_URL
    collector_id = req.collector_id or settings.DEFAULT_COLLECTOR_ID

    job = await queue_manager.enqueue_job(
        QueueJobType.RUN_SCRAPER,
        {
            "collector_id": collector_id,
            "target_url": target_url,
            "auto_heal": req.auto_heal
        }
    )

    try:
        # Wait up to timeout for execution
        completed_job = await queue_manager.wait_for_job(job.job_id, timeout=180.0)
        if completed_job.error:
            raise HTTPException(status_code=500, detail=completed_job.error)
        return {
            "status": "success",
            "job_id": job.job_id,
            "result": completed_job.result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraper execution error: {str(e)}")

@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    job = queue_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
