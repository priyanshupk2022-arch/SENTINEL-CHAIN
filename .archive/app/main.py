"""Aegis AI Security Guardrail Proxy & Commercial B2B SaaS Platform - Main Application."""
import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import (
    FastAPI, Request, Response, UploadFile, File, Form, Depends, HTTPException, Query, status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse

from app.config import settings, BASE_DIR
from app.models.database import db, DEFAULT_DEFAULT_ORG_ID
from app.models.schemas import (
    UserRegisterRequest, UserLoginRequest, TokenResponse, UserOut,
    OrganizationCreate, OrganizationOut,
    WorkspaceCreate, WorkspaceOut,
    MemberOut, MemberRoleUpdate, InvitationCreate, InvitationOut,
    APIKeyCreate, APIKeyOut, APIKeyCreatedResponse,
    WebhookCreate, WebhookOut,
    CheckoutSessionRequest, CheckoutSessionResponse,
    TextScanRequest, ScanReport, ChatCompletionRequest
)
from app.auth.hasher import hash_password, verify_password
from app.auth.tokens import create_access_token, create_refresh_token, decode_token, revoke_token
from app.security.auth import (
    get_current_user, get_current_user_optional, get_current_active_org, require_role
)
from app.security.api_key import generate_api_key, verify_api_key, invalidate_key_cache
from app.security.license import license_manager
from app.security.middleware import SecurityHeadersMiddleware
from app.security.ssrf import validate_safe_url
from app.security.rate_limiter import enforce_auth_rate_limit
from app.rbac.roles import Permission, has_permission
from app.billing.service import billing_service
from app.workers.bus import event_bus
from app.workers.tasks import deliver_webhook_with_retry
from app.reports.exporter import report_exporter
from app.forensics.sanitizer import sanitizer
from app.api.observability import router as observability_router
from src.proxy.handler import ProxyHandler, broadcaster

TEMPLATES_DIRS = [
    str(BASE_DIR / "app" / "templates"),
    str(BASE_DIR / "src" / "templates")
]
STATIC_DIRS = [
    str(BASE_DIR / "app" / "static"),
    str(BASE_DIR / "src" / "static")
]

templates = Jinja2Templates(directory=TEMPLATES_DIRS[0])

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure DB tables and default seed records exist
    db._init_db()
    await event_bus.initialize()
    lic_status = license_manager.get_status(os.getenv("AEGIS_LICENSE_TOKEN"))
    print(f"[*] Aegis Commercial B2B SaaS Platform Initialized. License: {lic_status.get('tier')}, Version: {settings.APP_VERSION}")
    yield
    print("[*] Aegis B2B SaaS Platform shutting down safely.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise Multi-Tenant AI Security Guardrail Proxy & Deep Document Forensics Platform",
    lifespan=lifespan
)

# Add Middleware Pipeline
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Observability Metrics
app.include_router(observability_router)

# Mount Static Files
static_dir_path = Path(STATIC_DIRS[0]) if Path(STATIC_DIRS[0]).exists() else Path(STATIC_DIRS[1])
static_dir_path.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir_path)), name="static")

# ============================================================================
# Public & UI Views
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def landing_page_view(request: Request):
    """Renders the High-Converting Marketing Landing Page."""
    return templates.TemplateResponse(request=request, name="index.html", context={})

@app.get("/login", response_class=HTMLResponse)
async def login_view(request: Request):
    """Renders the B2B User Login Page."""
    return templates.TemplateResponse(request=request, name="login.html", context={})

