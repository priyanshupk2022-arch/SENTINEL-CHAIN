"""Unicode, Steganography & Homoglyph Sanitization Engine."""
import re
import unicodedata
from typing import Tuple, List
from app.models.schemas import ScanFinding

# Mapping of common zero-width and invisible control characters
ZERO_WIDTH_CHARS = {
    '\u200B': 'ZERO_WIDTH_SPACE',
    '\u200C': 'ZERO_WIDTH_NON_JOINER',
    '\u200D': 'ZERO_WIDTH_JOINER',
    '\uFEFF': 'ZERO_WIDTH_NO_BREAK_SPACE',
    '\u2060': 'WORD_JOINER',
    '\u200E': 'LEFT_TO_RIGHT_MARK',
    '\u200F': 'RIGHT_TO_LEFT_MARK',
    '\u202A': 'LEFT_TO_RIGHT_EMBEDDING',
    '\u202B': 'RIGHT_TO_LEFT_EMBEDDING',
    '\u202C': 'POP_DIRECTIONAL_FORMATTING',
    '\u202D': 'LEFT_TO_RIGHT_OVERRIDE',
    '\u202E': 'RIGHT_TO_LEFT_OVERRIDE',
}

# Homoglyphs dictionary mapping Cyrillic, Greek, and other script lookalikes to Latin ASCII
HOMOGLYPH_MAP = {
    # Cyrillic lookalikes
    'а': 'a', 'А': 'A', 'с': 'c', 'С': 'C', 'е': 'e', 'Е': 'E',
    'о': 'o', 'О': 'O', 'р': 'p', 'Р': 'P', 'х': 'x', 'Х': 'X',
    'у': 'y', 'У': 'Y', 'і': 'i', 'І': 'I', 'ј': 'j', 'Ј': 'J',
    'ѕ': 's', 'Ѕ': 'S', 'ԁ': 'd', 'Ԃ': 'D', 'ԛ': 'q', 'Ԝ': 'W',
    # Greek lookalikes
    'α': 'a', 'Α': 'A', 'β': 'b', 'Β': 'B', 'γ': 'y', 'Γ': 'r',
    'ε': 'e', 'Ε': 'E', 'η': 'n', 'Η': 'H', 'ι': 'i', 'Ι': 'I',
    'κ': 'k', 'Κ': 'K', 'ν': 'v', 'Ν': 'N', 'ο': 'o', 'Ο': 'O',
    'ρ': 'p', 'Ρ': 'P', 'τ': 't', 'Τ': 'T', 'υ': 'u', 'Υ': 'Y',
    'χ': 'x', 'Χ': 'X',
}

ZERO_WIDTH_REGEX = re.compile(r'[\u200B-\u200F\u202A-\u202E\u2060\uFEFF]')

class UnicodeSanitizer:
    @staticmethod
    def sanitize(text: str) -> Tuple[str, List[ScanFinding]]:
        findings: List[ScanFinding] = []
        if not text:
            return "", findings

        # 1. Detect and count Zero-Width & Invisible Characters
        zero_width_matches = ZERO_WIDTH_REGEX.findall(text)
        if zero_width_matches:
            char_names = [ZERO_WIDTH_CHARS.get(c, hex(ord(c))) for c in zero_width_matches]
            findings.append(ScanFinding(
                category="steganography",
                severity="CRITICAL",
                description=f"Detected {len(zero_width_matches)} invisible zero-width/bidi control characters ({', '.join(set(char_names))}).",
                original_snippet=f"Count: {len(zero_width_matches)} characters"
            ))
            # Strip zero-width characters
            cleaned_text = ZERO_WIDTH_REGEX.sub('', text)
        else:
            cleaned_text = text

        # 2. Detect and normalize Homoglyphs (Cyrillic/Greek spoofed Latin)
        homoglyph_detected = []
        normalized_chars = []
        for char in cleaned_text:
            if char in HOMOGLYPH_MAP:
                homoglyph_detected.append(f"{char} -> {HOMOGLYPH_MAP[char]}")
                normalized_chars.append(HOMOGLYPH_MAP[char])
            else:
                normalized_chars.append(char)
                
        if homoglyph_detected:
            findings.append(ScanFinding(
                category="homoglyph",
                severity="HIGH",
                description=f"Detected {len(homoglyph_detected)} spoofed homoglyph characters.",
                original_snippet=f"Examples: {', '.join(homoglyph_detected[:5])}"
            ))
            cleaned_text = "".join(normalized_chars)

        # 3. Unicode NFKC Normalization
        nfkc_text = unicodedata.normalize('NFKC', cleaned_text)
        
        return nfkc_text, findings
