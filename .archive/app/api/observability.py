"""Observability, Prometheus Metrics, and Health/Readiness Probes."""
import time
from typing import Dict, Any
from fastapi import APIRouter, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

from app.config import settings
from app.models.database import db

router = APIRouter(tags=["Observability"])

# Prometheus Metrics Definitions
AEGIS_REQUESTS_TOTAL = Counter(
    "aegis_requests_total",
    "Total number of requests inspected by Aegis",
    ["endpoint", "status"]
)
AEGIS_THREATS_BLOCKED = Counter(
    "aegis_threats_blocked_total",
    "Total number of malicious threats blocked",
    ["category"]
)
AEGIS_LATENCY_HISTOGRAM = Histogram(
    "aegis_processing_latency_seconds",
    "Histogram of forensic guardrail processing latency",
    buckets=[0.001, 0.005, 0.010, 0.020, 0.050, 0.100, 0.500]
)

@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint for scraping telemetry."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@router.get("/ready")
async def readiness_check():
    """Readiness probe checking database connectivity."""
    try:
        stats = await db.get_stats()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return Response(
            content=f'{{"status": "not_ready", "error": "{str(e)}"}}',
            status_code=503,
            media_type="application/json"
        )
