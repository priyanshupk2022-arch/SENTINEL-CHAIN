import math
from typing import Dict, Any, Optional

def fnv1a_64(data: str) -> int:
    """Computes a 64-bit FNV-1a hash for a given string."""
    hash_val = 14695981039346656037
    for char in data:
        hash_val ^= ord(char)
        hash_val *= 1099511628211
        hash_val &= 0xFFFFFFFFFFFFFFFF
    return hash_val

def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Computes the Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0

class ASTHealer:
    def __init__(self):
        # We could initialize tree-sitter-html here if needed.
        pass

    def compute_similarity(self, baseline: Dict[str, Any], candidate: Dict[str, Any]) -> float:
        """
        Computes the combined attribute similarity score (S_attr) between a baseline
        element and a candidate element.
        
        Dictionaries should contain:
        - 'attrs': Dict[str, str] of HTML attributes
        - 'tag': str
        - 'role': str (optional, defaults to '')
        - 'text': str (textContent, trimmed)
        - 'depth': int (DOM depth)
        """
        # 1. J_attrs
        b_attrs = set(f"{k}={v}" for k, v in baseline.get('attrs', {}).items())
        c_attrs = set(f"{k}={v}" for k, v in candidate.get('attrs', {}).items())
        j_attrs = jaccard_similarity(b_attrs, c_attrs)

        # 2. J_tag+role
        b_tag_role = {baseline.get('tag', ''), baseline.get('role', '')}
        b_tag_role.discard('')
        c_tag_role = {candidate.get('tag', ''), candidate.get('role', '')}
        c_tag_role.discard('')
        j_tag_role = jaccard_similarity(b_tag_role, c_tag_role)

        # 3. sim_text
        b_text = baseline.get('text', '').strip()
        c_text = candidate.get('text', '').strip()
        sim_text = 1.0 if (b_text and c_text and fnv1a_64(b_text) == fnv1a_64(c_text)) else 0.0
        if not b_text and not c_text:
            sim_text = 1.0  # Both empty counts as match

        # 4. delta_depth
        b_depth = baseline.get('depth', 0)
        c_depth = candidate.get('depth', 0)
        delta_depth = 1.0 - math.exp(-0.4 * abs(b_depth - c_depth))

        # Combined Similarity Score
        s_attr = 0.50 * j_attrs + 0.25 * j_tag_role + 0.15 * sim_text + 0.10 * (1.0 - delta_depth)
        return s_attr

    def evaluate_candidates(self, baseline: Dict[str, Any], candidates: list[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Evaluates a list of candidates and returns the best match if S_attr >= 0.85.
        Uses FNV-1a shortcut if structural hash matches.
        """
        baseline_hash = baseline.get('structural_hash')

        best_score = 0.0
        best_candidate = None

        for candidate in candidates:
            # O(1) Shortcut
            if baseline_hash and candidate.get('structural_hash') == baseline_hash:
                candidate['s_attr'] = 1.0
                return candidate

            score = self.compute_similarity(baseline, candidate)
            if score > best_score:
                best_score = score
                best_candidate = candidate

        if best_score >= 0.85 and best_candidate:
            best_candidate['s_attr'] = best_score
            return best_candidate

        return None
