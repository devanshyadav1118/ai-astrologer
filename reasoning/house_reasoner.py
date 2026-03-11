"""Phase 5 house analysis built on the Phase 4 chart graph."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reasoning.models import ReasoningFact, ReasoningNode, SupportingFact
from reasoning.novel_synthesizer import NovelCombinationSynthesizer
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
        self.planets_by_name = self._load_planets()
        self.novel_synthesizer = NovelCombinationSynthesizer(self.ontology_dir)

    def analyze_house(self, chart_id: str, house: int) -> dict[str, Any] | None:
        house_data = self.houses_by_number.get(house)
        lord_data = self.get_house_lord(chart_id, house)
        if house_data is None or lord_data is None:
            return None
        lord_name = str(lord_data["lord"])
        placement = self.get_placement_of(chart_id, lord_name)
        if placement is None:
            return None
        placement_house = int(placement["house"])
        placement_data = self.houses_by_number.get(placement_house, {})
        theme = self._theme_for_house(house, house_data)
        supporting_rules = self.find_supporting_rules(chart_id, house, lord_name)
        aspects = self.get_aspects_to(chart_id, lord_name)
        conjunctions = self.get_conjunctions(chart_id, lord_name)
        occupied_by = [
            planet for planet in self.chart_queries.get_planets_in_house(chart_id, house) if planet != lord_name
        ]
        dispositor_chain = self.get_dispositor_chain(chart_id, lord_name)
        analogous_rules = self.find_analogous_rules(
            chart_id=chart_id,
            house=house,
            lord=lord_name,
            placement_house=placement_house,
            aspect_planets=[str(item["from_planet"]) for item in aspects],
        )
        facts = self._build_facts(
            chart_id=chart_id,
            house=house,
            theme=theme,
            house_data=house_data,
            lord_data=lord_data,
            placement=placement,
            placement_data=placement_data,
            aspects=aspects,
            conjunctions=conjunctions,
            occupied_by=occupied_by,
            supporting_rules=supporting_rules,
            dispositor_chain=dispositor_chain,
        )
        novel_synthesis = self.novel_synthesizer.synthesize_house(
            house_number=house,
            lord_name=lord_name,
            placement_house=placement_house,
            aspects=aspects,
            conjunctions=conjunctions,
            occupied_by=occupied_by,
            analogous_rules=analogous_rules,
        )
        confidence = self._compute_confidence(facts, supporting_rules)
        rank_score = self._compute_rank_score(facts, house_data, supporting_rules)
        reasoning_chain = [
            f"House {house} signifies {self._format_meanings(house_data.get('primary_meanings', []), limit=3)}.",
            f"The lord is {lord_name} in House {placement_house}.",
            f"The lord's dignity is {lord_data['lord_dignity']}.",
            f"House {placement_house} adds {self._format_meanings(placement_data.get('primary_meanings', []), limit=3)}.",
        ]
        if aspects:
            reasoning_chain.append(
                "Aspects to the lord: "
                + ", ".join(f"{item['from_planet']} ({item['type']})" for item in aspects)
                + "."
            )
        if conjunctions:
            reasoning_chain.append(
                "Conjunctions with the lord: "
                + ", ".join(f"{item['planet']} (orb {item['orb']})" for item in conjunctions)
                + "."
            )
        if dispositor_chain:
            reasoning_chain.append(
                "Dispositor chain: " + " -> ".join(item["planet"] for item in dispositor_chain) + "."
            )
        synthesis = self._build_synthesis(
            house=house,
            theme=theme,
            lord=lord_name,
            placement_house=placement_house,
            dignity=str(lord_data["lord_dignity"]),
            house_meanings=house_data.get("primary_meanings", []),
            placement_meanings=placement_data.get("primary_meanings", []),
            aspects=[f"{item['from_planet']} ({item['type']})" for item in aspects],
            conjunctions=[item["planet"] for item in conjunctions],
            occupied_by=occupied_by,
        )
        reasoning_tree = self._build_reasoning_tree(
            synthesis=synthesis,
            facts=facts,
            supporting_rules=supporting_rules,
            confidence=confidence,
            rank_score=rank_score,
        )
        return {
            "house": house,
            "theme": theme,
            "lord": lord_name,
            "lord_placement": f"House {placement_house}",
            "lord_dignity": lord_data["lord_dignity"],
            "synthesis": synthesis,
            "supporting_rules": supporting_rules,
            "reasoning_chain": reasoning_chain,
            "occupied_by": occupied_by,
            "dispositor_chain": dispositor_chain,
            "analogous_rules": analogous_rules,
            "novel_synthesis": novel_synthesis,
            "facts": [fact.to_dict() for fact in facts],
            "contradictions": [fact.content for fact in facts if fact.contradictions],
            "confidence": confidence,
            "rank_score": rank_score,
            "reasoning_tree": reasoning_tree.to_dict(),
        }

    def get_house_lord(self, chart_id: str, house: int) -> dict[str, Any] | None:
        return self.chart_queries.get_house_lord(chart_id, house)

    def get_placement_of(self, chart_id: str, planet: str) -> dict[str, Any] | None:
        return self.chart_queries.get_planet_placement(chart_id, planet)

    def get_aspects_to(self, chart_id: str, planet: str) -> list[dict[str, Any]]:
        return self.chart_queries.get_aspects_to_planet(chart_id, planet)

    def get_conjunctions(self, chart_id: str, planet: str) -> list[dict[str, Any]]:
        return self.chart_queries.get_conjunctions(chart_id, planet)

    def get_dispositor_chain(self, chart_id: str, planet: str) -> list[dict[str, Any]]:
        return self.chart_queries.get_dispositor_chain(chart_id, planet)

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

    def find_analogous_rules(
        self,
        chart_id: str,
        house: int,
        lord: str,
        placement_house: int,
        aspect_planets: list[str],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        del chart_id, aspect_planets
        with self.neo4j_client.driver.session() as session:
            result = session.run(
                """
                MATCH (r:Rule)-[:REFERS_TO]->(:Planet {name: $lord})
                MATCH (r)-[:REFERS_TO]->(:House {name: $placement_house_name})
                RETURN r.rule_id AS rule_id,
                       r.effect_summary AS effect_summary,
                       r.source_text AS source_text,
                       r.confidence AS confidence
                ORDER BY r.confidence DESC, r.rule_id
                LIMIT $limit
                """,
                lord=lord,
                placement_house_name=f"HOUSE_{placement_house}",
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

    def _load_planets(self) -> dict[str, dict[str, Any]]:
        with (self.ontology_dir / "planets.json").open(encoding="utf-8") as handle:
            payload = json.load(handle)
        return {
            str(item["canonical_name"]): item
            for item in payload["planets"]
            if isinstance(item, dict) and item.get("canonical_name")
        }

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
        conjunctions: list[str],
        occupied_by: list[str],
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
        if conjunctions:
            parts.append(f"Conjunction with {', '.join(conjunctions)} further shapes the outcome.")
        if occupied_by:
            parts.append(f"Direct occupancy by {', '.join(occupied_by)} intensifies the house.")
        return " ".join(parts)

    def _build_facts(
        self,
        chart_id: str,
        house: int,
        theme: str,
        house_data: dict[str, Any],
        lord_data: dict[str, Any],
        placement: dict[str, Any],
        placement_data: dict[str, Any],
        aspects: list[dict[str, Any]],
        conjunctions: list[dict[str, Any]],
        occupied_by: list[str],
        supporting_rules: list[dict[str, Any]],
        dispositor_chain: list[dict[str, Any]],
    ) -> list[ReasoningFact]:
        del chart_id
        rule_ids = [str(rule["rule_id"]) for rule in supporting_rules]
        house_weight = float(house_data.get("importance_weight", 0.5))
        lord_name = str(lord_data["lord"])
        lord_strength = float(lord_data.get("lord_strength", 0.0))
        placement_house = int(placement["house"])
        lord_profile = self.planets_by_name.get(lord_name, {})
        facts = [
            ReasoningFact(
                id=f"house-{house}-base",
                type="house_meaning",
                source_step="house_profile",
                entities_involved=[f"HOUSE_{house}"],
                content=f"House {house} primarily governs {self._format_meanings(house_data.get('primary_meanings', []), 3)}.",
                strength_weight=house_weight,
                confidence=0.95,
                supporting_rules=rule_ids,
            ),
            ReasoningFact(
                id=f"house-{house}-lord",
                type="lord_identity",
                source_step="house_lord",
                entities_involved=[f"HOUSE_{house}", lord_name],
                content=f"{lord_name} rules House {house} and carries {theme.lower()} themes.",
                strength_weight=max(house_weight, lord_strength),
                confidence=0.9,
                supporting_rules=rule_ids,
            ),
            ReasoningFact(
                id=f"house-{house}-placement",
                type="lord_placement",
                source_step="lord_placement",
                entities_involved=[lord_name, f"HOUSE_{placement_house}"],
                content=(
                    f"{lord_name} is placed in House {placement_house}, linking {theme.lower()} "
                    f"to {self._format_meanings(placement_data.get('primary_meanings', []), 3)}."
                ),
                strength_weight=max(lord_strength, 0.5),
                confidence=0.88,
                supporting_rules=rule_ids,
            ),
        ]
        if lord_profile:
            facts.append(
                ReasoningFact(
                    id=f"house-{house}-nature",
                    type="lord_nature",
                    source_step="lord_nature",
                    entities_involved=[lord_name],
                    content=(
                        f"{lord_name} adds {self._format_meanings(lord_profile.get('natural_karakatvam', []), 3)} "
                        f"with a {lord_profile.get('nature', 'neutral')} temperament."
                    ),
                    strength_weight=max(lord_strength, 0.5),
                    confidence=0.84,
                    supporting_rules=rule_ids,
                )
            )
        facts.append(
            ReasoningFact(
                id=f"house-{house}-strength",
                type="strength_modifier",
                source_step="strength_assessment",
                entities_involved=[lord_name],
                content=f"{lord_name} shows {lord_data['lord_dignity']} dignity with strength modifier {lord_strength:.2f}.",
                strength_weight=lord_strength,
                confidence=0.9,
                supporting_rules=rule_ids,
                contradictions=[] if lord_strength >= 0 else [f"{lord_name} is weakened"],
            )
        )
        for aspect in aspects:
            aspect_planet = str(aspect["from_planet"])
            strength = float(aspect.get("strength", 0.0))
            contradictions = [f"{aspect_planet} is strongly malefic to the lord"] if strength < 0 else []
            facts.append(
                ReasoningFact(
                    id=f"house-{house}-aspect-{aspect_planet.lower()}",
                    type="aspect_influence",
                    source_step="aspect_analysis",
                    entities_involved=[aspect_planet, lord_name],
                    content=f"{aspect_planet} aspects {lord_name} through {aspect['type']} with weight {strength:.2f}.",
                    strength_weight=abs(strength),
                    confidence=0.8,
                    supporting_rules=rule_ids,
                    contradictions=contradictions,
                )
            )
        for conjunction in conjunctions:
            conjunct_planet = str(conjunction["planet"])
            orb = float(conjunction.get("orb", 0.0))
            facts.append(
                ReasoningFact(
                    id=f"house-{house}-conjunction-{conjunct_planet.lower()}",
                    type="conjunction_effect",
                    source_step="conjunction_analysis",
                    entities_involved=[lord_name, conjunct_planet],
                    content=f"{lord_name} is conjunct {conjunct_planet} with orb {orb:.2f}.",
                    strength_weight=max(0.1, 10.0 - min(orb, 10.0)) / 10.0,
                    confidence=0.78,
                    supporting_rules=rule_ids,
                )
            )
        for planet in occupied_by:
            facts.append(
                ReasoningFact(
                    id=f"house-{house}-occupant-{planet.lower()}",
                    type="occupant_influence",
                    source_step="house_occupants",
                    entities_involved=[f"HOUSE_{house}", planet],
                    content=f"{planet} directly occupies House {house} and amplifies its events.",
                    strength_weight=house_weight,
                    confidence=0.75,
                    supporting_rules=rule_ids,
                )
            )
        if dispositor_chain:
            facts.append(
                ReasoningFact(
                    id=f"house-{house}-dispositor",
                    type="dispositor_chain",
                    source_step="dispositor_analysis",
                    entities_involved=[lord_name] + [str(item["planet"]) for item in dispositor_chain],
                    content="Dispositor chain flows through " + " -> ".join(str(item["planet"]) for item in dispositor_chain) + ".",
                    strength_weight=0.7,
                    confidence=0.72,
                    supporting_rules=rule_ids,
                )
            )
        return facts

    def _compute_confidence(
        self,
        facts: list[ReasoningFact],
        supporting_rules: list[dict[str, Any]],
    ) -> float:
        if not facts:
            return 0.0
        fact_confidence = sum(fact.confidence for fact in facts) / len(facts)
        if not supporting_rules:
            return round(fact_confidence * 0.85, 3)
        rule_confidence = sum(float(rule.get("confidence", 0.0)) for rule in supporting_rules) / len(supporting_rules)
        normalized_rule_confidence = min(rule_confidence / 5.0, 1.0)
        return round((fact_confidence * 0.65) + (normalized_rule_confidence * 0.35), 3)

    def _compute_rank_score(
        self,
        facts: list[ReasoningFact],
        house_data: dict[str, Any],
        supporting_rules: list[dict[str, Any]],
    ) -> float:
        fact_weight = sum(fact.strength_weight for fact in facts)
        rule_confidence = sum(float(rule.get("confidence", 0.0)) for rule in supporting_rules)
        importance = float(house_data.get("importance_weight", 0.5))
        return round((fact_weight * 0.6) + (rule_confidence * 0.25) + (importance * 10 * 0.15), 3)

    def _build_reasoning_tree(
        self,
        synthesis: str,
        facts: list[ReasoningFact],
        supporting_rules: list[dict[str, Any]],
        confidence: float,
        rank_score: float,
    ) -> ReasoningNode:
        children = [
            ReasoningNode(
                statement=fact.content,
                confidence=fact.confidence,
                strength_score=fact.strength_weight,
                supporting_facts=[SupportingFact(fact=fact.content, source=fact.source_step)],
                classical_rules_applied=[],
                novel_synthesis=not bool(fact.supporting_rules),
                children=[],
            )
            for fact in facts
        ]
        return ReasoningNode(
            statement=synthesis,
            confidence=confidence,
            strength_score=rank_score,
            supporting_facts=[
                SupportingFact(fact=fact.content, source=fact.source_step) for fact in facts[:5]
            ],
            classical_rules_applied=supporting_rules,
            novel_synthesis=not bool(supporting_rules),
            children=children,
        )

    def _format_meanings(self, values: list[str], limit: int) -> str:
        cleaned = [str(value).replace("_", " ") for value in values[:limit]]
        return ", ".join(cleaned) if cleaned else "its core themes"
