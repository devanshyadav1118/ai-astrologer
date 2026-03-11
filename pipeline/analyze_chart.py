"""CLI for full Phase 5 chart reasoning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from reasoning.chart_reasoner import ChartReasoner
from reasoning.house_reasoner import HouseReasoner
from storage.chart_queries import ChartQueries
from storage.neo4j_client import Neo4jClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a full chart using the Phase 5 reasoning engine")
    parser.add_argument("--chart-id", required=True, help="Chart identifier")
    parser.add_argument(
        "--focus-area",
        action="append",
        default=[],
        help="Optional theme to prioritize in ranking, for example Career or Wealth",
    )
    args = parser.parse_args()

    neo4j_client = Neo4jClient()
    house_reasoner = HouseReasoner(ChartQueries(neo4j_client), neo4j_client)
    chart_reasoner = ChartReasoner(house_reasoner)
    analysis = chart_reasoner.analyze_full_chart(args.chart_id, focus_areas=args.focus_area)
    print(json.dumps(analysis, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