@app.get("/register", response_class=HTMLResponse)
async def register_view(request: Request):
    """Renders the B2B User & Organization Registration Page."""
    return templates.TemplateResponse(request=request, name="register.html", context={})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_view(
    request: Request,
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Renders the Multi-Tenant Enterprise Security & Forensics Dashboard."""
    org_id = DEFAULT_DEFAULT_ORG_ID
    active_user = user
    if user:
        orgs = await db.get_user_organizations(user["id"])
        if orgs:
            org_id = orgs[0]["id"]
    
    stats = await db.get_stats(organization_id=org_id)
    policies = await db.get_policies(organization_id=org_id)
    recent_logs = await db.get_audit_logs(limit=25, organization_id=org_id)
    lic_status = license_manager.get_status(os.getenv("AEGIS_LICENSE_TOKEN"))

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": active_user,
            "organization_id": org_id,
            "stats": stats,
            "policies": policies,
            "recent_logs": recent_logs,
            "license": lic_status,
            "settings": settings
        }
    )

@app.get("/health")
async def health():
    lic_status = license_manager.get_status(os.getenv("AEGIS_LICENSE_TOKEN"))
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "license": lic_status.get("tier", "community"),
        "license_active": lic_status.get("active", False)
    }

@app.get("/version")
async def version():
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }

# ============================================================================
# Control Plane: Authentication APIs (Argon2id + JWT Access/Refresh)
# ============================================================================

@app.post("/api/auth/register", response_model=TokenResponse, dependencies=[Depends(enforce_auth_rate_limit)])
async def register(req: UserRegisterRequest, response: Response):
    """Registers a new B2B user and creates their primary organization with OWNER role."""
    # CRITICAL: enforce password complexity
    from app.auth.password_policy import validate_password_strength
    is_strong, err = validate_password_strength(req.password)
    if not is_strong:
        raise HTTPException(status_code=400, detail=err)

    existing = await db.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    hashed_pw = hash_password(req.password)
    user = await db.create_user(
        email=req.email,
        hashed_password=hashed_pw,
        full_name=req.full_name,
        role="OWNER"
    )

    # If invitation token provided, accept and add user to that org instead of creating new
    if req.invitation_token:
        try:
            accept_result = await db.accept_invitation(token=req.invitation_token, user_id=user["id"])
            org_id = accept_result["organization_id"]
            # Fetch the org to return it
            orgs = await db.get_user_organizations(user["id"])
            org = orgs[0] if orgs else None
            access_token = create_access_token(
                user_id=user["id"], email=user["email"], role=accept_result["role"], organization_id=org_id
            )
            response.set_cookie("aegis_session", access_token, max_age=86400, httponly=True, samesite="lax")
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user=UserOut(id=user["id"], email=user["email"], full_name=user["full_name"], role=accept_result["role"], is_active=True),
                active_organization_id=org_id,
                organizations=orgs
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid invitation: {e}")

    org_name = req.organization_name or f"{req.full_name}'s Team"
    org_slug = req.email.split("@")[0].lower() + "-org-" + str(int(time.time()))[-4:]
    org = await db.create_organization(name=org_name, slug=org_slug, owner_user_id=user["id"], tier="free")

    # Generate initial API key for the new organization
    raw_key, prefix, key_hash = generate_api_key("Default Primary Key")
    await db.create_api_key(org["id"], "Default Primary Key", prefix, key_hash)

    # Issue JWT tokens
    access_token = create_access_token(user_id=user["id"], email=user["email"], role="OWNER", organization_id=org["id"])
    # CRITICAL: cookie hardening — secure flag when over TLS, SameSite=Lax, HttpOnly
    is_https = settings.ENVIRONMENT == "production"
    response.set_cookie(
        "aegis_session", access_token,
        max_age=86400, httponly=True, samesite="lax", secure=is_https, path="/"
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserOut(id=user["id"], email=user["email"], full_name=user["full_name"], role="OWNER", is_active=True),
        active_organization_id=org["id"],
        organizations=[org]
    )

@app.post("/api/auth/login", response_model=TokenResponse, dependencies=[Depends(enforce_auth_rate_limit)])
async def login(req: UserLoginRequest, response: Response):
    """Authenticates user credentials with Argon2id and issues session JWT."""
    user = await db.get_user_by_email(req.email)
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not user.get("is_active"):
        raise HTTPException(status_code=403, detail="Account suspended.")

    orgs = await db.get_user_organizations(user["id"])
    active_org_id = orgs[0]["id"] if orgs else DEFAULT_DEFAULT_ORG_ID
    role = orgs[0].get("user_role", user.get("role", "MEMBER")) if orgs else "MEMBER"

    access_token = create_access_token(user_id=user["id"], email=user["email"], role=role, organization_id=active_org_id)
    is_https = settings.ENVIRONMENT == "production"
    response.set_cookie("aegis_session", access_token, max_age=86400, httponly=True, samesite="lax", secure=is_https, path="/")

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserOut(id=user["id"], email=user["email"], full_name=user["full_name"], role=role, is_active=True),
        active_organization_id=active_org_id,
        organizations=orgs
    )

@app.get("/api/auth/me")
async def get_me(user: Dict[str, Any] = Depends(get_current_user)):
    """Returns current user details and organization memberships."""
    orgs = await db.get_user_organizations(user["id"])
    return {
        "user": UserOut(id=user["id"], email=user["email"], full_name=user["full_name"], role=user["role"], is_active=True),
        "organizations": orgs
    }

@app.post("/api/auth/logout")
async def logout(request: Request, response: Response):
    """Clears authentication session cookies and revokes tokens."""
    token = request.cookies.get("aegis_session")
    if token:
        revoke_token(token)
    response.delete_cookie("aegis_session")
    return {"message": "Logged out successfully."}

@app.post("/api/auth/refresh")
async def refresh_session(request: Request, response: Response):
    """Refreshes access token using a valid rotating refresh token."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    refresh_token = body.get("refresh_token") or request.cookies.get("aegis_refresh")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token required.")

    try:
        token_data = decode_token(refresh_token, expected_type="refresh")
        user = await db.get_user_by_id(token_data.get("sub"))
        if not user or not user.get("is_active"):
            raise HTTPException(status_code=401, detail="Invalid user or account suspended.")

        org_id = token_data.get("org_id", DEFAULT_DEFAULT_ORG_ID)
        access_token = create_access_token(user_id=user["id"], email=user["email"], role=user["role"], organization_id=org_id)
        is_https = settings.ENVIRONMENT == "production"
        response.set_cookie("aegis_session", access_token, max_age=86400, httponly=True, samesite="lax", secure=is_https, path="/")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or revoked refresh token: {str(e)}")

