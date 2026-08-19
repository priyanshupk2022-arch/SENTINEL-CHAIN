"""Production Stripe Billing Provider with Signature Verification."""
import json
import uuid
from typing import Dict, Any, Optional
import httpx
from fastapi import HTTPException

from app.config import settings
from app.billing.interface import BillingProvider

class StripeBillingProvider(BillingProvider):
    def __init__(self, api_key: str, webhook_secret: Optional[str] = None):
        self.api_key = api_key
        self.webhook_secret = webhook_secret

    async def create_checkout_session(
        self,
        organization_id: str,
        plan: str,
        user_email: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            data = {
                "payment_method_types[]": "card",
                "mode": "subscription",
                "customer_email": user_email,
                "client_reference_id": organization_id,
                "success_url": success_url or "http://localhost:8000/dashboard?session_id={CHECKOUT_SESSION_ID}",
                "cancel_url": cancel_url or "http://localhost:8000/dashboard?canceled=true",
                "metadata[organization_id]": organization_id,
                "metadata[plan]": plan
            }
            r = await client.post("https://api.stripe.com/v1/checkout/sessions", data=data, headers=headers)
            res_data = r.json()
            if r.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Stripe error: {res_data.get('error', {}).get('message')}")
            return {
                "checkout_url": res_data.get("url"),
                "session_id": res_data.get("id"),
                "provider": "stripe",
                "plan": plan
            }

    async def handle_webhook(
        self,
        payload_bytes: bytes,
        signature_header: str
    ) -> Dict[str, Any]:
        # CRITICAL: when the operator has configured Stripe (api_key + webhook_secret),
        # signature verification is mandatory. The previous fallback that accepted
        # any JSON body when no signature header was present allowed arbitrary
        # entitlement changes — fix it by always requiring signature when secret is set.
        if not self.webhook_secret:
            # Without a configured webhook secret we cannot verify authenticity;
            # in production this path must not be reachable.
            from app.config import settings
            if settings.ENVIRONMENT == "production":
                raise HTTPException(
                    status_code=503,
                    detail="Stripe webhook secret is not configured. Refusing to process unsigned webhooks in production."
                )
            # Dev-only: log and accept the event so local testing still works
            event = json.loads(payload_bytes.decode("utf-8")) if payload_bytes else {}
        else:
            if not signature_header:
                raise HTTPException(status_code=400, detail="Missing Stripe-Signature header.")
            try:
                import stripe
                event = stripe.Webhook.construct_event(
                    payload_bytes, signature_header, self.webhook_secret
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid Stripe webhook signature: {str(e)}")

        event_type = event.get("type", "")
        data_object = event.get("data", {}).get("object", {})

        # CRITICAL: when a subscription event is observed, propagate the
        # entitlement change to the local database so the proxy's quota
        # enforcement matches the customer's actual billing state.
        try:
            from app.models.database import db
            if event_type == "checkout.session.completed":
                org_id = data_object.get("client_reference_id") or data_object.get("metadata", {}).get("organization_id")
                plan = (data_object.get("metadata", {}).get("plan") or "pro").lower()
                if org_id:
                    await db.update_subscription(
                        organization_id=org_id,
                        plan=plan,
                        status="active",
                        stripe_customer_id=data_object.get("customer"),
                        stripe_subscription_id=data_object.get("subscription"),
                    )
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
        except Exception:
            # never fail the webhook handler on a propagation error
            pass

        return {
            "status": "processed",
            "event_type": event_type,
            "data": data_object
        }
