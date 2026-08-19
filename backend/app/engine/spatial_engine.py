import math
import numpy as np
from scipy.optimize import linear_sum_assignment
from typing import Dict, Any, List, Tuple, Optional

def compute_diou(box_a: Dict[str, float], box_b: Dict[str, float]) -> float:
    """
    Computes Distance-IoU (DIoU) between two bounding boxes.
    Boxes are expected to be dictionaries with 'x', 'y', 'w', 'h' in normalized [0, 1] coordinates.
    """
    # Parse coordinates
    ax1, ay1 = box_a['x'], box_a['y']
    aw, ah = box_a['w'], box_a['h']
    ax2, ay2 = ax1 + aw, ay1 + ah

    bx1, by1 = box_b['x'], box_b['y']
    bw, bh = box_b['w'], box_b['h']
    bx2, by2 = bx1 + bw, by1 + bh

    # Intersection Box
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    inter_w = max(0.0, ix2 - ix1)
    inter_h = max(0.0, iy2 - iy1)
    intersection = inter_w * inter_h

    # Union Box
    area_a = aw * ah
    area_b = bw * bh
    union = area_a + area_b - intersection

    iou = intersection / union if union > 0 else 0.0

    # Distance between centroids (rho)
    ac_x, ac_y = ax1 + aw / 2.0, ay1 + ah / 2.0
    bc_x, bc_y = bx1 + bw / 2.0, by1 + bh / 2.0
    rho_sq = (ac_x - bc_x) ** 2 + (ac_y - bc_y) ** 2

    # Diagonal length of smallest enclosing box (c)
    ex1 = min(ax1, bx1)
    ey1 = min(ay1, by1)
    ex2 = max(ax2, bx2)
    ey2 = max(ay2, by2)
    c_sq = (ex2 - ex1) ** 2 + (ey2 - ey1) ** 2

    diou = iou - (rho_sq / c_sq) if c_sq > 0 else iou
    return diou

def compute_neighbor_distortion(edges_a: List[Tuple[float, float, float, float]], 
                                edges_b: List[Tuple[float, float, float, float]]) -> float:
    """
    Calculates neighbor distortion D_spatial using Hungarian bipartite matching 
    over polar edge descriptors e_uv = (delta_x, delta_y, r, theta).
    """
    if not edges_a or not edges_b:
        return 0.0

    cost_matrix = np.zeros((len(edges_a), len(edges_b)))
    for i, ea in enumerate(edges_a):
        for j, eb in enumerate(edges_b):
            # Euclidean distance between descriptors as cost
            cost_matrix[i, j] = math.sqrt(sum((a - b) ** 2 for a, b in zip(ea, eb)))

    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    total_cost = cost_matrix[row_ind, col_ind].sum()
    # Normalize distortion by max possible edges matched
    max_edges = max(len(edges_a), len(edges_b))
    return total_cost / max_edges if max_edges > 0 else 0.0

class SpatialEngine:
    def __init__(self):
        pass

    def evaluate_candidates(self, baseline: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Evaluates a list of candidates and returns the best match if S_spatial >= 0.75.
        - baseline/candidate contain 'box' (x, y, w, h) and 'edges' (list of descriptors)
        """
        best_score = -float('inf')
        best_candidate = None

        b_box = baseline.get('box', {'x':0, 'y':0, 'w':0, 'h':0})
        b_edges = baseline.get('edges', [])

        for candidate in candidates:
            c_box = candidate.get('box', {'x':0, 'y':0, 'w':0, 'h':0})
            c_edges = candidate.get('edges', [])

            diou = compute_diou(b_box, c_box)
            d_spatial = compute_neighbor_distortion(b_edges, c_edges)

            s_spatial = 0.70 * math.exp(-2.5 * d_spatial) + 0.30 * diou

            if s_spatial > best_score:
                best_score = s_spatial
                best_candidate = candidate

        if best_score >= 0.75 and best_candidate:
            best_candidate['s_spatial'] = best_score
            return best_candidate

        return None
