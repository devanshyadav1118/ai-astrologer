"""Neo4j connection, ontology loading, and rule ingestion helpers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
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
    """Neo4j driver wrapper used by the ontology seeding and extraction pipeline."""

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
            "CREATE CONSTRAINT book_id IF NOT EXISTS FOR (b:Book) REQUIRE b.book_id IS UNIQUE",
            "CREATE CONSTRAINT rule_id IF NOT EXISTS FOR (r:Rule) REQUIRE r.rule_id IS UNIQUE",
            "CREATE CONSTRAINT rule_hash IF NOT EXISTS FOR (r:Rule) REQUIRE r.rule_hash IS UNIQUE",
            "CREATE CONSTRAINT chart_id IF NOT EXISTS FOR (c:Chart) REQUIRE c.chart_id IS UNIQUE",
            "CREATE CONSTRAINT chart_planet_id IF NOT EXISTS FOR (cp:ChartPlanet) REQUIRE cp.id IS UNIQUE",
            "CREATE CONSTRAINT chart_house_id IF NOT EXISTS FOR (ch:ChartHouse) REQUIRE ch.id IS UNIQUE",
        ]
        with self.driver.session() as session:
            for statement in constraints:
                session.run(statement)

    def load_rule(self, rule: dict[str, Any], book_id: str) -> str:
        """Load an extracted rule, deduplicating by content hash."""
        existing_id = self.check_duplicate_rule(rule)
        if existing_id is not None:
            self.increment_confidence(existing_id, book_id)
            return existing_id

        rule_id = str(rule.get("rule_id") or self._generate_rule_id(book_id))
        rule_hash = self._compute_rule_hash(rule)
        with self.driver.session() as session:
            session.run(
                """
                MERGE (b:Book {book_id: $book_id})
                ON CREATE SET b.created_at = $timestamp
                SET b.updated_at = $timestamp
                """,
                book_id=book_id,
                timestamp=self._now(),
            )
            session.run(
                """
                MERGE (r:Rule {rule_id: $rule_id})
                SET r.rule_hash = $rule_hash,
                    r.type = $rule_type,
                    r.source_text = $source_text,
                    r.condition_text = $condition_text,
                    r.effect_summary = $effect_summary,
                    r.validation_status = $validation_status,
                    r.confidence = 1,
                    r.source_chunks = $source_chunks,
                    r.source_books = [$book_id],
                    r.metadata_json = $metadata_json,
                    r.created_at = $timestamp,
                    r.updated_at = $timestamp
                """,
                rule_id=rule_id,
                rule_hash=rule_hash,
                rule_type=rule.get("type"),
                source_text=rule.get("source_text"),
                condition_text=rule.get("condition_text"),
                effect_summary=self._effect_summary(rule.get("effects", [])),
                validation_status=rule.get("validation_status"),
                source_chunks=rule.get("source_chunks", []),
                book_id=book_id,
                metadata_json=json.dumps(rule.get("metadata", {}), ensure_ascii=True, sort_keys=True),
                timestamp=self._now(),
            )
            session.run(
                """
                MATCH (r:Rule {rule_id: $rule_id})
                MATCH (b:Book {book_id: $book_id})
                MERGE (r)-[:EXTRACTED_FROM]->(b)
                """,
                rule_id=rule_id,
                book_id=book_id,
            )
            self._link_rule_entities(session, rule_id, rule)
        return rule_id

    def load_yoga(self, yoga: dict[str, Any], book_id: str) -> str:
        """Load a yoga node and link it to the source book."""
        yoga_name = str(yoga.get("name") or yoga.get("canonical_name") or yoga.get("yoga_id"))
        yoga_id = str(yoga.get("yoga_id") or yoga_name)
        with self.driver.session() as session:
            session.run(
                """
                MERGE (b:Book {book_id: $book_id})
                ON CREATE SET b.created_at = $timestamp
                SET b.updated_at = $timestamp
                """,
                book_id=book_id,
                timestamp=self._now(),
            )
            session.run(
                """
                MERGE (y:Yoga {name: $name})
                SET y.yoga_id = $yoga_id,
                    y.description = $description,
                    y.source_chunks = $source_chunks,
                    y.updated_at = $timestamp
                """,
                name=yoga_name,
                yoga_id=yoga_id,
                description=yoga.get("description"),
                source_chunks=yoga.get("source_chunks", []),
                timestamp=self._now(),
            )
            session.run(
                """
                MATCH (y:Yoga {name: $name})
                MATCH (b:Book {book_id: $book_id})
                MERGE (y)-[:EXTRACTED_FROM]->(b)
                """,
                name=yoga_name,
                book_id=book_id,
            )
        return yoga_id

    def check_duplicate_rule(self, rule: dict[str, Any]) -> str | None:
        """Return the existing rule_id for a duplicate rule, if any."""
        rule_hash = self._compute_rule_hash(rule)
        with self.driver.session() as session:
            record = session.run(
                """
                MATCH (r:Rule {rule_hash: $rule_hash})
                RETURN r.rule_id AS rule_id
                LIMIT 1
                """,
                rule_hash=rule_hash,
            ).single()
        return None if record is None else str(record["rule_id"])

    def increment_confidence(self, rule_id: str, book_id: str) -> None:
        """Increment rule confidence when a duplicate is found in another book."""
        with self.driver.session() as session:
            session.run(
                """
                MERGE (b:Book {book_id: $book_id})
                ON CREATE SET b.created_at = $timestamp
                SET b.updated_at = $timestamp
                """,
                book_id=book_id,
                timestamp=self._now(),
            )
            session.run(
                """
                MATCH (r:Rule {rule_id: $rule_id})
                MATCH (b:Book {book_id: $book_id})
                SET r.confidence = COALESCE(r.confidence, 1) + 1,
                    r.source_books = CASE
                        WHEN $book_id IN COALESCE(r.source_books, []) THEN r.source_books
                        ELSE COALESCE(r.source_books, []) + $book_id
                    END,
                    r.updated_at = $timestamp
                MERGE (r)-[:EXTRACTED_FROM]->(b)
                """,
                rule_id=rule_id,
                book_id=book_id,
                timestamp=self._now(),
            )

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

    def _link_rule_entities(self, session: Any, rule_id: str, rule: dict[str, Any]) -> None:
        for canonical in self._collect_entities(rule):
            label = self._label_for_entity(canonical)
            if label is None:
                continue
            session.run(
                f"""
                MATCH (r:Rule {{rule_id: $rule_id}})
                MATCH (e:{label} {{name: $name}})
                MERGE (r)-[:REFERS_TO]->(e)
                """,
                rule_id=rule_id,
                name=canonical,
            )

    def _collect_entities(self, rule: dict[str, Any]) -> set[str]:
        entities: set[str] = set()
        normalised_entities = rule.get("normalised_entities", {})
        if isinstance(normalised_entities, dict):
            entities.update(str(value) for value in normalised_entities.values() if isinstance(value, str))
        conditions = rule.get("conditions", {})
        if isinstance(conditions, dict):
            for clause in conditions.get("clauses", []):
                if not isinstance(clause, dict):
                    continue
                for key in ("planet", "sign", "house", "nakshatra"):
                    value = clause.get(key)
                    if isinstance(value, str):
                        entities.add(value)
        return entities

    def _label_for_entity(self, canonical: str) -> str | None:
        if canonical.startswith("HOUSE_"):
            return "House"
        if canonical in {"SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN", "RAHU", "KETU"}:
            return "Planet"
        if canonical in {
            "ARIES",
            "TAURUS",
            "GEMINI",
            "CANCER",
            "LEO",
            "VIRGO",
            "LIBRA",
            "SCORPIO",
            "SAGITTARIUS",
            "CAPRICORN",
            "AQUARIUS",
            "PISCES",
        }:
            return "Sign"
        if canonical.isupper() and "_" not in canonical:
            return "Nakshatra"
        return None

    def _compute_rule_hash(self, rule: dict[str, Any]) -> str:
        payload = {
            "type": rule.get("type"),
            "source_text": rule.get("source_text"),
            "conditions": rule.get("conditions"),
            "effects": rule.get("effects"),
        }
        serialised = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        return hashlib.sha256(serialised.encode("utf-8")).hexdigest()

    def _generate_rule_id(self, book_id: str) -> str:
        return f"{book_id}_rule_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"

    def _effect_summary(self, effects: Any) -> str | None:
        if not isinstance(effects, list):
            return None
        descriptions = [
            effect.get("description")
            for effect in effects
            if isinstance(effect, dict) and effect.get("description")
        ]
        return "; ".join(descriptions) if descriptions else None

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

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
