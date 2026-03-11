"""Phase 4 batch chart processor coverage."""

from __future__ import annotations

from pathlib import Path

import pipeline.run_chart_batch as run_chart_batch


class StubChartProcessor:
    def __init__(
        self,
        chart_id: str,
        date: str,
        time: str,
        latitude: float,
        longitude: float,
        timezone: float,
    ) -> None:
        self.chart_id = chart_id

    def run(self, dry_run: bool = False) -> dict[str, object]:
        return {"chart_id": self.chart_id, "ingested": not dry_run}


def test_process_csv_runs_all_rows(monkeypatch: object, tmp_path: Path) -> None:
    csv_path = tmp_path / "charts.csv"
    csv_path.write_text(
        "chart_id,date,time,latitude,longitude,timezone\n"
        "c1,1990-05-15,14:30:00,26.9124,75.7873,5.5\n"
        "c2,1992-01-01,06:15:00,28.6139,77.2090,5.5\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(run_chart_batch, "ChartProcessor", StubChartProcessor)

    results = run_chart_batch.process_csv(csv_path, dry_run=True)

    assert results == [
        {"chart_id": "c1", "ingested": False},
        {"chart_id": "c2", "ingested": False},
    ]
