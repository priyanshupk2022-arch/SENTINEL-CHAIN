"""Password complexity policy for the Aegis control plane.

Replaces the previous `min_length=8` Pydantic constraint which accepted
trivial passwords like "password" or "12345678".
"""
import re
from typing import Tuple

_MIN_LENGTH = 12

_COMMON = {
    "password", "123456789012", "qwertyuiop12", "letmein123456",
    "welcome12345", "admin1234567", "iloveyou12345",
}


def validate_password_strength(password: str) -> Tuple[bool, str]:
    if password is None:
        return False, "Password is required."
    if len(password) < _MIN_LENGTH:
        return False, f"Password must be at least {_MIN_LENGTH} characters long."
    if len(password) > 256:
        return False, "Password must be 256 characters or fewer."
    has_lower = bool(re.search(r"[a-z]", password))
    has_upper = bool(re.search(r"[A-Z]", password))
    has_digit = bool(re.search(r"\d", password))
    has_symbol = bool(re.search(r"[^A-Za-z0-9]", password))
    classes = sum([has_lower, has_upper, has_digit, has_symbol])
    if classes < 3:
        return False, "Password must contain at least 3 of: lowercase, uppercase, digit, symbol."
    if password.lower() in _COMMON:
        return False, "Password is too common; choose a different one."
    # Reject obvious sequences
    if re.search(r"(.)\1{4,}", password):
        return False, "Password may not contain 5+ repeated characters."
    if re.search(r"(0123|1234|2345|3456|4567|5678|6789|abcd|qwer|asdf|zxcv)", password.lower()):
        return False, "Password may not contain a simple sequence."
    return True, "Password accepted."
