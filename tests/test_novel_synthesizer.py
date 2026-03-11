"""Phase 5 novel synthesis coverage."""

from __future__ import annotations

from pathlib import Path

from reasoning.novel_synthesizer import NovelCombinationSynthesizer


def test_novel_synthesizer_builds_summary_and_confidence() -> None:
    synthesizer = NovelCombinationSynthesizer(ontology_dir=Path("normaliser/ontology"))

    result = synthesizer.synthesize_house(
        house_number=8,
        lord_name="MERCURY",
        placement_house=8,
        aspects=[{"from_planet": "JUPITER", "type": "OPPOSITION", "strength": 1.0}],
        conjunctions=[{"planet": "KETU", "orb": 2.0, "same_nakshatra": False}],
        occupied_by=["MERCURY"],
        analogous_rules=[],
    )

    assert result["summary"]
    assert result["confidence_band"] in {"medium", "low"}
    assert result["novel"] is True
