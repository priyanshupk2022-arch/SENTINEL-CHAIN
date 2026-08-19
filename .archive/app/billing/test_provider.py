"""Deterministic Test Billing Provider for Offline & CI Environments."""
import uuid
from typing import Dict, Any, Optional
from app.billing.interface import BillingProvider

class DeterministicTestBillingProvider(BillingProvider):
    async def create_checkout_session(
        self,
        organization_id: str,
        plan: str,
        user_email: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, Any]:
        session_id = f"test_cs_{uuid.uuid4().hex[:16]}"
        return {
            "checkout_url": f"/dashboard?upgrade_success=true&session_id={session_id}&plan={plan}",
            "session_id": session_id,
            "provider": "test_deterministic",
            "plan": plan
        }

    async def handle_webhook(
        self,
        payload_bytes: bytes,
        signature_header: str
    ) -> Dict[str, Any]:
        try:
            import json
            from app.models.database import db
            data = json.loads(payload_bytes.decode('utf-8')) if isinstance(payload_bytes, (bytes, bytearray)) else payload_bytes
            evt_type = data.get("type", "")
            obj = data.get("data", {}).get("object", {})
            org_id = obj.get("metadata", {}).get("organization_id")
            if org_id:
                if evt_type in ("customer.subscription.deleted", "subscription.canceled") or obj.get("status") == "canceled":
                    await db.update_subscription(org_id, "free", status="canceled")
                elif evt_type in ("checkout.session.completed", "customer.subscription.created"):
                    plan = obj.get("metadata", {}).get("plan", "pro")
                    await db.update_subscription(org_id, plan, status="active")
        except Exception:
            pass

        return {
            "status": "processed",
            "received": True,
            "provider": "test_deterministic"
        }

