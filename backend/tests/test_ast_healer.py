import pytest
from backend.app.engine.ast_healer import ASTHealer, fnv1a_64

def test_ast_healer_hash_shortcut():
    healer = ASTHealer()
    baseline = {'structural_hash': 12345}
    candidates = [{'structural_hash': 54321}, {'structural_hash': 12345, 'tag': 'div'}]
    
    best = healer.evaluate_candidates(baseline, candidates)
    
    assert best is not None
    assert best['s_attr'] == 1.0
    assert best['tag'] == 'div'

def test_ast_healer_jaccard_recovery():
    healer = ASTHealer()
    # Scrambled classes and tags but similar
    baseline = {
        'attrs': {'class': 'btn primary', 'id': 'submit-1'},
        'tag': 'button',
        'text': 'Submit Order',
        'depth': 5
    }
    candidate = {
        'attrs': {'class': 'btn btn-primary', 'id': 'submit-1'},
        'tag': 'div',
        'role': 'button',
        'text': 'Submit Order',
        'depth': 5
    }
    
    score = healer.compute_similarity(baseline, candidate)
    
    # Let's calculate manually what it should be approx
    # attrs baseline: 'class=btn primary', 'id=submit-1'
    # attrs cand: 'class=btn btn-primary', 'id=submit-1'
    # Intersection = 1 ('id=submit-1'), Union = 3. J_attr = 1/3 ~ 0.33
    
    # tags+roles baseline: {'button'}
    # tags+roles cand: {'div', 'button'}
    # Intersection = 1, Union = 2. J_tag+role = 0.5
    
    # sim_text: Both 'Submit Order', match = 1.0
    
    # delta_depth: 0 (same depth), match = 1.0
    
    # S_attr = 0.5*(1/3) + 0.25*(0.5) + 0.15*(1.0) + 0.10*(1.0)
    # 0.166 + 0.125 + 0.15 + 0.10 = 0.541
    # We want it to be accurate.
    assert score > 0.5 and score < 0.6

def test_ast_healer_threshold_respected():
    healer = ASTHealer()
    baseline = {
        'attrs': {'class': 'identical'},
        'tag': 'div',
        'text': 'Hello',
        'depth': 3
    }
    candidates = [
        # Candidate 1: Exactly same -> score 1.0
        {
            'attrs': {'class': 'identical'},
            'tag': 'div',
            'text': 'Hello',
            'depth': 3
        },
        # Candidate 2: Completely different -> score low
        {
            'attrs': {'class': 'different'},
            'tag': 'span',
            'text': 'World',
            'depth': 10
        }
    ]
    
    best = healer.evaluate_candidates(baseline, candidates)
    
    assert best is not None
    assert best['s_attr'] >= 0.85
    assert best['text'] == 'Hello'
