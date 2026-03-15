"""Test for Phase 6 Strength Engine (Production Grade)."""

import pytest
from chart.strength_engine import StrengthEngine

def test_strength_engine_basics():
    engine = StrengthEngine()
    
    # Mock chart data
    chart_data = {
        "planets": [
            {
                "name": "SUN",
                "sign": "ARIES",
                "degree": 10.0,
                "longitude": 10.0,
                "house": 10,
                "dignity": {"status": "exalted"},
                "retrograde": False,
                "combustion": False
            }
        ],
        "houses": [
            {"number": 1, "sign": "CANCER"} # Lagna for Sun in 10th
        ],
        "aspects": []
    }
    
    strength = engine.calculate_planet_strength("SUN", chart_data)
    
    # Sun exalted in 10th (Dig Bala)
    assert strength["total_strength"] > 7.0
    # New structure: breakdown -> raw_components -> dignity
    assert strength["breakdown"]["raw_components"]["dignity"] == 5.5 
    assert strength["breakdown"]["raw_components"]["house"] == 2.5   
    assert strength["band"] == "Strong"

def test_neecha_bhanga():
    engine = StrengthEngine()
    
    # Saturn debilitated in Aries
    # Dispositor (Mars) in Capricorn (10th house - Kendra)
    chart_data = {
        "planets": [
            {
                "name": "SATURN",
                "sign": "ARIES",
                "degree": 20.0,
                "longitude": 20.0,
                "house": 1,
                "dignity": {"status": "debilitated"},
                "retrograde": False
            },
            {
                "name": "MARS",
                "sign": "CAPRICORN",
                "degree": 28.0,
                "longitude": 298.0,
                "house": 10,
                "dignity": {"status": "exalted"},
                "retrograde": False
            }
        ],
        "houses": [
            {"number": 1, "sign": "ARIES"} # Lagna is Aries
        ],
        "aspects": []
    }
    
    strength = engine.calculate_planet_strength("SATURN", chart_data)
    
    assert strength["flags"]["neecha_bhanga"] is True
    assert strength["breakdown"]["raw_components"]["dignity"] == 2.0 # Cancelled debilitation

def test_functional_nature():
    engine = StrengthEngine()
    
    # Aries Lagna: Mars (Lord 1) = Benefic, Saturn (Lord 10, 11) = Malefic
    nature_mars = engine.get_functional_nature("MARS", "ARIES")
    nature_saturn = engine.get_functional_nature("SATURN", "ARIES")
    
    assert nature_mars == "benefic"
    assert nature_saturn == "malefic"

def test_graha_yuddha():
    engine = StrengthEngine()
    
    # Mars and Saturn within 1 degree
    chart_data = {
        "planets": [
            {
                "name": "MARS",
                "sign": "ARIES",
                "degree": 10.5,
                "longitude": 10.5,
                "house": 1,
                "dignity": {"status": "own_sign"},
                "retrograde": False
            },
            {
                "name": "SATURN",
                "sign": "ARIES",
                "degree": 11.0,
                "longitude": 11.0,
                "house": 1,
                "dignity": {"status": "debilitated"},
                "retrograde": False
            }
        ],
        "houses": [
            {"number": 1, "sign": "ARIES"}
        ],
        "aspects": []
    }
    
    s1 = engine.calculate_planet_strength("MARS", chart_data)
    s2 = engine.calculate_planet_strength("SATURN", chart_data)
    
    assert s1["flags"]["is_in_war"] is True
    assert s2["flags"]["is_in_war"] is True
    
    # Saturn at higher longitude (11.0) wins over Mars (10.5) in our simplified proxy
    assert s2["breakdown"]["raw_components"]["special"] > s1["breakdown"]["raw_components"]["special"]

if __name__ == "__main__":
    pytest.main([__file__])
