"""Phase 6 Strength Engine for Vedic Astrology (Production Grade).

Implements the 5-component scoring model from Phase6theorey.md:
1. Dignity (40%) - includes Peak Degree and Neecha Bhanga.
2. House Position & Dig Bala (25%).
3. Aspect Score (20%) - uses Functional Benefic/Malefic logic.
4. Special States (10%) - Combustion, Retrograde, Graha Yuddha, Gandanta.
5. Dispositor Strength (5%).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class StrengthEngine:
    """Calculates planetary strength based on the Phase 6 Theoretical Roadmap."""

    # Theoretical Weights
    W_DIGNITY = 0.40
    W_HOUSE = 0.25
    W_ASPECT = 0.20
    W_SPECIAL = 0.10
    W_DISPOSITOR = 0.05
    
    BASE_SCORE = 5.0

    def __init__(self, ontology_dir: str | Path = "normaliser/ontology") -> None:
        self.ontology_dir = Path(ontology_dir)
        self.planets_by_name = self._load_ontology_map("planets.json", "planets")
        self.signs_by_name = self._load_ontology_map("signs.json", "signs")

    def calculate_planet_strength(
        self, 
        planet_name: str, 
        chart_data: dict[str, Any],
        dispositor_score: float = 5.0
    ) -> dict[str, Any]:
        """Calculate complete strength score for a planet in a specific chart."""
        planet_data = next(p for p in chart_data["planets"] if p["name"] == planet_name)
        lagna_sign = next(h["sign"] for h in chart_data["houses"] if h["number"] == 1)

        # 1. Dignity Component (±5.0)
        dignity_comp = self.compute_dignity_score(planet_data, chart_data)
        
        # 2. House Position & Dig Bala (±2.5)
        house_comp = self.compute_house_score(planet_data)
        
        # 3. Aspect Score (±3.0)
        aspect_comp = self.compute_aspect_score(planet_name, chart_data, lagna_sign)
        
        # 4. Special States (±3.0)
        special_comp = self.compute_special_states(planet_data, chart_data)
        
        # 5. Dispositor Strength (±0.5)
        dispositor_comp = self.map_dispositor_contribution(dispositor_score)

        # Aggregation Formula: base (5.0) + weighted components
        raw_score = (
            self.BASE_SCORE
            + (dignity_comp * self.W_DIGNITY)
            + (house_comp * self.W_HOUSE)
            + (aspect_comp * self.W_ASPECT)
            + (special_comp * self.W_SPECIAL)
            + (dispositor_comp * self.W_DISPOSITOR)
        )
        
        final_score = max(0.0, min(10.0, raw_score))
        
        # Classification Bands
        if final_score >= 7.5:
            band = "Strong"
        elif final_score >= 4.5:
            band = "Moderate"
        else:
            band = "Weak"

        return {
            "total_strength": round(final_score, 3),
            "band": band,
            "breakdown": {
                "dignity_contribution": round(dignity_comp * self.W_DIGNITY, 3),
                "house_contribution": round(house_comp * self.W_HOUSE, 3),
                "aspect_contribution": round(aspect_comp * self.W_ASPECT, 3),
                "special_contribution": round(special_comp * self.W_SPECIAL, 3),
                "dispositor_contribution": round(dispositor_comp * self.W_DISPOSITOR, 3),
                "raw_components": {
                    "dignity": round(dignity_comp, 3),
                    "house": round(house_comp, 3),
                    "aspect": round(aspect_comp, 3),
                    "special": round(special_comp, 3),
                    "dispositor": round(dispositor_comp, 3),
                }
            },
            "flags": {
                "is_combust": planet_data.get("combustion", False),
                "is_retrograde": planet_data.get("retrograde", False),
                "is_in_war": self._check_planetary_war(planet_data, chart_data) is not None,
                "neecha_bhanga": self.check_neecha_bhanga(planet_data, chart_data)
            }
        }

    def compute_dignity_score(self, planet_data: dict[str, Any], chart_data: dict[str, Any]) -> float:
        """Dignity scoring with Peak Degree and Neecha Bhanga overrides."""
        planet_name = planet_data["name"]
        status = planet_data.get("dignity", {}).get("status", "neutral")
        degree = planet_data["degree"]

        dignity_map = {
            "exalted": 5.0, "moolatrikona": 3.5, "own_sign": 2.5,
            "friend": 1.0, "neutral": 0.0, "enemy": -2.0, "debilitated": -5.0,
        }
        score = dignity_map.get(status, 0.0)

        # Peak Degree Bonus (+0.5)
        ontology_planet = self.planets_by_name.get(planet_name, {})
        if status == "exalted":
            peak = ontology_planet.get("exaltation_degree")
            if peak is not None and abs(degree - peak) <= 1.0:
                score += 0.5
        
        # Neecha Bhanga Override
        if status == "debilitated" and self.check_neecha_bhanga(planet_data, chart_data):
            score = 2.0  # Reverse penalty to moderate positive per theory

        return score

    def compute_house_score(self, planet_data: dict[str, Any]) -> float:
        """House position score (-2.5 to +2.5) including Dig Bala."""
        house = planet_data.get("house", 1)
        planet_name = planet_data["name"]
        
        # Theory: Kendras/Trikonas amplify (+1.5), Dusthanas suppress (-1.5)
        house_scores = {
            1: 1.5, 4: 1.5, 7: 1.5, 10: 1.5,
            5: 1.5, 9: 1.5,
            3: 0.5, 11: 0.5,
            6: -1.0, 8: -1.5, 12: -1.5,
            2: 0.0
        }
        score = house_scores.get(house, 0.0)
        
        # Dig Bala sub-step (+1.0)
        dig_bala_map = {
            "JUPITER": 1, "MERCURY": 1, "MOON": 4, "VENUS": 4,
            "SATURN": 7, "SUN": 10, "MARS": 10, "RAHU": 7, "KETU": 10
        }
        if dig_bala_map.get(planet_name) == house:
            score += 1.0
            
        return max(-2.5, min(2.5, score))

    def compute_aspect_score(self, planet_name: str, chart_data: dict[str, Any], lagna_sign: str) -> float:
        """Running aspect tally (±3.0 cap) using Functional Natures."""
        tally = 0.0
        aspects = [a for a in chart_data.get("aspects", []) if a["to_planet"] == planet_name]
        
        for aspect in aspects:
            aspector = aspect["from_planet"]
            nature = self.get_functional_nature(aspector, lagna_sign)
            
            # Modifier: Functional Benefic +1, Functional Malefic -1
            modifier = 1.0 if nature == "benefic" else -1.0
            if nature == "neutral":
                modifier = 0.0
            
            # Apply aspect strength (partial aspects handled via 'strength' field)
            tally += modifier * aspect.get("strength", 1.0)
            
        return max(-3.0, min(3.0, tally))

    def compute_special_states(self, planet_data: dict[str, Any], chart_data: dict[str, Any]) -> float:
        """Combustion (-3.0), Retrograde (+0.5), Graha Yuddha (±2.0), Gandanta (-1.0)."""
        score = 0.0
        planet_name = planet_data["name"]
        
        # 1. Combustion
        if planet_data.get("combustion", False) and planet_name != "MOON":
            status = planet_data.get("dignity", {}).get("status", "neutral")
            score -= 1.5 if status in ["exalted", "own_sign"] else 3.0
                    
        # 2. Retrograde
        if planet_data.get("retrograde", False):
            score += 0.5
            
        # 3. Graha Yuddha (Planetary War)
        war_result = self._check_planetary_war(planet_data, chart_data)
        if war_result == "winner":
            score += 0.5
        elif war_result == "loser":
            score -= 2.0
            
        # 4. Gandanta
        sign = planet_data["sign"]
        degree = planet_data["degree"]
        if (sign in ["ARIES", "LEO", "SAGITTARIUS"] and degree <= 1.0) or \
           (sign in ["PISCES", "CANCER", "SCORPIO"] and degree >= 29.0):
            score -= 1.0
            
        return max(-3.0, min(3.0, score))

    def map_dispositor_contribution(self, dispositor_score: float) -> float:
        """Map dispositor's total score to a ±0.5 additive modifier."""
        if dispositor_score < 3.0: return -0.5
        if dispositor_score < 5.0: return 0.0
        if dispositor_score < 7.0: return 0.3
        return 0.5

    def check_neecha_bhanga(self, planet_data: dict[str, Any], chart_data: dict[str, Any]) -> bool:
        """Classical debilitation cancellation conditions."""
        if planet_data.get("dignity", {}).get("status") != "debilitated":
            return False
        
        sign = planet_data["sign"]
        sign_lord = self.signs_by_name[sign]["ruler"]
        exalt_planet = self.signs_by_name[sign].get("exaltation_planet")
        
        # 1. Sign lord or Exaltation lord is in Kendra from Lagna
        for lord in [sign_lord, exalt_planet]:
            if not lord: continue
            lord_p = next((p for p in chart_data["planets"] if p["name"] == lord), None)
            if lord_p and lord_p["house"] in [1, 4, 7, 10]:
                return True
                
        # 2. Sign lord and Exaltation lord are in mutual Kendra (optional check)
        # 3. Planet is conjunct its own sign lord or exaltation lord
        for lord in [sign_lord, exalt_planet]:
            if not lord: continue
            if any(c for c in chart_data.get("conjunctions", []) 
                   if (c["planet_1"] == planet_data["name"] and c["planet_2"] == lord) or
                      (c["planet_2"] == planet_data["name"] and c["planet_1"] == lord)):
                return True

        return False

    def get_functional_nature(self, planet: str, lagna_sign: str) -> str:
        """Determine functional benefic/malefic status for the specific Lagna."""
        # Standard Parashari logic: 
        # Lords of 1, 5, 9 are Benefics. 
        # Lords of 3, 6, 11 are Malefics. 
        # Neutral/Mixed for others unless they rule a Kendra + Trikona (Yogakaraka).
        
        lagna_num = self.signs_by_name[lagna_sign]["number"]
        benefic_houses = {1, 5, 9}
        malefic_houses = {3, 6, 11}
        
        owned_houses = []
        for h_num in range(1, 13):
            sign_at_cusp = ((lagna_num + h_num - 2) % 12) + 1
            sign_name = next(s["canonical_name"] for s in self.signs_by_name.values() if s["number"] == sign_at_cusp)
            if self.signs_by_name[sign_name]["ruler"] == planet:
                owned_houses.append(h_num)
        
        owned_set = set(owned_houses)
        if owned_set & benefic_houses: return "benefic"
        if owned_set & malefic_houses: return "malefic"
        return "neutral"

    def _check_planetary_war(self, planet_data: dict[str, Any], chart_data: dict[str, Any]) -> str | None:
        """Determine if planet is in Graha Yuddha (within 1°)."""
        if planet_data["name"] in ["SUN", "MOON", "RAHU", "KETU"]:
            return None # Nodes and luminaries don't participate in war
            
        for other in chart_data["planets"]:
            if other["name"] == planet_data["name"] or other["name"] in ["SUN", "MOON", "RAHU", "KETU"]:
                continue
            
            # 1 degree orb
            diff = abs(planet_data["longitude"] - other["longitude"])
            if min(diff, 360 - diff) <= 1.0:
                # Winner is usually lower latitude, but here we use higher longitude 
                # as a simplified proxy if latitude isn't available.
                # Theoretical preference: planet with lower ecliptic latitude wins.
                if planet_data["longitude"] > other["longitude"]:
                    return "winner"
                return "loser"
        return None

    def _load_ontology_map(self, filename: str, top_key: str) -> dict[str, dict[str, Any]]:
        with (self.ontology_dir / filename).open(encoding="utf-8") as handle:
            payload = json.load(handle)
        return {item["canonical_name"]: item for item in payload[top_key] if isinstance(item, dict)}
