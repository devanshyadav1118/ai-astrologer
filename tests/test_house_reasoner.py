"""Phase 5 house reasoner coverage."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reasoning.house_reasoner import HouseReasoner


class StubChartQueries:
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

    def get_planet_placement(self, chart_id: str, planet: str) -> dict[str, Any] | None:
        assert chart_id == "chart_1"
        assert planet == "SATURN"
        return {
            "house": 3,
            "sign": "GEMINI",
            "degree": 15.23,
            "nakshatra": "ARDRA",
            "pada": 2,
            "dignity": "neutral",
        }

    def get_aspects_to_planet(self, chart_id: str, planet: str) -> list[dict[str, Any]]:
        assert chart_id == "chart_1"
        assert planet == "SATURN"
        return [{"from_planet": "JUPITER", "type": "OPPOSITION", "strength": 1.0}]

    def get_conjunctions(self, chart_id: str, planet: str) -> list[dict[str, Any]]:
        assert chart_id == "chart_1"
        assert planet == "SATURN"
        return [{"planet": "MERCURY", "orb": 3.5, "same_nakshatra": True}]

    def get_planets_in_house(self, chart_id: str, house: int) -> list[str]:
        assert chart_id == "chart_1"
        assert house == 10
        return ["MARS", "SATURN"]

    def get_dispositor_chain(self, chart_id: str, planet: str) -> list[dict[str, Any]]:
        assert chart_id == "chart_1"
        assert planet == "SATURN"
        return [{"planet": "MERCURY", "depth": 1}, {"planet": "MERCURY", "depth": 2}]


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
        if "MATCH (r:Rule)-[:REFERS_TO]->(:House {name: $house_name})" in query:
            assert params["house_name"] == "HOUSE_10"
            assert params["lord"] == "SATURN"
            return FakeResult(self.records)
        if "MATCH (r)-[:REFERS_TO]->(:House {name: $placement_house_name})" in query:
            assert params["placement_house_name"] == "HOUSE_3"
            assert params["lord"] == "SATURN"
            return FakeResult(
                [
                    {
                        "rule_id": "r_analog",
                        "effect_summary": "career through effort",
                        "source_text": "Saturn in the 3rd drives effortful work.",
                        "confidence": 3,
                    }
                ]
            )
        raise AssertionError(f"Unexpected query: {query}")


class FakeDriver:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self.records = records

    def session(self) -> FakeSession:
        return FakeSession(self.records)


class FakeNeo4jClient:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self.driver = FakeDriver(records)


def build_reasoner() -> HouseReasoner:
    neo4j_client = FakeNeo4jClient(
        [
            {
                "rule_id": "r1",
                "effect_summary": "career success",
                "source_text": "Saturn influencing the 10th supports career through discipline.",
                "confidence": 4,
            }
        ]
    )
    return HouseReasoner(
        chart_queries=StubChartQueries(),  # type: ignore[arg-type]
        neo4j_client=neo4j_client,  # type: ignore[arg-type]
        ontology_dir=Path("normaliser/ontology"),
    )


def test_house_reasoner_atomic_queries_delegate_to_chart_queries() -> None:
    reasoner = build_reasoner()

    assert reasoner.get_house_lord("chart_1", 10)["lord"] == "SATURN"
    assert reasoner.get_placement_of("chart_1", "SATURN")["house"] == 3
    assert reasoner.get_aspects_to("chart_1", "SATURN")[0]["from_planet"] == "JUPITER"
    assert reasoner.get_conjunctions("chart_1", "SATURN")[0]["planet"] == "MERCURY"
    assert reasoner.get_dispositor_chain("chart_1", "SATURN")[0]["planet"] == "MERCURY"


def test_analyze_house_returns_structured_reasoning_output() -> None:
    reasoner = build_reasoner()

    analysis = reasoner.analyze_house("chart_1", 10)

    assert analysis is not None
    assert analysis["house"] == 10
    assert analysis["theme"] == "Career"
    assert analysis["lord"] == "SATURN"
    assert analysis["lord_placement"] == "House 3"
    assert analysis["supporting_rules"][0]["rule_id"] == "r1"
    assert analysis["analogous_rules"][0]["rule_id"] == "r_analog"
    assert analysis["occupied_by"] == ["MARS"]
    assert analysis["novel_synthesis"]["summary"]
    assert analysis["facts"]
    assert analysis["confidence"] > 0.0
    assert analysis["rank_score"] > 0.0
    assert analysis["reasoning_tree"]["children"]
    assert any("JUPITER" in step for step in analysis["reasoning_chain"])
