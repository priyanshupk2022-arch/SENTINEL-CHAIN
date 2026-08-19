"""Multi-Layer PDF Forensic Parsing Engine with Layer, Annotation, and Steganography Detection."""
try:
    import pymupdf as fitz
except ImportError:
    import fitz

import io
import math
from typing import Tuple, List, Dict, Any, Optional
from app.models.schemas import ScanFinding
from app.forensics.unicode_sanitizer import UnicodeSanitizer

def color_distance(c1: Tuple[float, float, float], c2: Tuple[float, float, float]) -> float:
    """Calculates Euclidean distance in RGB color space (0.0 to 1.0 components)."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

class PDFAnalyzer:
    """
    Advanced Multi-Layer PDF Forensic Analyzer.
    Detects:
    1. Invisible White-on-White text.
    2. Sub-pixel / Micro-fonts (< 2.0 pt).
    3. Off-canvas / Out-of-bounds text positioning.
    4. Hidden Optional Content Groups (OCG layers).
    5. Hidden Annotations / Forms / JavaScript action streams.
    6. Steganographic payloads in PDF metadata (Author, Subject, Keywords, Title).
    """
    @staticmethod
    def inspect(file_bytes: bytes) -> Tuple[str, List[ScanFinding], Dict[str, Any]]:
        findings: List[ScanFinding] = []
        extracted_text_blocks: List[str] = []
        metadata_findings: Dict[str, Any] = {}
        
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            metadata = doc.metadata or {}
            metadata_findings = {
                "page_count": len(doc),
                "author": metadata.get("author", ""),
                "title": metadata.get("title", ""),
                "subject": metadata.get("subject", ""),
                "keywords": metadata.get("keywords", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", "")
            }
            
            # 1. Inspect Metadata for Injection Payloads
            for key in ["author", "title", "subject", "keywords"]:
                val = metadata.get(key, "")
                if val:
                    _, u_findings = UnicodeSanitizer.sanitize(val)
                    if u_findings:
                        findings.extend(u_findings)
                    
                    val_lower = val.lower()
                    if any(bad in val_lower for bad in [
                        "ignore previous", "system override", "<|im_start|>", 
                        "admin override", "developer mode", "disregard instructions"
                    ]):
                        findings.append(ScanFinding(
                            category="metadata_injection",
                            severity="CRITICAL",
                            description=f"Prompt injection payload detected in PDF metadata field '{key}'.",
                            location=f"PDF Metadata: {key}",
                            original_snippet=val
                        ))

            # 2. Check for Embedded JavaScript or Action Streams
            try:
                for xref in range(1, doc.xref_length()):
                    obj_keys = doc.xref_get_keys(xref)
                    if "JS" in obj_keys or "JavaScript" in obj_keys:
                        findings.append(ScanFinding(
                            category="pdf_javascript",
                            severity="CRITICAL",
                            description=f"Active embedded JavaScript stream detected in PDF object (xref: {xref}).",
                            location=f"XREF {xref}",
                            original_snippet="Embedded JavaScript Action"
                        ))
                        break
            except Exception:
                pass

            # 3. Check for Optional Content Groups (OCGs / Hidden Layers)
            try:
                ocgs = doc.get_ocgs()
                if ocgs:
                    for ocg_id, ocg_info in ocgs.items():
                        # If layer is configured OFF or hidden
                        if ocg_info.get("on") is False:
                            findings.append(ScanFinding(
                                category="hidden_layer",
                                severity="HIGH",
                                description=f"Hidden PDF Optional Content Group (OCG) layer detected: '{ocg_info.get('name', ocg_id)}'.",
                                location=f"OCG Layer {ocg_id}",
                                original_snippet=f"Layer state: hidden, Name: {ocg_info.get('name')}"
                            ))
            except Exception:
                pass

            # 4. Multi-Page Text Span & Geometry Inspection (with page cap limit)
            MAX_PAGES = 200
            if len(doc) > MAX_PAGES:
                findings.append(ScanFinding(
                    category="resource_exhaustion",
                    severity="HIGH",
                    description=f"PDF page count ({len(doc)}) exceeds maximum security processing limit ({MAX_PAGES} pages). Parsing capped at first {MAX_PAGES} pages.",
                    location="Document Structure",
                    original_snippet=f"Total pages: {len(doc)}"
                ))

            for page_num in range(min(len(doc), MAX_PAGES)):
                page = doc[page_num]
                page_rect = page.rect

                
                # Check for hidden or suspicious annotations
                try:
                    for annot in page.annots():
                        annot_info = annot.info
                        annot_content = annot_info.get("content", "")
                        if annot_content:
                            annot_lower = annot_content.lower()
                            if any(bad in annot_lower for bad in ["ignore", "override", "system", "<|im_start|>"]):
                                findings.append(ScanFinding(
                                    category="hidden_annotation",
                                    severity="CRITICAL",
                                    description=f"Adversarial payload found in PDF annotation on page {page_num + 1}.",
                                    location=f"Page {page_num + 1} Annotation",
                                    original_snippet=annot_content
                                ))
                except Exception:
                    pass

                # Extract text blocks with detailed font and color data (unclipped for off-canvas detection)
                clip_rect = fitz.Rect(-5000, -5000, 10000, 10000)
                text_page = page.get_text("dict", clip=clip_rect)
                
                for block in text_page.get("blocks", []):
                    if block.get("type") == 0:  # Text block
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                text = span.get("text", "").strip()
                                if not text:
                                    continue
                                
                                font_size = span.get("size", 10.0)
                                bbox = span.get("bbox", (0, 0, 0, 0))
                                color_int = span.get("color", 0)
                                
                                # Convert integer color to RGB tuple (0.0 - 1.0)
                                r = ((color_int >> 16) & 0xFF) / 255.0
                                g = ((color_int >> 8) & 0xFF) / 255.0
                                b = (color_int & 0xFF) / 255.0
                                span_rgb = (r, g, b)
                                
                                # A. Check for White-on-White text (RGB distance to pure white < 0.15)
                                white_rgb = (1.0, 1.0, 1.0)
                                if color_distance(span_rgb, white_rgb) < 0.15:
                                    findings.append(ScanFinding(
                                        category="white_text",
                                        severity="CRITICAL",
                                        description=f"Invisible white text detected on page {page_num + 1} (color RGB: {span_rgb}).",
                                        location=f"Page {page_num + 1}, coords: {[round(c, 1) for c in bbox]}",
                                        original_snippet=text
                                    ))
                                
                                # B. Check for Micro-Font / Sub-pixel text (< 2.0 pt)
                                if font_size < 2.0:
                                    findings.append(ScanFinding(
                                        category="micro_font",
                                        severity="HIGH",
                                        description=f"Microscopic sub-pixel text detected ({font_size:.2f}pt) on page {page_num + 1}.",
                                        location=f"Page {page_num + 1}, coords: {[round(c, 1) for c in bbox]}",
                                        original_snippet=text
                                    ))
                                    
                                # C. Check for Off-canvas rendering (outside visible page bounds)
                                x0, y0, x1, y1 = bbox
                                if x0 < -5 or y0 < -5 or x1 > page_rect.width + 10 or y1 > page_rect.height + 10:
                                    findings.append(ScanFinding(
                                        category="off_canvas",
                                        severity="HIGH",
                                        description=f"Off-canvas text rendered outside visible margins on page {page_num + 1}.",
                                        location=f"Page {page_num + 1}, coords: {[round(c, 1) for c in bbox]}",
                                        original_snippet=text
                                    ))

                                extracted_text_blocks.append(text)

            doc.close()
            full_text = "\n".join(extracted_text_blocks)
            
            # Check extracted text for Unicode steganography & homoglyphs
            sanitized_text, u_findings = UnicodeSanitizer.sanitize(full_text)
            findings.extend(u_findings)
            
            return sanitized_text, findings, metadata_findings
            
        except Exception as e:
            findings.append(ScanFinding(
                category="pdf_parsing_error",
                severity="HIGH",
                description=f"PDF parsing encountered an anomaly: {str(e)}"
            ))
            return "", findings, metadata_findings

# Alias for backward and cross-import compatibility
PDFInspector = PDFAnalyzer
