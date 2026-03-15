"""Test for Unified Horoscope Adapter."""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from reasoning.unified_adapter import UnifiedHoroscopeAdapter
import json

def test_unified_data():
    adapter = UnifiedHoroscopeAdapter()
    
    # Devansh's Data
    birth_data = {
        "date": "2003-05-27",
        "time": "06:45:00",
        "latitude": 25.4484,
        "longitude": 78.5685,
        "timezone": 5.5
    }
    
    print("--- GENERATING UNIFIED HOROSCOPE DATA ---")
    data = adapter.get_all_horoscope_data(**birth_data)
    
    # 1. Verify Planets
    print(f"Planets Found: {len(data['planets'])}")
    
    # 2. Verify Significators
    print(f"Planet Significators: {len(data['significators']['planets'])}")
    print(f"House Significators: {len(data['significators']['houses'])}")
    
    # 3. Verify Dashas
    print(f"Dasha Table Keys: {list(data['dashas'].keys())}")
    
    # 4. Verify Aspects
    print(f"Aspects Count: {len(data['aspects'])}")

if __name__ == "__main__":
    test_unified_data()
