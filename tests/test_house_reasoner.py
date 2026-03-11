"""Phase 5 house reasoner coverage."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reasoning.house_reasoner import HouseReasoner


class StubChartQueries:
    def traverse_house_chain(self, chart_id: str, house: int) -> dict[str, Any] | None:
        assert chart_id == "chart_1"
        assert house == 10
        return {
            "house_sign": "AQUARIUS",
            "lord_name": "SATURN",
            "lord_dignity": "neutral",
            "lord_placement": 3,
            "planet_meanings": ["discipline", "structure"],
            "house_meanings": ["communication", "skills"],
            "aspects": ["JUPITER"],
        }

    def get_house_lord(self, chart_id: str, house: int) -> dict[str, Any] | None:
        assert chart_id == "chart_1"
        assert house == 10
        return {
            "lord": "SATURN",
            "lord_house": 3,
            "lord_sign": "GEMINI",
            "lord_dignity": "neutral",
            "lord_strength": 2.0,
        }


class FakeResult:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self.records = records

    def __iter__(self) -> Any:
        return iter(self.records)


class FakeSession:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self.records = records

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    def run(self, query: str, **params: Any) -> FakeResult:
        assert "MATCH (r:Rule)-[:REFERS_TO]->(:House {name: $house_name})" in query
        assert params["house_name"] == "HOUSE_10"
        assert params["lord"] == "SATURN"
        return FakeResult(self.records)


class FakeDriver:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self.records = records

    def session(self) -> FakeSession:
        return FakeSession(self.records)


class FakeNeo4jClient:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self.driver = FakeDriver(records)


def test_analyze_house_returns_reasoning_summary() -> None:
    neo4j_client = FakeNeo4jClient(
        [
            {
                "rule_id": "r1",
                "effect_summary": "career success",
                "source_text": "Saturn influencing the 10th supports career through discipline.",
                "confidence": 2,
            }
        ]
    )
    reasoner = HouseReasoner(
        chart_queries=StubChartQueries(),  # type: ignore[arg-type]
        neo4j_client=neo4j_client,  # type: ignore[arg-type]
        ontology_dir=Path("normaliser/ontology"),
    )

    analysis = reasoner.analyze_house("chart_1", 10)

    assert analysis is not None
    assert analysis["house"] == 10
    assert analysis["theme"] == "Career"
    assert analysis["lord"] == "SATURN"
    assert analysis["lord_placement"] == "House 3"
    assert analysis["supporting_rules"][0]["rule_id"] == "r1"
    assert any("JUPITER" in step for step in analysis["reasoning_chain"])
