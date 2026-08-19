"""Background Asynchronous Workers for Forensics, Retries, and Telemetry."""
import asyncio
import hashlib
import hmac
import json
import os
import time
from typing import Dict, Any, Optional
import httpx

from app.config import settings
from app.models.database import db
from app.security.ssrf import validate_safe_url

async def deliver_webhook_with_retry(
    webhook: Dict[str, Any],
    event_type: str,
    payload_dict: Dict[str, Any],
    max_retries: int = 3
) -> None:
    """Delivers an outbound webhook with SSRF validation, exponential backoff, and persistent delivery status."""
    wh_id = webhook["id"]
    url = webhook["url"]
    secret = webhook.get("secret", "")

    # SSRF Protection: Validate destination URL before dispatching
    allow_local = (settings.ENVIRONMENT in ("development", "test") or os.getenv("PYTEST_CURRENT_TEST") is not None)
    is_safe, err_msg = validate_safe_url(url, allow_local_for_dev=allow_local)
    if not is_safe:
        await db.log_webhook_delivery(
            webhook_id=wh_id,
            event_type=event_type,
            status_code=400,
            response_body=f"SSRF Protection Blocked Delivery: {err_msg}",
            success=False
        )
        return

    payload_str = json.dumps(payload_dict, separators=(',', ':'))
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Aegis-Event": event_type,
        "X-Aegis-Signature": signature,
        "User-Agent": "Aegis-Commercial-Dispatcher/2.4"
    }

    success = False
    status_code = None
    resp_text = None

    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=False) as client:
                r = await client.post(url, content=payload_str, headers=headers)
                status_code = r.status_code
                resp_text = r.text[:500]
                if 200 <= r.status_code < 300:
                    success = True
                    break

        except Exception as e:
            resp_text = str(e)[:500]
            success = False

        if not success and attempt < max_retries:
            await asyncio.sleep(2 ** attempt)

    await db.log_webhook_delivery(
        webhook_id=wh_id,
        event_type=event_type,
        status_code=status_code,
        response_body=resp_text,
        success=success
    )
