"""Unified Billing Service Delegating to Configured Provider."""
from typing import Dict, Any, Optional

from app.config import settings
from app.billing.interface import BillingProvider
from app.billing.stripe_provider import StripeBillingProvider
from app.billing.test_provider import DeterministicTestBillingProvider

class BillingService:
    def __init__(self):
        if settings.STRIPE_SECRET_KEY and not settings.ENABLE_MOCK_BILLING:
            self.provider: BillingProvider = StripeBillingProvider(
                api_key=settings.STRIPE_SECRET_KEY,
                webhook_secret=settings.STRIPE_WEBHOOK_SECRET
            )
        else:
            self.provider: BillingProvider = DeterministicTestBillingProvider()

    async def create_checkout_session(
        self,
        organization_id: str,
        plan: str,
        user_email: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, Any]:
        return await self.provider.create_checkout_session(
            organization_id=organization_id,
            plan=plan,
            user_email=user_email,
            success_url=success_url,
            cancel_url=cancel_url
        )

    async def handle_webhook(
        self,
        payload_bytes: bytes,
        signature_header: str
    ) -> Dict[str, Any]:
        return await self.provider.handle_webhook(
            payload_bytes=payload_bytes,
            signature_header=signature_header
        )

billing_service = BillingService()
