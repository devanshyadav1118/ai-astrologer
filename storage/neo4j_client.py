"""Neo4j connection and ontology loading helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from neo4j import GraphDatabase

from normaliser.normaliser import load_ontology_file


@dataclass(slots=True)
class Neo4jSettings:
    """Runtime settings for Neo4j access."""

    uri: str
    user: str
    password: str


def load_neo4j_settings() -> Neo4jSettings:
    """Load Neo4j settings from `.env`."""
    load_dotenv()
    uri = os.getenv("NEO4J_URI", "").strip()
    user = os.getenv("NEO4J_USER", "").strip()
    password = os.getenv("NEO4J_PASSWORD", "").strip()
    if not uri or not user or not password:
        raise RuntimeError("Neo4j settings are incomplete")
    return Neo4jSettings(uri=uri, user=user, password=password)


class Neo4jClient:
    """Neo4j driver wrapper used by the ontology seeding pipeline."""

    def __init__(self) -> None:
        settings = load_neo4j_settings()
        self.driver = GraphDatabase.driver(
            settings.uri,
            auth=(settings.user, settings.password),
        )

    def verify_connection(self) -> str:
        with self.driver.session() as session:
            return session.run("RETURN 'connected' AS msg").single()["msg"]

    def create_constraints(self) -> None:
        constraints = [
            "CREATE CONSTRAINT planet_name IF NOT EXISTS FOR (p:Planet) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT sign_name IF NOT EXISTS FOR (s:Sign) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT house_name IF NOT EXISTS FOR (h:House) REQUIRE h.name IS UNIQUE",
            "CREATE CONSTRAINT nakshatra_name IF NOT EXISTS FOR (n:Nakshatra) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT yoga_name IF NOT EXISTS FOR (y:Yoga) REQUIRE y.name IS UNIQUE",
        ]
        with self.driver.session() as session:
            for statement in constraints:
                session.run(statement)

    def load_planets(self, filepath: str | Path) -> int:
        data = load_ontology_file(filepath)
        with self.driver.session() as session:
            for planet in data["planets"]:
                session.run(
                    """
                    MERGE (p:Planet {name: $name})
                    SET p += $properties
                    """,
                    name=planet["canonical_name"],
                    properties=self._neo4j_properties(planet),
                )
        return len(data["planets"])

    def load_signs(self, filepath: str | Path) -> int:
        data = load_ontology_file(filepath)
        with self.driver.session() as session:
            for sign in data["signs"]:
                session.run(
                    """
                    MERGE (s:Sign {name: $name})
                    SET s += $properties
                    """,
                    name=sign["canonical_name"],
                    properties=self._neo4j_properties(sign),
                )
        return len(data["signs"])

    def load_houses(self, filepath: str | Path) -> int:
        data = load_ontology_file(filepath)
        with self.driver.session() as session:
            for house in data["houses"]:
                session.run(
                    """
                    MERGE (h:House {name: $name})
                    SET h += $properties
                    """,
                    name=house["canonical_name"],
                    properties=self._neo4j_properties(house),
                )
        return len(data["houses"])

    def load_nakshatras(self, filepath: str | Path) -> int:
        data = load_ontology_file(filepath)
        with self.driver.session() as session:
            for nakshatra in data["nakshatras"]:
                session.run(
                    """
                    MERGE (n:Nakshatra {name: $name})
                    SET n += $properties
                    """,
                    name=nakshatra["canonical_name"],
                    properties=self._neo4j_properties(nakshatra),
                )
        return len(data["nakshatras"])

    def load_yogas(self, filepath: str | Path) -> int:
        data = load_ontology_file(filepath)
        with self.driver.session() as session:
            for yoga in data["yogas"]:
                session.run(
                    """
                    MERGE (y:Yoga {name: $name})
                    SET y += $properties
                    """,
                    name=yoga["canonical_name"],
                    properties=self._neo4j_properties(yoga),
                )
        return len(data["yogas"])

    def load_planet_relationships(self, filepath: str | Path) -> None:
        data = load_ontology_file(filepath)
        with self.driver.session() as session:
            for planet in data["planets"]:
                planet_name = planet["canonical_name"]
                if planet.get("exaltation_sign"):
                    session.run(
                        """
                        MATCH (p:Planet {name: $planet_name})
                        MATCH (s:Sign {name: $sign_name})
                        MERGE (p)-[r:IS_EXALTED_IN]->(s)
                        SET r.degree = $degree
                        """,
                        planet_name=planet_name,
                        sign_name=planet["exaltation_sign"],
                        degree=planet.get("exaltation_degree"),
                    )
                if planet.get("debilitation_sign"):
                    session.run(
                        """
                        MATCH (p:Planet {name: $planet_name})
                        MATCH (s:Sign {name: $sign_name})
                        MERGE (p)-[r:IS_DEBILITATED_IN]->(s)
                        SET r.degree = $degree
                        """,
                        planet_name=planet_name,
                        sign_name=planet["debilitation_sign"],
                        degree=planet.get("debilitation_degree"),
                    )
                for own_sign in planet.get("own_signs", []):
                    session.run(
                        """
                        MATCH (p:Planet {name: $planet_name})
                        MATCH (s:Sign {name: $sign_name})
                        MERGE (p)-[:OWNS]->(s)
                        """,
                        planet_name=planet_name,
                        sign_name=own_sign,
                    )
                for friend in planet.get("friends", []):
                    session.run(
                        """
                        MATCH (p1:Planet {name: $planet_name})
                        MATCH (p2:Planet {name: $other_name})
                        MERGE (p1)-[:NATURAL_FRIEND_OF]->(p2)
                        """,
                        planet_name=planet_name,
                        other_name=friend,
                    )
                for enemy in planet.get("enemies", []):
                    session.run(
                        """
                        MATCH (p1:Planet {name: $planet_name})
                        MATCH (p2:Planet {name: $other_name})
                        MERGE (p1)-[:NATURAL_ENEMY_OF]->(p2)
                        """,
                        planet_name=planet_name,
                        other_name=enemy,
                    )
                for neutral in planet.get("neutrals", []):
                    session.run(
                        """
                        MATCH (p1:Planet {name: $planet_name})
                        MATCH (p2:Planet {name: $other_name})
                        MERGE (p1)-[:NATURAL_NEUTRAL_TO]->(p2)
                        """,
                        planet_name=planet_name,
                        other_name=neutral,
                    )

    def verify_entity_counts(self) -> dict[str, int]:
        labels = ["Planet", "Sign", "House", "Nakshatra", "Yoga"]
        counts: dict[str, int] = {}
        with self.driver.session() as session:
            for label in labels:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) AS count")
                counts[label] = result.single()["count"]
        return counts

    def close(self) -> None:
        self.driver.close()

    def _neo4j_properties(self, entity: dict[str, Any]) -> dict[str, Any]:
        properties: dict[str, Any] = {}
        for key, value in entity.items():
            if key == "canonical_name":
                continue
            if self._is_neo4j_primitive(value):
                properties[key] = value
            else:
                properties[f"{key}_json"] = json.dumps(value, ensure_ascii=True, sort_keys=True)
        return properties

    def _is_neo4j_primitive(self, value: Any) -> bool:
        if value is None or isinstance(value, (str, int, float, bool)):
            return True
        if isinstance(value, list):
            return all(item is None or isinstance(item, (str, int, float, bool)) for item in value)
        return False
