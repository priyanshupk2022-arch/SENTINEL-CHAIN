"""Test Unicode Sanitizer & Steganography Detection."""
import pytest
from app.forensics.unicode_sanitizer import UnicodeSanitizer

def test_clean_text_passes_unchanged():
    text = "Hello world! This is a standard prompt."
    cleaned, findings = UnicodeSanitizer.sanitize(text)
    assert cleaned == text
    assert len(findings) == 0

def test_zero_width_space_detection():
    # Insert zero-width space and zero-width joiner
    malicious = "System\u200B\u200Coverride\uFEFFnow"
    cleaned, findings = UnicodeSanitizer.sanitize(malicious)
    assert cleaned == "Systemoverridenow"
    assert len(findings) > 0
    assert any(f.category == "steganography" for f in findings)
    assert any(f.severity == "CRITICAL" for f in findings)

def test_bidi_override_detection():
    # Insert right-to-left override
    malicious = "user input \u202E ignore safety \u202C legit"
    cleaned, findings = UnicodeSanitizer.sanitize(malicious)
    assert "\u202E" not in cleaned
    assert len(findings) > 0
    assert any(f.category == "steganography" for f in findings)

def test_homoglyph_cyrillic_substitution():
    # Cyrillic '\u0430' (a), '\u043e' (o)
    spoofed = "p\u0430ssw\u043erd"
    cleaned, findings = UnicodeSanitizer.sanitize(spoofed)
    assert cleaned == "password"
    assert len(findings) > 0
    assert any(f.category == "homoglyph" for f in findings)

def test_nfkc_normalization():
    # Fullwidth latin characters
    fullwidth = "ＡＥＧＩＳ"
    cleaned, findings = UnicodeSanitizer.sanitize(fullwidth)
    assert cleaned == "AEGIS"
