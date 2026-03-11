"""CLI for the first Phase 5 house reasoning slice."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from reasoning.house_reasoner import HouseReasoner
from storage.chart_queries import ChartQueries
from storage.neo4j_client import Neo4jClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze one house using the Phase 5 reasoning chain")
    parser.add_argument("--chart-id", required=True, help="Chart identifier")
    parser.add_argument("--house", required=True, type=int, choices=range(1, 13), help="House number")
    args = parser.parse_args()

    neo4j_client = Neo4jClient()
    reasoner = HouseReasoner(ChartQueries(neo4j_client), neo4j_client)
    print(json.dumps(reasoner.analyze_house(args.chart_id, args.house), ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
