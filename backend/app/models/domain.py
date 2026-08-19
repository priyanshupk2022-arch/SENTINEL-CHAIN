from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

class ScraperJobState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    BROKEN = "BROKEN"
    EVIDENCE_COLLECTING = "EVIDENCE_COLLECTING"
    HEALING = "HEALING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVING = "APPROVING"
    HEALTHY = "HEALTHY"
    FAILED = "FAILED"

class ThreatRecord(BaseModel):
    id: Optional[int] = None
    cve_id: str = Field(..., description="Unique CVE identifier e.g. CVE-2026-1234")
    title: str = Field(default="", description="Vulnerability title or description")
    severity: str = Field(default="UNKNOWN", description="CRITICAL, HIGH, MEDIUM, LOW")
    published_date: Optional[str] = None
    url: Optional[str] = None
    source: str = Field(default="Exploit-DB", description="Data source")
    raw_payload: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class EvidenceBundle(BaseModel):
    target_url: str
    error_message: str
    status_code: int = 200
    pruned_dom: str = Field(default="", description="Pruned Semantic HTML DOM structure")
    aom_tree: str = Field(default="", description="Accessibility Object Model / ARIA accessibility tree")
    screenshot_b64: Optional[str] = Field(default=None, description="Base64 PNG screenshot with set-of-marks annotations")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TelemetryEvent(BaseModel):
    id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    node_id: str = Field(..., description="DAG node: runner, detector, evidence, diagnoser, validator, healer, approval, verifier")
    status: str = Field(..., description="State or status of the node")
    message: str = Field(default="")
    payload: Optional[Dict[str, Any]] = None
