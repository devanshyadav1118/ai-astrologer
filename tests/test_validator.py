"""Phase 1 validator coverage."""

from __future__ import annotations

from normaliser.validator import RuleValidator


def test_validate_rule_marks_valid_rule() -> None:
    validator = RuleValidator()
    rule = {
        "schema_version": "2.0",
        "rule_id": "R-1",
        "type": "prediction",
        "source_text": "Guru in Mesha aspecting Lagna grants wisdom.",
        "condition_text": "If Guru is in Mesha and aspects Lagna",
        "conditions": {
            "operator": "AND",
            "clauses": [
                {"raw_text": "Guru in Mesha", "type": "planet_state", "planet": "Guru", "sign": "Mesha"},
                {"raw_text": "aspects Lagna", "type": "aspect", "planet": "Guru", "house": "Lagna", "aspect_type": "full_aspect"},
            ],
        },
        "effects": [
            {
                "category": "wealth",
                "description": "native gains wisdom",
                "impact": "positive",
                "intensity": "medium",
                "probability": "likely",
            }
        ],
        "metadata": {"source_book": "Brihat Parashara Hora Shastra", "confidence": 0.5},
        "source_text": "Guru in Mesha aspecting Lagna grants wisdom.",
    }
    validated = validator.validate_rule(rule)
    assert validated["validation_status"] == "valid"
    assert validated["normalised_entities"]["Guru"] == "JUPITER"
    assert validated["normalised_entities"]["Mesha"] == "ARIES"
    assert validated["normalised_entities"]["Lagna"] == "HOUSE_1"


def test_validate_rule_marks_invalid_missing_fields() -> None:
    validator = RuleValidator()
    validated = validator.validate_rule({"rule_id": "R-2", "type": "prediction", "schema_version": "2.0"})
    assert validated["validation_status"] == "invalid"
    assert len(validated["validation_errors"]) >= 1


def test_validate_rule_warns_on_unknown_type() -> None:
    validator = RuleValidator()
    rule = {
        "schema_version": "2.0",
        "rule_id": "R-3",
        "type": "mystery",
        "conditions": {
            "operator": "AND",
            "clauses": [{"raw_text": "Surya in Lagna", "type": "planet_state", "planet": "Surya", "house": "Lagna"}],
        },
        "effects": [
            {
                "category": "character",
                "description": "strong self",
                "impact": "positive",
                "intensity": "medium",
                "probability": "likely",
            }
        ],
        "metadata": {"source_book": "Test Book"},
        "source_text": "Surya in Lagna gives strength.",
    }
    validated = validator.validate_rule(rule)
    assert validated["validation_status"] == "invalid"
    assert validated["normalised_entities"]["Surya"] == "SUN"


def test_validate_batch_summary_counts() -> None:
    validator = RuleValidator()
    batch = [
        {
            "schema_version": "2.0",
            "rule_id": "R-1",
            "type": "prediction",
            "conditions": {
                "operator": "AND",
                "clauses": [{"raw_text": "Surya in Lagna", "type": "planet_state", "planet": "Surya", "house": "Lagna"}],
            },
            "effects": [
                {
                    "category": "character",
                    "description": "strong self",
                    "impact": "positive",
                    "intensity": "medium",
                    "probability": "likely",
                }
            ],
            "metadata": {"source_book": "Test Book"},
            "source_text": "Surya in Lagna gives strength.",
        },
        {"rule_id": "R-2", "type": "prediction", "schema_version": "2.0"},
    ]
    summary = validator.validate_batch(batch)["summary"]
    assert summary["total"] == 2
    assert summary["valid"] == 1
    assert summary["invalid"] == 1


def test_validate_rule_warns_on_unknown_entity() -> None:
    validator = RuleValidator()
    rule = {
        "schema_version": "2.0",
        "rule_id": "R-4",
        "type": "prediction",
        "conditions": {
            "operator": "AND",
            "clauses": [
                {"raw_text": "Guru", "type": "planet_state", "planet": "Guru"},
                {"raw_text": "FooBar in Mesha", "type": "other", "sign": "Mesha", "planet": "FooBar"},
            ],
        },
        "effects": [
            {
                "category": "fortune",
                "description": "mixed results",
                "impact": "neutral",
                "intensity": "low",
                "probability": "possible",
            }
        ],
        "metadata": {"source_book": "Test Book"},
        "source_text": "Guru joins FooBar in Mesha.",
    }
    validated = validator.validate_rule(rule)
    assert validated["validation_status"] == "warning"
    assert validated["normalised_entities"]["Guru"] == "JUPITER"
    assert validated["normalised_entities"]["Mesha"] == "ARIES"
    assert any("foobar" in warning.casefold() for warning in validated["validation_warnings"])


def test_validate_rule_rejects_bad_effect_enum() -> None:
    validator = RuleValidator()
    rule = {
        "schema_version": "2.0",
        "rule_id": "R-5",
        "type": "prediction",
        "conditions": {"operator": "AND", "clauses": [{"type": "planet_state", "planet": "Guru"}]},
        "effects": [
            {
                "category": "wealth",
                "description": "gain",
                "impact": "Positive",
                "intensity": "medium",
                "probability": "likely",
            }
        ],
        "metadata": {"source_book": "Test Book"},
        "source_text": "Guru gives gain.",
    }
    validated = validator.validate_rule(rule)
    assert validated["validation_status"] == "invalid"
    assert any("invalid impact" in error.casefold() for error in validated["validation_errors"])


def test_validate_rule_normalises_external_alias_enums() -> None:
    validator = RuleValidator()
    rule = {
        "id": "R-6",
        "original_text": "If Saturn is in the 7th house, there is delay.",
        "conditions": {
            "logic_block": {
                "operator": "AND",
                "clauses": [{"type": "placement", "planet": "Saturn", "house": 7}],
            }
        },
        "effects": [
            {
                "category": "status",
                "description": "delay",
                "impact": "Negative",
                "intensity": "High",
                "probability": "Likely",
            }
        ],
        "metadata": {"source": "Test Book"},
    }
    validated = validator.validate_rule(rule)

    assert validated["validation_status"] == "valid"
    assert validated["conditions"]["clauses"][0]["house"] == "HOUSE_7"
    assert validated["effects"][0]["category"] == "social_status"
