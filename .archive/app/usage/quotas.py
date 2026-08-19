"""Central Entitlement & Quota Enforcement Engine."""
from typing import Dict, Any
from fastapi import HTTPException, status

class QuotaExceededException(HTTPException):
    def __init__(self, org_name: str, tier: str, current_usage: int, limit: int):
        detail = {
            "error": {
                "code": "QUOTA_EXCEEDED",
                "message": f"Monthly API quota of {limit:,} requests exceeded for organization '{org_name}'. Please upgrade your subscription tier.",
                "retry_after": 86400,
                "tier": tier,
                "current_usage": current_usage,
                "limit": limit
            }
        }
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )

class QuotaService:
    @staticmethod
    def enforce_request_quota(org_data: Dict[str, Any]) -> None:
        """
        Validates whether the organization is within its monthly request limit.
        Raises QuotaExceededException (HTTP 429) if exceeded.
        """
        current = org_data.get("current_period_requests", 0)
        limit = org_data.get("max_monthly_requests", 1000)
        tier = org_data.get("tier", "free")
        name = org_data.get("name", "Unknown Organization")

        if current >= limit:
            raise QuotaExceededException(
                org_name=name,
                tier=tier,
                current_usage=current,
                limit=limit
            )

quota_service = QuotaService()
