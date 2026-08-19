"""Distributed-Ready In-Memory Sliding-Window Rate Limiter.

NOTE: the previous version had a `PYTEST_CURRENT_TEST` env-var shortcut that
silently raised the rate limit ceiling 67x in any environment where that
environment variable happened to be set. An attacker controlling CI env
or exploiting a misconfigured secret could trivially bypass the limit.
The bypass is removed. Tests must call `reset_rate_limits()` between cases
instead.
"""
import time
from collections import defaultdict
from typing import Tuple, Dict, List
from fastapi import Request, HTTPException, status

from app.config import settings

# In-memory sliding window store: key -> list of timestamps
_RATE_LIMIT_STORE: Dict[str, List[float]] = defaultdict(list)

def check_rate_limit(
    key: str,
    max_requests: int,
    window_sec: float = 60.0
) -> Tuple[bool, int, float]:
    """
    Evaluates sliding window rate limit for a given key.
    Returns (is_allowed, remaining_requests, retry_after_sec).
    """
    now = time.time()
    timestamps = _RATE_LIMIT_STORE[key]

    # Evict timestamps older than window
    cutoff = now - window_sec
    _RATE_LIMIT_STORE[key] = [ts for ts in timestamps if ts > cutoff]
    current_count = len(_RATE_LIMIT_STORE[key])

    if current_count >= max_requests:
        oldest = _RATE_LIMIT_STORE[key][0]
        retry_after = max(1.0, window_sec - (now - oldest))
        return False, 0, retry_after

    _RATE_LIMIT_STORE[key].append(now)
    remaining = max_requests - (current_count + 1)
    return True, remaining, 0.0

def reset_rate_limits():
    """Resets rate limit store (useful for clean test isolation)."""
    global _RATE_LIMIT_STORE
    _RATE_LIMIT_STORE.clear()

def enforce_auth_rate_limit(request: Request):
    """FastAPI dependency enforcing strict rate limits on authentication endpoints.

    Tests that need a higher ceiling should either:
      (a) call `reset_rate_limits()` in test setup, or
      (b) patch the `max_requests` argument via a Depends() override.
    The previous env-var shortcut is removed because it is a security
    bypass if the env var is set in production by accident.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"auth_rate:{client_ip}"
    allowed, remaining, retry_after = check_rate_limit(
        key=key,
        max_requests=settings.AUTH_RATE_LIMIT_PER_MIN,
        window_sec=60.0
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many authentication attempts. Please retry in {int(retry_after)} seconds.",
            headers={"Retry-After": str(int(retry_after))}
        )
