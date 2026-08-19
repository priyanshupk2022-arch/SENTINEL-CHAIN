from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.chaos.chaos_proxy import ChaosProxyManager, ChaosMode

router = APIRouter(prefix="/api/chaos", tags=["Chaos Engine"])
chaos_manager = ChaosProxyManager()

class ChaosMutationRequest(BaseModel):
    mode: str

@router.get("/status")
async def get_chaos_status():
    return {
        "current_mode": chaos_manager.get_current_mode(),
        "available_modes": [m.value for m in ChaosMode]
    }

@router.post("/mutate")
async def mutate_target_dom(req: ChaosMutationRequest):
    try:
        mode_enum = ChaosMode(req.mode)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid chaos mode '{req.mode}'. Valid modes: {[m.value for m in ChaosMode]}"
        )
    chaos_manager.set_mode(mode_enum)
    return {
        "status": "success",
        "current_mode": mode_enum.value,
        "message": f"Target markup mutated to {mode_enum.value}"
    }

@router.post("/reset")
async def reset_chaos():
    chaos_manager.set_mode(ChaosMode.CLEAN)
    return {
        "status": "success",
        "current_mode": ChaosMode.CLEAN.value,
        "message": "Target markup reset to clean baseline"
    }
