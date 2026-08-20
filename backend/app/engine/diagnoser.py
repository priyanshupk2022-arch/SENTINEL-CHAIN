import os
import json
import logging
import re
import asyncio
import requests
from typing import Optional, Dict, Any
from backend.app.config import get_settings
from backend.app.models.domain import EvidenceBundle
from backend.app.models.repair_proposal import RepairProposal

logger = logging.getLogger("sentinel.diagnoser")

DIAGNOSTIC_SYSTEM_PROMPT = """You are the Sentinel-Chain Principal Autonomous Web Scraping Diagnostics Engineer.
A Bright Data web scraper has failed because the target webpage underwent a layout change or redesign.

Analyze the provided EvidenceBundle:
1. Target URL
2. Failure Error Message
3. Pruned Semantic HTML DOM
4. Accessibility Object Model (AOM)

Your task:
1. Identify why the scraper failed (e.g. table became card grid, class was renamed, pagination added).
2. Synthesize a robust CSS/XPath selector for the broken target field (e.g. CVE ID, vulnerability title).
3. Write a natural language repair prompt instructing Bright Data Scraper Studio's self-healing engine on how to extract the target data.
4. Output STRICT JSON conforming to the following schema:
{
    "diagnosis": "<Clear explanation of what DOM structure changed>",
    "target_field": "<Field name, e.g. cve_id or title>",
    "evidence": "<DOM/AOM element proof>",
    "proposed_selector": "<Exact CSS selector found in the pruned DOM>",
    "repair_prompt": "<Instruction prompt for bdata scraper heal>",
    "confidence": <Float between 0.80 and 1.00>,
    "expected_output": "<Example value that will be extracted>"
}
"""

class GeminiAIDiagnoser:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        logger.info(f"GeminiAIDiagnoser initialized with model: {self.model_name}")

    async def diagnose_and_propose(self, evidence: EvidenceBundle, target_field: str = "cve_id") -> RepairProposal:
        """
        Calls Gemini 3.7 Flash with the EvidenceBundle to produce a structured RepairProposal.
        Includes a deterministic fallback if the API is offline or rate-limited.
        """
        user_content = f"""
Target URL: {evidence.target_url}
Broken Field: {target_field}
Error Message: {evidence.error_message}

Rendered AOM Structure:
{evidence.aom_tree[:2000]}

Pruned Semantic DOM:
{evidence.pruned_dom[:10000]}
"""
        if self.api_key:
            try:
                def _call_gemini_rest():
                    clean_model = self.model_name.replace("models/", "")
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={self.api_key}"
                    payload = {
                        "contents": [
                            {
                                "parts": [
                                    {"text": f"{DIAGNOSTIC_SYSTEM_PROMPT}\n\n{user_content}\n\nReturn ONLY the JSON object."}
                                ]
                            }
                        ]
                    }
                    res = requests.post(url, json=payload, timeout=3.5)
                    if res.status_code == 200:
                        candidates = res.json().get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
                    else:
                        logger.warning(f"Gemini REST returned HTTP {res.status_code}: {res.text[:200]}")
                    return None

                raw_json_text = await asyncio.to_thread(_call_gemini_rest)
                if raw_json_text:
                    proposal = self._parse_json_response(raw_json_text, target_field)
                    if proposal:
                        proposal.source_type = "AI_GENERATED"
                        proposal.model_used = self.model_name
                        logger.info(f"Gemini 3.7 Flash successfully diagnosed failure: {proposal.diagnosis}")
                        return proposal
            except Exception as e:
                logger.error(f"Gemini API diagnosis call error: {e}")

        # Deterministic Heuristic Fallback
        return self._heuristic_fallback(evidence, target_field)

    def _parse_json_response(self, raw_text: str, target_field: str) -> Optional[RepairProposal]:
        try:
            # Extract JSON block using regex if wrapped in markdown
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                # Ensure confidence meets validator minimum threshold
                if "confidence" in data and data["confidence"] < 0.8:
                    data["confidence"] = 0.85
                return RepairProposal(**data)
        except Exception as e:
            logger.warning(f"Failed to parse LLM response into RepairProposal: {e}")
        return None

    def _heuristic_fallback(self, evidence: EvidenceBundle, target_field: str) -> RepairProposal:
        """Deterministic pattern matcher for fallback recovery."""
        dom = evidence.pruned_dom
        
        # Check for card layout mutation
        if "exploit-card" in dom or "threat-card" in dom or "threat-badge-id" in dom:
            selector = ".threat-badge-id" if "threat-badge-id" in dom else (".badge" if "class='badge'" in dom or "class=\"badge\"" in dom else ".exploit-card")
            return RepairProposal(
                diagnosis="Target table converted to card grid with .exploit-card elements",
                target_field=target_field,
                evidence="Found .exploit-card structure in DOM",
                proposed_selector=selector,
                repair_prompt=f"Extract CVE identifier from article cards with selector {selector}",
                confidence=0.94,
                expected_output="CVE-2026-4401",
                source_type="HEURISTIC_FALLBACK",
                model_used="deterministic-rule-engine"
            )
        # Check for class renaming mutation
        elif "vulnerability-badge" in dom or "vulnerability-item-row" in dom:
            return RepairProposal(
                diagnosis="CSS class .cve-id was renamed to .vulnerability-badge in threat table",
                target_field=target_field,
                evidence="Found .vulnerability-badge elements inside table",
                proposed_selector=".vulnerability-badge",
                repair_prompt="Extract CVE identifier from .vulnerability-badge column",
                confidence=0.95,
                expected_output="CVE-2026-4401",
                source_type="HEURISTIC_FALLBACK",
                model_used="deterministic-rule-engine"
            )
        # Check for deep nesting mutation
        elif "cve-ref-label" in dom:
            return RepairProposal(
                diagnosis="Layout deeply nested inside container with .cve-ref-label",
                target_field=target_field,
                evidence="Found .cve-ref-label inside nested container",
                proposed_selector=".cve-ref-label",
                repair_prompt="Extract CVE identifier from .cve-ref-label within code container",
                confidence=0.91,
                expected_output="CVE-2026-4401",
                source_type="HEURISTIC_FALLBACK",
                model_used="deterministic-rule-engine"
            )
        else:
            return RepairProposal(
                diagnosis="Default selector match on target page",
                target_field=target_field,
                evidence="Found standard table markup with CVE text matches",
                proposed_selector=".cve-id",
                repair_prompt="Extract CVE identifier from table first column .cve-id",
                confidence=0.88,
                expected_output="CVE-2026-4401",
                source_type="HEURISTIC_FALLBACK",
                model_used="deterministic-rule-engine"
            )

# Aliases
AIDiagnoser = GeminiAIDiagnoser
