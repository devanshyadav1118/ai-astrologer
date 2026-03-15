"""Robust Vimshottari Dasha Engine.

Calculates the 120-year Vimshottari Dasha cycle using the fixed classical 
sequence and precise birth balance.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any


class VimshottariCalculator:
    """Fixed-sequence dasha calculator based on standard Parashari rules."""

    # Classical Sequence and Durations (Years)
    SEQUENCE = [
        "KETU", "VENUS", "SUN", "MOON", "MARS", 
        "RAHU", "JUPITER", "SATURN", "MERCURY"
    ]
    DURATIONS = {
        "KETU": 7, "VENUS": 20, "SUN": 6, "MOON": 10, "MARS": 7,
        "RAHU": 18, "JUPITER": 16, "SATURN": 19, "MERCURY": 17
    }
    
    # 365.25 days per year (standard Julian year for dasha)
    DAYS_PER_YEAR = 365.25

    def calculate_dasha_timeline(
        self, 
        birth_date: str, 
        birth_time: str, 
        moon_longitude: float
    ) -> list[dict[str, Any]]:
        """Compute complete 120-year timeline starting from birth balance."""
        # 1. Determine Starting Nakshatra and Lord
        # Nakshatra arc is 13°20' = 13.3333...°
        arc = 360.0 / 27.0
        nak_idx = int(moon_longitude / arc)
        nak_progress = (moon_longitude % arc) / arc
        
        # Mapping Nakshatra index to Lord sequence
        # Ashwini (0) is Ketu (0), etc.
        lord_idx = nak_idx % 9
        start_lord = self.SEQUENCE[lord_idx]
        
        # 2. Calculate Birth Balance
        # Remaining duration = (1 - progress) * full_duration
        total_years = self.DURATIONS[start_lord]
        remaining_years = total_years * (1 - nak_progress)
        elapsed_years = total_years * nak_progress
        
        # 3. Build Timeline
        birth_dt = datetime.strptime(f"{birth_date} {birth_time}", "%Y-%m-%d %H:%M:%S")
        
        # First Mahadasha starts BEFORE birth
        # MD_start = birth - elapsed
        md_start = birth_dt - timedelta(days=elapsed_years * self.DAYS_PER_YEAR)
        
        periods = []
        current_md_start = md_start
        
        # We run the sequence starting from the birth lord for 9 cycles (complete round)
        seq_idx = lord_idx
        for _ in range(9):
            planet = self.SEQUENCE[seq_idx % 9]
            duration = self.DURATIONS[planet]
            md_end = current_md_start + timedelta(days=duration * self.DAYS_PER_YEAR)
            
            md_node = {
                "dasha_type": "mahadasha",
                "planet": planet,
                "start_date": current_md_start.strftime("%Y-%m-%d"),
                "end_date": md_end.strftime("%Y-%m-%d"),
                "source": "internal_engine"
            }
            periods.append(md_node)
            
            # Antardashas (Bhuktis)
            # The first MD might start before birth, so ADs also need to be sequenced
            ad_start = current_md_start
            # AD sequence always starts with MD lord then follows fixed sequence
            for j in range(9):
                ad_planet = self.SEQUENCE[(seq_idx + j) % 9]
                ad_duration_years = (duration * self.DURATIONS[ad_planet]) / 120.0
                ad_end = ad_start + timedelta(days=ad_duration_years * self.DAYS_PER_YEAR)
                
                periods.append({
                    "dasha_type": "antardasha",
                    "planet": ad_planet,
                    "parent_planet": planet,
                    "start_date": ad_start.strftime("%Y-%m-%d"),
                    "end_date": ad_end.strftime("%Y-%m-%d"),
                    "source": "internal_engine"
                })
                ad_start = ad_end
            
            current_md_start = md_end
            seq_idx += 1
            
        return periods


class DashaEngine:
    """Orchestrates dasha calculation, enrichment with Phase 6/7 scores, and ingestion."""

    def __init__(
        self, 
        neo4j_client: Any | None = None,
        calculator: VimshottariCalculator | None = None
    ) -> None:
        self.neo4j = neo4j_client
        self.calculator = calculator or VimshottariCalculator()
        self.logger = logging.getLogger(__name__)

    def process_dashas(self, chart_id: str, birth_data: dict[str, Any], moon_longitude: float | None = None, precalculated_periods: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        """Run the full dasha pipeline: Compute -> Enrich -> Ingest."""
        # 1. Get raw timeline from internal calculator OR use precalculated
        if precalculated_periods:
            periods = precalculated_periods
        else:
            if moon_longitude is None:
                raise ValueError("moon_longitude is required if no precalculated_periods are provided.")
            periods = self.calculator.calculate_dasha_timeline(
                birth_date=birth_data["date"],
                birth_time=birth_data["time"],
                moon_longitude=moon_longitude
            )
        
        # 2. Enrich with Phase 6 (Strength) and Phase 7 (Yogas)
        if self.neo4j:
            enriched_periods = self._enrich_periods(chart_id, periods)
            # 3. Ingest into Neo4j
            self._ingest_periods(chart_id, enriched_periods)
            return enriched_periods
        else:
            self.logger.warning("No Neo4j client provided, skipping enrichment and ingestion")
            return periods

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
            p["yogas_activated"] = [y["name"] for y in yogas if planet in y.get("planets", [])]
            
        return periods

    def _ingest_periods(self, chart_id: str, periods: list[dict[str, Any]]) -> None:
        """Store the enriched dasha chain in Neo4j."""
        with self.neo4j.driver.session() as session:
            # Clear old dashas
            session.run("MATCH (:Chart {chart_id: $chart_id})-[:HAS_DASHA]->(d:Dashaperiod) DETACH DELETE d", chart_id=chart_id)
            
            for p in periods:
                # Filter to only store periods that start or end AFTER birth (no need to store long-past history)
                # For simplicity in this step, we store all for now.
                
                if p["dasha_type"] == "mahadasha":
                    session.run(
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
                    
                elif p["dasha_type"] == "antardasha":
                    parent_planet = p["parent_planet"]
                    session.run(
                        """
                        MATCH (c:Chart {chart_id: $chart_id})-[:HAS_DASHA]->(parent:Dashaperiod {dasha_type: 'mahadasha', planet: $parent_planet})
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
                        chart_id=chart_id,
                        parent_planet=parent_planet,
                        id=f"{chart_id}_AD_{parent_planet}_{p['planet']}",
                        planet=p["planet"],
                        start=p["start_date"],
                        end=p["end_date"],
                        weight=p["activation_weight"],
                        yogas=p["yogas_activated"],
                        source=p["source"]
                    )
