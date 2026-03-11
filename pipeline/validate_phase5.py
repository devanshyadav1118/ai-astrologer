"""Run Phase 5 validation cases against stored charts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from reasoning.chart_reasoner import ChartReasoner
from reasoning.house_reasoner import HouseReasoner
from reasoning.validation import Phase5Validator
from storage.chart_queries import ChartQueries
from storage.neo4j_client import Neo4jClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Phase 5 reasoning against a chart test library")
    parser.add_argument(
        "--library",
        default="reasoning/test_chart_library.json",
        help="Path to the Phase 5 test-chart library JSON",
    )
    parser.add_argument(
        "--focus-area",
        action="append",
        default=[],
        help="Optional focus area to pass into full-chart analysis",
    )
    args = parser.parse_args()

    neo4j_client = Neo4jClient()
    chart_reasoner = ChartReasoner(HouseReasoner(ChartQueries(neo4j_client), neo4j_client))
    validator = Phase5Validator()
    report = validator.evaluate_library(
        args.library,
        analysis_provider=lambda case: chart_reasoner.analyze_full_chart(
            str(case["chart_id"]),
            focus_areas=list(args.focus_area),
        ),
    )
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
