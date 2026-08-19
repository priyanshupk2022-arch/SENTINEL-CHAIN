"""Prompt Injection & Delimiter Breakout Guard Engine."""
import re
from typing import Tuple, List
from app.models.schemas import ScanFinding

# Delimiter breakout patterns
DELIMITER_PATTERNS = [
    (re.compile(r'<\s*\|\s*(?:im_start|im_end|endoftext|system|user|assistant)\s*\|?\s*>', re.IGNORECASE), "Special token tag smuggling"),
    (re.compile(r'\[\s*/?INST\s*\]|<<\s*/?SYS\s*>>|</?\s*system\s*>', re.IGNORECASE), "LLM framing token tag smuggling"),
    (re.compile(r'(?:===+|\*\*\*+|---+)\s*(?:END\s+OF\s+(?:SYSTEM|PROMPT|RESUME)|ADMIN\s+OVERRIDE|SYSTEM\s+PROMPT)\s*(?:===+|\*\*\*+|---+)?', re.IGNORECASE), "Delimiter breakout boundary"),
    (re.compile(r'\[\s*(?:ADMIN|SYSTEM|ROOT|DEV|OVERRIDE|DEVELOPER\s+MODE)\s*\]', re.IGNORECASE), "System role spoofing bracket"),
    (re.compile(r'```(?:system|developer|admin|override)', re.IGNORECASE), "Fenced system code block spoofing")
]

# Prompt injection and jailbreak heuristic patterns
JAILBREAK_PATTERNS = [
    (re.compile(r'ignore\s+(?:all\s+)?(?:previous|above|prior)?\s*(?:instructions|rules|prompts|directives)', re.IGNORECASE), "Direct instruction override attempt"),
    (re.compile(r'disregard\s+(?:all\s+)?(?:previous|above|prior|instructions\s+given\s+previously|rules|prompts|directives|safety\s+rules)', re.IGNORECASE), "Direct instruction disregard attempt"),
    (re.compile(r'(?:reveal|print|output|display|show|dump)\s+(?:all\s+)?(?:your\s+)?(?:the\s+)?(?:initial\s+)?(?:system\s+prompt|master\s+prompt|secret|instructions|initial\s+prompt|system\s+instructions)', re.IGNORECASE), "System prompt exfiltration attempt"),
    (re.compile(r'(?:you\s+are\s+now(?:\s+in)?|enter|activate|switch\s+to|enable|now)?\s*(?:DAN\s+mode|developer\s+mode|jailbreak\s+mode|unrestricted\s+mode|god\s+mode|unrestricted\s+access)', re.IGNORECASE), "Persona jailbreak trigger"),
    (re.compile(r'system\s+override\b|admin\s+override\b|maintenance\s+mode\b', re.IGNORECASE), "System override claim"),
    (re.compile(r'bypass\s+(?:all\s+)?(?:safety|security|content)\s+(?:filters|protocols|checks)', re.IGNORECASE), "Safety filter bypass instruction"),
    (re.compile(r'!\[.*?\]\((?:https?://[^\s\)]+)\)', re.IGNORECASE), "Markdown image exfiltration trigger"),

]


class PromptGuard:
    @staticmethod
    def inspect(text: str) -> Tuple[str, List[ScanFinding]]:
        findings: List[ScanFinding] = []
        if not text:
            return "", findings

        # 1. Delimiter Breakout Inspection
        for pattern, desc in DELIMITER_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                findings.append(ScanFinding(
                    category="delimiter_breakout",
                    severity="CRITICAL",
                    description=f"Delimiter breakout vector detected: {desc}.",
                    original_snippet=str(matches[:3])
                ))

        # 2. Jailbreak & Direct Prompt Injection Inspection
        for pattern, desc in JAILBREAK_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                findings.append(ScanFinding(
                    category="prompt_injection",
                    severity="CRITICAL",
                    description=f"Prompt injection pattern detected: {desc}.",
                    original_snippet=str(matches[:3])
                ))

        return text, findings
