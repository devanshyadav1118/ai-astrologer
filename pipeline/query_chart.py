"""CLI access to Phase 4 chart queries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from storage.chart_queries import ChartQueries
from storage.neo4j_client import Neo4jClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Query a stored chart subgraph")
    parser.add_argument("--chart-id", required=True, help="Chart identifier")
    parser.add_argument("--house-lord", type=int, help="Get lord details for a house")
    parser.add_argument("--planet-placement", help="Get placement for a planet")
    parser.add_argument("--aspects-to", help="Get aspects to a planet")
    parser.add_argument("--planets-in-house", type=int, help="List planets in a house")
    parser.add_argument("--conjunctions", help="List conjunctions for a planet")
    parser.add_argument("--house-chain", type=int, help="Traverse one house reasoning chain")
    parser.add_argument("--dispositor-chain", help="Get dispositor chain for a planet")
    parser.add_argument("--max-depth", type=int, default=5, help="Max dispositor depth")
    args = parser.parse_args()

    queries = ChartQueries(Neo4jClient())
    result: Any
    if args.house_lord is not None:
        result = queries.get_house_lord(args.chart_id, args.house_lord)
    elif args.planet_placement:
        result = queries.get_planet_placement(args.chart_id, args.planet_placement)
    elif args.aspects_to:
        result = queries.get_aspects_to_planet(args.chart_id, args.aspects_to)
    elif args.planets_in_house is not None:
        result = queries.get_planets_in_house(args.chart_id, args.planets_in_house)
    elif args.conjunctions:
        result = queries.get_conjunctions(args.chart_id, args.conjunctions)
    elif args.house_chain is not None:
        result = queries.traverse_house_chain(args.chart_id, args.house_chain)
    elif args.dispositor_chain:
        result = queries.get_dispositor_chain(args.chart_id, args.dispositor_chain, args.max_depth)
    else:
        parser.error("choose one query flag")
        return
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
