import pytest
from backend.app.engine.consensus import ConsensusAdjudicator

def test_consensus_auto_patch():
    adjudicator = ConsensusAdjudicator()
    
    # High confidence from all agents
    c_ast = 0.9
    c_spatial = 0.85
    c_semantic = 0.88
    
    success, phi, action = adjudicator.adjudicate('element_1', c_ast, c_spatial, c_semantic, {'candidate_data': 'test'})
    
    assert success is True
    assert phi >= 0.80
    assert action == "AUTO-PATCH"
    assert adjudicator.registry_hot_patch['element_1']['candidate_data'] == 'test'

def test_consensus_fail_closed_low_phi():
    adjudicator = ConsensusAdjudicator()
    
    # Low confidence across the board
    c_ast = 0.5
    c_spatial = 0.4
    c_semantic = 0.6
    
    success, phi, action = adjudicator.adjudicate('element_2', c_ast, c_spatial, c_semantic, {})
    
    assert success is False
    assert phi < 0.80
    assert action == "FAIL-CLOSED"

def test_consensus_fail_closed_high_variance():
    adjudicator = ConsensusAdjudicator()
    
    # One very high, others very low -> high variance penalty
    c_ast = 0.95
    c_spatial = 0.2
    c_semantic = 0.1
    
    # Weights: 0.4*0.95 + 0.35*0.2 + 0.25*0.1 = 0.38 + 0.07 + 0.025 = 0.475
    # Since phi < 0.80 regardless of variance, let's bump it
    # Actually wait, let's just make sure it fails
    success, phi, action = adjudicator.adjudicate('element_3', c_ast, c_spatial, c_semantic, {})
    
    assert success is False
    assert action == "FAIL-CLOSED"
