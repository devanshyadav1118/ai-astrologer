"""Phase 9 Dasha Engine (Orchestration & Enrichment).

Calculates, enriches, and persists the Vimshottari Dasha timeline.
"""

from __future__ import annotations

import logging
from typing import Any

from reasoning.vedic_astro_adapter import VedicAstroAdapter
from storage.neo4j_client import Neo4jClient


class DashaEngine:
    """Orchestrates dasha calculation, enrichment with Phase 6/7 scores, and ingestion."""

    def __init__(
        self, 
        neo4j_client: Neo4jClient | None = None,
        adapter: VedicAstroAdapter | None = None
    ) -> None:
        self.neo4j = neo4j_client or Neo4jClient()
        self.adapter = adapter or VedicAstroAdapter()
        self.logger = logging.getLogger(__name__)

    def process_dashas(self, chart_id: str, birth_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Run the full dasha pipeline: Compute -> Enrich -> Ingest."""
        # 1. Get raw timeline from adapter
        periods = self.adapter.get_dasha_timeline(
            birth_date=birth_data["date"],
            birth_time=birth_data["time"],
            lat=birth_data["latitude"],
            lon=birth_data["longitude"],
            tz=birth_data["timezone"]
        )
        
        # 2. Enrich with Phase 6 (Strength) and Phase 7 (Yogas)
        enriched_periods = self._enrich_periods(chart_id, periods)
        
        # 3. Ingest into Neo4j
        self._ingest_periods(chart_id, enriched_periods)
        
        return enriched_periods

    def _enrich_periods(self, chart_id: str, periods: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Attach activation weights and yoga flags from Neo4j."""
        with self.neo4j.driver.session() as session:
            # Get planet strengths
            planet_res = session.run(
                "MATCH (:Chart {chart_id: $chart_id})-[:CONTAINS_PLANET]->(cp:ChartPlanet) "
                "RETURN cp.planet_name AS name, cp.strength_total AS strength",
                chart_id=chart_id
            )
            strengths = {r["name"]: r["strength"] for r in planet_res}
            
            # Get active yogas and their participants
            yoga_res = session.run(
                "MATCH (:Chart {chart_id: $chart_id})-[:HAS_YOGA]->(dy:DetectedYoga) "
                "RETURN dy.yoga_name AS name, dy.planets_involved AS planets",
                chart_id=chart_id
            )
            yogas = []
            for r in yoga_res:
                yogas.append({"name": r["name"], "planets": r["planets"]})

        # Attach to periods
        for p in periods:
            planet = p["planet"]
            # Activation weight (0-1)
            p["activation_weight"] = strengths.get(planet, 5.0) / 10.0
            
            # Find yogas where this planet participates
            p["yogas_activated"] = [y["name"] for y in yogas if planet in y["planets"]]
            
        return periods

    def _ingest_periods(self, chart_id: str, periods: list[dict[str, Any]]) -> None:
        """Store the enriched dasha chain in Neo4j."""
        with self.neo4j.driver.session() as session:
            # Clear old dashas for this chart to avoid duplicates on rerun
            session.run("MATCH (:Chart {chart_id: $chart_id})-[:HAS_DASHA]->(d:Dashaperiod) DETACH DELETE d", chart_id=chart_id)
            
            # Map to keep track of mahadasha node IDs for linking
            md_node_map = {}
            
            for p in periods:
                if p["dasha_type"] == "mahadasha":
                    res = session.run(
                        """
                        MATCH (c:Chart {chart_id: $chart_id})
                        CREATE (d:Dashaperiod {
                            id: $id,
                            dasha_type: 'mahadasha',
                            planet: $planet,
                            start_date: $start,
                            end_date: $end,
                            activation_weight: $weight,
                            yogas_activated: $yogas,
                            source: $source
                        })
                        MERGE (c)-[:HAS_DASHA]->(d)
                        WITH d
                        MATCH (p:Planet {name: $planet})
                        MERGE (d)-[:GOVERNED_BY]->(p)
                        RETURN id(d) AS internal_id
                        """,
                        chart_id=chart_id,
                        id=f"{chart_id}_MD_{p['planet']}",
                        planet=p["planet"],
                        start=p["start_date"],
                        end=p["end_date"],
                        weight=p["activation_weight"],
                        yogas=p["yogas_activated"],
                        source=p["source"]
                    )
                    md_node_map[p["planet"]] = res.single()["internal_id"]
                    
                elif p["dasha_type"] == "antardasha":
                    parent_planet = p["parent_planet"]
                    session.run(
                        """
                        MATCH (parent:Dashaperiod {id: $parent_id})
                        CREATE (d:Dashaperiod {
                            id: $id,
                            dasha_type: 'antardasha',
                            planet: $planet,
                            start_date: $start,
                            end_date: $end,
                            activation_weight: $weight,
                            yogas_activated: $yogas,
                            source: $source
                        })
                        MERGE (parent)-[:CONTAINS]->(d)
                        WITH d
                        MATCH (p:Planet {name: $planet})
                        MERGE (d)-[:GOVERNED_BY]->(p)
                        """,
                        parent_id=f"{chart_id}_MD_{parent_planet}",
                        id=f"{chart_id}_AD_{parent_planet}_{p['planet']}",
                        planet=p["planet"],
                        start=p["start_date"],
                        end=p["end_date"],
                        weight=p["activation_weight"],
                        yogas=p["yogas_activated"],
                        source=p["source"]
                    )
