"""Phase 1 validator coverage."""

from __future__ import annotations

from normaliser.validator import RuleValidator


def test_validate_rule_marks_valid_rule() -> None:
    validator = RuleValidator()
    rule = {
        "rule_id": "R-1",
        "type": "prediction",
        "condition": "If Guru is in Mesha and aspects Lagna",
        "result": "native gains wisdom",
        "source_text": "Guru in Mesha aspecting Lagna grants wisdom.",
    }
    validated = validator.validate_rule(rule)
    assert validated["validation_status"] == "valid"
    assert validated["normalised_entities"]["guru"] == "JUPITER"
    assert validated["normalised_entities"]["mesha"] == "ARIES"
    assert validated["normalised_entities"]["lagna"] == "HOUSE_1"


def test_validate_rule_marks_invalid_missing_fields() -> None:
    validator = RuleValidator()
    validated = validator.validate_rule({"rule_id": "R-2", "type": "prediction"})
    assert validated["validation_status"] == "invalid"
    assert len(validated["validation_errors"]) >= 1


def test_validate_rule_warns_on_unknown_type() -> None:
    validator = RuleValidator()
    rule = {
        "rule_id": "R-3",
        "type": "mystery",
        "condition": "Surya in Lagna",
        "result": "strong self",
        "source_text": "Surya in Lagna gives strength.",
    }
    validated = validator.validate_rule(rule)
    assert validated["validation_status"] == "warning"
    assert validated["normalised_entities"]["surya"] == "SUN"


def test_validate_batch_summary_counts() -> None:
    validator = RuleValidator()
    batch = [
        {
            "rule_id": "R-1",
            "type": "prediction",
            "condition": "Surya in Lagna",
            "result": "strong self",
            "source_text": "Surya in Lagna gives strength.",
        },
        {"rule_id": "R-2", "type": "prediction"},
    ]
    summary = validator.validate_batch(batch)["summary"]
    assert summary["total"] == 2
    assert summary["valid"] == 1
    assert summary["invalid"] == 1
