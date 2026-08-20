import urllib.parse
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from backend.app.config import get_settings
from backend.app.storage.db import DatabaseManager
from backend.app.models.domain import (
    Target, TargetStatus, TargetInspection, ExtractionSchema, ExtractionField,
    ScraperDefinition, DynamicRecord, MonitorSchedule
)
from backend.app.security.url_validator import SecurityUrlValidator
from backend.app.engine.target_inspector import TargetInspectionEngine
from backend.app.engine.schema_generator import SchemaGenerator
from backend.app.engine.recovery_orchestrator import RecoveryOrchestrator
from backend.app.telemetry.sse_hub import sse_hub

logger = logging.getLogger("sentinel.api.targets")
router = APIRouter(prefix="/api/targets", tags=["Targets & Onboarding"])

inspector = TargetInspectionEngine(headless=True)
schema_gen = SchemaGenerator()
orchestrator = RecoveryOrchestrator()
orchestrator.subscribe_telemetry(sse_hub.broadcast)

def get_db():
    settings = get_settings()
    return DatabaseManager(settings.DATABASE_PATH)

# =========================================================================
# REQUEST / RESPONSE MODELS
# =========================================================================

class CreateTargetRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    url: str = Field(..., description="Target website URL")
    is_demo: bool = Field(default=False)

class UpdateTargetRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[TargetStatus] = None
    monitoring_enabled: Optional[bool] = None
    schedule: Optional[MonitorSchedule] = None

class GenerateSchemaRequest(BaseModel):
    intent_prompt: str = Field(..., description="Natural language extraction intent")

class SaveSchemaRequest(BaseModel):
    name: str = "Target Extraction Schema"
    intent_prompt: Optional[str] = None
    fields: List[ExtractionField]

class CreateScraperRequest(BaseModel):
    name: str
    collector_id: Optional[str] = "c_sentinel_cve_threats"
    instructions: Optional[str] = ""

class UpdateMonitorRequest(BaseModel):
    enabled: bool
    schedule: MonitorSchedule = MonitorSchedule.MANUAL

# =========================================================================
# TARGET ONBOARDING & MANAGEMENT ROUTES
# =========================================================================

