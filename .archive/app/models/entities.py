"""Production-grade SQLAlchemy 2.0 Multi-Tenant Enterprise Models."""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index, BigInteger
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

# ============================================================================
# Core Identity & Multi-Tenancy Models
# ============================================================================

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    status = Column(String(50), nullable=False, default="active")  # active, suspended, deleted
    tier = Column(String(50), nullable=False, default="free")  # free, pro, enterprise
    max_monthly_requests = Column(Integer, nullable=False, default=1000)
    current_period_requests = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    workspaces = relationship("Workspace", back_populates="organization", cascade="all, delete-orphan")
    memberships = relationship("Membership", back_populates="organization", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")
    policies = relationship("Policy", back_populates="organization", cascade="all, delete-orphan")
    webhooks = relationship("WebhookEndpoint", back_populates="organization", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="organization", uselist=False, cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="organization", cascade="all, delete-orphan")
    invitations = relationship("Invitation", back_populates="organization", cascade="all, delete-orphan")
    documents = relationship("DocumentScan", back_populates="organization", cascade="all, delete-orphan")


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="workspaces")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="active")  # active, suspended, pending
    email_verified = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    verify_tokens = relationship("EmailVerificationToken", back_populates="user", cascade="all, delete-orphan")


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="ADMIN")  # OWNER, ADMIN, SECURITY_LEAD, AUDITOR, VIEWER
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="memberships")
    user = relationship("User", back_populates="memberships")


class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="MEMBER")
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="invitations")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", back_populates="reset_tokens")


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", back_populates="verify_tokens")


# ============================================================================
# API Key Management
# ============================================================================

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(String(36), nullable=True)
    name = Column(String(255), nullable=False)
    key_prefix = Column(String(16), nullable=False, index=True)
    hashed_key = Column(String(64), nullable=False, unique=True, index=True)
    scopes = Column(String(255), nullable=False, default="proxy:all,scans:all")
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="api_keys")


# ============================================================================
# Guardrail Policies & Forensics
# ============================================================================

class Policy(Base):
    __tablename__ = "policies"

    id = Column(String(64), primary_key=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    enabled = Column(Integer, nullable=False, default=1)
    action = Column(String(50), nullable=False, default="BLOCK")  # BLOCK, REDACT, WARN
    severity_threshold = Column(String(50), nullable=False, default="HIGH")  # CRITICAL, HIGH, MEDIUM, LOW
    config_json = Column(Text, nullable=True, default="{}")
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    organization = relationship("Organization", back_populates="policies")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    workspace_id = Column(String(36), nullable=True, index=True)
    actor_id = Column(String(36), nullable=True)
    actor_type = Column(String(50), nullable=False, default="api_key")  # api_key, user, anonymous
    request_id = Column(String(64), nullable=True, index=True)
    endpoint = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, index=True)  # ALLOWED, BLOCKED, SANITIZED
    risk_score = Column(Float, nullable=False, default=0.0)
    latency_ms = Column(Float, nullable=False, default=0.0)
    findings_count = Column(Integer, nullable=False, default=0)
    categories = Column(Text, nullable=False, default="[]")
    input_preview = Column(Text, nullable=True)
    output_preview = Column(Text, nullable=True)
    details_json = Column(Text, nullable=True, default="{}")
    timestamp = Column(String(64), nullable=False, index=True)

    organization = relationship("Organization", back_populates="audit_logs")


class DocumentScan(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by = Column(String(36), nullable=True)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="COMPLETED")  # QUEUED, PROCESSING, COMPLETED, FAILED
    risk_score = Column(Float, default=0.0)
    execution_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="documents")
    findings = relationship("SecurityFinding", back_populates="document", cascade="all, delete-orphan")


class SecurityFinding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True)
    category = Column(String(100), nullable=False)  # white_text, micro_font, pii_leak, prompt_injection, steganography
    severity = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    confidence = Column(Float, default=1.0)
    location = Column(String(255), nullable=True)
    original_snippet = Column(Text, nullable=True)
    redacted_snippet = Column(Text, nullable=True)
    details_json = Column(Text, nullable=True, default="{}")
    created_at = Column(DateTime(timezone=True), default=utc_now)

    document = relationship("DocumentScan", back_populates="findings")


# ============================================================================
# Billing, Plans & Subscriptions
# ============================================================================

class Plan(Base):
    __tablename__ = "plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    slug = Column(String(50), nullable=False, unique=True, index=True)  # free, pro, enterprise
    price_cents = Column(Integer, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    billing_interval = Column(String(20), nullable=False, default="month")
    request_limit = Column(Integer, nullable=False, default=1000)
    document_limit = Column(Integer, nullable=False, default=50)
    features_json = Column(Text, nullable=False, default="[]")
    is_active = Column(Boolean, default=True)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    provider = Column(String(50), nullable=False, default="stripe")
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    stripe_subscription_id = Column(String(255), nullable=True, index=True)
    plan = Column(String(50), nullable=False, default="free")
    status = Column(String(50), nullable=False, default="active")  # active, past_due, canceled
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    organization = relationship("Organization", back_populates="subscription")


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    api_key_id = Column(String(36), nullable=True, index=True)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    requests = Column(Integer, default=0)
    documents = Column(Integer, default=0)
    document_bytes = Column(BigInteger, default=0)
    tokens = Column(Integer, default=0)
    blocked_requests = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="usage_records")


# ============================================================================
# Outbound Webhooks & In-App Notifications
# ============================================================================

class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(1024), nullable=False)
    secret_hash = Column(String(255), nullable=False)
    events = Column(String(512), nullable=False, default="threat.blocked,scan.completed")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    organization = relationship("Organization", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="endpoint", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    webhook_endpoint_id = Column(String(36), ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(String(64), nullable=False)
    event_type = Column(String(100), nullable=False)
    attempt_count = Column(Integer, default=1)
    status = Column(String(50), nullable=False)  # SUCCESS, RETRY, FAILED, DEAD_LETTER
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    next_attempt_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    endpoint = relationship("WebhookEndpoint", back_populates="deliveries")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    type = Column(String(50), nullable=False)  # SECURITY_ALERT, QUOTA_WARNING, POLICY_CHANGE, BILLING
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", back_populates="notifications")
