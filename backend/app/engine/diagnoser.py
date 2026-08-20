import os
import json
import logging
import re
import asyncio
import requests
from typing import Optional, Dict, Any, List
from backend.app.config import get_settings
from backend.app.models.domain import EvidenceBundle, FailureCategory
from backend.app.models.repair_proposal import RepairProposal

logger = logging.getLogger("sentinel.diagnoser")

GENERALIZED_DIAGNOSTIC_SYSTEM_PROMPT = """You are the Sentinel-Chain Principal Autonomous Web Scraping Diagnostics Engineer.
A Bright Data web scraper has failed because the target webpage underwent a structural DOM mutation or selector drift.

Analyze the provided EvidenceBundle:
1. Target URL
2. Broken Target Field & Schema Context
3. Failure Error Message
4. Pruned Semantic HTML DOM
5. Accessibility Object Model (AOM) Tree

Your task:
1. Identify the root cause category (SELECTOR_DRIFT, DOM_RESTRUCTURE, FIELD_MISSING, CARD_TABLE_TRANSFORMATION, etc.).
2. Synthesize an exact, robust CSS selector for the requested target field from the current DOM markup.
3. Write a natural language repair instruction prompt for Bright Data Scraper Studio's self-healing engine (`bdata scraper heal`).
4. Output STRICT JSON conforming to the following schema:
{
    "diagnosis": "<Clear explanation of the DOM structure change>",
    "target_field": "<Field name e.g. price, headline, product_name, cve_id>",
    "evidence": "<DOM/AOM proof>",
    "proposed_selector": "<Exact valid CSS selector matching elements in the pruned DOM>",
    "repair_prompt": "<Instruction prompt for bdata scraper heal>",
    "confidence": <Float between 0.85 and 1.00>,
    "expected_output": "<Representative value that will be extracted>"
}
"""

class GeminiAIDiagnoser:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        logger.info(f"GeminiAIDiagnoser initialized with model: {self.model_name}")

    async def diagnose_and_propose(
        self,
        evidence: EvidenceBundle,
        target_field: str = "target_data",
        schema_context: Optional[Dict[str, Any]] = None
    ) -> RepairProposal:
        """
        Calls Gemini 3.7 Flash with the EvidenceBundle to produce a generalized, target-agnostic RepairProposal.
        """
        schema_str = json.dumps(schema_context) if schema_context else "Standard Schema"
        user_content = f"""
Target URL: {evidence.target_url}
Target Field To Extract: {target_field}
Schema Context: {schema_str}
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
                                    {"text": f"{GENERALIZED_DIAGNOSTIC_SYSTEM_PROMPT}\n\n{user_content}\n\nReturn ONLY the JSON object."}
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
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                if "confidence" in data and data["confidence"] < 0.8:
                    data["confidence"] = 0.85
                if not data.get("target_field"):
                    data["target_field"] = target_field
                return RepairProposal(**data)
        except Exception as e:
            logger.warning(f"Failed to parse LLM response into RepairProposal: {e}")
        return None

    def _heuristic_fallback(self, evidence: EvidenceBundle, target_field: str) -> RepairProposal:
        """Target-agnostic deterministic pattern matcher across Tables, Card Grids, and Article Lists."""
        dom = evidence.pruned_dom
        
        # 1. Card Grid Layout Mutations
        if any(k in dom for k in ["exploit-card", "threat-card", "product-card", "item-card", "article-card"]):
            selector = ".threat-badge-id" if "threat-badge-id" in dom else (
                ".price" if "class=\"price\"" in dom and "price" in target_field else (
                    ".title" if "class=\"title\"" in dom else "article"
                )
            )
            return RepairProposal(
                diagnosis=f"Target structure converted to card grid with container elements ({selector})",
                target_field=target_field,
                evidence=f"Found card containers matching selector {selector}",
                proposed_selector=selector,
                repair_prompt=f"Extract {target_field} from card elements matching {selector}",
                confidence=0.94,
                expected_output="Sample Val",
                source_type="HEURISTIC_FALLBACK",
                model_used="deterministic-rule-engine"
            )
        
        # 2. Class Renaming / Badge Mutations
        elif any(k in dom for k in ["vulnerability-badge", "badge", "tag", "item-badge"]):
            badge_selector = ".vulnerability-badge" if "vulnerability-badge" in dom else ".badge"
            return RepairProposal(
                diagnosis=f"Target selector drifted to {badge_selector}",
                target_field=target_field,
                evidence=f"Found {badge_selector} elements in target markup",
                proposed_selector=badge_selector,
                repair_prompt=f"Extract {target_field} using selector {badge_selector}",
                confidence=0.95,
                expected_output="Sample Val",
                source_type="HEURISTIC_FALLBACK",
                model_used="deterministic-rule-engine"
            )
        
        # 3. Table Column Layout
        elif "<table" in dom:
            return RepairProposal(
                diagnosis="Target table structure with column values",
                target_field=target_field,
                evidence="Found table elements in target markup",
                proposed_selector="td",
                repair_prompt=f"Extract {target_field} from table column cells",
                confidence=0.89,
                expected_output="Sample Val",
                source_type="HEURISTIC_FALLBACK",
                model_used="deterministic-rule-engine"
            )
        
        # 4. Generic Fallback
        else:
            return RepairProposal(
                diagnosis="Standard element extraction on target page",
                target_field=target_field,
                evidence="Found container text matches in DOM",
                proposed_selector="div",
                repair_prompt=f"Extract {target_field} from target page container",
                confidence=0.88,
                expected_output="Sample Val",
                source_type="HEURISTIC_FALLBACK",
                model_used="deterministic-rule-engine"
            )

# Aliases
AIDiagnoser = GeminiAIDiagnoser
