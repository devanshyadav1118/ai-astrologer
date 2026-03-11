"""Phase 5 chart reasoner coverage."""

from __future__ import annotations

from pathlib import Path

from reasoning.chart_reasoner import ChartReasoner


class StubHouseReasoner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def analyze_house(self, chart_id: str, house: int) -> dict[str, object]:
        self.calls.append((chart_id, house))
        return {
            "house": house,
            "theme": "Career" if house == 10 else f"Theme {house}",
            "lord": "SATURN" if house in {10, 11} else "MARS",
            "lord_placement": f"House {(house % 12) + 1}",
            "synthesis": f"House {house} synthesis",
            "confidence": 0.8 if house == 10 else 0.6,
            "rank_score": float(20 - house),
        }


def test_analyze_full_chart_builds_rankings_and_theme_reports() -> None:
    reasoner = ChartReasoner(StubHouseReasoner(), ontology_dir=Path("normaliser/ontology"))  # type: ignore[arg-type]

    analysis = reasoner.analyze_full_chart("chart_1", focus_areas=["Career"])

    assert analysis["chart_id"] == "chart_1"
    assert analysis["focus_areas"] == ["career"]
    assert len(analysis["house_analyses"]) == 12
    assert len(analysis["ranked_interpretations"]) == 12
    assert analysis["ranked_interpretations"][0]["house"] == 10
    assert analysis["ranked_interpretations"][0]["focus_match"] is True
    assert "HOUSE_10" in analysis["dependency_map"]
    assert analysis["life_theme_reports"]
    assert analysis["dominant_patterns"]["strongest_planets"][0]["planet"] in {"MARS", "SATURN"}
    assert analysis["chart_fingerprint"]
