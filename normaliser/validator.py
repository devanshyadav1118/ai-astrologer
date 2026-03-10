"""Validation helpers for extracted rules."""

from __future__ import annotations

from typing import Any, Iterable

from normaliser.normaliser import AstrologyNormaliser


def validate_required_entities(values: Iterable[str]) -> None:
    """Reject empty canonical entity values."""
    for value in values:
        if not value or not value.strip():
            raise ValueError("canonical entity values must be non-empty")


class RuleValidator:
    """Validate extracted rules against the ontology."""

    VALID_TYPES = {"prediction", "description", "yoga", "calculation", "modification"}

    def __init__(self, normaliser: AstrologyNormaliser | None = None) -> None:
        self.normaliser = normaliser or AstrologyNormaliser()

    def validate_rule(self, rule: dict[str, Any]) -> dict[str, Any]:
        """Validate one extracted rule and enrich it with ontology metadata."""
        errors: list[str] = []
        warnings: list[str] = []

        required = ["rule_id", "type", "condition", "result", "source_text"]
        for field in required:
            value = rule.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"Missing required field: {field}")

        rule_type = rule.get("type")
        if rule_type and rule_type not in self.VALID_TYPES:
            warnings.append(
                f"Unknown rule type: {rule_type} - expected one of {sorted(self.VALID_TYPES)}"
            )

        candidates = self._extract_entity_candidates(rule.get("condition", ""))
        normalised_entities: dict[str, str] = {}
        for entity in candidates:
            canonical = self.normaliser.normalise(entity)
            if canonical is None:
                warnings.append(f'Unknown entity in condition: "{entity}" - needs manual review')
            else:
                normalised_entities[entity] = canonical

        status = "invalid" if errors else ("warning" if warnings else "valid")
        return {
            **rule,
            "normalised_entities": normalised_entities,
            "validation_errors": errors,
            "validation_warnings": warnings,
            "validation_status": status,
        }

    def validate_batch(self, rules: list[dict[str, Any]]) -> dict[str, Any]:
        """Validate a batch of rules and return categorised results and a summary."""
        results: dict[str, list[dict[str, Any]]] = {"valid": [], "warning": [], "invalid": []}
        for rule in rules:
            validated = self.validate_rule(rule)
            results[validated["validation_status"]].append(validated)

        total = len(rules)
        valid_count = len(results["valid"])
        warning_count = len(results["warning"])
        invalid_count = len(results["invalid"])
        valid_pct = round(valid_count / total * 100, 1) if total else 0.0
        return {
            "results": results,
            "summary": {
                "total": total,
                "valid": valid_count,
                "warning": warning_count,
                "invalid": invalid_count,
                "valid_pct": valid_pct,
            },
        }

    def _extract_entity_candidates(self, text: str) -> list[str]:
        matches = self.normaliser.extract_known_terms(text)
        if matches:
            return sorted(set(matches))
        return []
