"""Test PII Masker & Secret Redaction."""
import pytest
from app.compliance.pii_masker import PIIMasker, luhn_checksum_is_valid

def test_luhn_algorithm_validation():
    # Valid Visa card
    assert luhn_checksum_is_valid("4532015112830366") is True
    # Invalid card number (fails checksum)
    assert luhn_checksum_is_valid("4532015112830367") is False
    # Short length
    assert luhn_checksum_is_valid("1234") is False

def test_credit_card_redaction():
    text = "My credit card is 4532-0151-1283-0366 and phone is 555-123-4567."
    sanitized, findings, r_map = PIIMasker.redact(text)
    assert "4532-0151-1283-0366" not in sanitized
    assert "<REDACTED:CREDIT_CARD_1>" in sanitized
    assert "<REDACTED:PHONE_NUMBER_1>" in sanitized
    assert len(findings) >= 2

def test_ssn_redaction():
    text = "User SSN is 123-45-6789 confidential."
    sanitized, findings, _ = PIIMasker.redact(text)
    assert "123-45-6789" not in sanitized
    assert "<REDACTED:SSN_1>" in sanitized

def test_api_keys_redaction():
    text = "Here is my secret sk-proj-abc12345678901234567890 and AWS key AKIAIOSFODNN7EXAMPLE"
    sanitized, findings, _ = PIIMasker.redact(text)
    assert "sk-proj-abc12345678901234567890" not in sanitized
    assert "AKIAIOSFODNN7EXAMPLE" not in sanitized
    assert "<REDACTED:OPENAI_API_KEY_1>" in sanitized
    assert "<REDACTED:AWS_ACCESS_KEY_1>" in sanitized
    assert any(f.severity == "CRITICAL" for f in findings)
