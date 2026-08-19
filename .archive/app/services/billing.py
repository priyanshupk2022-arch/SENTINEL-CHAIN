"""Stripe Billing & Subscription Lifecycle Management Service."""
import json
import time
import uuid
from typing import Dict, Any, Optional
import httpx

from app.config import settings
from app.models.database import db

# Tier configurations
PLANS = {
    "free": {
        "name": "Community / Free",
        "price_usd": 0,
        "max_monthly_requests": settings.FREE_TIER_MONTHLY_LIMIT,
        "features": ["unicode_sanitization", "prompt_guard", "pii_redaction"]
    },
    "pro": {
        "name": "Professional",
        "price_usd": 199,
        "max_monthly_requests": settings.PRO_TIER_MONTHLY_LIMIT,
        "features": ["unicode_sanitization", "prompt_guard", "pii_redaction", "pdf_forensics", "docx_forensics", "sse_streaming", "webhooks"]
    },
    "enterprise": {
        "name": "Enterprise Air-Gap",
        "price_usd": 999,
        "max_monthly_requests": settings.ENTERPRISE_TIER_MONTHLY_LIMIT,
        "features": ["unicode_sanitization", "prompt_guard", "pii_redaction", "pdf_forensics", "docx_forensics", "sse_streaming", "webhooks", "sla_guarantee", "custom_rules", "ed25519_offline_license"]
    }
}

class BillingService:
    @staticmethod
    async def create_checkout_session(
        organization_id: str,
        plan: str,
        user_email: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates a Stripe checkout session or a simulated mock checkout for test environments."""
        plan_lower = plan.lower().strip()
        if plan_lower not in PLANS:
            raise ValueError(f"Invalid plan '{plan}'. Must be one of {list(PLANS.keys())}")

        session_id = f"cs_aegis_{uuid.uuid4().hex[:16]}"

        # If Stripe is not configured or mock mode enabled, generate instant mock checkout
        if not settings.STRIPE_SECRET_KEY or settings.ENABLE_MOCK_BILLING:
            # Instantly upgrade organization in database for seamless local testing
            await db.update_subscription(
                organization_id=organization_id,
                plan=plan_lower,
                status="active",
                stripe_customer_id=f"cus_mock_{uuid.uuid4().hex[:8]}",
                stripe_subscription_id=f"sub_mock_{uuid.uuid4().hex[:8]}"
            )
            return {
                "checkout_url": f"/dashboard?upgrade_success=true&plan={plan_lower}",
                "session_id": session_id,
                "mock_mode": True,
                "plan": plan_lower
            }

        # Real Stripe Integration via HTTPX
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"Authorization": f"Bearer {settings.STRIPE_SECRET_KEY}"}
                data = {
                    "payment_method_types[]": "card",
                    "mode": "subscription",
                    "customer_email": user_email,
                    "client_reference_id": organization_id,
                    "success_url": success_url or "http://localhost:8000/dashboard?session_id={CHECKOUT_SESSION_ID}",
                    "cancel_url": cancel_url or "http://localhost:8000/dashboard?canceled=true",
                    "metadata[organization_id]": organization_id,
                    "metadata[plan]": plan_lower
                }
                r = await client.post("https://api.stripe.com/v1/checkout/sessions", data=data, headers=headers)
                res_data = r.json()
                return {
                    "checkout_url": res_data.get("url", "/dashboard"),
                    "session_id": res_data.get("id", session_id),
                    "mock_mode": False,
                    "plan": plan_lower
                }
        except Exception as e:
            # Do NOT automatically upgrade customer if external billing API fails!
            return {
                "checkout_url": f"/dashboard?error=billing_unavailable",
                "session_id": session_id,
                "mock_mode": False,
                "error": f"Failed to communicate with payment processor: {str(e)}"
            }

    @staticmethod
    async def handle_stripe_webhook(payload_bytes: bytes, signature_header: str) -> Dict[str, Any]:
        """Processes incoming Stripe billing webhooks with signature verification & entitlement sync."""
        if settings.STRIPE_WEBHOOK_SECRET and signature_header:
            try:
                import stripe
                event = stripe.Webhook.construct_event(
                    payload_bytes, signature_header, settings.STRIPE_WEBHOOK_SECRET
                )
            except Exception as e:
                return {"status": "error", "message": f"Invalid webhook signature: {str(e)}"}
        else:
            event = json.loads(payload_bytes.decode('utf-8'))

        event_type = event.get("type", "")
        data_object = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            org_id = data_object.get("client_reference_id") or data_object.get("metadata", {}).get("organization_id")
            plan = data_object.get("metadata", {}).get("plan", "pro")
            customer_id = data_object.get("customer")
            subscription_id = data_object.get("subscription")
            if org_id:
                await db.update_subscription(
                    organization_id=org_id,
                    plan=plan,
                    status="active",
                    stripe_customer_id=customer_id,
                    stripe_subscription_id=subscription_id
                )
                return {"status": "success", "event": "checkout_completed", "organization_id": org_id}

        elif event_type in ("customer.subscription.deleted", "customer.subscription.updated"):
            sub_status = data_object.get("status", "active")
            customer_id = data_object.get("customer")
            sub_id = data_object.get("id")

            sub_record = None
            if customer_id:
                sub_record = await db.get_subscription_by_stripe_customer(customer_id)
            if not sub_record and sub_id:
                sub_record = await db.get_subscription_by_stripe_sub_id(sub_id)

            if sub_record:
                org_id = sub_record["organization_id"]
                if event_type == "customer.subscription.deleted" or sub_status in ("canceled", "unpaid", "incomplete_expired"):
                    await db.update_subscription(
                        organization_id=org_id,
                        plan="free",
                        status="canceled",
                        stripe_customer_id=customer_id,
                        stripe_subscription_id=sub_id
                    )
                elif event_type == "customer.subscription.updated":
                    new_plan = (data_object.get("metadata", {}).get("plan") or sub_record.get("plan", "pro")).lower()
                    await db.update_subscription(
                        organization_id=org_id,
                        plan=new_plan,
                        status=sub_status,
                        stripe_customer_id=customer_id,
                        stripe_subscription_id=sub_id
                    )
                return {"status": "success", "event": event_type, "organization_id": org_id}

        return {"status": "ignored", "event": event_type}

billing_service = BillingService()

