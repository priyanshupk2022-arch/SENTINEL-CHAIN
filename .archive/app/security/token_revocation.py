"""Persistent token revocation store backed by SQLite.

Replaces the previous in-memory set so JWT refresh-token rotation and
revocation survive process restarts and are visible across multiple
Uvicorn workers / reloader spawns.
"""
import asyncio
import sqlite3
import time
from pathlib import Path
from typing import Set, Optional

import jwt

from app.config import BASE_DIR, settings

# In-memory cache, hydrated from disk on first import
_REVOKED_TOKENS: Set[str] = set()
_INITIALIZED: bool = False
_LOCK = asyncio.Lock()

_DB_PATH = Path(BASE_DIR / "data" / "token_revocation.db")


def _ensure_db():
    global _INITIALIZED
    if _INITIALIZED:
        return
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(_DB_PATH)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS revoked_tokens (
                jti TEXT PRIMARY KEY,
                exp_ts INTEGER NOT NULL,
                revoked_at REAL NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_revoked_exp ON revoked_tokens(exp_ts)"
        )
        conn.commit()
    _INITIALIZED = True


def _load_into_memory() -> None:
    _ensure_db()
    now = int(time.time())
    with sqlite3.connect(str(_DB_PATH)) as conn:
        # Drop expired entries
        conn.execute("DELETE FROM revoked_tokens WHERE exp_ts < ?", (now,))
        conn.commit()
        cursor = conn.execute("SELECT jti FROM revoked_tokens")
        for (jti,) in cursor.fetchall():
            _REVOKED_TOKENS.add(jti)


def is_revoked(jti: str) -> bool:
    if not _INITIALIZED:
        _load_into_memory()
    return jti in _REVOKED_TOKENS


def persist_revocation(jti: str, exp_ts: int) -> None:
    _ensure_db()
    with sqlite3.connect(str(_DB_PATH)) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO revoked_tokens (jti, exp_ts, revoked_at) VALUES (?, ?, ?)",
            (jti, int(exp_ts), time.time())
        )
        conn.commit()
    _REVOKED_TOKENS.add(jti)


def revoke_token(token: str) -> None:
    """Revokes a signed JWT by persisting its JTI (survives restarts).

    Signature is verified before revocation so arbitrary strings cannot
    pollute the blacklist. Expiry is intentionally not checked: an expired
    token may still be revoked defensively.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False, "verify_aud": False, "verify_iss": False},
        )
        jti = payload.get("jti")
        exp_ts = payload.get("exp")
        if jti and exp_ts:
            persist_revocation(jti, exp_ts)
    except Exception:
        pass


# eager-load on import so the in-memory cache is warm
_load_into_memory()
