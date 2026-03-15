"""Test for Phase 7 Yoga Detection Engine."""

import pytest
from reasoning.yoga_detector import YogaDetector

def test_gaja_kesari_detection():
    detector = YogaDetector()
    
    # Mock chart data where Jupiter is in 4th from Moon
    # And Jupiter is not in Dusthana from Lagna (Lagna is Aries, Jupiter in 1st)
    chart_data = {
        "planets": [
            {
                "name": "JUPITER",
                "house": 1,
                "sign": "ARIES",
                "dignity": {"status": "friend", "strength_modifier": 6.5}
            },
            {
                "name": "MOON",
                "house": 10,
                "sign": "CAPRICORN",
                "dignity": {"status": "neutral", "strength_modifier": 5.0}
            }
        ],
        "houses": [
            {"number": 1, "sign": "ARIES", "lord": "MARS"}
        ],
        "aspects": [],
        "conjunctions": [],
        "dispositors": []
    }
    
    # Jupiter in 1st is 4th house from Moon in 10th (10, 11, 12, 1)
    yogas = detector.detect_yogas(chart_data)
    names = [y["name"] for y in yogas]
    
    assert "GAJA_KESARI" in names
    gk = next(y for y in yogas if y["name"] == "GAJA_KESARI")
    assert gk["is_present"] is True
    assert gk["strength_score"] > 0.5

def test_hamsa_yoga_detection():
    detector = YogaDetector()
    
    # Hamsa: Jupiter in Kendra + Own/Exaltation sign
    chart_data = {
        "planets": [
            {
                "name": "JUPITER",
                "house": 4,
                "sign": "CANCER",
                "dignity": {"status": "exalted", "strength_modifier": 9.5}
            }
        ],
        "houses": [
            {"number": 1, "sign": "ARIES", "lord": "MARS"}
        ],
        "aspects": [],
        "conjunctions": [],
        "dispositors": []
    }
    
    yogas = detector.detect_yogas(chart_data)
    names = [y["name"] for y in yogas]
    
    assert "HAMSA" in names
    hamsa = next(y for y in yogas if y["name"] == "HAMSA")
    assert hamsa["strength_band"] == "exceptional"

def test_raja_yoga_conjunction():
    detector = YogaDetector()
    
    # Aries Lagna: Sun (Lord 5 - Trikona) and Mars (Lord 1 - Kendra)
    chart_data = {
        "planets": [
            {"name": "SUN", "house": 10, "sign": "CAPRICORN", "dignity": {"status": "friend", "strength_modifier": 6.0}},
            {"name": "MARS", "house": 10, "sign": "CAPRICORN", "dignity": {"status": "exalted", "strength_modifier": 9.0}}
        ],
        "houses": [
            {"number": 1, "sign": "ARIES", "lord": "MARS"},
            {"number": 10, "sign": "CAPRICORN", "lord": "SATURN"},
            {"number": 5, "sign": "LEO", "lord": "SUN"}
        ],
        "aspects": [],
        "conjunctions": [
            {"planet_1": "SUN", "planet_2": "MARS", "orb": 2.0}
        ],
        "dispositors": []
    }
    
    yogas = detector.detect_yogas(chart_data)
    names = [y["name"] for y in yogas]
    
    assert "RAJA_YOGA" in names

if __name__ == "__main__":
    pytest.main([__file__])
