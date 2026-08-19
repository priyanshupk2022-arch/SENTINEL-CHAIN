"""Enterprise Database Layer with strict Multi-Tenant PostgreSQL and SQLite WAL engine."""
import asyncio
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey,
    create_engine, event, Index
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import settings

Base = declarative_base()

# ============================================================================
# Declarative Core ORM Entities
# ============================================================================

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    tier = Column(String(50), default="free", nullable=False)
    max_monthly_requests = Column(Integer, default=1000, nullable=False)
    current_period_requests = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    workspaces = relationship("Workspace", back_populates="organization", cascade="all, delete-orphan")
    memberships = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")
    policies = relationship("Policy", back_populates="organization", cascade="all, delete-orphan")
    subscription = relationship("Subscription", uselist=False, back_populates="organization", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="organization", cascade="all, delete-orphan")


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="workspaces")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="admin", nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), default="member", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="memberships")
    user = relationship("User", back_populates="memberships")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    key_prefix = Column(String(32), nullable=False, index=True)
    hashed_key = Column(String(255), unique=True, nullable=False, index=True)
    scopes = Column(String(512), default="proxy:all,scans:all", nullable=False)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="api_keys")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_id = Column(String(36), nullable=True)
    actor_type = Column(String(50), default="api_key", nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    endpoint = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    risk_score = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    findings_count = Column(Integer, default=0)
    categories = Column(Text, default="[]")
    input_preview = Column(Text, default="")
    output_preview = Column(Text, default="")
    details_json = Column(Text, default="{}")

    organization = relationship("Organization", back_populates="audit_logs")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(String(100), primary_key=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    enabled = Column(Boolean, default=True)
    action = Column(String(50), default="BLOCK")
    severity_threshold = Column(String(50), default="HIGH")
    rules_json = Column(Text, default="{}")

    organization = relationship("Organization", back_populates="policies")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    plan = Column(String(50), default="free", nullable=False)
    status = Column(String(50), default="active", nullable=False)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="subscription")


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(1024), nullable=False)
    secret = Column(String(255), nullable=False)
    event_types = Column(String(512), nullable=False, default="threat.blocked,scan.completed")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    webhook_id = Column(String(36), ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    success = Column(Boolean, default=False)
    attempts = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    webhook = relationship("Webhook", back_populates="deliveries")


# ============================================================================
# Database Manager
# ============================================================================

DEFAULT_DEFAULT_ORG_ID = "00000000-0000-0000-0000-000000000001"

class DatabaseManager:
    """Async Database Manager with complete Multi-Tenant B2B support."""
    def __init__(self, db_path: str = settings.DB_PATH, database_url: str = settings.DATABASE_URL):
        self.db_path = db_path
        self.database_url = database_url
        self._init_db()

    def _get_raw_connection(self) -> sqlite3.Connection:
        """Raw connection for fast synchronous fallback & SQLite pragmas."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA temp_store=MEMORY;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    _get_connection = _get_raw_connection

    def _init_db(self):
        """Initializes raw tables and handles automatic schema migration for SQLite."""
        with self._get_raw_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Organizations
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT NOT NULL UNIQUE,
                tier TEXT NOT NULL DEFAULT 'free',
                max_monthly_requests INTEGER NOT NULL DEFAULT 1000,
                current_period_requests INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)

            # 2. Workspaces
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                name TEXT NOT NULL,
                slug TEXT NOT NULL,
                is_default INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            );
            """)

            # 3. Users
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                hashed_password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'admin',
                is_active INTEGER DEFAULT 1,
                is_verified INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            );
            """)

            # 4. Organization Memberships
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS organization_members (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'member',
                created_at TEXT NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)

            # 5. Invitations
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS invitations (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                email TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'member',
                token TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'pending',
                invited_by_user_id TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            );
            """)

            # 6. API Keys
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                name TEXT NOT NULL,
                key_prefix TEXT NOT NULL,
                hashed_key TEXT NOT NULL UNIQUE,
                scopes TEXT NOT NULL DEFAULT 'proxy:all,scans:all',
                is_active INTEGER DEFAULT 1,
                last_used_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            );
            """)

            # 7. Audit Logs
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                workspace_id TEXT,
                actor_id TEXT,
                actor_type TEXT DEFAULT 'api_key',
                timestamp TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                status TEXT NOT NULL,
                risk_score REAL DEFAULT 0.0,
                latency_ms REAL DEFAULT 0.0,
                findings_count INTEGER DEFAULT 0,
                categories TEXT DEFAULT '[]',
                input_preview TEXT DEFAULT '',
                output_preview TEXT DEFAULT '',
                details_json TEXT DEFAULT '{}',
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            );
            """)

            # 8. Security Policies
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS policies (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                name TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                action TEXT NOT NULL DEFAULT 'BLOCK',
                severity_threshold TEXT NOT NULL DEFAULT 'HIGH',
                rules_json TEXT DEFAULT '{}',
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            );
            """)

            # 9. Subscriptions
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL UNIQUE,
                plan TEXT NOT NULL DEFAULT 'free',
                status TEXT NOT NULL DEFAULT 'active',
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                current_period_end TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            );
            """)

            # 10. Webhooks & Deliveries
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS webhooks (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                url TEXT NOT NULL,
                secret TEXT NOT NULL,
                event_types TEXT NOT NULL DEFAULT 'threat.blocked,scan.completed',
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS webhook_deliveries (
                id TEXT PRIMARY KEY,
                webhook_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                status_code INTEGER,
                response_body TEXT,
                success INTEGER DEFAULT 0,
                attempts INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (webhook_id) REFERENCES webhooks(id) ON DELETE CASCADE
            );
            """)

            # Auto-migration: check columns for existing databases
            cursor.execute("PRAGMA table_info(audit_logs);")
            audit_cols = [row[1] for row in cursor.fetchall()]
            if "organization_id" not in audit_cols:
                cursor.execute("ALTER TABLE audit_logs ADD COLUMN organization_id TEXT;")
            if "workspace_id" not in audit_cols:
                cursor.execute("ALTER TABLE audit_logs ADD COLUMN workspace_id TEXT;")
            if "actor_id" not in audit_cols:
                cursor.execute("ALTER TABLE audit_logs ADD COLUMN actor_id TEXT;")
            if "actor_type" not in audit_cols:
                cursor.execute("ALTER TABLE audit_logs ADD COLUMN actor_type TEXT DEFAULT 'api_key';")

            cursor.execute("PRAGMA table_info(policies);")
            pol_cols = [row[1] for row in cursor.fetchall()]
            if "organization_id" not in pol_cols:
                cursor.execute("ALTER TABLE policies ADD COLUMN organization_id TEXT;")
            cursor.execute("UPDATE policies SET organization_id = ? WHERE organization_id IS NULL;", (DEFAULT_DEFAULT_ORG_ID,))

            # Indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_status ON audit_logs(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_org ON audit_logs(organization_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_apikeys_hash ON api_keys(hashed_key);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orgs_slug ON organizations(slug);")

            # Seed Default Organization
            cursor.execute("SELECT COUNT(*) FROM organizations WHERE id = ?", (DEFAULT_DEFAULT_ORG_ID,))
            if cursor.fetchone()[0] == 0:
                now_iso = datetime.now(timezone.utc).isoformat()
                cursor.execute(
                    "INSERT INTO organizations (id, name, slug, tier, max_monthly_requests, current_period_requests, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (DEFAULT_DEFAULT_ORG_ID, "Default Organization", "default-org", "enterprise", 10000000, 0, now_iso, now_iso)
                )
                cursor.execute(
                    "INSERT INTO workspaces (id, organization_id, name, slug, is_default, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), DEFAULT_DEFAULT_ORG_ID, "Production", "prod-us-east", 1, now_iso)
                )
                cursor.execute(
                "INSERT INTO subscriptions (id, organization_id, plan, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), DEFAULT_DEFAULT_ORG_ID, "enterprise", "active", now_iso)
            )

            # Seed Global/Default Policies
            cursor.execute("SELECT COUNT(*) FROM policies WHERE organization_id = ?;", (DEFAULT_DEFAULT_ORG_ID,))
            if cursor.fetchone()[0] == 0:
                default_policies = [
                    ("pol_steg", DEFAULT_DEFAULT_ORG_ID, "Zero-Width & Unicode Steganography", 1, "BLOCK", "CRITICAL", json.dumps({"description": "Block invisible zero-width and bi-directional payload overrides"})),
                    ("pol_white_text", DEFAULT_DEFAULT_ORG_ID, "Hidden Text & Micro-Font Forensics", 1, "BLOCK", "HIGH", json.dumps({"description": "Neutralize text rendered in white font on white background or off-canvas"})),
                    ("pol_prompt_inj", DEFAULT_DEFAULT_ORG_ID, "Prompt Injection & Delimiter Breakouts", 1, "BLOCK", "HIGH", json.dumps({"description": "Detect delimiter breakouts and prompt hijacking taxonomy"})),
                    ("pol_pii", DEFAULT_DEFAULT_ORG_ID, "PII & Secret Masking", 1, "REDACT", "HIGH", json.dumps({"description": "Sanitize SSNs, Credit Cards, API Keys, Passwords and PII from prompt streams"}))
                ]
                cursor.executemany("INSERT OR REPLACE INTO policies (id, organization_id, name, enabled, action, severity_threshold, rules_json) VALUES (?, ?, ?, ?, ?, ?, ?)", default_policies)

            conn.commit()

    # ========================================================================
    # Audit Logging & Telemetry Methods (Strict Tenant-Scoped)
    # ========================================================================

    async def log_audit_event(
        self,
        endpoint: str = "/v1/chat/completions",
        status: str = "ALLOWED",
        risk_score: float = 0.0,
        latency_ms: float = 0.0,
        findings: Optional[List[Dict[str, Any]]] = None,
        input_preview: str = "",
        output_preview: str = "",
        details: Optional[Dict[str, Any]] = None,
        organization_id: Optional[str] = None,
        actor_type: str = "api_key",
        actor_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        event_id: Optional[str] = None,
        timestamp_iso: Optional[str] = None,
        source: Optional[str] = None,
        model: Optional[str] = None,
        sanitized_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ) -> str:
        log_id = event_id or str(uuid.uuid4())
        timestamp = timestamp_iso or datetime.now(timezone.utc).isoformat()
        findings_list = findings or []
        categories = list({f.get("category", "unknown") for f in findings_list})
        categories_json = json.dumps(categories)
        det = details or metadata or {}
        if model:
            det["model"] = model
        if source:
            det["source"] = source
        details_json = json.dumps(det)
        org_id = organization_id or DEFAULT_DEFAULT_ORG_ID
        ws_id = workspace_id or "default-ws"
        act_id = actor_id or "system"
        lat = duration_ms if duration_ms is not None else latency_ms
        in_prev = input_preview or sanitized_prompt or ""
        out_prev = output_preview or sanitized_prompt or ""

        def _insert():
            with self._get_raw_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO audit_logs (id, organization_id, workspace_id, actor_id, actor_type, timestamp, endpoint, status, risk_score, latency_ms, findings_count, categories, input_preview, output_preview, details_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (log_id, org_id, ws_id, act_id, actor_type, timestamp, endpoint, status, risk_score, lat, len(findings_list), categories_json, str(in_prev)[:500], str(out_prev)[:500], details_json)
                )
                conn.commit()

        await asyncio.to_thread(_insert)
        return log_id

    async def get_audit_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None,
        organization_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        filter_st = status_filter or status
        def _fetch():
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM audit_logs WHERE 1=1"
                params = []

                if organization_id:
                    query += " AND organization_id = ?"
                    params.append(organization_id)

                if filter_st and filter_st != "ALL":
                    query += " AND status = ?"
                    params.append(filter_st)

                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    item = dict(row)
                    item["categories"] = json.loads(item["categories"]) if item.get("categories") else []
                    item["details"] = json.loads(item["details_json"]) if item.get("details_json") else {}
                    item["findings"] = [{"category": c} for c in item["categories"]]
                    item["metadata"] = item["details"]
                    results.append(item)
                return results

        return await asyncio.to_thread(_fetch)


    async def get_stats(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        def _calc():
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                org_id = organization_id or DEFAULT_DEFAULT_ORG_ID
                where_clause = " WHERE organization_id = ?"
                params = [org_id]

                cursor.execute(f"SELECT COUNT(*), AVG(latency_ms), AVG(risk_score) FROM audit_logs{where_clause};", tuple(params))
                total, avg_lat, avg_risk = cursor.fetchone()

                blocked_query = f"SELECT COUNT(*) FROM audit_logs{where_clause} AND status = 'BLOCKED';"
                cursor.execute(blocked_query, tuple(params))
                blocked = cursor.fetchone()[0]

                sanitized_query = f"SELECT COUNT(*) FROM audit_logs{where_clause} AND status = 'SANITIZED';"
                cursor.execute(sanitized_query, tuple(params))
                sanitized = cursor.fetchone()[0]

                allowed_query = f"SELECT COUNT(*) FROM audit_logs{where_clause} AND status = 'ALLOWED';"
                cursor.execute(allowed_query, tuple(params))
                allowed = cursor.fetchone()[0]

                # Category breakdown
                cat_query = f"SELECT categories FROM audit_logs{where_clause} AND findings_count > 0 ORDER BY timestamp DESC LIMIT 500;"
                cursor.execute(cat_query, tuple(params))
                cat_rows = cursor.fetchall()
                cat_counts: Dict[str, int] = {}
                for row in cat_rows:
                    if row[0]:
                        try:
                            cats = json.loads(row[0])
                            for c in cats:
                                cat_counts[c] = cat_counts.get(c, 0) + 1
                        except Exception:
                            pass

                return {
                    "total_requests": total or 0,
                    "blocked_requests": blocked or 0,
                    "sanitized_requests": sanitized or 0,
                    "allowed_requests": allowed or 0,
                    "avg_latency_ms": round(avg_lat or 0.0, 2),
                    "avg_risk_score": round(avg_risk or 0.0, 2),
                    "category_distribution": cat_counts
                }
        return await asyncio.to_thread(_calc)

    # ========================================================================
    # Policy Management Methods (Tenant Scoped)
    # ========================================================================

    async def get_policies(self, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
        def _fetch():
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                org_id = organization_id or DEFAULT_DEFAULT_ORG_ID
                cursor.execute("SELECT * FROM policies WHERE organization_id = ?;", (org_id,))
                rows = cursor.fetchall()
                if not rows:
                    default_policies = [
                        ("pol_steg", org_id, "Zero-Width & Unicode Steganography", 1, "BLOCK", "CRITICAL", json.dumps({"description": "Block invisible zero-width and bi-directional payload overrides"})),
                        ("pol_white_text", org_id, "Hidden Text & Micro-Font Forensics", 1, "BLOCK", "HIGH", json.dumps({"description": "Neutralize text rendered in white font on white background or off-canvas"})),
                        ("pol_prompt_inj", org_id, "Prompt Injection & Delimiter Breakouts", 1, "BLOCK", "HIGH", json.dumps({"description": "Detect delimiter breakouts and prompt hijacking taxonomy"})),
                        ("pol_pii", org_id, "PII & Credential Redaction", 1, "REDACT", "MEDIUM", json.dumps({"description": "Redact SSN, Credit Cards (Luhn), API keys, and contact info before upstream"}))
                    ]
                    cursor.executemany("INSERT OR REPLACE INTO policies VALUES (?, ?, ?, ?, ?, ?, ?)", default_policies)
                    conn.commit()
                    cursor.execute("SELECT * FROM policies WHERE organization_id = ?;", (org_id,))
                    rows = cursor.fetchall()
                return [dict(r) for r in rows]
        return await asyncio.to_thread(_fetch)


    async def update_policy(self, policy_id: str, enabled: bool, action: str, severity: str, organization_id: Optional[str] = None) -> bool:
        def _update():
            with self._get_raw_connection() as conn:
                org_id = organization_id or DEFAULT_DEFAULT_ORG_ID
                # Check if policy exists for tenant
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM policies WHERE id = ? AND organization_id = ?", (policy_id, org_id))
                if cursor.fetchone()[0] == 0 and org_id != DEFAULT_DEFAULT_ORG_ID:
                    # Clone default policy for this organization
                    cursor.execute("SELECT name, rules_json FROM policies WHERE id = ?", (policy_id,))
                    row = cursor.fetchone()
                    name = row[0] if row else "Custom Policy"
                    rules_json = row[1] if row else "{}"
                    cursor.execute(
                        "INSERT INTO policies (id, organization_id, name, enabled, action, severity_threshold, rules_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (policy_id, org_id, name, 1 if enabled else 0, action, severity, rules_json)
                    )
                else:
                    cursor.execute(
                        "UPDATE policies SET enabled = ?, action = ?, severity_threshold = ? WHERE id = ? AND organization_id = ?",
                        (1 if enabled else 0, action, severity, policy_id, org_id)
                    )
                conn.commit()
                return True
        return await asyncio.to_thread(_update)

    # ========================================================================
    # User & Organization Management Methods
    # ========================================================================

    async def create_user(self, email: str, hashed_password: str, full_name: str, role: str = "admin") -> Dict[str, Any]:
        user_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        def _create():
            with self._get_raw_connection() as conn:
                conn.execute(
                    "INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (user_id, email.lower().strip(), hashed_password, full_name, role, 1, 1, now_iso)
                )
                conn.commit()
                return {"id": user_id, "email": email.lower().strip(), "full_name": full_name, "role": role}
        return await asyncio.to_thread(_create)

    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        def _get():
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
                row = cursor.fetchone()
                return dict(row) if row else None
        return await asyncio.to_thread(_get)

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        def _get():
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        return await asyncio.to_thread(_get)

    async def delete_user(self, user_id: str) -> bool:
        def _del():
            with self._get_raw_connection() as conn:
                conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()
                return True
        return await asyncio.to_thread(_del)

    async def create_organization(self, name: str, slug: str, owner_user_id: str, tier: str = "free") -> Dict[str, Any]:
        org_id = str(uuid.uuid4())
        workspace_id = str(uuid.uuid4())
        sub_id = str(uuid.uuid4())
        member_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        max_req = settings.PRO_TIER_MONTHLY_LIMIT if tier == "pro" else (settings.ENTERPRISE_TIER_MONTHLY_LIMIT if tier == "enterprise" else settings.FREE_TIER_MONTHLY_LIMIT)

        def _create():
            with self._get_raw_connection() as conn:
                conn.execute(
                    "INSERT INTO organizations (id, name, slug, tier, max_monthly_requests, current_period_requests, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (org_id, name, slug.lower().strip(), tier, max_req, 0, now_iso, now_iso)
                )
                conn.execute(
                    "INSERT INTO workspaces (id, organization_id, name, slug, is_default, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (workspace_id, org_id, "Production", "prod", 1, now_iso)
                )
                conn.execute(
                    "INSERT INTO organization_members (id, organization_id, user_id, role, created_at) VALUES (?, ?, ?, ?, ?)",
                    (member_id, org_id, owner_user_id, "owner", now_iso)
                )
                conn.execute(
                    "INSERT INTO subscriptions (id, organization_id, plan, status, created_at) VALUES (?, ?, ?, ?, ?)",
                    (sub_id, org_id, tier, "active", now_iso)
                )
                # Seed default policies for new organization
                default_policies = [
                    ("pol_steg", org_id, "Zero-Width & Unicode Steganography", 1, "BLOCK", "CRITICAL", json.dumps({"description": "Block invisible zero-width and bi-directional payload overrides"})),
                    ("pol_white_text", org_id, "Hidden Text & Micro-Font Forensics", 1, "BLOCK", "HIGH", json.dumps({"description": "Neutralize text rendered in white font on white background or off-canvas"})),
                    ("pol_prompt_inj", org_id, "Prompt Injection & Delimiter Breakouts", 1, "BLOCK", "HIGH", json.dumps({"description": "Detect delimiter breakouts and prompt hijacking taxonomy"})),
                    ("pol_pii", org_id, "PII & Credential Redaction", 1, "REDACT", "MEDIUM", json.dumps({"description": "Redact SSN, Credit Cards (Luhn), API keys, and contact info before upstream"}))
                ]
                conn.executemany("INSERT OR REPLACE INTO policies VALUES (?, ?, ?, ?, ?, ?, ?)", default_policies)
                conn.commit()
                return {"id": org_id, "name": name, "slug": slug, "tier": tier, "max_monthly_requests": max_req}
        return await asyncio.to_thread(_create)

    async def get_user_organizations(self, user_id: str) -> List[Dict[str, Any]]:
        def _get():
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT o.*, m.role as user_role 
                FROM organizations o
                JOIN organization_members m ON o.id = m.organization_id
                WHERE m.user_id = ?
                """, (user_id,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        return await asyncio.to_thread(_get)

    async def get_organization(self, org_id: str) -> Optional[Dict[str, Any]]:
        def _get():
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM organizations WHERE id = ?", (org_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        return await asyncio.to_thread(_get)

    async def delete_organization(self, org_id: str) -> bool:
        def _del():
            with self._get_raw_connection() as conn:
                conn.execute("DELETE FROM organizations WHERE id = ?", (org_id,))
                conn.commit()
                return True
        return await asyncio.to_thread(_del)

    # ========================================================================
    # Team Members & Invitations Methods
    # ========================================================================

    async def list_organization_members(self, organization_id: str) -> List[Dict[str, Any]]:
        def _list():
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                # CRITICAL: tenant-scoped. The previous code already filtered
                # by organization_id, but we now also surface the join timestamp
                # under both `created_at` and `joined_at` for the dashboard.
                cursor.execute("""
                SELECT m.id, m.organization_id, m.user_id, m.role, m.created_at,
                       m.created_at AS joined_at, u.email, u.full_name, u.is_active
                FROM organization_members m
                JOIN users u ON m.user_id = u.id
                WHERE m.organization_id = ?
                ORDER BY m.created_at ASC
                """, (organization_id,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        return await asyncio.to_thread(_list)

    async def add_organization_member(self, organization_id: str, user_id: str, role: str = "member") -> Dict[str, Any]:
        member_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        def _add():
            with self._get_raw_connection() as conn:
                conn.execute(
                    "INSERT INTO organization_members (id, organization_id, user_id, role, created_at) VALUES (?, ?, ?, ?, ?)",
                    (member_id, organization_id, user_id, role.lower(), now_iso)
                )
                conn.commit()
                return {"id": member_id, "organization_id": organization_id, "user_id": user_id, "role": role}
        return await asyncio.to_thread(_add)

    async def update_member_role(self, organization_id: str, user_id: str, role: str) -> bool:
        def _update():
            with self._get_raw_connection() as conn:
                conn.execute(
                    "UPDATE organization_members SET role = ? WHERE organization_id = ? AND user_id = ?",
                    (role.lower(), organization_id, user_id)
                )
                conn.commit()
                return True
        return await asyncio.to_thread(_update)

    async def remove_organization_member(self, organization_id: str, user_id: str) -> bool:
        def _rem():
            with self._get_raw_connection() as conn:
                conn.execute(
                    "DELETE FROM organization_members WHERE organization_id = ? AND user_id = ?",
                    (organization_id, user_id)
                )
                conn.commit()
                return True
        return await asyncio.to_thread(_rem)

    async def create_invitation(self, organization_id: str, email: str, role: str, invited_by_user_id: str) -> Dict[str, Any]:
        inv_id = str(uuid.uuid4())
        # CRITICAL: use a high-entropy token (32 bytes) for the invitation
        import secrets as _secrets
        token = _secrets.token_urlsafe(32)
        now_iso = datetime.now(timezone.utc).isoformat()
        expires_at = datetime.fromtimestamp(datetime.now(timezone.utc).timestamp() + 7 * 86400, timezone.utc).isoformat()
        def _inv():
            with self._get_raw_connection() as conn:
                # CRITICAL: refuse if email is already a member of this org
                cur = conn.cursor()
                cur.execute(
                    """SELECT u.id FROM users u
                       JOIN organization_members m ON m.user_id = u.id
                       WHERE m.organization_id = ? AND u.email = ?""",
                    (organization_id, email.lower().strip())
                )
                if cur.fetchone() is not None:
                    raise ValueError("User with this email is already a member of this organization.")
                # CRITICAL: refuse if a non-expired pending invitation already exists
                cur.execute(
                    "SELECT id FROM invitations WHERE organization_id = ? AND email = ? AND status = 'pending' AND expires_at > ?",
                    (organization_id, email.lower().strip(), now_iso)
                )
                if cur.fetchone() is not None:
                    raise ValueError("A pending invitation already exists for this email.")
                conn.execute(
                    "INSERT INTO invitations (id, organization_id, email, role, token, status, invited_by_user_id, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (inv_id, organization_id, email.lower().strip(), role.lower(), token, "pending", invited_by_user_id, now_iso, expires_at)
                )
                conn.commit()
                return {"id": inv_id, "organization_id": organization_id, "email": email, "role": role, "token": token, "expires_at": expires_at}
        return await asyncio.to_thread(_inv)

    async def list_invitations(self, organization_id: str) -> List[Dict[str, Any]]:
        def _list():
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, organization_id, email, role, status, created_at, expires_at FROM invitations WHERE organization_id = ? AND status = 'pending' AND expires_at > ?", (organization_id, datetime.now(timezone.utc).isoformat()))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        return await asyncio.to_thread(_list)

    async def get_invitation_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        def _get():
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM invitations WHERE token = ?", (token,))
                row = cursor.fetchone()
                return dict(row) if row else None
        return await asyncio.to_thread(_get)

    async def accept_invitation(self, token: str, user_id: str) -> Dict[str, Any]:
        """Accepts an invitation: marks it accepted and adds the user as a member."""
        def _accept():
            with self._get_raw_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM invitations WHERE token = ?", (token,))
                inv = cur.fetchone()
                if not inv:
                    raise ValueError("Invitation not found.")
                inv = dict(inv)
                if inv["status"] != "pending":
                    raise ValueError(f"Invitation is {inv['status']}.")
                now = datetime.now(timezone.utc).isoformat()
                if inv["expires_at"] < now:
                    cur.execute("UPDATE invitations SET status = 'expired' WHERE id = ?", (inv["id"],))
                    conn.commit()
                    raise ValueError("Invitation has expired.")
                # Mark accepted
                cur.execute("UPDATE invitations SET status = 'accepted' WHERE id = ?", (inv["id"],))
                # Add membership
                member_id = str(uuid.uuid4())
                try:
                    cur.execute(
                        "INSERT INTO organization_members (id, organization_id, user_id, role, created_at) VALUES (?, ?, ?, ?, ?)",
                        (member_id, inv["organization_id"], user_id, inv["role"], now)
                    )
                except Exception:
                    pass  # already a member
                conn.commit()
                return {"organization_id": inv["organization_id"], "role": inv["role"]}
        return await asyncio.to_thread(_accept)

    # ========================================================================
    # Workspaces Methods
    # ========================================================================

    async def list_workspaces(self, organization_id: str) -> List[Dict[str, Any]]:
        def _list():
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, organization_id, name, slug, is_default, created_at FROM workspaces WHERE organization_id = ? ORDER BY created_at ASC", (organization_id,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        return await asyncio.to_thread(_list)

    async def create_workspace(self, organization_id: str, name: str, slug: str) -> Dict[str, Any]:
        ws_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        def _create():
            with self._get_raw_connection() as conn:
                conn.execute(
                    "INSERT INTO workspaces (id, organization_id, name, slug, is_default, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (ws_id, organization_id, name, slug.lower().strip(), 0, now_iso)
                )
                conn.commit()
                return {"id": ws_id, "organization_id": organization_id, "name": name, "slug": slug, "is_default": False}
        return await asyncio.to_thread(_create)

    async def delete_workspace(self, workspace_id: str, organization_id: str) -> bool:
        def _del():
            with self._get_raw_connection() as conn:
                conn.execute("DELETE FROM workspaces WHERE id = ? AND organization_id = ? AND is_default = 0", (workspace_id, organization_id))
                conn.commit()
                return True
        return await asyncio.to_thread(_del)

    # ========================================================================
    # API Key Management Methods
    # ========================================================================

    async def create_api_key(self, organization_id: str, name: str, key_prefix: str, hashed_key: str, scopes: str = "proxy:all,scans:all") -> Dict[str, Any]:
        key_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        def _create():
            with self._get_raw_connection() as conn:
                conn.execute(
                    "INSERT INTO api_keys (id, organization_id, name, key_prefix, hashed_key, scopes, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (key_id, organization_id, name, key_prefix, hashed_key, scopes, 1, now_iso)
                )
                conn.commit()
                return {"id": key_id, "organization_id": organization_id, "name": name, "key_prefix": key_prefix, "scopes": scopes, "is_active": True}
        return await asyncio.to_thread(_create)

    async def get_api_key_by_hash(self, hashed_key: str) -> Optional[Dict[str, Any]]:
        def _get():
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT k.*, o.name as org_name, o.tier as org_tier, o.max_monthly_requests, o.current_period_requests
                FROM api_keys k
                JOIN organizations o ON k.organization_id = o.id
                WHERE k.hashed_key = ? AND k.is_active = 1
                """, (hashed_key,))
                row = cursor.fetchone()
                return dict(row) if row else None
        return await asyncio.to_thread(_get)

    async def list_api_keys(self, organization_id: str) -> List[Dict[str, Any]]:
        def _list():
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, organization_id, name, key_prefix, scopes, is_active, last_used_at, created_at FROM api_keys WHERE organization_id = ? ORDER BY created_at DESC", (organization_id,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        return await asyncio.to_thread(_list)

    async def revoke_api_key(self, key_id: str, organization_id: str) -> bool:
        def _revoke():
            with self._get_raw_connection() as conn:
                conn.execute("UPDATE api_keys SET is_active = 0 WHERE id = ? AND organization_id = ?", (key_id, organization_id))
                conn.commit()
                return True
        return await asyncio.to_thread(_revoke)

    async def record_api_key_usage(self, key_id: str, organization_id: str) -> None:
        """Atomically increments per-org usage counter to prevent race-condition quota bypass."""
        now_iso = datetime.now(timezone.utc).isoformat()
        def _update():
            with self._get_raw_connection() as conn:
                conn.execute("UPDATE api_keys SET last_used_at = ? WHERE id = ?", (now_iso, key_id))
                conn.execute(
                    "UPDATE organizations SET current_period_requests = current_period_requests + 1 WHERE id = ?",
                    (organization_id,)
                )
                conn.commit()
        await asyncio.to_thread(_update)

    async def atomic_increment_quota(self, organization_id: str) -> bool:
        """
        Atomically increments current_period_requests only if it has not reached max_monthly_requests.
        Returns True if incremented successfully, False if monthly quota exceeded.
        Enforces Gate 7 atomic database-level quota invariant.
        """
        def _inc():
            with self._get_raw_connection() as conn:
                cursor = conn.execute(
                    "UPDATE organizations SET current_period_requests = current_period_requests + 1 WHERE id = ? AND current_period_requests < max_monthly_requests",
                    (organization_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
        return await asyncio.to_thread(_inc)


    # ========================================================================
    # Webhooks Management Methods
    # ========================================================================

    async def create_webhook(self, organization_id: str, url: str, secret: str, event_types: str) -> Dict[str, Any]:
        webhook_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        def _create():
            with self._get_raw_connection() as conn:
                conn.execute(
                    "INSERT INTO webhooks (id, organization_id, url, secret, event_types, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (webhook_id, organization_id, url, secret, event_types, 1, now_iso)
                )
                conn.commit()
                return {"id": webhook_id, "url": url, "event_types": event_types, "is_active": True}
        return await asyncio.to_thread(_create)

    async def list_webhooks(self, organization_id: str) -> List[Dict[str, Any]]:
        def _list():
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, organization_id, url, event_types, is_active, created_at FROM webhooks WHERE organization_id = ? AND is_active = 1", (organization_id,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        return await asyncio.to_thread(_list)

    async def log_webhook_delivery(self, webhook_id: str, event_type: str, status_code: Optional[int], response_body: Optional[str], success: bool) -> None:
        delivery_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        def _log():
            with self._get_raw_connection() as conn:
                conn.execute(
                    "INSERT INTO webhook_deliveries (id, webhook_id, event_type, status_code, response_body, success, attempts, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (delivery_id, webhook_id, event_type, status_code, (response_body or "")[:500], 1 if success else 0, 1, now_iso)
                )
                conn.commit()
        await asyncio.to_thread(_log)

    # ========================================================================
    # Billing & Subscription Methods
    # ========================================================================

    async def get_subscription_by_stripe_customer(self, stripe_customer_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves subscription record by Stripe customer ID."""
        def _get():
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM subscriptions WHERE stripe_customer_id = ?", (stripe_customer_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        return await asyncio.to_thread(_get)

    async def get_subscription_by_stripe_sub_id(self, stripe_sub_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves subscription record by Stripe subscription ID."""
        def _get():
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM subscriptions WHERE stripe_subscription_id = ?", (stripe_sub_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        return await asyncio.to_thread(_get)

    async def get_subscription(self, organization_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves subscription record for an organization."""
        def _get():
            with self._get_raw_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM subscriptions WHERE organization_id = ?", (organization_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        return await asyncio.to_thread(_get)

    async def update_subscription(self, organization_id: str, plan: str, status: str = "active", stripe_customer_id: Optional[str] = None, stripe_subscription_id: Optional[str] = None) -> bool:
        max_req = settings.PRO_TIER_MONTHLY_LIMIT if plan == "pro" else (settings.ENTERPRISE_TIER_MONTHLY_LIMIT if plan == "enterprise" else settings.FREE_TIER_MONTHLY_LIMIT)
        def _update():
            with self._get_raw_connection() as conn:
                conn.execute("UPDATE organizations SET tier = ?, max_monthly_requests = ? WHERE id = ?", (plan, max_req, organization_id))
                conn.execute("""
                UPDATE subscriptions 
                SET plan = ?, status = ?, stripe_customer_id = COALESCE(?, stripe_customer_id), stripe_subscription_id = COALESCE(?, stripe_subscription_id)
                WHERE organization_id = ?
                """, (plan, status, stripe_customer_id, stripe_subscription_id, organization_id))
                conn.commit()
                return True
        return await asyncio.to_thread(_update)


db = DatabaseManager()

