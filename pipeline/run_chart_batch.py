"""Batch chart processing from CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.run_chart import ChartProcessor
from chart.vedicastro_api_calculator import VedicAstroAPICalculator
from chart.vedicastro_calculator import VedicAstroCalculator


def process_csv(csv_path: str | Path, dry_run: bool = False, use_api: bool = False, api_url: str = "http://127.0.0.1:8088") -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    
    if use_api:
        calculator = VedicAstroAPICalculator(api_url=api_url)
    else:
        calculator = VedicAstroCalculator()
        
    with Path(csv_path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            processor = ChartProcessor(
                chart_id=str(row["chart_id"]),
                date=str(row["date"]),
                time=str(row["time"]),
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                timezone=float(row["timezone"]),
                calculator=calculator
            )
            results.append(processor.run(dry_run=dry_run))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch calculate and ingest charts from CSV")
    parser.add_argument("--csv", required=True, help="CSV with chart_id,date,time,latitude,longitude,timezone")
    parser.add_argument("--use-api", action="store_true", help="Use VedicAstro API for calculations")
    parser.add_argument("--api-url", default="http://127.0.0.1:8088", help="Base URL for the VedicAstro API")
    parser.add_argument("--dry-run", action="store_true", help="Calculate and write JSON without Neo4j ingestion")
    args = parser.parse_args()
    print(json.dumps(process_csv(args.csv, dry_run=args.dry_run, use_api=args.use_api, api_url=args.api_url), ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
