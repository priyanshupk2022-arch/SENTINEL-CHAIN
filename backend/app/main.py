from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio

from backend.app.integrations.scraper_studio import router as scraper_studio_router

app = FastAPI(title="RADAR-X Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scraper_studio_router)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/stream/telemetry")
async def stream_telemetry():
    async def event_generator():
        while True:
            # Yield a keep-alive comment or empty frame for now
            yield "data: {}\n\n"
            await asyncio.sleep(1)
    return StreamingResponse(event_generator(), media_type="text/event-stream")
