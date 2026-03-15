"""Phase 7 Yoga Detection Engine.

Implements a pattern-matching engine to detect classical astrological 
combinations (Yogas) based on definitions in the ontology.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reasoning.models import ReasoningFact


class YogaDetector:
    """Evaluates chart data against yoga definitions in yogas.json."""

    def __init__(self, ontology_dir: str | Path = "normaliser/ontology") -> None:
        self.ontology_dir = Path(ontology_dir)
        self.yogas = self._load_yogas()
        self.functional_natures = self._load_functional_nature()
        self.signs = self._load_ontology_map("signs.json", "signs")

    def detect_yogas(self, chart_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Run all yoga definitions against the provided chart."""
        detected = []
        for yoga_def in self.yogas:
            result = self.evaluate_yoga(yoga_def, chart_data)
            if result["is_present"]:
                detected.append(result)
        return detected

    def evaluate_yoga(self, yoga_def: dict[str, Any], chart_data: dict[str, Any]) -> dict[str, Any]:
        """Evaluate a single yoga definition against chart facts."""
        conditions = yoga_def.get("conditions", {})
        logic = conditions.get("logic", "AND")
        rules = conditions.get("rules", [])
        
        passed_rules = []
        participating_planets = set()
        
        for rule in rules:
            rule_result = self._evaluate_rule(rule, chart_data)
            if rule_result["passed"]:
                passed_rules.append(rule_result)
                participating_planets.update(rule_result.get("planets", []))
            
        # Logic check
        is_present = False
        if logic == "AND":
            is_present = len(passed_rules) == len(rules)
        elif logic == "OR":
            is_present = len(passed_rules) > 0
            
        # Check Cancellations if present
        is_cancelled = False
        cancellation_reason = None
        if is_present:
            cancellation_check = self._check_cancellations(yoga_def, chart_data)
            is_cancelled = cancellation_check["is_cancelled"]
            cancellation_reason = cancellation_check["reason"]

        # Calculate Strength (Weighted average of participating planets + context)
        strength = 0.0
        if is_present:
            strength = self._calculate_yoga_strength(yoga_def, chart_data, participating_planets, is_cancelled)

        return {
            "name": yoga_def["canonical_name"],
            "is_present": is_present,
            "is_cancelled": is_cancelled,
            "cancellation_reason": cancellation_reason,
            "strength_score": round(strength, 3),
            "strength_band": self._get_strength_band(strength),
            "participating_planets": list(participating_planets),
            "source_text": yoga_def.get("source_text", ""),
            "reasoning_steps": passed_rules
        }

    def _evaluate_rule(self, rule: dict[str, Any], chart_data: dict[str, Any]) -> dict[str, Any]:
        """Evaluate a single condition rule (e.g. 'Jupiter in kendra from Moon')."""
        # This is the heart of the pattern matcher.
        # Implementation for Day 2-4 will expand this.
        passed = False
        planets_involved = []
        
        # Example: planet in_kendra_from reference
        if rule.get("relation") == "in_kendra_from":
            p_name = rule["planet"]
            ref_name = rule["reference"]
            
            p_data = next((p for p in chart_data["planets"] if p["name"] == p_name), None)
            ref_data = next((p for p in chart_data["planets"] if p["name"] == ref_name), None)
            
            if p_data and ref_data:
                # Kendra = 1, 4, 7, 10 houses away (inclusive counting)
                # 1st from self = 1, 2nd = 2... 12th = 12
                diff = (p_data["house"] - ref_data["house"] + 12) % 12 + 1
                if diff in [1, 4, 7, 10]:
                    passed = True
                    planets_involved = [p_name, ref_name]

        # Example: planet in_house_type (kendra, trikona, etc)
        elif "in_house_type" in rule:
            p_name = rule["planet"]
            h_type = rule["in_house_type"]
            p_data = next((p for p in chart_data["planets"] if p["name"] == p_name), None)
            
            if p_data:
                h_num = p_data["house"]
                if h_type == "kendra" and h_num in [1, 4, 7, 10]:
                    passed = True
                elif h_type == "trikona" and h_num in [1, 5, 9]:
                    passed = True
                if passed:
                    planets_involved = [p_name]

        # Example: planet not_in houses
        elif "not_in" in rule:
            p_name = rule["planet"]
            houses = rule["not_in"]
            p_data = next((p for p in chart_data["planets"] if p["name"] == p_name), None)
            if p_data:
                h_name = f"HOUSE_{p_data['house']}"
                if h_name not in houses:
                    passed = True
                    planets_involved = [p_name]

        # Example: planet in houses (or planets_in_house count)
        elif "planets_in_house" in rule:
            # For Sunapha/Anapha: planets in 2nd from Moon, etc
            ref_name = rule.get("from_reference")
            target_offset = rule["planets_in_house"]
            exclude = rule.get("exclude_planets", [])
            
            ref_data = next((p for p in chart_data["planets"] if p["name"] == ref_name), None)
            if ref_data:
                target_house = ((ref_data["house"] + target_offset - 2) % 12) + 1
                occupants = [p["name"] for p in chart_data["planets"] 
                             if p["house"] == target_house and p["name"] not in exclude]
                if occupants:
                    passed = True
                    planets_involved = [ref_name] + occupants

        # Example: planet in_own_or_exaltation_sign
        elif rule.get("in_own_or_exaltation_sign") is True:
            p_name = rule["planet"]
            p_data = next((p for p in chart_data["planets"] if p["name"] == p_name), None)
            if p_data:
                status = p_data.get("dignity", {}).get("status")
                if status in ["exalted", "own_sign", "moolatrikona"]:
                    passed = True
                    planets_involved = [p_name]

        # Example: conjunction_between two lord groups
        elif "conjunction_between" in rule:
            group_a, group_b = rule["conjunction_between"]
            planets_a = self._resolve_planet_group(group_a, chart_data)
            planets_b = self._resolve_planet_group(group_b, chart_data)
            
            for p_a in planets_a:
                for p_b in planets_b:
                    if p_a == p_b: continue # Same planet doesn't form conjunction with self
                    if any(c for c in chart_data.get("conjunctions", []) 
                           if (c["planet_1"] == p_a and c["planet_2"] == p_b) or
                              (c["planet_2"] == p_a and c["planet_1"] == p_b)):
                        passed = True
                        planets_involved = [p_a, p_b]
                        break
                if passed: break

        # Example: aspect_between two lord groups
        elif "aspect_between" in rule:
            group_a, group_b = rule["aspect_between"]
            planets_a = self._resolve_planet_group(group_a, chart_data)
            planets_b = self._resolve_planet_group(group_b, chart_data)
            
            for p_a in planets_a:
                for p_b in planets_b:
                    if p_a == p_b: continue
                    if any(a for a in chart_data.get("aspects", []) 
                           if (a["from_planet"] == p_a and a["to_planet"] == p_b) or
                              (a["from_planet"] == p_b and a["to_planet"] == p_a)):
                        passed = True
                        planets_involved = [p_a, p_b]
                        break
                if passed: break

        # Example: mutual_reception_between
        elif "mutual_reception_between" in rule:
            group_a, group_b = rule["mutual_reception_between"]
            planets_a = self._resolve_planet_group(group_a, chart_data)
            planets_b = self._resolve_planet_group(group_b, chart_data)
            
            for p_a in planets_a:
                for p_b in planets_b:
                    if p_a == p_b: continue
                    if any(d for d in chart_data.get("dispositors", []) if d["planet"] == p_a and d["dispositor"] == p_b) and \
                       any(d for d in chart_data.get("dispositors", []) if d["planet"] == p_b and d["dispositor"] == p_a):
                        passed = True
                        planets_involved = [p_a, p_b]
                        break
                if passed: break

        # Example: planet in_house (specific house name like HOUSE_1)
        elif "in_house" in rule:
            p_name = rule["planet"]
            target_house = rule["in_house"]
            p_data = next((p for p in chart_data["planets"] if p["name"] == p_name), None)
            if p_data and f"HOUSE_{p_data['house']}" == target_house:
                passed = True
                planets_involved = [p_name]

        # Example: planet strong (using Phase 6 total_strength)
        elif rule.get("strong") is True:
            p_name = rule["planet"]
            p_data = next((p for p in chart_data["planets"] if p["name"] == p_name), None)
            # Threshold 6.0 for 'strong' as per roadmap suggestion
            if p_data and p_data["dignity"].get("strength_modifier", 0.0) >= 6.0:
                passed = True
                planets_involved = [p_name]

        return {
            "rule": rule,
            "passed": passed,
            "planets": planets_involved
        }

    def _calculate_yoga_strength(
        self, 
        yoga_def: dict[str, Any], 
        chart_data: dict[str, Any], 
        planets: set[str],
        is_cancelled: bool
    ) -> float:
        """Calculate yoga strength (0.0 to 1.0) based on Phase 6 planet scores."""
        if not planets: return 0.5
        
        scores = []
        for p_name in planets:
            p_data = next((p for p in chart_data["planets"] if p["name"] == p_name), None)
            if p_data:
                # Convert 0-10 planet score to 0-1 scale
                scores.append(p_data["dignity"].get("strength_modifier", 5.0) / 10.0)
        
        avg_score = sum(scores) / len(scores) if scores else 0.5
        
        # Apply cancellation penalty
        if is_cancelled:
            avg_score *= 0.5
            
        return max(0.0, min(1.0, avg_score))

    def _get_strength_band(self, score: float) -> str:
        if score >= 0.85: return "exceptional"
        if score >= 0.6: return "strong"
        if score >= 0.3: return "moderate"
        return "weak"

    def _check_cancellations(self, yoga_def: dict[str, Any], chart_data: dict[str, Any]) -> dict[str, Any]:
        """Check for cancellation conditions defined in the ontology."""
        # Stub for Day 3-4
        return {"is_cancelled": False, "reason": None}

    def _load_yogas(self) -> list[dict[str, Any]]:
        with (self.ontology_dir / "yogas.json").open(encoding="utf-8") as h:
            return json.load(h)["yogas"]

    def _load_functional_nature(self) -> dict[str, Any]:
        with (self.ontology_dir / "functional_nature.json").open(encoding="utf-8") as h:
            return json.load(h)["functional_natures"]

    def _load_ontology_map(self, filename: str, top_key: str) -> dict[str, dict[str, Any]]:
        with (self.ontology_dir / filename).open(encoding="utf-8") as h:
            payload = json.load(h)
        return {item["canonical_name"]: item for item in payload[top_key] if isinstance(item, dict)}

    def _get_lords_of_houses(self, houses: list[int], chart_data: dict[str, Any]) -> list[str]:
        """Find planets ruling the specified houses for the current Lagna."""
        lords = []
        for h_num in houses:
            house_data = next((h for h in chart_data["houses"] if h["number"] == h_num), None)
            if house_data:
                lords.append(house_data["lord"])
        return list(set(lords))

    def _get_kendra_lords(self, chart_data: dict[str, Any]) -> list[str]:
        return self._get_lords_of_houses([1, 4, 7, 10], chart_data)

    def _get_trikona_lords(self, chart_data: dict[str, Any]) -> list[str]:
        return self._get_lords_of_houses([1, 5, 9], chart_data)

    def _resolve_planet_group(self, group_name: str, chart_data: dict[str, Any]) -> list[str]:
        """Translate terms like 'trikona_lord' or 'HOUSE_2_lord' into planet names."""
        if group_name == "trikona_lord":
            return self._get_trikona_lords(chart_data)
        if group_name == "kendra_lord":
            return self._get_kendra_lords(chart_data)
        if group_name.startswith("HOUSE_") and group_name.endswith("_lord"):
            h_num = int(group_name.split("_")[1])
            return self._get_lords_of_houses([h_num], chart_data)
        
        # Literal planet name
        return [group_name]
