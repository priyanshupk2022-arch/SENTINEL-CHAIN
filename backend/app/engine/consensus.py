import numpy as np
from typing import Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ConsensusAdjudicator:
    def __init__(self, lambda_penalty: float = 0.50):
        self.w_ast = 0.40
        self.w_spatial = 0.35
        self.w_semantic = 0.25
        self.lambda_penalty = lambda_penalty

        self.registry_hot_patch = {} # In-memory selector registry

    def adjudicate(self, element_id: str, c_ast: float, c_spatial: float, c_semantic: float, candidate: Dict[str, Any]) -> Tuple[bool, float, str]:
        """
        Multi-agent weighted voting logic.
        Returns: (success: bool, phi_score: float, action: str)
        """
        # Calculate Weighted Confidence
        weighted_sum = (self.w_ast * c_ast) + (self.w_spatial * c_spatial) + (self.w_semantic * c_semantic)

        # Calculate Inter-agent variance penalty
        confidences = [c_ast, c_spatial, c_semantic]
        variance = np.var(confidences)

        # Final Phi(e) score
        phi_e = weighted_sum - (self.lambda_penalty * variance)

        # Calculate Agreement (e.g. how many agents scored >= 0.75)
        agreement = sum(1 for c in confidences if c >= 0.75)

        if phi_e >= 0.80 and agreement >= 2:
            # AUTO-PATCH IN-MEMORY
            self.registry_hot_patch[element_id] = candidate
            action = "AUTO-PATCH"
            return True, phi_e, action
        else:
            # FAIL-CLOSED -> Dead Letter Queue
            action = "FAIL-CLOSED"
            return False, phi_e, action