# ============================================================================
# Control Plane: Organizations & Workspaces
# ============================================================================

@app.get("/api/organizations", response_model=List[Dict[str, Any]])
async def list_organizations(user: Dict[str, Any] = Depends(get_current_user)):
    return await db.get_user_organizations(user["id"])

@app.post("/api/organizations", response_model=Dict[str, Any])
async def create_organization_endpoint(
    req: OrganizationCreate,
    user: Dict[str, Any] = Depends(get_current_user)
):
    slug = req.slug or (req.name.lower().replace(" ", "-") + "-" + str(int(time.time()))[-4:])
    org = await db.create_organization(name=req.name, slug=slug, owner_user_id=user["id"], tier="free")
    return org

@app.get("/api/workspaces", response_model=List[WorkspaceOut])
async def list_workspaces_endpoint(
    user: Dict[str, Any] = Depends(get_current_user),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    return await db.list_workspaces(org["id"])

@app.post("/api/workspaces", response_model=Dict[str, Any])
async def create_workspace_endpoint(
    req: WorkspaceCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    slug = req.slug or req.name.lower().replace(" ", "-")
    return await db.create_workspace(organization_id=org["id"], name=req.name, slug=slug)

@app.delete("/api/workspaces/{workspace_id}")
async def delete_workspace_endpoint(
    workspace_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    success = await db.delete_workspace(workspace_id=workspace_id, organization_id=org["id"])
    return {"success": success, "workspace_id": workspace_id}

# ============================================================================
# Control Plane: Team Members & Invitations (RBAC Protected)
# ============================================================================

@app.get("/api/members", response_model=List[MemberOut])
async def list_members_endpoint(
    user: Dict[str, Any] = Depends(get_current_user),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    return await db.list_organization_members(org["id"])

@app.post("/api/invitations", response_model=Dict[str, Any])
async def create_invitation_endpoint(
    req: InvitationCreate,
    user: Dict[str, Any] = Depends(require_role(["OWNER", "ADMIN"])),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    try:
        return await db.create_invitation(
            organization_id=org["id"],
            email=req.email,
            role=req.role,
            invited_by_user_id=user["id"]
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@app.get("/api/invitations", response_model=List[InvitationOut])
async def list_invitations_endpoint(
    user: Dict[str, Any] = Depends(get_current_user),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    return await db.list_invitations(org["id"])

@app.post("/api/invitations/accept", response_model=Dict[str, Any])
async def accept_invitation_endpoint(
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user)
):
    body = await request.json()
    token = body.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Invitation token required.")
    try:
        return await db.accept_invitation(token=token, user_id=user["id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/members/{member_user_id}/role")
async def update_member_role_endpoint(
    member_user_id: str,
    req: MemberRoleUpdate,
    user: Dict[str, Any] = Depends(require_role(["OWNER", "ADMIN"])),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    if member_user_id == user["id"] and req.role != "owner":
        raise HTTPException(status_code=400, detail="Cannot demote yourself from owner.")
    success = await db.update_member_role(organization_id=org["id"], user_id=member_user_id, role=req.role)
    return {"success": success, "updated_user_id": member_user_id, "role": req.role}

@app.delete("/api/members/{member_user_id}")
async def remove_member_endpoint(
    member_user_id: str,
    user: Dict[str, Any] = Depends(require_role(["OWNER", "ADMIN"])),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    if member_user_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot remove yourself from organization.")
    success = await db.remove_organization_member(organization_id=org["id"], user_id=member_user_id)
    return {"success": success, "removed_user_id": member_user_id}

# ============================================================================
# Control Plane: API Key Management
# ============================================================================

@app.get("/api/api-keys", response_model=List[APIKeyOut])
async def list_api_keys_endpoint(
    user: Dict[str, Any] = Depends(get_current_user),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    return await db.list_api_keys(org["id"])

@app.post("/api/api-keys", response_model=APIKeyCreatedResponse)
async def create_api_key_endpoint(
    req: APIKeyCreate,
    user: Dict[str, Any] = Depends(require_role(["OWNER", "ADMIN", "SECURITY_LEAD"])),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    raw_key, prefix, key_hash = generate_api_key(req.name)
    created = await db.create_api_key(
        organization_id=org["id"],
        name=req.name,
        key_prefix=prefix,
        hashed_key=key_hash,
        scopes=req.scopes or "proxy:all,scans:all"
    )
    return APIKeyCreatedResponse(
        id=created["id"],
        name=created["name"],
        raw_api_key=raw_key,
        key_prefix=prefix,
        scopes=created["scopes"],
        organization_id=org["id"]
    )

@app.delete("/api/api-keys/{key_id}")
async def revoke_api_key_endpoint(
    key_id: str,
    user: Dict[str, Any] = Depends(require_role(["OWNER", "ADMIN", "SECURITY_LEAD"])),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    success = await db.revoke_api_key(key_id, org["id"])
    invalidate_key_cache()
    return {"success": success, "revoked_key_id": key_id}

# ============================================================================
# Control Plane: Outbound Webhooks (SSRF Protected)
# ============================================================================

@app.get("/api/webhooks", response_model=List[WebhookOut])
async def list_webhooks_endpoint(
    user: Dict[str, Any] = Depends(get_current_user),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    return await db.list_webhooks(org["id"])

@app.post("/api/webhooks", response_model=Dict[str, Any])
async def create_webhook_endpoint(
    req: WebhookCreate,
    user: Dict[str, Any] = Depends(require_role(["OWNER", "ADMIN", "SECURITY_LEAD"])),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    allow_local = (settings.ENVIRONMENT in ("development", "test") or os.getenv("PYTEST_CURRENT_TEST") is not None)
    is_safe, err_msg = validate_safe_url(req.url, allow_local_for_dev=allow_local)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook URL: {err_msg}"
        )

    secret = req.secret or os.urandom(16).hex()
    wh = await db.create_webhook(
        organization_id=org["id"],
        url=req.url,
        secret=secret,
        event_types=req.event_types or "threat.blocked,scan.completed"
    )
    wh["secret"] = secret
    return wh

# ============================================================================
# Control Plane: Billing & Subscriptions
# ============================================================================

@app.post("/api/billing/checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session_endpoint(
    req: CheckoutSessionRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    # CRITICAL: only OWNER/ADMIN may create a billing session
    role = user.get("role", "MEMBER").upper()
    if role not in ("OWNER", "ADMIN"):
        raise HTTPException(status_code=403, detail="Only OWNER/ADMIN may manage billing.")
    session = await billing_service.create_checkout_session(
        organization_id=org["id"],
        plan=req.plan,
        user_email=user["email"],
        success_url=req.success_url,
        cancel_url=req.cancel_url
    )
    return CheckoutSessionResponse(
        checkout_url=session["checkout_url"],
        session_id=session["session_id"],
        mock_mode=(session.get("provider") == "test_deterministic")
    )

# Alias endpoint the dashboard's JS expects (POST /api/billing/checkout)
@app.post("/api/billing/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_alias(
    req: CheckoutSessionRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    role = user.get("role", "MEMBER").upper()
    if role not in ("OWNER", "ADMIN"):
        raise HTTPException(status_code=403, detail="Only OWNER/ADMIN may manage billing.")
    session = await billing_service.create_checkout_session(
        organization_id=org["id"],
        plan=req.plan,
        user_email=user["email"],
        success_url=req.success_url,
        cancel_url=req.cancel_url
    )
    return CheckoutSessionResponse(
        checkout_url=session["checkout_url"],
        session_id=session["session_id"],
        mock_mode=(session.get("provider") == "test_deterministic")
    )

@app.post("/api/billing/webhook")
async def stripe_webhook_endpoint(request: Request):
    # CRITICAL: webhook must NOT require a session cookie; the provider
    # authenticates by signature. We do not call Depends(get_current_user).
    payload_bytes = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    return await billing_service.handle_webhook(payload_bytes, sig)

# Health check (alias for k8s readiness probe)
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

# ============================================================================
# Control Plane: Reports & Compliance Export (Tenant-Scoped)
# ============================================================================

@app.get("/api/reports/audit/csv")
async def export_audit_csv_endpoint(
    user: Dict[str, Any] = Depends(get_current_user),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    csv_data = await report_exporter.export_audit_csv(organization_id=org["id"])
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=aegis_audit_{org['id'][:8]}.csv"}
    )

@app.get("/api/reports/audit/json")
async def export_audit_json_endpoint(
    user: Dict[str, Any] = Depends(get_current_user),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    json_data = await report_exporter.export_audit_json(organization_id=org["id"])
    return json_data

# ============================================================================
# Control Plane: Policies & Governance (RBAC & Tenant Protected)
# ============================================================================

@app.get("/api/policies")
async def get_policies(
    user: Dict[str, Any] = Depends(get_current_user),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    # CRITICAL: tenant-scoped. Users only see policies for their active org.
    return await db.get_policies(organization_id=org["id"])

@app.post("/api/policies/{policy_id}")
async def update_policy(
    policy_id: str,
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    role = user.get("role", "MEMBER").upper()
    if role not in ("OWNER", "ADMIN", "SECURITY_LEAD"):
        raise HTTPException(status_code=403, detail="Insufficient permissions to update security policies.")

    body = await request.json()
    enabled = body.get("enabled", True)
    action = body.get("action", "BLOCK")
    severity = body.get("severity_threshold", "HIGH")

    # CRITICAL: scope policy update to the active org (not user_orgs[0]).
    success = await db.update_policy(
        policy_id=policy_id,
        enabled=enabled,
        action=action,
        severity=severity,
        organization_id=org["id"]
    )
    return {"success": success, "policy_id": policy_id, "organization_id": org["id"]}

@app.get("/api/license")
async def get_license():
    return license_manager.get_status(os.getenv("AEGIS_LICENSE_TOKEN"))

# ============================================================================
# Control Plane: Telemetry, Logs & SSE Streaming (Tenant Scoped)
# ============================================================================

@app.get("/api/stats")
async def get_stats(
    user: Dict[str, Any] = Depends(get_current_user),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    # CRITICAL: tenant-scoped, authenticated required.
    return await db.get_stats(organization_id=org["id"])

@app.get("/api/logs")
async def get_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    user: Dict[str, Any] = Depends(get_current_user),
    org: Dict[str, Any] = Depends(get_current_active_org)
):
    # CRITICAL: tenant-scoped, authenticated required.
    logs = await db.get_audit_logs(limit=limit, offset=offset, status_filter=status, organization_id=org["id"])
    return {"logs": logs, "limit": limit, "offset": offset, "organization_id": org["id"]}

@app.get("/api/stream/logs")
async def stream_audit_logs(request: Request):
    queue = await broadcaster.subscribe()

    async def event_generator():
        try:
            yield {
                "event": "connected",
                "data": json.dumps({"status": "connected", "time": time.time()})
            }
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event_data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {
                        "event": "audit_event",
                        "data": json.dumps(event_data)
                    }
                except asyncio.TimeoutError:
                    yield {
                        "event": "ping",
                        "data": json.dumps({"ping": True, "time": time.time()})
                    }
        finally:
            await broadcaster.unsubscribe(queue)

    return EventSourceResponse(event_generator())

# ============================================================================
# Data Plane: Guardrail Proxy Endpoints (API Key & Quota Gated)
# ============================================================================

@app.post("/v1/chat/completions")
async def proxy_chat_completions(
    request: Request,
    auth_context: Dict[str, Any] = Depends(verify_api_key)
):
    return await ProxyHandler.handle_openai_chat(request, auth_context=auth_context)

@app.post("/v1/completions")
async def proxy_completions(
    request: Request,
    auth_context: Dict[str, Any] = Depends(verify_api_key)
):
    return await ProxyHandler.handle_openai_chat(request, auth_context=auth_context)

@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {"id": "gpt-4o", "object": "model", "owned_by": "openai", "permission": []},
            {"id": "gpt-4-turbo", "object": "model", "owned_by": "openai", "permission": []},
            {"id": "claude-3-5-sonnet-20241022", "object": "model", "owned_by": "anthropic", "permission": []}
        ]
    }

@app.post("/v1/messages")
async def proxy_anthropic_messages(
    request: Request,
    auth_context: Dict[str, Any] = Depends(verify_api_key)
):
    return await ProxyHandler.handle_anthropic_messages(request, auth_context=auth_context)

# ============================================================================
# Data Plane: Direct Forensics & Document Analysis
# ============================================================================

@app.post("/v1/scan/text", response_model=ScanReport)
async def scan_text_endpoint(
    req: TextScanRequest,
    auth_context: Dict[str, Any] = Depends(verify_api_key)
):
    report = sanitizer.scan_text(
        req.text,
        apply_pii=req.apply_pii_redaction if req.apply_pii_redaction is not None else True,
        strict_mode=req.strict_mode or False
    )
    
    org_id = auth_context.get("organization_id", DEFAULT_DEFAULT_ORG_ID)
    audit_status = "BLOCKED" if report.is_blocked else ("SANITIZED" if len(report.findings) > 0 else "ALLOWED")
    
    await db.log_audit_event(
        endpoint="/v1/scan/text",
        status=audit_status,
        risk_score=report.risk_score,
        latency_ms=report.execution_time_ms,
        findings=[f.model_dump() for f in report.findings],
        input_preview=req.text[:200],
        output_preview=report.sanitized_text[:200],
        organization_id=org_id,
        actor_type=auth_context.get("actor_type", "anonymous")
    )
    
    return report

@app.post("/v1/scan/document", response_model=ScanReport)
async def scan_document_endpoint(
    file: UploadFile = File(...),
    apply_pii_redaction: bool = Form(True),
    auth_context: Dict[str, Any] = Depends(verify_api_key)
):
    file_bytes = await file.read()
    filename = file.filename or "unknown.bin"
    
    max_bytes = settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_DOCUMENT_SIZE_MB}MB."
        )

    report = sanitizer.scan_document(
        filename=filename,
        file_bytes=file_bytes,
        apply_pii=apply_pii_redaction
    )
    
    org_id = auth_context.get("organization_id", DEFAULT_DEFAULT_ORG_ID)
    audit_status = "BLOCKED" if report.is_blocked else ("SANITIZED" if len(report.findings) > 0 else "ALLOWED")
    
    await db.log_audit_event(
        endpoint="/v1/scan/document",
        status=audit_status,
        risk_score=report.risk_score,
        latency_ms=report.execution_time_ms,
        findings=[f.model_dump() for f in report.findings],
        input_preview=f"Document: {filename} ({len(file_bytes)} bytes)",
        output_preview=report.sanitized_text[:200],
        details={"filename": filename, "file_size": len(file_bytes)},
        organization_id=org_id,
        actor_type=auth_context.get("actor_type", "anonymous")
    )

    return report
