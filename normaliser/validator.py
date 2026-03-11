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
    """Validate extracted astrological rules against schema v2.0 and the ontology."""

    VALID_TYPES = ["prediction", "description", "yoga", "calculation", "modification"]
    VALID_CLAUSE_TYPES = ["planet_state", "aspect", "conjunction", "house_lord", "dignity", "other"]
    VALID_OPERATORS = ["AND", "OR"]
    VALID_IMPACTS = ["positive", "negative", "neutral"]
    VALID_INTENSITIES = ["low", "medium", "high"]
    VALID_PROBABILITIES = ["certain", "likely", "possible", "conditional"]
    VALID_EFFECT_CATEGORIES = [
        "career",
        "wealth",
        "marriage",
        "health",
        "education",
        "children",
        "character",
        "physical_appearance",
        "spiritual",
        "social_status",
        "family",
        "enemies",
        "losses",
        "gains",
        "fortune",
        "longevity",
    ]

    def __init__(self, normaliser: AstrologyNormaliser | None = None) -> None:
        self.normaliser = normaliser or AstrologyNormaliser()
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate_rule(self, rule: dict[str, Any]) -> dict[str, Any]:
        """Validate a single extracted rule against schema v2.0."""
        errors: list[str] = []
        warnings: list[str] = []

        if rule.get("schema_version") != "2.0":
            warnings.append('Missing or incorrect schema_version (expected "2.0")')

        required = ["rule_id", "type", "source_text", "conditions", "effects", "metadata"]
        for field in required:
            if field not in rule or rule[field] is None:
                errors.append(f"Missing required field: {field}")

        if rule.get("type") not in self.VALID_TYPES:
            errors.append(
                f'Invalid rule type: {rule.get("type")} (must be one of {self.VALID_TYPES})'
            )

        if rule.get("conditions"):
            errors.extend(self._validate_conditions(rule["conditions"]))

        if rule.get("effects"):
            errors.extend(self._validate_effects(rule["effects"]))

        if rule.get("metadata"):
            errors.extend(self._validate_metadata(rule["metadata"]))

        normalised_entities: dict[str, str] = {}
        if isinstance(rule.get("conditions"), dict):
            for clause in rule["conditions"].get("clauses", []):
                if not isinstance(clause, dict):
                    continue
                for key in ("planet", "sign", "house"):
                    raw_term = clause.get(key)
                    if not raw_term:
                        continue
                    canonical = self.normaliser.normalise(str(raw_term))
                    if canonical is None:
                        warnings.append(f'Unknown entity in condition: "{raw_term}" - needs review')
                    else:
                        normalised_entities[str(raw_term)] = canonical

        tags = rule.get("tags", [])
        if isinstance(tags, list):
            for tag in tags:
                if not isinstance(tag, str):
                    continue
                canonical = self.normaliser.normalise(tag)
                if canonical and tag.casefold() != canonical.casefold():
                    normalised_entities[tag] = canonical

        status = "invalid" if errors else ("warning" if warnings else "valid")
        return {
            **rule,
            "normalised_entities": normalised_entities,
            "validation_errors": errors,
            "validation_warnings": warnings,
            "validation_status": status,
        }

    def _validate_conditions(self, conditions: dict[str, Any]) -> list[str]:
        """Validate the `conditions` structure."""
        errors: list[str] = []
        if "operator" not in conditions:
            errors.append("conditions.operator is required")
        elif conditions["operator"] not in self.VALID_OPERATORS:
            errors.append(
                f'Invalid operator: {conditions["operator"]} (must be AND or OR)'
            )

        if "clauses" not in conditions:
            errors.append("conditions.clauses is required")
        elif not isinstance(conditions["clauses"], list):
            errors.append("conditions.clauses must be an array")
        else:
            for index, clause in enumerate(conditions["clauses"]):
                if not isinstance(clause, dict):
                    errors.append(f"Clause {index}: must be an object")
                    continue
                errors.extend(self._validate_clause(clause, index))
        return errors

    def _validate_clause(self, clause: dict[str, Any], index: int) -> list[str]:
        """Validate one condition clause."""
        errors: list[str] = []
        if "type" not in clause:
            errors.append(f'Clause {index}: missing required field "type"')
        elif clause["type"] not in self.VALID_CLAUSE_TYPES:
            errors.append(
                f'Clause {index}: invalid type "{clause["type"]}" '
                f"(must be one of {self.VALID_CLAUSE_TYPES})"
            )

        clause_type = clause.get("type")
        if clause_type == "planet_state" and "planet" not in clause:
            errors.append(f'Clause {index}: planet_state requires "planet" field')
        if clause_type == "aspect" and "aspect_type" not in clause:
            errors.append(f'Clause {index}: aspect requires "aspect_type" field')
        return errors

    def _validate_effects(self, effects: list[Any]) -> list[str]:
        """Validate the `effects` array."""
        errors: list[str] = []
        if not isinstance(effects, list):
            return ["effects must be an array"]

        for index, effect in enumerate(effects):
            if not isinstance(effect, dict):
                errors.append(f"Effect {index}: must be an object")
                continue
            for field in ["category", "description", "impact", "intensity", "probability"]:
                if field not in effect:
                    errors.append(f'Effect {index}: missing required field "{field}"')

            if "category" in effect and effect["category"] not in self.VALID_EFFECT_CATEGORIES:
                errors.append(
                    f'Effect {index}: unknown category "{effect["category"]}" '
                    "(consider adding to VALID_EFFECT_CATEGORIES)"
                )
            if "impact" in effect and effect["impact"] not in self.VALID_IMPACTS:
                errors.append(
                    f'Effect {index}: invalid impact "{effect["impact"]}" '
                    f"(must be one of {self.VALID_IMPACTS})"
                )
            if "intensity" in effect and effect["intensity"] not in self.VALID_INTENSITIES:
                errors.append(
                    f'Effect {index}: invalid intensity "{effect["intensity"]}" '
                    f"(must be one of {self.VALID_INTENSITIES})"
                )
            if "probability" in effect and effect["probability"] not in self.VALID_PROBABILITIES:
                errors.append(
                    f'Effect {index}: invalid probability "{effect["probability"]}" '
                    f"(must be one of {self.VALID_PROBABILITIES})"
                )
        return errors

    def _validate_metadata(self, metadata: dict[str, Any]) -> list[str]:
        """Validate the `metadata` block."""
        errors: list[str] = []
        if not isinstance(metadata, dict):
            return ["metadata must be an object"]

        if not metadata.get("source_book"):
            errors.append("metadata.source_book is required")

        if "confidence" in metadata:
            confidence = metadata["confidence"]
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                errors.append(
                    f"metadata.confidence must be a number between 0 and 1 (got {confidence})"
                )
        return errors

    def validate_batch(self, rules: list[dict[str, Any]]) -> dict[str, Any]:
        """Validate a list of rules and return categorised results plus summary stats."""
        results: dict[str, list[dict[str, Any]]] = {"valid": [], "warning": [], "invalid": []}
        for rule in rules:
            validated = self.validate_rule(rule)
            results[validated["validation_status"]].append(validated)

        total = len(rules)
        summary = {
            "total": total,
            "valid": len(results["valid"]),
            "warning": len(results["warning"]),
            "invalid": len(results["invalid"]),
            "valid_pct": round(len(results["valid"]) / total * 100, 1) if total > 0 else 0,
        }
        print(f'Validation complete: {summary["valid_pct"]}% valid')
        print(f'  Valid: {summary["valid"]}')
        print(f'  Warning: {summary["warning"]}')
        print(f'  Invalid: {summary["invalid"]}')
        return {"results": results, "summary": summary}
