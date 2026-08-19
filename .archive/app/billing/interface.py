"""Abstract Billing Provider Interface."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BillingProvider(ABC):
    @abstractmethod
    async def create_checkout_session(
        self,
        organization_id: str,
        plan: str,
        user_email: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates a checkout session URL."""
        pass

    @abstractmethod
    async def handle_webhook(
        self,
        payload_bytes: bytes,
        signature_header: str
    ) -> Dict[str, Any]:
        """Handles verified provider webhooks."""
        pass
