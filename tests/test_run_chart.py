"""Phase 4 chart processor coverage."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.run_chart import ChartProcessor


class StubCalculator:
    def calculate_chart(
        self,
        date: str,
        time: str,
        latitude: float,
        longitude: float,
        timezone: float,
    ) -> dict[str, object]:
        return {
            "metadata": {
                "date": date,
                "time": time,
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone,
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
                    "sublord": None,
                    "retrograde": False,
                    "combustion": False,
                    "dignity": {"status": "own_sign", "strength_modifier": 4.0},
                }
            ],
            "aspects": [],
        }


class StubIngestor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def ingest_chart(self, chart_id: str, chart_data: dict[str, object]) -> str:
        self.calls.append((chart_id, chart_data))
        return chart_id


def test_chart_processor_runs_end_to_end(tmp_path: Path) -> None:
    ingestor = StubIngestor()
    processor = ChartProcessor(
        chart_id="john_doe",
        date="1990-05-15",
        time="14:30:00",
        latitude=26.9124,
        longitude=75.7873,
        timezone=5.5,
        calculator=StubCalculator(),  # type: ignore[arg-type]
        neo4j_client=None,
        chart_ingestor=ingestor,  # type: ignore[arg-type]
    )
    processor.output_dir = tmp_path

    summary = processor.run()

    assert summary["chart_id"] == "john_doe"
    assert summary["ingested"] is True
    assert ingestor.calls
    payload = json.loads((tmp_path / "john_doe.json").read_text(encoding="utf-8"))
    assert payload["planets"][0]["name"] == "MARS"


def test_chart_processor_dry_run_skips_ingestion(tmp_path: Path) -> None:
    ingestor = StubIngestor()
    processor = ChartProcessor(
        chart_id="dry_chart",
        date="1990-05-15",
        time="14:30:00",
        latitude=26.9124,
        longitude=75.7873,
        timezone=5.5,
        calculator=StubCalculator(),  # type: ignore[arg-type]
        neo4j_client=None,
        chart_ingestor=ingestor,  # type: ignore[arg-type]
    )
    processor.output_dir = tmp_path

    summary = processor.run(dry_run=True)

    assert summary["ingested"] is False
    assert ingestor.calls == []
    assert (tmp_path / "dry_chart.json").exists()