@router.post("", response_model=Dict[str, Any])
async def create_target(req: CreateTargetRequest, db: DatabaseManager = Depends(get_db)):
    """Validates URL security (SSRF) and creates a new target entity."""
    is_valid, reason, canonical_url = SecurityUrlValidator.validate_url(req.url, allow_local_demo=req.is_demo)
    if not is_valid:
        raise HTTPException(status_code=400, detail=reason)

    parsed = urllib.parse.urlparse(canonical_url or req.url)
    domain = parsed.hostname or ""

    target = Target(
        id=str(uuid.uuid4()),
        name=req.name,
        url=canonical_url or req.url,
        domain=domain,
        status=TargetStatus.READY,
        health=1.0,
        is_demo=req.is_demo,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    await db.save_target(target)
    return {"status": "success", "target": target.model_dump()}

@router.get("", response_model=List[Dict[str, Any]])
async def list_targets(db: DatabaseManager = Depends(get_db)):
    """Lists all user targets."""
    targets = await db.list_targets()
    return [t.model_dump() for t in targets]

@router.get("/{target_id}", response_model=Dict[str, Any])
async def get_target(target_id: str, db: DatabaseManager = Depends(get_db)):
    target = await db.get_target(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target.model_dump()

@router.delete("/{target_id}")
async def delete_target(target_id: str, db: DatabaseManager = Depends(get_db)):
    success = await db.delete_target(target_id)
    return {"status": "success", "deleted": success}

# =========================================================================
# TARGET INSPECTION
# =========================================================================

@router.post("/{target_id}/inspect", response_model=Dict[str, Any])
async def inspect_target(target_id: str, db: DatabaseManager = Depends(get_db)):
    """Deeply inspects target website to extract page type, candidate fields, and sample DOM."""
    target = await db.get_target(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    target.status = TargetStatus.INSPECTING
    await db.save_target(target)

    insp: TargetInspection = await inspector.inspect_target(target.id, target.url)
    await db.save_inspection(insp)

    target.status = TargetStatus.READY
    await db.save_target(target)

    return insp.model_dump()

@router.get("/{target_id}/inspection/latest", response_model=Optional[Dict[str, Any]])
async def get_latest_inspection(target_id: str, db: DatabaseManager = Depends(get_db)):
    insp = await db.get_latest_inspection(target_id)
    return insp

# =========================================================================
# EXTRACTION INTENT & SCHEMA GENERATION
# =========================================================================

@router.post("/{target_id}/schema/generate", response_model=Dict[str, Any])
async def generate_schema_from_intent(
    target_id: str,
    req: GenerateSchemaRequest,
    db: DatabaseManager = Depends(get_db)
):
    """Uses Gemini 3.7 Flash to convert natural language extraction intent into a typed schema."""
    target = await db.get_target(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    inspection_data = await db.get_latest_inspection(target_id)
    inspection_obj = TargetInspection(**inspection_data) if inspection_data else None

    schema: ExtractionSchema = await schema_gen.generate_schema_from_intent(
        target_id=target.id,
        intent_prompt=req.intent_prompt,
        inspection=inspection_obj
    )

    await db.save_schema(schema)
    return schema.model_dump()

@router.put("/{target_id}/schema", response_model=Dict[str, Any])
async def save_schema(
    target_id: str,
    req: SaveSchemaRequest,
    db: DatabaseManager = Depends(get_db)
):
    """Allows user to review, edit, add, or remove schema fields."""
    target = await db.get_target(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    existing = await db.get_latest_schema(target_id)
    version = (existing.version + 1) if existing else 1

    schema = ExtractionSchema(
        id=str(uuid.uuid4()),
        target_id=target_id,
        name=req.name,
        version=version,
        intent_prompt=req.intent_prompt or (existing.intent_prompt if existing else ""),
        fields=req.fields,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    await db.save_schema(schema)
    return schema.model_dump()

@router.get("/{target_id}/schema", response_model=Optional[Dict[str, Any]])
async def get_schema(target_id: str, db: DatabaseManager = Depends(get_db)):
    schema = await db.get_latest_schema(target_id)
    return schema.model_dump() if schema else None

# =========================================================================
# SCRAPER CREATION & EXECUTION
# =========================================================================

@router.post("/{target_id}/scraper", response_model=Dict[str, Any])
async def create_scraper(
    target_id: str,
    req: CreateScraperRequest,
    db: DatabaseManager = Depends(get_db)
):
    """Binds target and schema to a ScraperDefinition."""
    target = await db.get_target(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    schema = await db.get_latest_schema(target_id)
    scraper = ScraperDefinition(
        id=str(uuid.uuid4()),
        target_id=target_id,
        schema_id=schema.id if schema else None,
        name=req.name,
        collector_id=req.collector_id or "c_sentinel_cve_threats",
        instructions=req.instructions or "",
        status="ACTIVE"
    )

    await db.save_scraper_def(scraper)
    return scraper.model_dump()

@router.post("/{target_id}/run", response_model=Dict[str, Any])
async def run_target_scraper(
    target_id: str,
    auto_heal: bool = Query(default=True),
    db: DatabaseManager = Depends(get_db)
):
    """Triggers real scraper execution for this specific target."""
    target = await db.get_target(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    scraper = await db.get_scraper_def(target_id)
    collector_id = scraper.collector_id if scraper else "c_sentinel_cve_threats"

    res = await orchestrator.execute_scraper_cycle(
        collector_id=collector_id,
        target_url=target.url,
        target_id=target.id,
        scraper_id=scraper.id if scraper else None,
        auto_heal=auto_heal
    )

    return res

@router.get("/{target_id}/records", response_model=List[Dict[str, Any]])
async def get_target_records(
    target_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    db: DatabaseManager = Depends(get_db)
):
    """Returns actual dynamic records harvested from the target website."""
    records = await db.get_target_records(target_id, limit=limit)
    return records

# =========================================================================
# MONITORING & SCHEDULE
# =========================================================================

@router.post("/{target_id}/monitor", response_model=Dict[str, Any])
async def update_monitor(
    target_id: str,
    req: UpdateMonitorRequest,
    db: DatabaseManager = Depends(get_db)
):
    """Configures scheduled monitoring for the target."""
    target = await db.get_target(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    target.monitoring_enabled = req.enabled
    target.schedule = req.schedule
    target.updated_at = datetime.utcnow()
    await db.save_target(target)

    return {
        "status": "success",
        "monitoring_enabled": target.monitoring_enabled,
        "schedule": target.schedule.value
    }
