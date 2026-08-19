from pydantic import BaseModel, Field, field_validator
import re

class RepairProposal(BaseModel):
    diagnosis: str = Field(..., description="Root cause explanation of why extraction failed")
    target_field: str = Field(..., description="The field being targeted, e.g. cve_id, title, severity")
    evidence: str = Field(..., description="Extracted snippet or reasoning from DOM/AOM")
    proposed_selector: str = Field(..., description="CSS/XPath selector for the element")
    repair_prompt: str = Field(..., description="Natural language prompt passed to Bright Data CLI heal command")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0 (must be >= 0.8)")
    expected_output: str = Field(..., description="Expected sample value from the target field")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if v < 0.8:
            raise ValueError("Confidence must be at least 0.8 for autonomous approval")
        return v

    @field_validator("repair_prompt")
    @classmethod
    def sanitize_repair_prompt(cls, v: str) -> str:
        # Prevent CLI injection characters or shell metacharacters
        forbidden = [";", "&&", "||", "`", "$", "|", ">", "<", "\n", "\r"]
        for char in forbidden:
            if char in v:
                raise ValueError(f"Repair prompt contains illegal shell character: {char}")
        if len(v.strip()) < 5 or len(v.strip()) > 500:
            raise ValueError("Repair prompt length must be between 5 and 500 characters")
        return v.strip()
