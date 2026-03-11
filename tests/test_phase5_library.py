"""Phase 5 validation library coverage."""

from __future__ import annotations

from pathlib import Path

from reasoning.validation import Phase5Validator


def test_phase5_validator_evaluates_test_chart_library() -> None:
    validator = Phase5Validator()

    report = validator.evaluate_library(
        Path("reasoning/test_chart_library.json"),
        analysis_provider=lambda case: {
            "chart_id": case["chart_id"],
            "house_analyses": [
                {
                    "house": 1,
                    "facts": [{"id": "f1"}],
                    "supporting_rules": [{"rule_id": case.get("expected_rule_ids", ["R"])[0]}]
                    if case.get("expected_rule_ids")
                    else [],
                    "contradictions": ["x"] if case.get("expected_contradiction_houses") else [],
                    "reasoning_tree": {
                        "children": [{"statement": "child"}],
                        "supporting_facts": [{"fact": "x", "source": "house_lord"}],
                        "novel_synthesis": not bool(case.get("expected_rule_ids")),
                    },
                }
            ],
            "ranked_interpretations": [{"house": 1}],
        },
    )

    assert report["case_count"] == 20
    assert report["reports"]
    assert "aggregate_metrics" in report
