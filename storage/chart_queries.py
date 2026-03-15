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

    def get_full_chart_data(self, chart_id: str) -> dict[str, Any]:
        """Retrieve all graph data needed for complex yoga detection."""
        with self.neo4j_client.driver.session() as session:
            # 1. Planets
            planets_res = session.run(
                """
                MATCH (:Chart {chart_id: $chart_id})-[:CONTAINS_PLANET]->(cp:ChartPlanet)
                RETURN cp.planet_name AS name, cp.house AS house, cp.sign AS sign, 
                       cp.degree AS degree, cp.longitude AS longitude,
                       cp.dignity_status AS dignity_status, cp.strength_modifier AS strength_modifier,
                       cp.is_combust AS combustion, cp.is_retrograde AS retrograde
                """, chart_id=chart_id
            )
            planets = []
            for p in planets_res:
                p_dict = dict(p)
                p_dict["dignity"] = {"status": p_dict.pop("dignity_status"), "strength_modifier": p_dict.pop("strength_modifier")}
                planets.append(p_dict)

            # 2. Houses
            houses_res = session.run(
                """
                MATCH (:Chart {chart_id: $chart_id})-[:CONTAINS_HOUSE]->(ch:ChartHouse)
                MATCH (ch)-[:RULED_BY]->(lord:ChartPlanet)
                RETURN ch.house_number AS number, ch.sign AS sign, lord.planet_name AS lord
                """, chart_id=chart_id
            )
            houses = [dict(h) for h in houses_res]

            # 3. Aspects
            aspects_res = session.run(
                """
                MATCH (:Chart {chart_id: $chart_id})-[:CONTAINS_PLANET]->(source:ChartPlanet)-[a:ASPECTS]->(target:ChartPlanet)
                RETURN source.planet_name AS from_planet, target.planet_name AS to_planet, a.strength AS strength
                """, chart_id=chart_id
            )
            aspects = [dict(a) for a in aspects_res]

            # 4. Conjunctions
            conjunctions_res = session.run(
                """
                MATCH (:Chart {chart_id: $chart_id})-[:CONTAINS_PLANET]->(p1:ChartPlanet)-[c:CONJOINS]->(p2:ChartPlanet)
                RETURN p1.planet_name AS planet_1, p2.planet_name AS planet_2, c.orb AS orb
                """, chart_id=chart_id
            )
            conjunctions = [dict(c) for c in conjunctions_res]

            # 5. Dispositors (Mutual Reception check)
            dispositors_res = session.run(
                """
                MATCH (:Chart {chart_id: $chart_id})-[:CONTAINS_PLANET]->(p:ChartPlanet)-[:DISPOSED_BY]->(d:ChartPlanet)
                RETURN p.planet_name AS planet, d.planet_name AS dispositor
                """, chart_id=chart_id
            )
            dispositors = [dict(d) for d in dispositors_res]

        return {
            "planets": planets,
            "houses": houses,
            "aspects": aspects,
            "conjunctions": conjunctions,
            "dispositors": dispositors
        }
