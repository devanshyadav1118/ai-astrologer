"""Phase 4 chart query coverage."""

from __future__ import annotations

from typing import Any

from storage.chart_queries import ChartQueries


class FakeResult:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self.records = records

    def single(self) -> dict[str, Any] | None:
        return self.records[0] if self.records else None

    def __iter__(self) -> Any:
        return iter(self.records)


class FakeSession:
    def __init__(self, responses: list[list[dict[str, Any]]]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    def run(self, query: str, **params: Any) -> FakeResult:
        self.calls.append((query, params))
        return FakeResult(self.responses.pop(0))


class FakeDriver:
    def __init__(self, session: FakeSession) -> None:
        self._session = session

    def session(self) -> FakeSession:
        return self._session


class FakeNeo4jClient:
    def __init__(self, responses: list[list[dict[str, Any]]]) -> None:
        self.session = FakeSession(responses)
        self.driver = FakeDriver(self.session)


def test_chart_queries_return_expected_shapes() -> None:
    client = FakeNeo4jClient(
        responses=[
            [{"lord": "SATURN", "lord_house": 3, "lord_sign": "GEMINI", "lord_dignity": "neutral", "lord_strength": 2.0}],
            [{"house": 10, "sign": "CAPRICORN", "degree": 15.23, "nakshatra": "SHRAVANA", "pada": 2, "dignity": "exalted"}],
            [{"from_planet": "JUPITER", "type": "OPPOSITION", "strength": 1.0}],
            [{"planet": "MARS"}, {"planet": "MERCURY"}],
            [{"planet": "MERCURY", "orb": 3.5, "same_nakshatra": True}],
            [{"house_sign": "AQUARIUS", "lord_name": "SATURN", "lord_dignity": "neutral", "lord_placement": 3, "planet_meanings": ["discipline"], "house_meanings": ["communication"], "aspects": ["JUPITER"]}],
            [{"planets": ["MARS", "MERCURY", "MERCURY"]}],
        ]
    )
    queries = ChartQueries(client)  # type: ignore[arg-type]

    assert queries.get_house_lord("chart", 10)["lord"] == "SATURN"
    assert queries.get_planet_placement("chart", "MARS")["sign"] == "CAPRICORN"
    assert queries.get_aspects_to_planet("chart", "MARS")[0]["from_planet"] == "JUPITER"
    assert queries.get_planets_in_house("chart", 1) == ["MARS", "MERCURY"]
    assert queries.get_conjunctions("chart", "MARS")[0]["same_nakshatra"] is True
    assert queries.traverse_house_chain("chart", 10)["lord_name"] == "SATURN"
    assert queries.get_dispositor_chain("chart", "MARS")[-1]["planet"] == "MERCURY"
