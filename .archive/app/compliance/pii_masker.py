"""PII & Sensitive Credential Detection and Redaction Engine."""
import re
from typing import Tuple, List, Dict
from app.models.schemas import ScanFinding

def luhn_checksum_is_valid(card_number_str: str) -> bool:
    """Validates credit card number with standard Luhn algorithm."""
    digits = [int(c) for c in card_number_str if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = digit * 2
            checksum += (doubled - 9) if doubled > 9 else doubled
        else:
            checksum += digit
    return checksum % 10 == 0

# Compiled regex patterns for fast evaluation (<2ms overhead)
REGEX_SSN = re.compile(r'\b(?!000|666)\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b')
REGEX_EMAIL = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
REGEX_PHONE = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
REGEX_CREDIT_CARD = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b|\b\d{13,19}\b')
REGEX_OPENAI_KEY = re.compile(r'\bsk-(?:proj-|live-)?[a-zA-Z0-9_-]{20,}\b')
REGEX_AWS_KEY = re.compile(r'\bAKIA[0-9A-Z]{16}\b')
REGEX_JWT = re.compile(r'\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b')
REGEX_PRIVATE_KEY = re.compile(r'-----BEGIN (?:[A-Z0-9_-]+\s+)?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z0-9_-]+\s+)?PRIVATE KEY-----')
REGEX_PASSPORT = re.compile(r'\b[A-Z][0-9]{8}\b')


class PIIMasker:
    @staticmethod
    def redact(text: str) -> Tuple[str, List[ScanFinding], Dict[str, str]]:
        findings: List[ScanFinding] = []
        redaction_map: Dict[str, str] = {}
        if not text:
            return "", findings, redaction_map

        sanitized = text
        counter: Dict[str, int] = {}

        def _replace_match(match: re.Match, pii_type: str, severity: str, validate_func=None) -> str:
            val = match.group(0)
            if validate_func and not validate_func(val):
                return val
            
            counter[pii_type] = counter.get(pii_type, 0) + 1
            placeholder = f"<REDACTED:{pii_type}_{counter[pii_type]}>"
            redaction_map[placeholder] = val
            
            findings.append(ScanFinding(
                category="pii_leak",
                severity=severity,
                description=f"Sensitive {pii_type} detected and sanitized.",
                original_snippet=f"{val[:4]}...{val[-2:]}" if len(val) > 6 else "***",
                redacted_snippet=placeholder
            ))
            return placeholder

        # 1. API Keys & Secrets (CRITICAL)
        sanitized = REGEX_PRIVATE_KEY.sub(lambda m: _replace_match(m, "PRIVATE_KEY_BLOCK", "CRITICAL"), sanitized)
        sanitized = REGEX_OPENAI_KEY.sub(lambda m: _replace_match(m, "OPENAI_API_KEY", "CRITICAL"), sanitized)
        sanitized = REGEX_AWS_KEY.sub(lambda m: _replace_match(m, "AWS_ACCESS_KEY", "CRITICAL"), sanitized)
        sanitized = REGEX_JWT.sub(lambda m: _replace_match(m, "JWT_BEARER_TOKEN", "CRITICAL"), sanitized)

        # 2. Credit Cards (HIGH, verified by Luhn)
        sanitized = REGEX_CREDIT_CARD.sub(lambda m: _replace_match(m, "CREDIT_CARD", "HIGH", luhn_checksum_is_valid), sanitized)

        # 3. Social Security Numbers & Passports (HIGH)
        sanitized = REGEX_SSN.sub(lambda m: _replace_match(m, "SSN", "HIGH"), sanitized)
        sanitized = REGEX_PASSPORT.sub(lambda m: _replace_match(m, "PASSPORT_NUMBER", "HIGH"), sanitized)

        # 4. Emails & Phones (MEDIUM)
        sanitized = REGEX_EMAIL.sub(lambda m: _replace_match(m, "EMAIL_ADDRESS", "MEDIUM"), sanitized)
        sanitized = REGEX_PHONE.sub(lambda m: _replace_match(m, "PHONE_NUMBER", "MEDIUM"), sanitized)


        return sanitized, findings, redaction_map
