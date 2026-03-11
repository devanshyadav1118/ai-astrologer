"""Post-processing and entity normalisation for extracted book data."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any

from extractor.adapter import adapt_rule, adapt_yoga
from normaliser.normaliser import AstrologyNormaliser
from normaliser.validator import RuleValidator

ENTITY_KEYS = ("planet", "sign", "house", "nakshatra", "yoga")


class PostProcessor:
    """Normalise extracted entities and collect review warnings."""

    def __init__(
        self,
        normaliser: AstrologyNormaliser | None = None,
        validator: RuleValidator | None = None,
    ) -> None:
        self.normaliser = normaliser or AstrologyNormaliser()
        self.validator = validator or RuleValidator(self.normaliser)
        self._ordered_synonyms = sorted(
            self.normaliser.synonym_map.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        )

    def normalise_book_data(self, raw_book_data: dict[str, Any]) -> dict[str, Any]:
        """Normalise stitched extraction output."""
        warnings: list[dict[str, Any]] = []
        stats = {
            "entities_normalised": 0,
            "unknown_entities": 0,
            "rules_processed": 0,
            "yogas_processed": 0,
        }

        normalised_rules = [
            self._normalise_rule(rule, warnings, stats)
            for rule in raw_book_data.get("rules", [])
        ]
        normalised_yogas = [
            self._normalise_generic_item(yoga, stats)
            for yoga in raw_book_data.get("yogas", [])
        ]

        return {
            "book_id": raw_book_data["book_id"],
            "normalised_rules": normalised_rules,
            "normalised_yogas": normalised_yogas,
            "warnings": warnings,
            "stats": stats,
            "metadata": deepcopy(raw_book_data.get("metadata", {})),
        }

    def _normalise_rule(
        self,
        rule: dict[str, Any],
        warnings: list[dict[str, Any]],
        stats: dict[str, int],
    ) -> dict[str, Any]:
        normalised_rule = adapt_rule(rule)
        normalised_entities: dict[str, str] = {}

        for text_key in ("condition", "result", "source_text", "condition_text", "description"):
            text_value = normalised_rule.get(text_key)
            if isinstance(text_value, str):
                normalised_rule[text_key] = self._normalise_text(text_value)

        conditions = normalised_rule.get("conditions")
        if isinstance(conditions, dict):
            for clause in conditions.get("clauses", []):
                if not isinstance(clause, dict):
                    continue
                for key in ENTITY_KEYS:
                    value = clause.get(key)
                    if not isinstance(value, str):
                        continue
                    canonical = self.normaliser.normalise(value)
                    if canonical is None:
                        warnings.append(
                            {
                                "type": "unknown_entity",
                                "entity": value,
                                "context": clause.get("raw_text", ""),
                                "rule_id": normalised_rule.get("rule_id"),
                            }
                        )
                        stats["unknown_entities"] += 1
                        continue
                    if canonical != value:
                        stats["entities_normalised"] += 1
                    clause[key] = canonical
                    normalised_entities[value] = canonical
                planets = clause.get("planets")
                if isinstance(planets, list):
                    normalised_planets: list[str] = []
                    for planet in planets:
                        if not isinstance(planet, str):
                            continue
                        canonical = self.normaliser.normalise(planet)
                        if canonical is None:
                            warnings.append(
                                {
                                    "type": "unknown_entity",
                                    "entity": planet,
                                    "context": clause.get("raw_text", ""),
                                    "rule_id": normalised_rule.get("rule_id"),
                                }
                            )
                            stats["unknown_entities"] += 1
                            normalised_planets.append(planet)
                            continue
                        if canonical != planet:
                            stats["entities_normalised"] += 1
                        normalised_planets.append(canonical)
                        normalised_entities[planet] = canonical
                    clause["planets"] = normalised_planets

        validated = self.validator.validate_rule(normalised_rule)
        merged_entities = dict(validated.get("normalised_entities", {}))
        merged_entities.update(normalised_entities)
        validated["normalised_entities"] = merged_entities
        stats["rules_processed"] += 1
        return validated

    def _normalise_generic_item(self, item: dict[str, Any], stats: dict[str, int]) -> dict[str, Any]:
        normalised_item = adapt_yoga(item) if "formation_logic" in item or "standard_effects" in item else deepcopy(item)
        for key, value in list(normalised_item.items()):
            if isinstance(value, str):
                normalised_item[key] = self._normalise_text(value)
            if key == "effects" and isinstance(value, list):
                for effect in value:
                    if isinstance(effect, dict) and isinstance(effect.get("description"), str):
                        effect["description"] = self._normalise_text(effect["description"])
        stats["yogas_processed"] += 1
        return normalised_item

    def _normalise_text(self, text: str) -> str:
        normalised_text = text
        for synonym, canonical in self._ordered_synonyms:
            pattern = rf"(?<![A-Za-z0-9]){re.escape(synonym)}(?![A-Za-z0-9])"
            normalised_text = re.sub(pattern, canonical, normalised_text, flags=re.IGNORECASE)
        return normalised_text


def normalise_book_data(raw_book_data: dict[str, Any]) -> dict[str, Any]:
    """Compatibility wrapper matching the roadmap API."""
    return PostProcessor().normalise_book_data(raw_book_data)
