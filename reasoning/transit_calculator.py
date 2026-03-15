"""Phase 9 Transit Dynamics Engine.

Calculates real-time transit positions and their interactions with the natal chart.
"""

from __future__ import annotations

import swisseph as swe
from datetime import datetime
from pathlib import Path
from typing import Any

from normaliser.normaliser import AstrologyNormaliser


class TransitEngine:
    """Calculates planetary transits and evaluates interactions with natal points."""

    def __init__(self, ontology_dir: str | Path = "normaliser/ontology") -> None:
        self.ontology_dir = Path(ontology_dir)
        self.normaliser = AstrologyNormaliser(self.ontology_dir)

    def calculate_transits(self, target_date: str, target_time: str) -> list[dict[str, Any]]:
        """Compute sidereal positions for all planets on a specific date."""
        # Setup Swiss Ephemeris for Sidereal
        # 1 = Lahiri
        swe.set_sid_mode(1) 
        
        y, m, d = map(int, target_date.split("-"))
        h, mn, s = map(int, target_time.split(":"))
        
        # Julian Day
        jd = swe.julday(y, m, d, h + mn/60.0 + s/3600.0)
        
        flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
        
        planets = []
        planet_map = {
            "SUN": swe.SUN, "MOON": swe.MOON, "MARS": swe.MARS,
            "MERCURY": swe.MERCURY, "JUPITER": swe.JUPITER, 
            "VENUS": swe.VENUS, "SATURN": swe.SATURN, "RAHU": swe.MEAN_NODE
        }
        
        for name, swe_id in planet_map.items():
            res, _ = swe.calc_ut(jd, swe_id, flags)
            lon = res[0]
            planets.append({
                "name": name,
                "longitude": round(lon, 6),
                "sign": self._get_sign(lon)
            })
            
        # Add Ketu
        rahu = next(p for p in planets if p["name"] == "RAHU")
        planets.append({
            "name": "KETU",
            "longitude": (rahu["longitude"] + 180.0) % 360.0,
            "sign": self._get_sign((rahu["longitude"] + 180.0) % 360.0)
        })
        
        return planets

    def evaluate_interactions(self, transits: list[dict[str, Any]], natal_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Detect interactions: Transit over Planet, House, and Aspect."""
        interactions = []
        
        for tp in transits:
            # 1. Transit over Natal Planet (Orb 1.0 deg)
            for np in natal_data["planets"]:
                diff = abs(tp["longitude"] - np["longitude"])
                if min(diff, 360 - diff) <= 1.0:
                    interactions.append({
                        "type": "conjunction",
                        "transit_planet": tp["name"],
                        "natal_target": np["name"],
                        "strength": 1.0
                    })
            
            # 2. Transit over Natal House Cusps (Optional - usually sign based)
            # 3. Transit via Drishti (from Phase 7 rules)
            # Use a simplified sign-based aspect for now
            aspected_signs = self._get_aspected_signs(tp["name"], tp["sign"])
            for np in natal_data["planets"]:
                if np["sign"] in aspected_signs:
                    interactions.append({
                        "type": "aspect",
                        "transit_planet": tp["name"],
                        "natal_target": np["name"],
                        "strength": 0.8
                    })
                    
        return interactions

    def _get_sign(self, lon: float) -> str:
        signs = ["ARIES", "TAURUS", "GEMINI", "CANCER", "LEO", "VIRGO", 
                 "LIBRA", "SCORPIO", "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES"]
        return signs[int(lon // 30) % 12]

    def _get_aspected_signs(self, planet: str, sign: str) -> list[str]:
        """Get signs aspected by a planet in a specific sign."""
        signs = ["ARIES", "TAURUS", "GEMINI", "CANCER", "LEO", "VIRGO", 
                 "LIBRA", "SCORPIO", "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES"]
        idx = signs.index(sign)
        
        aspected = []
        # 7th aspect for all
        aspected.append(signs[(idx + 6) % 12])
        
        if planet == "MARS":
            aspected.append(signs[(idx + 3) % 12])
            aspected.append(signs[(idx + 7) % 12])
        elif planet == "JUPITER":
            aspected.append(signs[(idx + 4) % 12])
            aspected.append(signs[(idx + 8) % 12])
        elif planet == "SATURN":
            aspected.append(signs[(idx + 2) % 12])
            aspected.append(signs[(idx + 9) % 12])
            
        return aspected
