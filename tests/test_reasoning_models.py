"""Phase 5 reasoning model coverage."""

from __future__ import annotations

from reasoning.models import ReasoningFact, ReasoningNode, SupportingFact


def test_reasoning_models_to_dict_round_trip() -> None:
    node = ReasoningNode(
        statement="Career involves disciplined communication.",
        confidence=0.85,
        strength_score=7.2,
        supporting_facts=[SupportingFact(fact="Saturn rules the 10th", source="house_lord")],
        classical_rules_applied=[{"rule_id": "SAR_CH12_045"}],
        novel_synthesis=False,
        children=[
            ReasoningNode(
                statement="Saturn is in the 3rd house.",
                confidence=0.9,
                strength_score=1.0,
            )
        ],
    )
    fact = ReasoningFact(
        id="fact-1",
        type="lord_placement",
        source_step="lord_placement",
        entities_involved=["SATURN", "HOUSE_3"],
        content="Saturn is placed in House 3.",
        strength_weight=2.0,
        confidence=0.9,
    )

    payload = node.to_dict()
    fact_payload = fact.to_dict()

    assert payload["statement"] == "Career involves disciplined communication."
    assert payload["supporting_facts"][0]["source"] == "house_lord"
    assert payload["children"][0]["statement"] == "Saturn is in the 3rd house."
    assert fact_payload["entities_involved"] == ["SATURN", "HOUSE_3"]
