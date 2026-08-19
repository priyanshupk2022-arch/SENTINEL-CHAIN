"""Adversarial Levels 1 to 4 Verification Test Suite for Aegis."""
from pathlib import Path
import pytest
from app.forensics.sanitizer import sanitizer
from app.forensics.unicode_sanitizer import UnicodeSanitizer
from app.forensics.pdf_analyzer import PDFAnalyzer
from app.forensics.docx_analyzer import DOCXAnalyzer

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

class TestAdversarialLevels:
    """End-to-end verification that all multi-layer adversarial attack vectors (Level 1-4) are blocked."""

    def test_level1_unicode_steganography_and_homoglyphs(self):
        """Level 1: Zero-Width Characters + Cyrillic Homoglyphs."""
        fixture_path = FIXTURES_DIR / "level1_unicode_homoglyphs.txt"
        assert fixture_path.exists(), "Level 1 fixture missing"

        raw_content = fixture_path.read_text(encoding="utf-8")
        report = sanitizer.scan_text(raw_content)

        # 1. Zero-width characters must be stripped
        for zw in ['\u200B', '\u200C', '\u200D', '\uFEFF', '\u202E']:
            assert zw not in report.sanitized_text

        # 2. Cyrillic homoglyphs must be normalized to standard ASCII
        assert "Password" in report.sanitized_text
        assert "admin" in report.sanitized_text

        # 3. Findings & Security assessment
        categories = {f.category for f in report.findings}
        assert "steganography" in categories
        assert "homoglyph" in categories
        assert "prompt_injection" in categories

        assert report.is_blocked is True
        assert report.risk_score >= 60.0

    def test_level2_pii_leakage_and_delimiter_injection(self):
        """Level 2: Valid Luhn Credit Card + SSN + API Keys + Delimiter Breakouts."""
        fixture_path = FIXTURES_DIR / "level2_pii_and_injection.txt"
        assert fixture_path.exists(), "Level 2 fixture missing"

        raw_content = fixture_path.read_text(encoding="utf-8")
        report = sanitizer.scan_text(raw_content)

        # 1. Verify all PII elements are sanitized with redaction tags
        assert "4532-0151-1283-0366" not in report.sanitized_text
        assert "<REDACTED:CREDIT_CARD" in report.sanitized_text

        assert "123-45-6789" not in report.sanitized_text
        assert "<REDACTED:SSN" in report.sanitized_text

        assert "sk-proj-" not in report.sanitized_text
        assert "<REDACTED:OPENAI_API_KEY" in report.sanitized_text

        assert "AKIAIOSFODNN7EXAMPLE" not in report.sanitized_text
        assert "<REDACTED:AWS_ACCESS_KEY" in report.sanitized_text

        assert "john.doe.security@example.com" not in report.sanitized_text
        assert "<REDACTED:EMAIL_ADDRESS" in report.sanitized_text

        # 2. Delimiter & Prompt Injection detection
        categories = {f.category for f in report.findings}
        assert "pii_leak" in categories
        assert "delimiter_breakout" in categories
        assert "prompt_injection" in categories

        assert report.is_blocked is True
        assert report.risk_score >= 80.0

    def test_level3_adversarial_white_text_and_micro_fonts_pdf(self):
        """Level 3: White-on-white text, micro-fonts (<1pt), and off-canvas text in PDF."""
        fixture_path = FIXTURES_DIR / "level3_adversarial_white_text.pdf"
        assert fixture_path.exists(), "Level 3 PDF fixture missing"

        pdf_bytes = fixture_path.read_bytes()
        report = sanitizer.scan_document("level3_adversarial_white_text.pdf", pdf_bytes)

        categories = {f.category for f in report.findings}
        
        # Verify all Level 3 evasion techniques are detected
        assert "white_text" in categories, "Invisible white text was not detected"
        assert "micro_font" in categories, "Micro-font (<1pt) was not detected"
        assert "off_canvas" in categories, "Off-canvas rendering was not detected"
        assert "metadata_injection" in categories, "Metadata prompt injection was not detected"

        assert report.is_blocked is True
        assert report.risk_score == 100.0

    def test_level4_hidden_openxml_and_metadata_injections_docx(self):
        """Level 4: OpenXML hidden runs (w:vanish), white fonts, table steganography, metadata in DOCX."""
        fixture_path = FIXTURES_DIR / "level4_hidden_docx.docx"
        assert fixture_path.exists(), "Level 4 DOCX fixture missing"

        docx_bytes = fixture_path.read_bytes()
        report = sanitizer.scan_document("level4_hidden_docx.docx", docx_bytes)

        categories = {f.category for f in report.findings}

        # Verify all Level 4 OpenXML vectors are detected
        assert "hidden_text" in categories, "w:vanish hidden text run was not detected"
        assert "white_text" in categories, "White font (#FFFFFF) was not detected"
        assert "micro_font" in categories, "Micro-font size was not detected"
        assert "metadata_injection" in categories, "CoreProperties metadata injection was not detected"

        assert report.is_blocked is True
        assert report.risk_score == 100.0
