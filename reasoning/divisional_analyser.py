from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from normaliser.normaliser import AstrologyNormaliser
from chart.strength_engine import StrengthEngine

class DivisionalAnalyser:
    """Evaluates divisional charts and computes reinforcement scores."""

    def __init__(self, ontology_dir: str | Path = "normaliser/ontology", strength_engine: StrengthEngine | None = None):
        self.ontology_dir = Path(ontology_dir)
        self.normaliser = AstrologyNormaliser(self.ontology_dir)
        self.strength_engine = strength_engine or StrengthEngine(self.ontology_dir)
        self.logger = logging.getLogger(__name__)
        
        # Mapping dignity names to the Phase 6 scoring scale (-5 to +5)
        self.dignity_score_map = {
            "exalted": 5.0,
            "moolatrikona": 3.5,
            "own_sign": 2.5,
            "friend": 1.0,
            "neutral": 0.0,
            "enemy": -2.0,
            "debilitated": -5.0
        }

    def detect_vargottama(self, natal_planets: list[dict[str, Any]], d9_planets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Identifies Vargottama status and retrograde boundary review flags.
        """
        d9_map = {p["name"]: p["divisional_sign"] for p in d9_planets}
        results = []
        
        for p in natal_planets:
            name = p["name"]
            d1_sign = p["sign"]
            d9_sign = d9_map.get(name)
            
            is_varg = (d1_sign == d9_sign)
            
            # Retrograde Consideration (Roadmap Section 5)
            is_review = False
            if p.get("retrograde", False):
                if p["degree"] <= 1.0 or p["degree"] >= 29.0:
                    is_review = True
            
            results.append({
                "name": name,
                "divisional_sign": d9_sign,
                "is_vargottama": is_varg,
                "vargottama_review": is_review
            })
            
        return results

    def calculate_reinforcement_scores(
        self, 
        chart_id: str, 
        natal_planets: list[dict[str, Any]], 
        divisional_data: dict[str, list[dict[str, Any]]]
    ) -> dict[str, dict[str, Any]]:
        """
        Computes reinforcement scores for all planets across all divisional charts.
        Returns map: { chart_type: { planet_name: { score, state, div_dignity } } }
        """
        all_reinforcements = {}
        
        for chart_type, div_planets in divisional_data.items():
            chart_reinforcements = {}
            for dp in div_planets:
                planet_name = dp["name"]
                div_sign = dp["divisional_sign"]
                div_degree = dp.get("degree", 15.0) # Default mid-sign if not provided
                
                # Get natal info for this planet
                np = next((p for p in natal_planets if p["name"] == planet_name), None)
                if not np: continue
                
                d1_dignity_status = np["dignity"]["status"]
                is_varg = dp.get("is_vargottama", False)
                
                # 1. Determine Dignity in Divisional Sign
                div_dignity = self._determine_div_dignity(planet_name, div_sign, div_degree)
                
                # 2. Compute Reinforcement Score
                res = self.compute_reinforcement(
                    planet_name=planet_name,
                    d1_dignity_status=d1_dignity_status,
                    div_dignity_status=div_dignity["status"],
                    div_chart_code=chart_type,
                    is_vargottama=is_varg
                )
                
                chart_reinforcements[planet_name] = {
                    "score": res["score"],
                    "state": res["state"],
                    "div_dignity": div_dignity["status"]
                }
            all_reinforcements[chart_type] = chart_reinforcements
            
        return all_reinforcements

    def compute_reinforcement(
        self, 
        planet_name: str, 
        d1_dignity_status: str, 
        div_dignity_status: str, 
        div_chart_code: str,
        is_vargottama: bool = False
    ) -> dict[str, Any]:
        """
        Calculates reinforcement score for a planet in a divisional chart.
        Formula based on Section 6.2 of Roadmap.
        """
        # 1. Divisional Dignity Modifier (Normalized -1.0 to +1.0)
        div_raw_score = self.dignity_score_map.get(div_dignity_status, 0.0)
        div_mod = div_raw_score / 5.0
        
        # 2. D1 vs Divisional Agreement
        d1_raw_score = self.dignity_score_map.get(d1_dignity_status, 0.0)
        
        agreement_multiplier = 1.0
        # If signs are opposite (one pos, one neg), charts disagree
        if (d1_raw_score > 0 and div_raw_score < 0) or (d1_raw_score < 0 and div_raw_score > 0):
            agreement_multiplier = 0.5
            
        # 3. Base Reinforcement
        score = div_mod * agreement_multiplier
        
        # 4. Vargottama Bonus (+0.25 for D9)
        if is_vargottama and div_chart_code == "D9":
            score += 0.25
            
        score = max(-1.0, min(1.0, score))
        
        # 5. Agreement State
        if score > 0.2:
            state = "Reinforced"
        elif score < -0.2:
            state = "Undermined"
        else:
            state = "Neutral"
            
        return {
            "score": round(score, 3),
            "state": state
        }

    def aggregate_domain_reinforcement(
        self, 
        reinforcements: dict[str, dict[str, Any]], 
        natal_planets: list[dict[str, Any]],
        houses: list[dict[str, Any]]
    ) -> dict[str, float]:
        """
        Calculates aggregate reinforcement scores for life domains.
        D9 -> Marriage, Dharma, General
        D10 -> Career
        D12 -> Parents
        D7 -> Children
        """
        # Define domain mappings (which planets to check in which chart)
        # Career (D10): 10th lord, Sun, Saturn, planets in 10th
        # Relationship (D9): 7th lord, Venus, Jupiter, planets in 7th
        
        domains = {}
        
        # Helper to get 10th lord
        h10_lord = next((h["lord"] for h in houses if h["number"] == 10), None)
        p_in_h10 = [p["name"] for p in natal_planets if p["house"] == 10]
        career_planets = set([h10_lord, "SUN", "SATURN"] + p_in_h10)
        domains["CAREER"] = self._avg_reinforcement("D10", career_planets, reinforcements)

        h7_lord = next((h["lord"] for h in houses if h["number"] == 7), None)
        p_in_h7 = [p["name"] for p in natal_planets if p["house"] == 7]
        rel_planets = set([h7_lord, "VENUS", "JUPITER"] + p_in_h7)
        domains["RELATIONSHIPS"] = self._avg_reinforcement("D9", rel_planets, reinforcements)
        
        h9_lord = next((h["lord"] for h in houses if h["number"] == 9), None)
        dharma_planets = set([h9_lord, "JUPITER"])
        domains["DHARMA"] = self._avg_reinforcement("D9", dharma_planets, reinforcements)
        
        h4_lord = next((h["lord"] for h in houses if h["number"] == 4), None)
        h9_lord = next((h["lord"] for h in houses if h["number"] == 9), None) # Re-get
        parent_planets = set([h4_lord, h9_lord, "SUN", "MOON"])
        domains["PARENTS"] = self._avg_reinforcement("D12", parent_planets, reinforcements)
        
        h5_lord = next((h["lord"] for h in houses if h["number"] == 5), None)
        child_planets = set([h5_lord, "JUPITER"])
        domains["CHILDREN"] = self._avg_reinforcement("D7", child_planets, reinforcements)
        
        return {k: round(v, 3) for k, v in domains.items() if v is not None}

    def enrich_dashas_with_divisional_support(
        self, 
        dasha_periods: list[dict[str, Any]], 
        reinforcements: dict[str, dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Cross-references dasha periods with divisional reinforcement scores.
        Roadmap Section 7.
        """
        # Mapping of domain to divisional chart code
        DOMAIN_CHART_MAP = {
            "CAREER": "D10",
            "RELATIONSHIPS": "D9",
            "CHILDREN": "D7",
            "PARENTS": "D12",
            "GENERAL": "D9",
            "SPIRITUAL": "D9"
        }
        
        for p in dasha_periods:
            planet = p["planet"]
            # We add a support map for each dasha period
            # e.g., p["divisional_support"] = {"CAREER": 0.8, "RELATIONSHIPS": -0.2}
            support = {}
            for domain, chart_code in DOMAIN_CHART_MAP.items():
                chart_data = reinforcements.get(chart_code, {})
                if planet in chart_data:
                    support[domain] = chart_data[planet]["score"]
            
            p["divisional_support"] = support
            
        return dasha_periods

    def get_reinforcement_for_domain(
        self, 
        reinforcements: dict[str, dict[str, Any]], 
        natal_planets: list[dict[str, Any]], 
        houses: list[dict[str, Any]], 
        domain: str
    ) -> dict[str, Any]:
        """
        Public interface for Phase 11 to query domain-specific support.
        Roadmap Section 6.3.
        """
        domain = domain.upper()
        # 1. Identify relevant planets for the domain
        relevant_planets = []
        chart_code = "D9" # Default
        
        if domain == "CAREER":
            chart_code = "D10"
            h10_lord = next((h["lord"] for h in houses if h["number"] == 10), None)
            p_in_h10 = [p["name"] for p in natal_planets if p["house"] == 10]
            relevant_planets = list(set([h10_lord, "SUN", "SATURN"] + p_in_h10))
        elif domain == "RELATIONSHIPS":
            chart_code = "D9"
            h7_lord = next((h["lord"] for h in houses if h["number"] == 7), None)
            p_in_h7 = [p["name"] for p in natal_planets if p["house"] == 7]
            relevant_planets = list(set([h7_lord, "VENUS", "JUPITER"] + p_in_h7))
        elif domain == "CHILDREN":
            chart_code = "D7"
            h5_lord = next((h["lord"] for h in houses if h["number"] == 5), None)
            relevant_planets = list(set([h5_lord, "JUPITER"]))
        elif domain == "PARENTS":
            chart_code = "D12"
            h4_lord = next((h["lord"] for h in houses if h["number"] == 4), None)
            h9_lord = next((h["lord"] for h in houses if h["number"] == 9), None)
            relevant_planets = list(set([h4_lord, h9_lord, "SUN", "MOON"]))
        
        # 2. Extract their reinforcement details
        planet_details = []
        chart_reinf = reinforcements.get(chart_code, {})
        
        for p_name in relevant_planets:
            if not p_name: continue
            natal_p = next((p for p in natal_planets if p["name"] == p_name), {})
            reinf = chart_reinf.get(p_name, {"score": 0.0, "state": "Neutral", "div_dignity": "neutral"})
            
            planet_details.append({
                "planet": p_name,
                "d1_strength": natal_p.get("strength_scores", {}).get("total_strength", 5.0),
                "div_reinforcement_score": reinf["score"],
                "agreement_state": reinf["state"],
                "div_dignity": reinf["div_dignity"],
                "is_vargottama": natal_p.get("is_vargottama", False)
            })
            
        return {
            "domain": domain,
            "chart_used": chart_code,
            "relevant_planets": planet_details,
            "aggregate_score": self._avg_reinforcement(chart_code, set(relevant_planets), reinforcements)
        }

    def _avg_reinforcement(self, chart_type: str, planets: set[str | None], reinforcements: dict[str, dict[str, Any]]) -> float | None:
        if chart_type not in reinforcements: return None
        relevant = [reinforcements[chart_type][p]["score"] for p in planets if p in reinforcements[chart_type]]
        if not relevant: return 0.0
        return sum(relevant) / len(relevant)

    def _determine_div_dignity(self, planet: str, sign: str, degree: float) -> dict[str, Any]:
        """Simplified dignity lookup for divisional signs."""
        # Reuse the logic from VedicAstroCalculator/StrengthEngine
        # We'll re-implement a minimal version here to avoid circular dependencies
        planet_data = self.strength_engine.planets_by_name.get(planet, {})
        sign_data = self.strength_engine.signs_by_name.get(sign, {})
        
        dignity = {"status": "neutral"}
        
        if sign == planet_data.get("exaltation_sign"):
            dignity["status"] = "exalted"
        elif sign == planet_data.get("debilitation_sign"):
            dignity["status"] = "debilitated"
        elif sign in planet_data.get("own_signs", []):
            dignity["status"] = "own_sign"
        elif planet in sign_data.get("friendly_planets", []):
            dignity["status"] = "friend"
        elif planet in sign_data.get("enemy_planets", []):
            dignity["status"] = "enemy"
            
        return dignity
