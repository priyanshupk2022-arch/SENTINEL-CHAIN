from fastapi import APIRouter, Response
from backend.app.chaos.chaos_proxy import ChaosProxyManager

router = APIRouter(tags=["Proxy"])
chaos_manager = ChaosProxyManager()

@router.get("/api/proxy/target", response_class=Response)
async def get_proxy_target():
    """Serves the dynamic Exploit-DB target markup, mutated in real time based on active chaos state."""
    html_content = chaos_manager.get_target_html()
    return Response(content=html_content, media_type="text/html")
