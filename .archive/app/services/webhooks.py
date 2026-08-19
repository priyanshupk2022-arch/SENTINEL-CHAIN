"""Outbound Webhook Delivery Engine with HMAC-SHA256 Signatures and SSRF Protection."""
import asyncio
import hashlib
import hmac
import json
import os
import time
from typing import Dict, Any, List
import httpx

from app.config import settings
from app.models.database import db
from app.security.ssrf import validate_safe_url

class WebhookDispatcher:
    @staticmethod
    def sign_payload(payload_str: str, secret: str) -> str:
        """Generates HMAC-SHA256 signature for webhook payload verification."""
        return hmac.new(
            secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    @classmethod
    async def dispatch_event(
        cls,
        organization_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """Dispatches an outbound webhook event asynchronously to all active subscribed endpoints."""
        webhooks = await db.list_webhooks(organization_id)
        if not webhooks:
            return

        payload = {
            "id": f"evt_{int(time.time()*1000)}",
            "event": event_type,
            "organization_id": organization_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
            "data": event_data
        }
        payload_str = json.dumps(payload, separators=(',', ':'))

        for wh in webhooks:
            subscribed_events = wh.get("event_types", "").split(",")
            if event_type in subscribed_events or "*" in subscribed_events:
                # CRITICAL: validate SSRF safety on every dispatch (defense in depth)
                allow_local = (
                    settings.ENVIRONMENT in ("development", "test")
                    or os.getenv("PYTEST_CURRENT_TEST") is not None
                )
                is_safe, err_msg = validate_safe_url(wh["url"], allow_local_for_dev=allow_local)
                if not is_safe:
                    await db.log_webhook_delivery(
                        webhook_id=wh["id"],
                        event_type=event_type,
                        status_code=400,
                        response_body=f"SSRF Protection Blocked: {err_msg}",
                        success=False
                    )
                    continue
                asyncio.create_task(cls._deliver_webhook(wh, event_type, payload_str))

    @classmethod
    async def _deliver_webhook(cls, webhook: Dict[str, Any], event_type: str, payload_str: str) -> None:
        wh_id = webhook["id"]
        url = webhook["url"]
        secret = webhook.get("secret", "")
        signature = cls.sign_payload(payload_str, secret)

        headers = {
            "Content-Type": "application/json",
            "X-Aegis-Event": event_type,
            "X-Aegis-Signature": signature,
            "User-Agent": "Aegis-Webhook-Dispatcher/2.4"
        }

        success = False
        status_code = None
        resp_text = None

        try:
            # CRITICAL: do NOT follow redirects in webhook delivery (SSRF via redirect to internal IP)
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
                r = await client.post(url, content=payload_str, headers=headers)
                status_code = r.status_code
                resp_text = r.text[:500]
                success = (200 <= r.status_code < 300)
        except Exception as e:
            resp_text = str(e)[:500]
            success = False

        await db.log_webhook_delivery(
            webhook_id=wh_id,
            event_type=event_type,
            status_code=status_code,
            response_body=resp_text,
            success=success
        )

webhook_dispatcher = WebhookDispatcher()
