"""Calculate Dasha for Devansh Yadav."""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from reasoning.vedic_astro_adapter import VedicAstroAdapter
import json

def get_devansh_dasha():
    birth_data = {
        "date": "2003-05-27",
        "time": "06:45:00",
        "latitude": 25.4484,
        "longitude": 78.5685,
        "timezone": 5.5
    }
    
    adapter = VedicAstroAdapter()
    periods = adapter.get_dasha_timeline(**birth_data)
    
    today = "2026-03-15"
    
    print(f"--- Dasha Timeline for Devansh Yadav (Born: {birth_data['date']}) ---")
    
    # 1. Find Current Active Periods
    active = [p for p in periods if p["start_date"] <= today <= p["end_date"]]
    print(f"\nACTIVE PERIODS (Today: {today}):")
    for p in active:
        print(f"  {p['dasha_type'].upper()}: {p['planet']} (Ends: {p['end_date']})")
    
    # 2. Show upcoming Antardashas in the current Mahadasha
    current_md = next(p["planet"] for p in active if p["dasha_type"] == "mahadasha")
    upcoming = [p for p in periods if p["dasha_type"] == "antardasha" 
                and p["parent_planet"] == current_md 
                and p["start_date"] > today]
    
    print(f"\nUPCOMING ANTARDASHAS (Under {current_md} Mahadasha):")
    for p in upcoming[:5]:
        print(f"  - {p['planet']}: {p['start_date']} to {p['end_date']}")

if __name__ == "__main__":
    get_devansh_dasha()
