"""Shared pytest bootstrap.

Sets a safe test environment BEFORE any `app.*` import so a fresh clone
runs without a `.env` file and without tripping the production secret
validation in app.config.
"""
import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "pytest-only-secret-key-that-is-at-least-32-chars-long",
)
os.environ.setdefault("ENABLE_MOCK_BILLING", "true")

# Isolate test databases from any real deployment data directory.
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEST_DATA = os.path.join(_BASE, "data", "test")
os.makedirs(_TEST_DATA, exist_ok=True)
os.environ.setdefault("DB_PATH", os.path.join(_TEST_DATA, "aegis_test.db"))
os.environ.setdefault(
    "DATABASE_URL", "sqlite+aiosqlite:///" + os.path.join(_TEST_DATA, "aegis_test.db").replace("\\", "/")
)

import pytest
from app.security.rate_limiter import reset_rate_limits
from app.security.api_key import invalidate_key_cache

@pytest.fixture(autouse=True)
def clean_test_isolation():
    """Resets rate limiting state and cached API key records between test cases."""
    reset_rate_limits()
    invalidate_key_cache()
    yield
    reset_rate_limits()
    invalidate_key_cache()

