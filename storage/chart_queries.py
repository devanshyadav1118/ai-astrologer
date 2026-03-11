"""High-level Neo4j chart queries for Phase 4."""

from __future__ import annotations

from typing import Any

from storage.neo4j_client import Neo4jClient


class ChartQueries:
    """Reusable chart-subgraph query interface."""

    def __init__(self, neo4j_client: Neo4jClient) -> None:
        self.neo4j_client = neo4j_client

    def get_house_lord(self, chart_id: str, house_number: int) -> dict[str, Any] | None:
        with self.neo4j_client.driver.session() as session:
            record = session.run(
                """
                MATCH (:Chart {chart_id: $chart_id})-[:CONTAINS_HOUSE]->(h:ChartHouse {house_number: $house_number})
                MATCH (h)-[:RULED_BY]->(lord:ChartPlanet)-[:PLACED_IN_HOUSE]->(lord_house:ChartHouse)
                RETURN lord.planet_name AS lord,
                       lord_house.house_number AS lord_house,
                       lord.sign AS lord_sign,
                       lord.dignity_status AS lord_dignity,
                       lord.strength_modifier AS lord_strength
                LIMIT 1
                """,
                chart_id=chart_id,
                house_number=house_number,
            ).single()
        return None if record is None else dict(record)

    def get_planet_placement(self, chart_id: str, planet: str) -> dict[str, Any] | None:
        with self.neo4j_client.driver.session() as session:
            record = session.run(
                """
                MATCH (:Chart {chart_id: $chart_id})-[:CONTAINS_PLANET]->(cp:ChartPlanet {planet_name: $planet})
                RETURN cp.house AS house,
                       cp.sign AS sign,
                       cp.degree AS degree,
                       cp.nakshatra AS nakshatra,
                       cp.nakshatra_pada AS pada,
                       cp.dignity_status AS dignity
                LIMIT 1
                """,
                chart_id=chart_id,
                planet=planet,
            ).single()
        return None if record is None else dict(record)

    def get_aspects_to_planet(self, chart_id: str, planet: str) -> list[dict[str, Any]]:
        with self.neo4j_client.driver.session() as session:
            result = session.run(
                """
                MATCH (:Chart {chart_id: $chart_id})-[:CONTAINS_PLANET]->(:ChartPlanet)-[a:ASPECTS]->(target:ChartPlanet {planet_name: $planet})
                MATCH (source:ChartPlanet)-[a]->(target)
                RETURN source.planet_name AS from_planet,
                       a.type AS type,
                       a.strength AS strength
                ORDER BY source.planet_name
                """,
                chart_id=chart_id,
                planet=planet,
            )
            return [dict(record) for record in result]

    def get_planets_in_house(self, chart_id: str, house: int) -> list[str]:
        with self.neo4j_client.driver.session() as session:
            result = session.run(
                """
                MATCH (:Chart {chart_id: $chart_id})-[:CONTAINS_PLANET]->(cp:ChartPlanet {house: $house})
                RETURN cp.planet_name AS planet
                ORDER BY cp.degree
                """,
                chart_id=chart_id,
                house=house,
            )
            return [str(record["planet"]) for record in result]

    def get_conjunctions(self, chart_id: str, planet: str) -> list[dict[str, Any]]:
        with self.neo4j_client.driver.session() as session:
            result = session.run(
                """
                MATCH (:Chart {chart_id: $chart_id})-[:CONTAINS_PLANET]->(cp:ChartPlanet {planet_name: $planet})
                MATCH (cp)-[c:CONJOINS]->(other:ChartPlanet)
                RETURN other.planet_name AS planet,
                       c.orb AS orb,
                       c.same_nakshatra AS same_nakshatra
                ORDER BY c.orb ASC, other.planet_name
                """,
                chart_id=chart_id,
                planet=planet,
            )
            return [dict(record) for record in result]

    def traverse_house_chain(self, chart_id: str, house: int) -> dict[str, Any] | None:
        with self.neo4j_client.driver.session() as session:
            record = session.run(
                """
                MATCH (:Chart {chart_id: $chart_id})-[:CONTAINS_HOUSE]->(h:ChartHouse {house_number: $house_number})
                MATCH (h)-[:RULED_BY]->(lord:ChartPlanet)-[:PLACED_IN_HOUSE]->(lord_house:ChartHouse)
                MATCH (lord)-[:INSTANCE_OF]->(base_planet:Planet)
                MATCH (lord_house)-[:REPRESENTS]->(base_house:House)
                OPTIONAL MATCH (aspector:ChartPlanet)-[:ASPECTS]->(lord)
                RETURN h.sign AS house_sign,
                       lord.planet_name AS lord_name,
                       lord.dignity_status AS lord_dignity,
                       lord_house.house_number AS lord_placement,
                       base_planet.natural_karakatvam AS planet_meanings,
                       base_house.primary_meanings AS house_meanings,
                       collect(DISTINCT aspector.planet_name) AS aspects
                LIMIT 1
                """,
                chart_id=chart_id,
                house_number=house,
            ).single()
        return None if record is None else dict(record)

    def get_dispositor_chain(self, chart_id: str, planet: str, max_depth: int = 5) -> list[dict[str, Any]]:
        depth = max(1, int(max_depth))
        with self.neo4j_client.driver.session() as session:
            result = session.run(
                f"""
                MATCH path = (:Chart {{chart_id: $chart_id}})-[:CONTAINS_PLANET]->(start:ChartPlanet {{planet_name: $planet}})
                             -[:DISPOSED_BY*1..{depth}]->(end:ChartPlanet)
                WITH nodes(path)[2..] AS chain
                RETURN [node IN chain | node.planet_name] AS planets
                ORDER BY size(chain) DESC
                LIMIT 1
                """,
                chart_id=chart_id,
                planet=planet,
            ).single()
        if result is None:
            return []
        planets = list(result["planets"])
        return [{"planet": planets[index], "depth": index + 1} for index in range(len(planets))]
