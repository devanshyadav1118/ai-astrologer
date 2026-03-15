"""Neo4j chart subgraph persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from storage.neo4j_client import Neo4jClient


class ChartGraphIngestor:
    """Persist a normalized chart payload into Neo4j."""

    def __init__(self, neo4j_client: Neo4jClient) -> None:
        self.neo4j_client = neo4j_client

    def ingest_chart(self, chart_id: str, chart_data: dict[str, Any]) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        with self.neo4j_client.driver.session() as session:
            session.run(
                """
                MERGE (c:Chart {chart_id: $chart_id})
                ON CREATE SET c.created_at = $timestamp
                SET c.updated_at = $timestamp,
                    c.date = $date,
                    c.time = $time,
                    c.latitude = $latitude,
                    c.longitude = $longitude,
                    c.timezone = $timezone
                """,
                chart_id=chart_id,
                timestamp=timestamp,
                date=chart_data["metadata"]["date"],
                time=chart_data["metadata"]["time"],
                latitude=chart_data["metadata"]["latitude"],
                longitude=chart_data["metadata"]["longitude"],
                timezone=chart_data["metadata"]["timezone"],
            )
            for house in chart_data.get("houses", []):
                house_id = f"{chart_id}_HOUSE_{house['number']}"
                session.run(
                    """
                    MERGE (ch:ChartHouse {id: $id})
                    SET ch.chart_id = $chart_id,
                        ch.house_number = $house_number,
                        ch.house_name = $house_name,
                        ch.sign = $sign,
                        ch.degree = $degree,
                        ch.lord = $lord,
                        ch.updated_at = $timestamp
                    """,
                    id=house_id,
                    chart_id=chart_id,
                    house_number=house["number"],
                    house_name=house["house"],
                    sign=house["sign"],
                    degree=house["degree"],
                    lord=house["lord"],
                    timestamp=timestamp,
                )
                session.run(
                    """
                    MATCH (c:Chart {chart_id: $chart_id})
                    MATCH (ch:ChartHouse {id: $house_id})
                    MERGE (c)-[:CONTAINS_HOUSE]->(ch)
                    """,
                    chart_id=chart_id,
                    house_id=house_id,
                )
                session.run(
                    """
                    MATCH (ch:ChartHouse {id: $house_id})
                    MATCH (s:Sign {name: $sign})
                    MERGE (ch)-[:SIGN_ON_CUSP]->(s)
                    """,
                    house_id=house_id,
                    sign=house["sign"],
                )
                session.run(
                    """
                    MATCH (ch:ChartHouse {id: $house_id})
                    MATCH (h:House {name: $house_name})
                    MERGE (ch)-[:REPRESENTS]->(h)
                    """,
                    house_id=house_id,
                    house_name=house["house"],
                )
            for planet in chart_data.get("planets", []):
                planet_id = f"{chart_id}_{planet['name']}"
                house_id = f"{chart_id}_HOUSE_{planet['house']}"
                session.run(
                    """
                    MERGE (cp:ChartPlanet {id: $id})
                    SET cp.chart_id = $chart_id,
                        cp.planet_name = $planet_name,
                        cp.sign = $sign,
                        cp.degree = $degree,
                        cp.longitude = $longitude,
                        cp.house = $house,
                        cp.nakshatra = $nakshatra,
                        cp.nakshatra_pada = $nakshatra_pada,
                        cp.sublord = $sublord,
                        cp.retrograde = $retrograde,
                        cp.combustion = $combustion,
                        cp.dignity_status = $dignity_status,
                        cp.strength_modifier = $strength_modifier,
                        cp.strength_total = $strength_total,
                        cp.strength_dignity = $strength_dignity,
                        cp.strength_house = $strength_house,
                        cp.strength_aspects = $strength_aspects,
                        cp.strength_special = $strength_special,
                        cp.strength_dispositor = $strength_dispositor,
                        cp.is_combust = $is_combust,
                        cp.is_retrograde = $is_retrograde,
                        cp.is_in_war = $is_in_war,
                        cp.neecha_bhanga_active = $neecha_bhanga_active,
                        cp.updated_at = $timestamp
                    """,
                    id=planet_id,
                    chart_id=chart_id,
                    planet_name=planet["name"],
                    sign=planet["sign"],
                    degree=planet["degree"],
                    longitude=planet["longitude"],
                    latitude=planet.get("latitude", 0.0),
                    house=planet["house"],
                    nakshatra=planet.get("nakshatra"),
                    nakshatra_pada=planet.get("nakshatra_pada"),
                    sublord=planet.get("sublord"),
                    retrograde=planet.get("retrograde", False),
                    combustion=planet.get("combustion", False),
                    dignity_status=planet["dignity"]["status"],
                    strength_modifier=planet["dignity"]["strength_modifier"],
                    strength_total=planet.get("strength_scores", {}).get("total_strength", 0.0),
                    strength_dignity=planet.get("strength_scores", {}).get("breakdown", {}).get("raw_components", {}).get("dignity", 0.0),
                    strength_house=planet.get("strength_scores", {}).get("breakdown", {}).get("raw_components", {}).get("house", 0.0),
                    strength_aspects=planet.get("strength_scores", {}).get("breakdown", {}).get("raw_components", {}).get("aspect", 0.0),
                    strength_special=planet.get("strength_scores", {}).get("breakdown", {}).get("raw_components", {}).get("special", 0.0),
                    strength_dispositor=planet.get("strength_scores", {}).get("breakdown", {}).get("raw_components", {}).get("dispositor", 0.0),
                    is_combust=planet.get("strength_scores", {}).get("flags", {}).get("is_combust", False),
                    is_retrograde=planet.get("strength_scores", {}).get("flags", {}).get("is_retrograde", False),
                    is_in_war=planet.get("strength_scores", {}).get("flags", {}).get("is_in_war", False),
                    neecha_bhanga_active=planet.get("strength_scores", {}).get("flags", {}).get("neecha_bhanga", False),
                    timestamp=timestamp,
                )
                session.run(
                    """
                    MATCH (c:Chart {chart_id: $chart_id})
                    MATCH (cp:ChartPlanet {id: $planet_id})
                    MERGE (c)-[:CONTAINS_PLANET]->(cp)
                    """,
                    chart_id=chart_id,
                    planet_id=planet_id,
                )
                session.run(
                    """
                    MATCH (cp:ChartPlanet {id: $planet_id})
                    MATCH (p:Planet {name: $planet_name})
                    MERGE (cp)-[:INSTANCE_OF]->(p)
                    """,
                    planet_id=planet_id,
                    planet_name=planet["name"],
                )
                session.run(
                    """
                    MATCH (cp:ChartPlanet {id: $planet_id})
                    MATCH (s:Sign {name: $sign})
                    MERGE (cp)-[:PLACED_IN_SIGN]->(s)
                    """,
                    planet_id=planet_id,
                    sign=planet["sign"],
                )
                session.run(
                    """
                    MATCH (cp:ChartPlanet {id: $planet_id})
                    MATCH (ch:ChartHouse {id: $house_id})
                    MERGE (cp)-[:PLACED_IN_HOUSE]->(ch)
                    """,
                    planet_id=planet_id,
                    house_id=house_id,
                )
                if planet.get("nakshatra"):
                    session.run(
                        """
                        MATCH (cp:ChartPlanet {id: $planet_id})
                        MATCH (n:Nakshatra {name: $nakshatra})
                        MERGE (cp)-[r:IN_NAKSHATRA]->(n)
                        SET r.pada = $pada
                        """,
                        planet_id=planet_id,
                        nakshatra=planet["nakshatra"],
                        pada=planet.get("nakshatra_pada"),
                    )
            for house in chart_data.get("houses", []):
                house_id = f"{chart_id}_HOUSE_{house['number']}"
                lord_planet_id = f"{chart_id}_{house['lord']}"
                session.run(
                    """
                    MATCH (ch:ChartHouse {id: $house_id})
                    MATCH (cp:ChartPlanet {id: $planet_id})
                    MERGE (ch)-[:RULED_BY]->(cp)
                    """,
                    house_id=house_id,
                    planet_id=lord_planet_id,
                )
            for aspect in chart_data.get("aspects", []):
                session.run(
                    """
                    MATCH (cp1:ChartPlanet {id: $from_id})
                    MATCH (cp2:ChartPlanet {id: $to_id})
                    MERGE (cp1)-[a:ASPECTS {type: $aspect_type}]->(cp2)
                    SET a.house_offset = $house_offset,
                        a.strength = $strength
                    """,
                    from_id=f"{chart_id}_{aspect['from_planet']}",
                    to_id=f"{chart_id}_{aspect['to_planet']}",
                    aspect_type=aspect["type"],
                    house_offset=aspect["house_offset"],
                    strength=aspect["strength"],
                )
            for aspect in chart_data.get("house_aspects", []):
                session.run(
                    """
                    MATCH (cp:ChartPlanet {id: $from_id})
                    MATCH (ch:ChartHouse {id: $to_id})
                    MERGE (cp)-[a:ASPECTS {type: $aspect_type}]->(ch)
                    SET a.house_offset = $house_offset,
                        a.strength = $strength
                    """,
                    from_id=f"{chart_id}_{aspect['from_planet']}",
                    to_id=f"{chart_id}_HOUSE_{aspect['to_house']}",
                    aspect_type=aspect["type"],
                    house_offset=aspect["house_offset"],
                    strength=aspect["strength"],
                )
            for conjunction in chart_data.get("conjunctions", []):
                left_id = f"{chart_id}_{conjunction['planet_1']}"
                right_id = f"{chart_id}_{conjunction['planet_2']}"
                session.run(
                    """
                    MATCH (cp1:ChartPlanet {id: $left_id})
                    MATCH (cp2:ChartPlanet {id: $right_id})
                    MERGE (cp1)-[c:CONJOINS]->(cp2)
                    SET c.orb = $orb,
                        c.same_nakshatra = $same_nakshatra
                    MERGE (cp2)-[c2:CONJOINS]->(cp1)
                    SET c2.orb = $orb,
                        c2.same_nakshatra = $same_nakshatra
                    """,
                    left_id=left_id,
                    right_id=right_id,
                    orb=conjunction["orb"],
                    same_nakshatra=conjunction["same_nakshatra"],
                )
            for dispositior in chart_data.get("dispositors", []):
                session.run(
                    """
                    MATCH (cp1:ChartPlanet {id: $planet_id})
                    MATCH (cp2:ChartPlanet {id: $dispositor_id})
                    MERGE (cp1)-[d:DISPOSED_BY]->(cp2)
                    SET d.same_planet = $same_planet
                    """,
                    planet_id=f"{chart_id}_{dispositior['planet']}",
                    dispositor_id=f"{chart_id}_{dispositior['dispositor']}",
                    same_planet=dispositior["same_planet"],
                )
        return chart_id

    def ingest_propagation_results(self, chart_id: str, results: dict[str, Any]) -> None:
        """Store Phase 8 propagation results (house importance and themes) in Neo4j."""
        timestamp = datetime.now(timezone.utc).isoformat()
        with self.neo4j_client.driver.session() as session:
            # 1. Store HouseInfluence nodes
            for hi in results.get("house_importance", []):
                hi_id = f"{chart_id}_HI_{hi['house']}"
                session.run(
                    """
                    MATCH (c:Chart {chart_id: $chart_id})
                    MERGE (hin:HouseInfluence {id: $id})
                    SET hin.house_number = $house_number,
                        hin.importance_score = $importance_score,
                        hin.importance_rank = $importance_rank,
                        hin.raw_score = $raw_score,
                        hin.updated_at = $timestamp
                    MERGE (c)-[:HAS_HOUSE_INFLUENCE]->(hin)
                    """,
                    id=hi_id,
                    chart_id=chart_id,
                    house_number=hi["house"],
                    importance_score=hi["importance_score"],
                    importance_rank=hi["rank"],
                    raw_score=hi["raw_score"],
                    timestamp=timestamp
                )

            # 2. Store DominantTheme nodes
            for dt in results.get("dominant_themes", []):
                dt_id = f"{chart_id}_THEME_{dt['theme_name']}"
                session.run(
                    """
                    MATCH (c:Chart {chart_id: $chart_id})
                    MERGE (tn:DominantTheme {id: $id})
                    SET tn.theme_name = $theme_name,
                        tn.theme_score = $theme_score,
                        tn.theme_rank = $theme_rank,
                        tn.key_houses = $key_houses,
                        tn.key_planets = $key_planets,
                        tn.yoga_contributors = $yoga_contributors,
                        tn.updated_at = $timestamp
                    MERGE (c)-[:HAS_DOMINANT_THEME]->(tn)
                    """,
                    id=dt_id,
                    chart_id=chart_id,
                    theme_name=dt["theme_name"],
                    theme_score=dt["theme_score"],
                    theme_rank=dt["theme_rank"],
                    key_houses=dt["key_houses"],
                    key_planets=dt["key_planets"],
                    yoga_contributors=dt["yoga_contributors"],
                    timestamp=timestamp
                )

            # 3. Store Influence Edges (Inter-house)
            for edge in results.get("edges", []):
                hi_from = f"{chart_id}_HI_{edge['from']}"
                hi_to = f"{chart_id}_HI_{edge['to']}"
                session.run(
                    """
                    MATCH (h1:HouseInfluence {id: $from_id})
                    MATCH (h2:HouseInfluence {id: $to_id})
                    MERGE (h1)-[r:INFLUENCES]->(h2)
                    SET r.weight = $weight
                    """,
                    from_id=hi_from,
                    to_id=hi_to,
                    weight=edge["weight"]
                )
