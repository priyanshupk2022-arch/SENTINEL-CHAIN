import pytest
from backend.app.engine.spatial_engine import SpatialEngine, compute_diou

def test_compute_diou():
    box_a = {'x': 0.1, 'y': 0.1, 'w': 0.2, 'h': 0.2}
    box_b = {'x': 0.15, 'y': 0.15, 'w': 0.2, 'h': 0.2}
    
    # Intersection is x:[0.15, 0.3], y:[0.15, 0.3] -> w=0.15, h=0.15 -> area=0.0225
    # Union area is 0.04 + 0.04 - 0.0225 = 0.0575
    # IoU = 0.0225 / 0.0575 = 0.3913
    
    diou = compute_diou(box_a, box_b)
    assert diou < 0.3913 # due to distance penalty
    assert diou > 0.0

def test_spatial_engine_threshold():
    engine = SpatialEngine()
    
    # Perfect match
    baseline = {
        'box': {'x': 0.5, 'y': 0.5, 'w': 0.1, 'h': 0.1},
        'edges': [(0.1, 0.1, 0.14, 0.78)]
    }
    candidate_perfect = {
        'box': {'x': 0.5, 'y': 0.5, 'w': 0.1, 'h': 0.1},
        'edges': [(0.1, 0.1, 0.14, 0.78)]
    }
    
    best = engine.evaluate_candidates(baseline, [candidate_perfect])
    assert best is not None
    assert best['s_spatial'] > 0.99
    
    # Poor match
    candidate_poor = {
        'box': {'x': 0.1, 'y': 0.1, 'w': 0.1, 'h': 0.1},
        'edges': [(0.9, 0.9, 1.2, 0.1)]
    }
    best_poor = engine.evaluate_candidates(baseline, [candidate_poor])
    assert best_poor is None # Threshold < 0.75
