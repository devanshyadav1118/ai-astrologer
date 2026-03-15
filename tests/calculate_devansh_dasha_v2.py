"""Recalculate Dasha for Devansh Yadav using robust internal engine."""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from reasoning.dasha_calculator import VimshottariCalculator
import json

def get_devansh_dasha_robust():
    birth_data = {
        "date": "2003-05-27",
        "time": "06:45:00",
        "latitude": 25.4484,
        "longitude": 78.5685,
        "timezone": 5.5
    }
    # From devansh_yadav.json
    moon_longitude = 356.609629 
    
    calc = VimshottariCalculator()
    periods = calc.calculate_dasha_timeline(
        birth_data["date"], 
        birth_data["time"], 
        moon_longitude
    )
    
    today = "2026-03-15"
    
    print(f"--- ROBUST Dasha Timeline for Devansh Yadav ---")
    
    # 1. Find Current Active Periods
    active = [p for p in periods if p["start_date"] <= today <= p["end_date"]]
    print(f"\nACTIVE PERIODS (Today: {today}):")
    for p in active:
        print(f"  {p['dasha_type'].upper()}: {p['planet']} (Ends: {p['end_date']})")
    
    # 2. Verify against user's 'real' dates
    # User said Mercury balance was 4Y 3M 30D
    mercury_md = next(p for p in periods if p["planet"] == "MERCURY" and p["dasha_type"] == "mahadasha")
    print(f"\nMercury MD End: {mercury_md['end_date']} (Expected: 2007-09-26)")

if __name__ == "__main__":
    get_devansh_dasha_robust()
