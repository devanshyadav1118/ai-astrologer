"""Test for Phase 9 Temporal Dynamics Engine."""

import pytest
from reasoning.dasha_calculator import DashaEngine
from reasoning.vedic_astro_adapter import VedicAstroAdapter

def test_dasha_timeline_generation():
    adapter = VedicAstroAdapter()
    
    # Test chart data (Jan 1, 2000)
    birth_date = "2000-01-01"
    birth_time = "12:00:00"
    lat = 28.6
    lon = 77.2
    tz = 5.5
    
    periods = adapter.get_dasha_timeline(birth_date, birth_time, lat, lon, tz)
    
    # Check structure
    assert len(periods) > 0
    mahadashas = [p for p in periods if p["dasha_type"] == "mahadasha"]
    assert len(mahadashas) == 9 # All 9 planets
    
    # Check normalization
    assert mahadashas[0]["planet"] in ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN", "RAHU", "KETU"]
    
    # Check date formatting (YYYY-MM-DD)
    assert "-" in mahadashas[0]["start_date"]
    assert len(mahadashas[0]["start_date"]) == 10

if __name__ == "__main__":
    pytest.main([__file__])
