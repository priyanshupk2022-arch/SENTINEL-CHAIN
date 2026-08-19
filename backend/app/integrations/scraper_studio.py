from fastapi import APIRouter, Request
from backend.app.scanner.wtp_scorer import WTPScorer

router = APIRouter()

@router.post("/api/webhooks/scraper-studio")
async def receive_scraper_studio_data(request: Request):
    """Webhook receiver for Bright Data Scraper Studio scheduled data pushes."""
    payload = await request.json()
    records = payload.get("data", [])

    scored_results = []
    for record in records:
        scored = await WTPScorer.score(record)
        scored_results.append(scored)

    # Store in SQLite and push to SSE stream
    # await store_and_broadcast(scored_results)
    return {"status": "ok", "processed": len(scored_results)}
