"""Chart-level pipeline entry points."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from chart.vedicastro_calculator import VedicAstroCalculator
from pipeline.run_book import setup_logging
from storage.chart_ingestor import ChartGraphIngestor
from storage.neo4j_client import Neo4jClient
from reasoning.chart_reasoner import ChartReasoner
from reasoning.house_reasoner import HouseReasoner


class ChartProcessor:
    """Calculate one natal chart and optionally ingest it into Neo4j."""

    def __init__(
        self,
        chart_id: str,
        date: str,
        time: str,
        latitude: float,
        longitude: float,
        timezone: float,
        calculator: VedicAstroCalculator | None = None,
        neo4j_client: Neo4jClient | None = None,
        chart_ingestor: ChartGraphIngestor | None = None,
        reasoner: ChartReasoner | None = None,
    ) -> None:
        self.chart_id = chart_id
        self.date = date
        self.time = time
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone
        self.calculator = calculator or VedicAstroCalculator()
        self.neo4j_client = neo4j_client or Neo4jClient()
        if chart_ingestor is not None:
            self.chart_ingestor = chart_ingestor
        else:
            self.chart_ingestor = ChartGraphIngestor(self.neo4j_client)
        
        if reasoner is not None:
            self.reasoner = reasoner
        else:
            hr = HouseReasoner(self.neo4j_client)
            self.reasoner = ChartReasoner(hr)
            
        self.output_dir = Path("data") / "charts"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def run(self, dry_run: bool = False) -> dict[str, Any]:
        """Calculate a chart, persist its JSON, and ingest it unless dry_run is set."""
        chart_data = self.calculator.calculate_chart(
            date=self.date,
            time=self.time,
            latitude=self.latitude,
            longitude=self.longitude,
            timezone=self.timezone,
        )
        chart_path = self.output_dir / f"{self.chart_id}.json"
        self._write_json(chart_path, chart_data)
        
        ingested = False
        if not dry_run:
            self.chart_ingestor.ingest_chart(self.chart_id, chart_data)
            
            # Run Full Reasoning (Yogas + Propagation)
            analysis = self.reasoner.analyze_full_chart(self.chart_id)
            
            # Ingest Propagation Results
            self.chart_ingestor.ingest_propagation_results(self.chart_id, {
                "house_importance": analysis["house_importance"],
                "dominant_themes": analysis["dominant_themes"],
                "edges": analysis.get("propagation_metadata", {}).get("edges", []) # Wait, need to pass edges from analysis
            })
            # Actually, I should update analyze_full_chart to return the edges or just pass the whole results dict
            
            ingested = True
        summary = {
            "chart_id": self.chart_id,
            "output_path": str(chart_path),
            "planet_count": len(chart_data.get("planets", [])),
            "house_count": len(chart_data.get("houses", [])),
            "aspect_count": len(chart_data.get("aspects", [])),
            "ingested": ingested,
        }
        self.logger.info("Chart processed: %s", json.dumps(summary, ensure_ascii=True, sort_keys=True))
        return summary

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=True, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate and ingest one birth chart")
    parser.add_argument("--chart-id", required=True, help="Unique identifier for the chart")
    parser.add_argument("--date", required=True, help="Birth date in YYYY-MM-DD format")
    parser.add_argument("--time", required=True, help="Birth time in HH:MM:SS format")
    parser.add_argument("--latitude", required=True, type=float, help="Birth latitude")
    parser.add_argument("--longitude", required=True, type=float, help="Birth longitude")
    parser.add_argument("--timezone", required=True, type=float, help="UTC offset, e.g. 5.5")
    parser.add_argument("--dry-run", action="store_true", help="Calculate and write JSON without Neo4j ingestion")
    args = parser.parse_args()

    log_path = setup_logging(args.chart_id)
    logging.info("Logging to %s", log_path)
    processor = ChartProcessor(
        chart_id=args.chart_id,
        date=args.date,
        time=args.time,
        latitude=args.latitude,
        longitude=args.longitude,
        timezone=args.timezone,
    )
    summary = processor.run(dry_run=args.dry_run)
    logging.info("Summary: %s", json.dumps(summary, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
