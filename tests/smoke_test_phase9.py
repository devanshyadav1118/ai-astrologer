"""Temporal Smoke Test for Phase 9."""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from reasoning.dasha_calculator import DashaEngine
from reasoning.transit_calculator import TransitEngine
from reasoning.temporal_synthesiser import TemporalSynthesiser
from chart.vedicastro_calculator import VedicAstroCalculator
import json

def smoke_test():
    # 1. Setup Natal Data (Jan 1, 1990)
    birth_data = {
        "date": "1990-01-01", "time": "12:00:00",
        "latitude": 28.6, "longitude": 77.2, "timezone": 5.5
    }
    calc = VedicAstroCalculator()
    natal_chart = calc.calculate_chart(**birth_data)
    
    # 2. Setup Engines
    # Note: Using mock Neo4j client behavior for enrichment during smoke test
    dasha_engine = DashaEngine()
    transit_engine = TransitEngine()
    synth = TemporalSynthesiser()
    
    print("--- 1. GENERATING DASHAS ---")
    # Get moon longitude from natal chart
    moon_lon = next(p["longitude"] for p in natal_chart["planets"] if p["name"] == "MOON")
    
    # Get dasha timeline
    periods = dasha_engine.calculator.calculate_dasha_timeline(
        birth_date=birth_data["date"],
        birth_time=birth_data["time"],
        moon_longitude=moon_lon
    )
    
    # Find Active Dasha for "Today" (2026-03-15)
    today = "2026-03-15"
    active_stack = [p for p in periods if p["start_date"] <= today <= p["end_date"]]
    print(f"Active Periods on {today}:")
    for p in active_stack:
        print(f"  - {p['dasha_type'].upper()}: {p['planet']}")

    print("\n--- 2. CALCULATING TRANSITS ---")
    transits = transit_engine.calculate_transits(today, "12:00:00")
    interactions = transit_engine.evaluate_interactions(transits, natal_chart)
    print(f"Detected {len(interactions)} transit interactions with natal chart.")

    print("\n--- 3. SYNTHESIZING PREDICTION ---")
    # Mock some theme importance from Phase 8
    theme_importance = {"CAREER": 9.5, "WEALTH": 7.0, "HEALTH": 4.0}
    
    predictions = synth.synthesize_prediction(active_stack, interactions, theme_importance)
    
    for pred in predictions[:3]:
        print(f"Theme: {pred['theme']}")
        print(f"  Intensity: {pred['intensity']} ({pred['confidence']} confidence)")
        print(f"  Reasoning: Active Dasha {pred['reasoning']['dasha_planets']}")

if __name__ == "__main__":
    smoke_test()
