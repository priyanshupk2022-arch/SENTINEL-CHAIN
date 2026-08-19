"""Unified Aegis Forensic Sanitization & Risk Evaluation Engine."""
import time
from typing import List, Dict, Any, Tuple, Optional
from app.models.schemas import ScanFinding, ScanReport
from app.forensics.unicode_sanitizer import UnicodeSanitizer
from app.forensics.prompt_guard import PromptGuard
from app.compliance.pii_masker import PIIMasker
from app.forensics.pdf_inspector import PDFAnalyzer
from app.forensics.docx_inspector import DOCXAnalyzer
from app.config import settings

SEVERITY_WEIGHTS = {
    "CRITICAL": 35.0,
    "HIGH": 20.0,
    "MEDIUM": 10.0,
    "LOW": 5.0
}

class ForensicSanitizer:
    """
    Orchestrates the entire multi-stage forensic pipeline:
    1. Unicode Steganography & Homoglyph normalization.
    2. Prompt Injection & Delimiter Breakout heuristics.
    3. PII & Secret Redaction (Luhn, SSN, API keys).
    4. Multi-Layer Binary Document parsing (PDF & DOCX).
    5. Calculates composite risk score and SLA latency.
    """

    @staticmethod
    def scan_text(
        raw_text: str,
        apply_pii: bool = True,
        strict_mode: bool = False
    ) -> ScanReport:
        t0 = time.perf_counter()
        findings: List[ScanFinding] = []
        
        if not raw_text:
            return ScanReport(
                is_safe=True,
                is_blocked=False,
                risk_score=0.0,
                execution_time_ms=0.0,
                findings=[],
                sanitized_text="",
                original_text_preview=""
            )

        # Stage 1: Unicode & Homoglyph sanitization
        sanitized, u_findings = UnicodeSanitizer.sanitize(raw_text)
        findings.extend(u_findings)

        # Stage 2: Prompt Injection & Delimiter Breakout Guard
        sanitized, pg_findings = PromptGuard.inspect(sanitized)
        findings.extend(pg_findings)

        # Stage 3: PII & Secret Redaction
        redaction_map: Dict[str, str] = {}
        if apply_pii:
            sanitized, pii_findings, redaction_map = PIIMasker.redact(sanitized)
            findings.extend(pii_findings)

        # Compute Risk Score
        raw_score = sum(SEVERITY_WEIGHTS.get(f.severity, 5.0) for f in findings)
        if strict_mode:
            raw_score *= 1.5
        risk_score = min(100.0, round(raw_score, 1))

        # Check blocking criteria
        has_critical = any(f.severity == "CRITICAL" for f in findings)
        is_blocked = (settings.BLOCK_ON_CRITICAL and has_critical) or (risk_score >= 60.0)
        is_safe = len(findings) == 0

        t1 = time.perf_counter()
        elapsed_ms = round((t1 - t0) * 1000.0, 2)

        return ScanReport(
            is_safe=is_safe,
            is_blocked=is_blocked,
            risk_score=risk_score,
            execution_time_ms=elapsed_ms,
            findings=findings,
            sanitized_text=sanitized,
            original_text_preview=raw_text[:200] + ("..." if len(raw_text) > 200 else ""),
            metadata={
                "redactions_count": len(redaction_map),
                "redaction_keys": list(redaction_map.keys()),
                "strict_mode": strict_mode
            }
        )

    @staticmethod
    def scan_document(
        filename: str,
        file_bytes: bytes,
        apply_pii: bool = True
    ) -> ScanReport:
        t0 = time.perf_counter()
        findings: List[ScanFinding] = []
        extracted_text = ""
        doc_metadata: Dict[str, Any] = {}

        MAX_DOCUMENT_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
        if len(file_bytes) > MAX_DOCUMENT_SIZE_BYTES:
            t1 = time.perf_counter()
            return ScanReport(
                is_safe=False,
                is_blocked=True,
                risk_score=100.0,
                execution_time_ms=round((t1 - t0) * 1000.0, 2),
                findings=[
                    ScanFinding(
                        category="resource_exhaustion",
                        severity="CRITICAL",
                        description=f"File size ({len(file_bytes) / (1024*1024):.1f} MB) exceeds maximum security limit (25 MB). Document parsing aborted.",
                        location="Document Stream",
                        original_snippet=f"Size: {len(file_bytes)} bytes"
                    )
                ],
                sanitized_text="",
                original_text_preview="[REJECTED: PAYLOAD_TOO_LARGE]",
                metadata={"filename": filename, "file_size_bytes": len(file_bytes)}
            )

        fname_lower = filename.lower()
        if fname_lower.endswith(".pdf"):
            extracted_text, doc_findings, doc_metadata = PDFAnalyzer.inspect(file_bytes)
            findings.extend(doc_findings)
        elif fname_lower.endswith(".docx"):
            extracted_text, doc_findings, doc_metadata = DOCXAnalyzer.inspect(file_bytes)
            findings.extend(doc_findings)
        else:
            try:
                extracted_text = file_bytes.decode('utf-8', errors='replace')
            except Exception:
                extracted_text = ""


        # Run text-level pipeline on extracted content
        text_report = ForensicSanitizer.scan_text(extracted_text, apply_pii=apply_pii)
        findings.extend(text_report.findings)

        # Merge findings
        raw_score = sum(SEVERITY_WEIGHTS.get(f.severity, 5.0) for f in findings)
        risk_score = min(100.0, round(raw_score, 1))
        has_critical = any(f.severity == "CRITICAL" for f in findings)
        is_blocked = (settings.BLOCK_ON_CRITICAL and has_critical) or (risk_score >= 60.0)

        t1 = time.perf_counter()
        elapsed_ms = round((t1 - t0) * 1000.0, 2)

        return ScanReport(
            is_safe=len(findings) == 0,
            is_blocked=is_blocked,
            risk_score=risk_score,
            execution_time_ms=elapsed_ms,
            findings=findings,
            sanitized_text=text_report.sanitized_text,
            original_text_preview=extracted_text[:200] + ("..." if len(extracted_text) > 200 else ""),
            metadata={
                "filename": filename,
                "file_size_bytes": len(file_bytes),
                "doc_metadata": doc_metadata
            }
        )

# Module-level instance
sanitizer = ForensicSanitizer()
