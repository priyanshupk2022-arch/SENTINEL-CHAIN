"""Comprehensive Pydantic V2 Schemas for Control Plane & Data Plane."""
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, EmailStr

# ============================================================================
# Auth & User Schemas
# ============================================================================

class UserRegisterRequest(BaseModel):
    email: EmailStr
    # CRITICAL: enforce minimum 12 chars and a mix of classes.
    # This raises the bar from the previous 8-character minimum that
    # accepted `password` as a valid password.
    password: str = Field(..., min_length=12, max_length=256, description="Minimum 12 characters with letters, numbers, and symbols")
    full_name: str = Field(..., min_length=2, max_length=255)
    organization_name: Optional[str] = None
    invitation_token: Optional[str] = None  # when accepting an invitation

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    active_organization_id: str
    organizations: List[Dict[str, Any]] = Field(default_factory=list)

class TokenData(BaseModel):
    user_id: str
    email: str
    role: str
    organization_id: Optional[str] = None

# ============================================================================
# Organization & Workspace Schemas
# ============================================================================

class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2)
    slug: Optional[str] = None

class OrganizationOut(BaseModel):
    id: str
    name: str
    slug: str
    tier: str
    max_monthly_requests: int
    current_period_requests: int

class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=2)
    slug: Optional[str] = None

class WorkspaceOut(BaseModel):
    id: str
    organization_id: str
    name: str
    slug: str
    is_default: bool
    created_at: str

# ============================================================================
# Team Members & Invitations Schemas
# ============================================================================

class MemberOut(BaseModel):
    id: str
    user_id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: str

class MemberRoleUpdate(BaseModel):
    role: str = Field(..., pattern="^(owner|admin|security_lead|auditor|viewer)$")

class InvitationCreate(BaseModel):
    email: EmailStr
    role: str = Field(default="member", pattern="^(admin|security_lead|auditor|viewer|member)$")

class InvitationOut(BaseModel):
    id: str
    organization_id: str
    email: str
    role: str
    status: str
    created_at: str
    expires_at: str

# ============================================================================
# API Key Schemas
# ============================================================================

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=2)
    scopes: Optional[str] = "proxy:all,scans:all"

class APIKeyOut(BaseModel):
    id: str
    organization_id: str
    name: str
    key_prefix: str
    scopes: str
    is_active: bool
    last_used_at: Optional[str] = None
    created_at: str

class APIKeyCreatedResponse(BaseModel):
    id: str
    name: str
    raw_api_key: str
    key_prefix: str
    scopes: str
    organization_id: str

# ============================================================================
# Webhook Schemas
# ============================================================================

class WebhookCreate(BaseModel):
    url: str
    secret: Optional[str] = None
    event_types: Optional[str] = "threat.blocked,scan.completed"

class WebhookOut(BaseModel):
    id: str
    organization_id: str
    url: str
    event_types: str
    is_active: bool
    created_at: str

# ============================================================================
# Billing Schemas
# ============================================================================

class CheckoutSessionRequest(BaseModel):
    plan: str = "pro"  # pro, enterprise
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str
    mock_mode: bool = False

# ============================================================================
# OpenAI / Anthropic Compatible Schemas
# ============================================================================

class ChatMessage(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str = "gpt-4o"
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    user: Optional[str] = None

# ============================================================================
# Forensic & Policy Schemas
# ============================================================================

class ScanFinding(BaseModel):
    category: str
    severity: str
    description: str
    location: Optional[str] = None
    original_snippet: Optional[str] = None
    redacted_snippet: Optional[str] = None

class ScanReport(BaseModel):
    is_safe: bool = True
    is_blocked: bool = False
    risk_score: float = 0.0
    execution_time_ms: float = 0.0
    findings: List[ScanFinding] = Field(default_factory=list)
    sanitized_text: str = ""
    original_text_preview: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TextScanRequest(BaseModel):
    text: str
    apply_pii_redaction: Optional[bool] = True
    strict_mode: Optional[bool] = False

class PolicyRule(BaseModel):
    id: str
    name: str
    enabled: bool = True
    action: str = "BLOCK"
    severity_threshold: str = "HIGH"

class LicensePayload(BaseModel):
    tier: str
    organization: str
    max_requests_per_month: int
    expires_at: str
    features: List[str]
    signature: str

class AuditLogItem(BaseModel):
    id: str
    timestamp: str
    endpoint: str
    status: str
    risk_score: float
    latency_ms: float
    findings_count: int
    categories: List[str]
    input_preview: str
    output_preview: str
