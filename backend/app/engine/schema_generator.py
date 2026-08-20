import json
import logging
import re
import requests
import asyncio
from typing import Optional, List, Dict, Any
from backend.app.config import get_settings
from backend.app.models.domain import ExtractionSchema, ExtractionField, FieldDataType, TargetInspection

logger = logging.getLogger("sentinel.schema_generator")

SCHEMA_SYSTEM_PROMPT = """You are the Sentinel-Chain Principal Data Extraction Schema Architect.
Convert the user's natural language extraction intent and the target website's inspection metadata into a precise, typed ExtractionSchema.

Output STRICT JSON conforming to:
{
    "name": "<Schema Name>",
    "fields": [
        {
            "name": "<canonical_snake_case_key>",
            "type": "<string|number|currency|date|url|boolean|array>",
            "description": "<What this field represents>",
            "required": true|false,
            "selector_hint": "<CSS selector or null>",
            "normalization": "<trim|to_lower|parse_float|null>",
            "validation_rule": "<optional validation rule or null>"
        }
    ]
}
"""

class SchemaGenerator:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL

    async def generate_schema_from_intent(
        self,
        target_id: str,
        intent_prompt: str,
        inspection: Optional[TargetInspection] = None
    ) -> ExtractionSchema:
        """
        Synthesizes an ExtractionSchema from natural language intent using Gemini 3.7 Flash,
        grounded by real DOM candidate fields and page structure.
        """
        candidates_str = ", ".join(inspection.candidate_fields) if inspection else "None"
        page_type = inspection.page_type.value if inspection else "UNKNOWN"

        prompt = f"""
Target Page Type: {page_type}
Candidate DOM Fields Discovered: {candidates_str}
User Extraction Intent: {intent_prompt}

Generate a clean, normalized ExtractionSchema containing all requested fields with proper data types.
"""

        if self.api_key:
            try:
                def _call_gemini():
                    clean_model = self.model_name.replace("models/", "")
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={self.api_key}"
                    payload = {
                        "contents": [
                            {
                                "parts": [
                                    {"text": f"{SCHEMA_SYSTEM_PROMPT}\n\n{prompt}\n\nReturn ONLY the JSON object."}
                                ]
                            }
                        ]
                    }
                    res = requests.post(url, json=payload, timeout=4.0)
                    if res.status_code == 200:
                        candidates = res.json().get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
                    return None

                raw_json = await asyncio.to_thread(_call_gemini)
                if raw_json:
                    schema_data = self._parse_json(raw_json)
                    if schema_data and "fields" in schema_data:
                        fields = [ExtractionField(**f) for f in schema_data["fields"]]
                        return ExtractionSchema(
                            target_id=target_id,
                            name=schema_data.get("name", "Extracted Schema"),
                            intent_prompt=intent_prompt,
                            fields=fields
                        )
            except Exception as e:
                logger.warning(f"Gemini schema generation failed: {e}")

        # Deterministic Heuristic Fallback
        return self._heuristic_schema_fallback(target_id, intent_prompt, inspection)

    def _parse_json(self, raw_text: str) -> Optional[Dict[str, Any]]:
        try:
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception as e:
            logger.warning(f"Failed to parse JSON from model output: {e}")
        return None

    def _heuristic_schema_fallback(
        self,
        target_id: str,
        intent_prompt: str,
        inspection: Optional[TargetInspection] = None
    ) -> ExtractionSchema:
        fields = []
        intent_lower = (intent_prompt or "").lower()

        # Parse key entities from prompt
        if "cve" in intent_lower or "threat" in intent_lower or "vulnerability" in intent_lower:
            fields = [
                ExtractionField(name="cve_id", type=FieldDataType.STRING, description="Vulnerability CVE ID", required=True, selector_hint=".cve-id, .vulnerability-badge"),
                ExtractionField(name="title", type=FieldDataType.STRING, description="Advisory summary", required=True, selector_hint=".cve-title"),
                ExtractionField(name="severity", type=FieldDataType.STRING, description="Severity score", required=False, selector_hint=".severity"),
                ExtractionField(name="published_date", type=FieldDataType.DATE, description="Advisory publication date", required=False, selector_hint=".date")
            ]
        elif "price" in intent_lower or "product" in intent_lower or "ecommerce" in intent_lower:
            fields = [
                ExtractionField(name="product_name", type=FieldDataType.STRING, description="Product Name", required=True),
                ExtractionField(name="price", type=FieldDataType.CURRENCY, description="Current Price", required=True),
                ExtractionField(name="rating", type=FieldDataType.NUMBER, description="Customer Rating", required=False),
                ExtractionField(name="availability", type=FieldDataType.STRING, description="In Stock status", required=False)
            ]
        elif "article" in intent_lower or "news" in intent_lower or "post" in intent_lower:
            fields = [
                ExtractionField(name="headline", type=FieldDataType.STRING, description="Article Headline", required=True),
                ExtractionField(name="author", type=FieldDataType.STRING, description="Article Author", required=False),
                ExtractionField(name="published_date", type=FieldDataType.DATE, description="Date Published", required=False),
                ExtractionField(name="url", type=FieldDataType.URL, description="Article Permalink", required=False)
            ]
        else:
            # Generate fields from words in intent
            tokens = [t.strip(",. ") for t in intent_prompt.split() if len(t) > 3 and t not in {"extract", "from", "with", "page", "data", "what", "should"}]
            if not tokens and inspection and inspection.candidate_fields:
                tokens = inspection.candidate_fields[:4]
            
            for t in tokens[:5]:
                field_type = FieldDataType.NUMBER if "rating" in t or "count" in t or "score" in t else (
                    FieldDataType.CURRENCY if "price" in t or "cost" in t else (
                        FieldDataType.DATE if "date" in t or "time" in t else FieldDataType.STRING
                    )
                )
                fields.append(ExtractionField(name=t.lower().replace("-", "_"), type=field_type, description=f"Extracted {t} field", required=True))

        if not fields:
            fields = [
                ExtractionField(name="title", type=FieldDataType.STRING, description="Title", required=True),
                ExtractionField(name="value", type=FieldDataType.STRING, description="Value", required=True)
            ]

        return ExtractionSchema(
            target_id=target_id,
            name="Synthesized Schema",
            intent_prompt=intent_prompt,
            fields=fields
        )
