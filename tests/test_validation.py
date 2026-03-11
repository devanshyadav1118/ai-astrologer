"""Phase 5 validation coverage."""

from __future__ import annotations

from reasoning.validation import Phase5Validator


def test_phase5_validator_computes_metrics() -> None:
    analysis = {
        "house_analyses": [
            {
                "house": 1,
                "facts": [{"id": "f1"}],
                "supporting_rules": [{"rule_id": "R1"}],
                "contradictions": [],
                "reasoning_tree": {
                    "children": [{"statement": "child"}],
                    "supporting_facts": [{"fact": "x", "source": "house_lord"}],
                    "novel_synthesis": False,
                },
            },
            {
                "house": 8,
                "facts": [{"id": "f2"}],
                "supporting_rules": [],
                "contradictions": ["weak lord"],
                "reasoning_tree": {
                    "children": [{"statement": "child"}],
                    "supporting_facts": [{"fact": "y", "source": "aspect_analysis"}],
                    "novel_synthesis": True,
                },
            },
        ],
        "ranked_interpretations": [{"house": 1}, {"house": 8}],
    }

    metrics = Phase5Validator().compute_metrics(
        analysis=analysis,
        expected_rule_ids={"R1", "R2"},
        expected_contradiction_houses={8},
        novel_review_scores=[True, False, True],
        elapsed_seconds=2.3456,
    )

    assert metrics["reasoning_chain_completeness"] == 1.0
    assert metrics["classical_rule_coverage"] == 0.5
    assert metrics["contradiction_handling"] == 1.0
    assert metrics["novel_synthesis_quality"] == 0.667
    assert metrics["response_time_seconds"] == 2.346
    assert metrics["ranked_output_count"] == 2.0
