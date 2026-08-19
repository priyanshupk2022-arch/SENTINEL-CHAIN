from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any
from backend.app.config import get_settings
from backend.app.storage.db import DatabaseManager

router = APIRouter(prefix="/api/threats", tags=["Threats"])

def get_db():
    settings = get_settings()
    return DatabaseManager(settings.DATABASE_PATH)

@router.get("", response_model=List[Dict[str, Any]])
async def list_recent_threats(limit: int = Query(default=50, ge=1, le=200)):
    db = get_db()
    return await db.get_recent_threats(limit=limit)
