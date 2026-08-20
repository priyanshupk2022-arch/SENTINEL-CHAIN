import uuid
from enum import Enum
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from pydantic import BaseModel, Field

# =========================================================================
# LIFECYCLE & STATE ENUMS
# =========================================================================

class TargetStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    INSPECTING = "INSPECTING"
    READY = "READY"
    RUNNING = "RUNNING"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    HEALING = "HEALING"
    DISABLED = "DISABLED"

class PageType(str, Enum):
    TABLE = "TABLE"
    CARD_GRID = "CARD_GRID"
    ARTICLE_LIST = "ARTICLE_LIST"
    SINGLE_DOCUMENT = "SINGLE_DOCUMENT"
    UNKNOWN = "UNKNOWN"

class FieldDataType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    CURRENCY = "currency"
    DATE = "date"
    URL = "url"
    BOOLEAN = "boolean"
    ARRAY = "array"

class FailureCategory(str, Enum):
    SELECTOR_DRIFT = "SELECTOR_DRIFT"
    DOM_RESTRUCTURE = "DOM_RESTRUCTURE"
    FIELD_MISSING = "FIELD_MISSING"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    EMPTY_RESULT = "EMPTY_RESULT"
    VALUE_TYPE_CHANGE = "VALUE_TYPE_CHANGE"
    PAGINATION_CHANGE = "PAGINATION_CHANGE"
    CARD_TABLE_TRANSFORMATION = "CARD_TABLE_TRANSFORMATION"
    ATTRIBUTE_CHANGE = "ATTRIBUTE_CHANGE"
    CONTENT_LOCATION_CHANGE = "CONTENT_LOCATION_CHANGE"

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

class MonitorSchedule(str, Enum):
    MANUAL = "MANUAL"
    INTERVAL_5M = "INTERVAL_5M"
    INTERVAL_15M = "INTERVAL_15M"
    HOURLY = "HOURLY"
    DAILY = "DAILY"

# =========================================================================
# PRODUCT DOMAIN MODELS
# =========================================================================

class ExtractionField(BaseModel):
    name: str = Field(..., description="Canonical field key e.g. price, title, cve_id")
    type: FieldDataType = Field(default=FieldDataType.STRING)
    description: str = Field(default="", description="Field purpose / semantic description")
    required: bool = Field(default=True)
    selector_hint: Optional[str] = Field(default=None, description="CSS or XPath hint if available")
    normalization: Optional[str] = Field(default=None, description="e.g. trim, to_lower, parse_float")
    validation_rule: Optional[str] = Field(default=None, description="e.g. min_val:0, regex:^CVE")

class ExtractionSchema(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_id: str
    name: str = Field(default="Default Schema")
    version: int = Field(default=1)
    intent_prompt: Optional[str] = Field(default=None, description="Natural language intent from user")
    fields: List[ExtractionField] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TargetInspection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_id: str
    url: str
    final_url: Optional[str] = None
    status_code: int = 200
    page_title: str = ""
    page_type: PageType = PageType.UNKNOWN
    rendering_required: bool = False
    candidate_fields: List[str] = Field(default_factory=list)
    candidate_selectors: Dict[str, str] = Field(default_factory=dict)
    candidate_containers: List[str] = Field(default_factory=list)
    sample_records: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    inspection_timestamp: datetime = Field(default_factory=datetime.utcnow)

class Target(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Human-readable target name")
    url: str = Field(..., description="Target website URL")
    domain: str = ""
    status: TargetStatus = TargetStatus.READY
    health: float = Field(default=1.0, description="Health score 0.0 to 1.0")
    monitoring_enabled: bool = False
    schedule: MonitorSchedule = MonitorSchedule.MANUAL
    last_run: Optional[datetime] = None
    last_healed: Optional[datetime] = None
    is_demo: bool = False
    configuration: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ScraperDefinition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_id: str
    schema_id: Optional[str] = None
    name: str
    collector_id: str = "c_sentinel_cve_threats"
    instructions: str = ""
    status: str = "ACTIVE"
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ScraperRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_id: str
    scraper_id: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: ScraperJobState = ScraperJobState.RUNNING
    records_count: int = 0
    duration_ms: float = 0.0
    recovered: bool = False
    error: Optional[str] = None

class DynamicRecord(BaseModel):
    id: Optional[int] = None
    target_id: str
    run_id: str
    data: Dict[str, Any] = Field(default_factory=dict)
    is_simulated: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# =========================================================================
# LEGACY & CORE VERIFICATION MODELS (PRESERVED FOR COMPATIBILITY)
# =========================================================================

class ThreatRecord(BaseModel):
    id: Optional[int] = None
    cve_id: str = Field(..., description="Unique identifier e.g. CVE-2026-1234 or Record ID")
    title: str = Field(default="", description="Record title or summary")
    severity: str = Field(default="UNKNOWN", description="CRITICAL, HIGH, MEDIUM, LOW")
    published_date: Optional[str] = None
    url: Optional[str] = None
    source: str = Field(default="Target Harvester", description="Data source")
    raw_payload: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class EvidenceBundle(BaseModel):
    target_url: str
    error_message: str
    status_code: int = 200
    pruned_dom: str = Field(default="", description="Pruned Semantic HTML DOM structure")
    aom_tree: str = Field(default="", description="Accessibility Object Model / ARIA accessibility tree")
    screenshot_b64: Optional[str] = Field(default=None, description="Base64 PNG screenshot")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TelemetryEvent(BaseModel):
    id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    target_id: Optional[str] = None
    node_id: str = Field(..., description="DAG node ID")
    status: str = Field(..., description="State or status of the node")
    message: str = Field(default="")
    payload: Optional[Dict[str, Any]] = None
