import re
import logging
from typing import Tuple
from bs4 import BeautifulSoup
from backend.app.models.repair_proposal import RepairProposal

logger = logging.getLogger("sentinel.validator")

# Comprehensive regex to detect suspicious shell characters and commands in repair prompts
DANGEROUS_SHELL_PATTERNS = [
    r";", r"&&", r"\|\|", r"\|", r"`", r"\$\(", r"\$\{",
    r">", r"<", r"\brm\b", r"\bcurl\b", r"\bwget\b", r"\bsh\b",
    r"\bbash\b", r"\bexec\b", r"\bpwsh\b", r"\bpowershell\b",
    r"\bcmd\b", r"\bnode\b", r"\bpython\b", r"--[a-zA-Z0-9_-]+",
    # Control characters (incl. NUL) are never legitimate in a natural-language
    # repair prompt and can corrupt argv handling downstream.
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
]

class RepairValidator:
    def __init__(self, min_confidence: float = 0.8):
        self.min_confidence = min_confidence

    def validate(self, proposal: RepairProposal, dom_html: str) -> Tuple[bool, str]:
        """
        Deterministically verifies the AI RepairProposal before allowing execution.
        Enforces confidence threshold, shell safety, and strict DOM element match verification.
        """
        # 1. Check confidence threshold
        if proposal.confidence < self.min_confidence:
            return False, f"Confidence {proposal.confidence:.2f} is below required threshold {self.min_confidence:.2f}"

        # 2. Check for empty fields
        if not proposal.repair_prompt or not proposal.proposed_selector:
            return False, "Missing repair_prompt or proposed_selector in RepairProposal"

        # 3. Check for shell injection / disallowed characters in repair_prompt
        for pattern in DANGEROUS_SHELL_PATTERNS:
            if re.search(pattern, proposal.repair_prompt, re.IGNORECASE):
                logger.warning(f"Disallowed token/pattern matched in repair_prompt: {pattern}")
                return False, f"Repair prompt contains disallowed shell injection pattern: {pattern}"

        # 4. Strict CSS Selector verification in target DOM
        if dom_html:
            try:
                soup = BeautifulSoup(dom_html, "html.parser")
                selector = proposal.proposed_selector.strip()
                
                matched_elements = soup.select(selector)
                if not matched_elements:
                    # Fallback check for exact class/id token
                    raw_token = selector.replace(".", "").replace("#", "").split(" ")[0].split(">")[0]
                    if raw_token not in dom_html:
                        return False, f"Proposed selector '{selector}' does not resolve to any element in target DOM markup"
            except Exception as e:
                return False, f"Selector validation syntax error: {str(e)}"

        return True, "VALID"

# Aliases
ProposalValidator = RepairValidator
