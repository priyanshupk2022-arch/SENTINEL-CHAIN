"""Enterprise B2B SaaS Configuration Settings."""
import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core Application
    APP_NAME: str = "Aegis AI Security Guardrail Proxy"
    APP_VERSION: str = "2.4.0"
    ENVIRONMENT: str = "production"  # development, staging, production, test
    DEBUG: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database Configuration (PostgreSQL primary with SQLite WAL fallback)
    DATABASE_URL: str = "sqlite+aiosqlite:///" + str(BASE_DIR / "data" / "aegis_saas.db")
    DB_PATH: str = str(BASE_DIR / "data" / "aegis_saas.db")
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_TIMEOUT_SEC: float = 10.0

    # Redis & Distributed Event Bus
    REDIS_URL: Optional[str] = None
    ENABLE_REDIS_BUS: bool = False

    # Security & JWT Tokens
    # CRITICAL: Secret must be provided via environment. If not, refuse to start in production.
    JWT_SECRET_KEY: Optional[str] = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "Aegis Commercial Authority"
    JWT_AUDIENCE: str = "aegis-api"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    EMAIL_VERIFY_TOKEN_EXPIRE_HOURS: int = 24

    # CORS & Security Headers
    CORS_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "https://app.aegis-security.io"
    ]
    ENABLE_SECURITY_HEADERS: bool = True
    HSTS_ENABLED: bool = False

    # Authentication policy
    REQUIRE_AUTH_FOR_API: bool = True  # CRITICAL: when True, all /v1/* data plane endpoints require API key
    REQUIRE_AUTH_FOR_DASHBOARD: bool = True  # when True, /api/stats /api/logs etc require session
    ANONYMOUS_ALLOWED_FOR_LOCAL_DEV: bool = False  # never allow anonymous in production

    # Upstream LLM Endpoints
    UPSTREAM_LLM_URL: str = "https://api.openai.com/v1"
    UPSTREAM_API_KEY: Optional[str] = None
    UPSTREAM_TIMEOUT_SEC: float = 60.0

    # Stripe Billing Configuration
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    ENABLE_MOCK_BILLING: bool = True

    # Quotas by Tier (Requests per Month)
    FREE_TIER_MONTHLY_LIMIT: int = 1000
    PRO_TIER_MONTHLY_LIMIT: int = 100000
    ENTERPRISE_TIER_MONTHLY_LIMIT: int = 1000000  # Reduced from 10M; upgrade required for true high-volume

    # Forensic & Guardrail Pipeline Thresholds
    BLOCK_ON_CRITICAL: bool = True
    CRITICAL_RISK_THRESHOLD: float = 80.0
    HIGH_RISK_THRESHOLD: float = 60.0
    MEDIUM_RISK_THRESHOLD: float = 40.0
    LOW_RISK_THRESHOLD: float = 20.0
    MAX_OVERHEAD_MS_SLA: float = 20.0

    # Document & Request Security Limits
    MAX_DOCUMENT_SIZE_MB: int = 25
    MAX_REQUEST_BODY_BYTES: int = 30 * 1024 * 1024
    MAX_PII_SNIPPET_LENGTH: int = 200
    ENABLE_PII_REDACTION: bool = True

    # Rate Limiting
    AUTH_RATE_LIMIT_PER_MIN: int = 15
    API_RATE_LIMIT_PER_MIN: int = 600

settings = Settings()

# CRITICAL: enforce secret presence in production.
def _validate_secrets():
    if settings.ENVIRONMENT == "production" and not settings.JWT_SECRET_KEY:
        raise RuntimeError(
            "FATAL: JWT_SECRET_KEY must be set via environment in production. "
            "Refusing to start with a missing secret."
        )
    if settings.JWT_SECRET_KEY and len(settings.JWT_SECRET_KEY) < 32:
        raise RuntimeError(
            "FATAL: JWT_SECRET_KEY must be at least 32 characters (256 bits). "
            "Generate a strong random secret and set it via JWT_SECRET_KEY env var."
        )
    # Default for dev only — never used in production
    if not settings.JWT_SECRET_KEY:
        import secrets
        settings.JWT_SECRET_KEY = "dev-only-" + secrets.token_urlsafe(48)

_validate_secrets()

# Ensure required directories exist
(BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
(BASE_DIR / "data" / "uploads").mkdir(parents=True, exist_ok=True)
