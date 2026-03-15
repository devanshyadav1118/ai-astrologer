"""Test for Phase 8 House Influence Propagation."""

import pytest
from reasoning.propagation import PropagationEngine

def test_propagation_basics():
    engine = PropagationEngine()
    
    # Mock chart data where House 1 lord is in House 10
    # This should make House 10 more important
    chart_data = {
        "planets": [
            {
                "name": "MARS",
                "house": 10,
                "sign": "CAPRICORN",
                "dignity": {"status": "exalted", "strength_modifier": 9.5}
            },
            {
                "name": "JUPITER",
                "house": 1,
                "sign": "ARIES",
                "dignity": {"status": "friend", "strength_modifier": 6.5}
            }
        ],
        "houses": [
            {"number": 1, "sign": "ARIES", "lord": "MARS"},
            {"number": 10, "sign": "CAPRICORN", "lord": "SATURN"}
        ],
        "aspects": []
    }
    
    yogas = []
    
    results = engine.compute_house_importance(chart_data, yogas)
    
    # Check that House 10 is relatively high rank (due to Lagna Lord placement)
    # House 1 should also be high due to seed boost
    house_10 = next(h for h in results["house_importance"] if h["house"] == 10)
    house_1 = next(h for h in results["house_importance"] if h["house"] == 1)
    
    assert house_1["rank"] in [1, 2]
    # House 10 receives influence from House 1 (via lord)
    assert any(e["from"] == 1 and e["to"] == 10 for e in results["edges"])

def test_yoga_influence():
    engine = PropagationEngine()
    
    # Gaja Kesari between House 1 and House 4
    chart_data = {
        "planets": [
            {"name": "JUPITER", "house": 1, "dignity": {"strength_modifier": 7.0}},
            {"name": "MOON", "house": 4, "dignity": {"strength_modifier": 7.0}}
        ],
        "houses": [
            {"number": 1, "lord": "MARS"},
            {"number": 4, "lord": "MOON"}
        ],
        "aspects": []
    }
    
    yogas = [
        {"name": "GAJA_KESARI", "participating_planets": ["JUPITER", "MOON"], "strength_score": 0.8}
    ]
    
    results = engine.compute_house_importance(chart_data, yogas)
    
    # Check for bidirectional edge between 1 and 4
    edges = results["edges"]
    assert any(e["from"] == 1 and e["to"] == 4 for e in edges)
    assert any(e["from"] == 4 and e["to"] == 1 for e in edges)

if __name__ == "__main__":
    pytest.main([__file__])
