"""Phase 4 Neo4j chart ingestion coverage."""

from __future__ import annotations

from typing import Any

from storage.chart_ingestor import ChartGraphIngestor


class FakeSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    def run(self, query: str, **params: Any) -> None:
        self.calls.append((query, params))


class FakeDriver:
    def __init__(self) -> None:
        self.session_instance = FakeSession()

    def session(self) -> FakeSession:
        return self.session_instance


class FakeNeo4jClient:
    def __init__(self) -> None:
        self.driver = FakeDriver()


def test_ingest_chart_creates_chart_nodes_and_relationships() -> None:
    client = FakeNeo4jClient()
    ingestor = ChartGraphIngestor(client)  # type: ignore[arg-type]
    chart_data = {
        "metadata": {
            "date": "1990-05-15",
            "time": "14:30:00",
            "latitude": 26.9124,
            "longitude": 75.7873,
            "timezone": 5.5,
        },
        "houses": [
            {"number": 1, "house": "HOUSE_1", "sign": "ARIES", "degree": 0.0, "lord": "MARS"},
        ],
        "planets": [
            {
                "name": "MARS",
                "sign": "ARIES",
                "degree": 10.0,
                "longitude": 10.0,
                "house": 1,
                "nakshatra": "ASHWINI",
                "nakshatra_pada": 1,
                "sublord": "KETU",
                "retrograde": False,
                "combustion": False,
                "dignity": {"status": "own_sign", "strength_modifier": 4.0},
            },
        ],
        "aspects": [
            {
                "from_planet": "MARS",
                "to_planet": "MARS",
                "house_offset": 7,
                "strength": 1.0,
                "type": "OPPOSITION",
            },
        ],
        "house_aspects": [
            {
                "from_planet": "MARS",
                "to_house": 7,
                "house_offset": 7,
                "strength": 1.0,
                "type": "OPPOSITION",
            }
        ],
        "conjunctions": [
            {
                "planet_1": "MARS",
                "planet_2": "MARS",
                "orb": 0.0,
                "same_nakshatra": True,
            }
        ],
        "dispositors": [
            {
                "planet": "MARS",
                "dispositor": "MARS",
                "same_planet": True,
            }
        ],
    }

    result = ingestor.ingest_chart("chart_123", chart_data)

    assert result == "chart_123"
    queries = "\n".join(query for query, _ in client.driver.session_instance.calls)
    assert "MERGE (c:Chart {chart_id: $chart_id})" in queries
    assert "MERGE (ch:ChartHouse {id: $id})" in queries
    assert "MERGE (cp:ChartPlanet {id: $id})" in queries
    assert "MERGE (ch)-[:RULED_BY]->(cp)" in queries
    assert "MERGE (cp1)-[a:ASPECTS {type: $aspect_type}]->(cp2)" in queries
    assert "MATCH (cp:ChartPlanet {id: $from_id})" in queries
    assert "MERGE (cp1)-[c:CONJOINS]->(cp2)" in queries
    assert "MERGE (cp1)-[d:DISPOSED_BY]->(cp2)" in queries
