from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

class DivisionalCalculator:
    """Calculates divisional chart positions based on Phase 10 roadmap."""

    SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]

    def __init__(self, ontology_dir: str | Path = "normaliser/ontology"):
        self.ontology_dir = Path(ontology_dir)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        with (self.ontology_dir / "divisional_charts.json").open("r", encoding="utf-8") as f:
            data = json.load(f)
        return {item["chart_code"]: item for item in data["divisional_charts"]}

    def calculate_position(self, chart_code: str, natal_sign: str, intra_sign_deg: float) -> str:
        """
        Calculates the divisional sign for a given planet position.
        
        Args:
            chart_code: e.g., 'D9', 'D10'
            natal_sign: e.g., 'Scorpio'
            intra_sign_deg: degrees within the sign (0-30)
        """
        if chart_code not in self.config:
            raise ValueError(f"Unsupported divisional chart: {chart_code}")
            
        chart_meta = self.config[chart_code]
        segment_size = chart_meta["segment_degrees"]
        
        # 1. Determine segment number (0-indexed)
        segment_nr = int(intra_sign_deg // segment_size)
        
        # 2. Get starting sign for the sequence
        # Ensure natal_sign is in Title Case for mapping
        natal_sign_key = natal_sign.capitalize()
        start_sign_name = self.config[chart_code]["sequence_map"].get(natal_sign_key)
        
        if not start_sign_name:
            raise ValueError(f"Sign {natal_sign} not found in sequence map for {chart_code}")
            
        start_sign_idx = self.SIGNS.index(start_sign_name)
        
        print(f"DEBUG: {chart_code} {natal_sign} {intra_sign_deg} -> segment {segment_nr}, start {start_sign_name}({start_sign_idx})")
        
        # 3. Map to final sign
        final_sign_idx = (start_sign_idx + segment_nr) % 12
        return self.SIGNS[final_sign_idx]

    def calculate_all_divisions(self, natal_planets: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Computes all priority divisional charts for a set of natal planets.
        
        Returns:
            Dict mapping chart_code to a list of planet placements.
        """
        results = {}
        for code in self.config.keys():
            chart_placements = []
            for p in natal_planets:
                # We need the sign and the degree WITHIN that sign (0-30)
                # Some objects might have 'degree' as intra-sign already
                div_sign = self.calculate_position(code, p["sign"], p["degree"])
                chart_placements.append({
                    "name": p["name"],
                    "divisional_sign": div_sign
                })
            results[code] = chart_placements
        return results
