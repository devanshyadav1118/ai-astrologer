"""Phase 5 house analysis built on the Phase 4 chart graph."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from storage.chart_queries import ChartQueries
from storage.neo4j_client import Neo4jClient


class HouseReasoner:
    """Analyze one house through lordship, placement, aspects, and supporting rules."""

    def __init__(
        self,
        chart_queries: ChartQueries,
        neo4j_client: Neo4jClient,
        ontology_dir: str | Path = "normaliser/ontology",
    ) -> None:
        self.chart_queries = chart_queries
        self.neo4j_client = neo4j_client
        self.ontology_dir = Path(ontology_dir)
        self.houses_by_number = self._load_houses()
        self.concepts = self._load_concepts()

    def analyze_house(self, chart_id: str, house: int) -> dict[str, Any] | None:
        house_data = self.houses_by_number.get(house)
        chain = self.chart_queries.traverse_house_chain(chart_id, house)
        lord_data = self.chart_queries.get_house_lord(chart_id, house)
        if house_data is None or chain is None or lord_data is None:
            return None
        placement_house = int(chain["lord_placement"])
        placement_data = self.houses_by_number.get(placement_house, {})
        theme = self._theme_for_house(house, house_data)
        supporting_rules = self.find_supporting_rules(chart_id, house, str(chain["lord_name"]))
        reasoning_chain = [
            f"House {house} signifies {self._format_meanings(house_data.get('primary_meanings', []), limit=3)}.",
            f"The lord is {chain['lord_name']} in House {placement_house}.",
            f"The lord's dignity is {chain['lord_dignity']}.",
            f"House {placement_house} adds {self._format_meanings(placement_data.get('primary_meanings', []), limit=3)}.",
        ]
        aspects = [value for value in chain.get("aspects", []) if value]
        if aspects:
            reasoning_chain.append(f"Aspects to the lord: {', '.join(aspects)}.")
        synthesis = self._build_synthesis(
            house=house,
            theme=theme,
            lord=str(chain["lord_name"]),
            placement_house=placement_house,
            dignity=str(chain["lord_dignity"]),
            house_meanings=house_data.get("primary_meanings", []),
            placement_meanings=placement_data.get("primary_meanings", []),
            aspects=aspects,
        )
        return {
            "house": house,
            "theme": theme,
            "lord": chain["lord_name"],
            "lord_placement": f"House {placement_house}",
            "lord_dignity": chain["lord_dignity"],
            "synthesis": synthesis,
            "supporting_rules": supporting_rules,
            "reasoning_chain": reasoning_chain,
        }

    def find_supporting_rules(self, chart_id: str, house: int, lord: str, limit: int = 5) -> list[dict[str, Any]]:
        del chart_id
        house_name = f"HOUSE_{house}"
        with self.neo4j_client.driver.session() as session:
            result = session.run(
                """
                MATCH (r:Rule)-[:REFERS_TO]->(:House {name: $house_name})
                MATCH (r)-[:REFERS_TO]->(:Planet {name: $lord})
                RETURN r.rule_id AS rule_id,
                       r.effect_summary AS effect_summary,
                       r.source_text AS source_text,
                       r.confidence AS confidence
                ORDER BY r.confidence DESC, r.rule_id
                LIMIT $limit
                """,
                house_name=house_name,
                lord=lord,
                limit=limit,
            )
            return [dict(record) for record in result]

    def _load_houses(self) -> dict[int, dict[str, Any]]:
        with (self.ontology_dir / "houses.json").open(encoding="utf-8") as handle:
            payload = json.load(handle)
        return {
            int(item["number"]): item
            for item in payload["houses"]
            if isinstance(item, dict) and item.get("number") is not None
        }

    def _load_concepts(self) -> list[dict[str, Any]]:
        with (self.ontology_dir / "concepts.json").open(encoding="utf-8") as handle:
            payload = json.load(handle)
        return [item for item in payload["concepts"] if isinstance(item, dict)]

    def _theme_for_house(self, house: int, house_data: dict[str, Any]) -> str:
        for concept in self.concepts:
            if house in concept.get("primary_houses", []):
                return str(concept["canonical_name"]).replace("_", " ").title()
        return self._format_meanings(house_data.get("primary_meanings", []), limit=2).title()

    def _build_synthesis(
        self,
        house: int,
        theme: str,
        lord: str,
        placement_house: int,
        dignity: str,
        house_meanings: list[str],
        placement_meanings: list[str],
        aspects: list[str],
    ) -> str:
        theme_text = self._format_meanings(house_meanings, limit=2)
        placement_text = self._format_meanings(placement_meanings, limit=2)
        parts = [
            f"House {house} emphasizes {theme_text}.",
            f"{lord} channels that through House {placement_house} themes of {placement_text}.",
            f"The lord operates with {dignity} dignity.",
        ]
        if aspects:
            parts.append(f"Influence from {', '.join(aspects)} modifies the result.")
        return " ".join(parts)

    def _format_meanings(self, values: list[str], limit: int) -> str:
        cleaned = [str(value).replace("_", " ") for value in values[:limit]]
        return ", ".join(cleaned) if cleaned else "its core themes"
