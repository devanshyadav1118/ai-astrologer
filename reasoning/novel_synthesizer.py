"""Novel-combination synthesis for Phase 5."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class NovelCombinationSynthesizer:
    """Build first-principles syntheses for combinations lacking direct rule support."""

    def __init__(self, ontology_dir: str | Path = "normaliser/ontology") -> None:
        self.ontology_dir = Path(ontology_dir)
        self.planets = self._load_ontology_map("planets.json", "planets")
        self.houses = self._load_ontology_map("houses.json", "houses", key="number")

    def synthesize_house(
        self,
        house_number: int,
        lord_name: str,
        placement_house: int,
        aspects: list[dict[str, Any]],
        conjunctions: list[dict[str, Any]],
        occupied_by: list[str],
        analogous_rules: list[dict[str, Any]],
    ) -> dict[str, Any]:
        lord = self.planets.get(lord_name, {})
        house = self.houses.get(house_number, {})
        placement = self.houses.get(placement_house, {})
        elemental_statement = self._elemental_statement(
            lord_element=str(lord.get("element", "neutral")),
            house_purushartha=str(house.get("purushartha", "mixed")),
            placement_purushartha=str(placement.get("purushartha", "mixed")),
        )
        functional_parts = [
            f"{lord_name} contributes {self._format_values(lord.get('natural_karakatvam', []), 3)}",
            f"House {house_number} governs {self._format_values(house.get('primary_meanings', []), 3)}",
            f"House {placement_house} redirects the result toward {self._format_values(placement.get('primary_meanings', []), 3)}",
        ]
        modulation = self._modulation_statement(aspects, conjunctions, occupied_by)
        confidence = self._confidence_from_analogies(analogous_rules, aspects, conjunctions)
        synthesis = " ".join(
            part
            for part in [
                elemental_statement,
                ". ".join(functional_parts) + ".",
                modulation,
            ]
            if part
        ).strip()
        return {
            "summary": synthesis,
            "confidence_band": confidence["band"],
            "confidence_score": confidence["score"],
            "analogous_rules": analogous_rules,
            "novel": len(analogous_rules) == 0,
        }

    def _elemental_statement(self, lord_element: str, house_purushartha: str, placement_purushartha: str) -> str:
        mapping = {
            ("fire", "dharma"): "Fire aligned with dharma produces purposeful initiative",
            ("fire", "artha"): "Fire in artha channels ambition into achievement",
            ("earth", "artha"): "Earth in artha stabilizes practical results",
            ("earth", "kama"): "Earth in kama turns desire into applied skill",
            ("air", "kama"): "Air in kama amplifies social and communicative expression",
            ("water", "moksha"): "Water in moksha deepens inner and emotional processing",
        }
        statement = mapping.get((lord_element.lower(), house_purushartha.lower()))
        if statement is None:
            statement = (
                f"{lord_element.title()} energy moving from {house_purushartha} to "
                f"{placement_purushartha} themes produces a mixed but interpretable outcome"
            )
        return statement + "."

    def _modulation_statement(
        self,
        aspects: list[dict[str, Any]],
        conjunctions: list[dict[str, Any]],
        occupied_by: list[str],
    ) -> str:
        parts: list[str] = []
        if aspects:
            parts.append(
                "Aspects add "
                + ", ".join(f"{item['from_planet'].title()} via {item['type'].lower()}" for item in aspects)
            )
        if conjunctions:
            parts.append(
                "conjunctions add "
                + ", ".join(f"{item['planet'].title()} blending" for item in conjunctions)
            )
        if occupied_by:
            parts.append("occupants emphasize " + ", ".join(planet.title() for planet in occupied_by))
        if not parts:
            return ""
        return "Modifiers: " + "; ".join(parts) + "."

    def _confidence_from_analogies(
        self,
        analogous_rules: list[dict[str, Any]],
        aspects: list[dict[str, Any]],
        conjunctions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if analogous_rules:
            avg = sum(float(rule.get("confidence", 0.0)) for rule in analogous_rules) / len(analogous_rules)
            score = round(min(avg / 5.0, 1.0), 3)
            return {"band": "high" if score >= 0.75 else "medium", "score": score}
        complexity = len(aspects) + len(conjunctions)
        score = round(max(0.35, 0.7 - (complexity * 0.05)), 3)
        return {"band": "medium" if score >= 0.5 else "low", "score": score}

    def _load_ontology_map(self, filename: str, top_key: str, key: str = "canonical_name") -> dict[Any, dict[str, Any]]:
        with (self.ontology_dir / filename).open(encoding="utf-8") as handle:
            payload = json.load(handle)
        return {
            item[key]: item
            for item in payload[top_key]
            if isinstance(item, dict) and item.get(key) is not None
        }

    def _format_values(self, values: Any, limit: int) -> str:
        if not isinstance(values, list):
            return "core themes"
        cleaned = [str(value).replace("_", " ") for value in values[:limit]]
        return ", ".join(cleaned) if cleaned else "core themes"
