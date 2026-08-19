import re
import logging
from typing import Tuple
from bs4 import BeautifulSoup
from backend.app.models.repair_proposal import RepairProposal

logger = logging.getLogger("sentinel.validator")

# Regex to detect suspicious shell characters in repair prompts
DANGEROUS_SHELL_PATTERNS = [
    r";", r"&&", r"\|\|", r"\|", r"`", r"\$\(", r"\$\{",
    r">", r"<", r"\brm\b", r"\bcurl\b", r"\bwget\b", r"\bsh\b",
    r"\bbash\b", r"\bexec\b", r"--[a-zA-Z0-9_-]+"
]

class RepairValidator:
    def __init__(self, min_confidence: float = 0.8):
        self.min_confidence = min_confidence

    def validate(self, proposal: RepairProposal, dom_html: str) -> Tuple[bool, str]:
        """
        Deterministically verifies the AI RepairProposal before allowing execution.
        Enforces confidence threshold, shell safety, and DOM match verification.
        """
        # 1. Check confidence threshold
        if proposal.confidence < self.min_confidence:
            return False, f"Confidence {proposal.confidence:.2f} is below required threshold {self.min_confidence:.2f}"

        # 2. Check for empty fields
        if not proposal.repair_prompt or not proposal.proposed_selector:
            return False, "Missing repair_prompt or proposed_selector in RepairProposal"

        # 3. Check for shell injection / disallowed characters in repair_prompt
        for pattern in DANGEROUS_SHELL_PATTERNS:
            if re.search(pattern, proposal.repair_prompt):
                logger.warning(f"Disallowed token/pattern matched in repair_prompt: {pattern}")
                return False, f"Repair prompt contains disallowed shell injection pattern: {pattern}"

        # 4. Verify proposed_selector matches elements in target DOM
        if dom_html:
            try:
                soup = BeautifulSoup(dom_html, "html.parser")
                selector = proposal.proposed_selector.strip()
                
                # Check CSS selector matching
                matched_elements = soup.select(selector)
                if not matched_elements:
                    # Fallback check for basic class/tag presence
                    clean_token = selector.replace(".", "").replace("#", "").split(" ")[0].split(">")[0]
                    if clean_token not in dom_html:
                        return False, f"Proposed selector '{selector}' not found in target DOM markup"
            except Exception as e:
                # If CSS selector is invalid syntax
                clean_token = proposal.proposed_selector.replace(".", "").replace("#", "").split(" ")[0]
                if clean_token not in dom_html:
                    return False, f"Selector validation error: {str(e)}"

        return True, "VALID"
