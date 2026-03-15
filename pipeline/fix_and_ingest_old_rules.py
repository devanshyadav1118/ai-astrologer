
"""
pipeline/fix_and_ingest_old_rules.py

Migrates existing 2000 raw extracted rules into the canonical schema:
  1. Flattens nested JSON chunk files into individual rule dicts
  2. Normalises all entity names (planet/sign/house) to canonical form
  3. Verifies each entity exists in the ontology
  4. Generates rule fingerprints for cross-book deduplication
  5. Builds neo4j relationship hints
  6. Loads into Neo4j as Rule nodes linked to Planet / Sign / House entities
  7. Produces a full migration report
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from neo4j import GraphDatabase

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from normaliser.normaliser import AstrologyNormaliser

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Initialize Global Normaliser
NORMALISER = AstrologyNormaliser()

VALID_PLANETS = {"SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN", "RAHU", "KETU"}
VALID_SIGNS = {"ARIES", "TAURUS", "GEMINI", "CANCER", "LEO", "VIRGO", "LIBRA", "SCORPIO", "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES"}
VALID_HOUSES = {f"HOUSE_{i}" for i in range(1, 13)}

def normalise(raw: str | None) -> str | None:
    """Map any raw entity string to its canonical form using the project's normaliser."""
    if not raw:
        return None
    
    # Handle numeric house strings "1" -> "HOUSE_1"
    if isinstance(raw, str) and raw.isdigit() and 1 <= int(raw) <= 12:
        return f"HOUSE_{raw}"
        
    return NORMALISER.normalise(raw)

# ──────────────────────────────────────────────────────────────────────────────
# 2.  EFFECT CATEGORY → HOUSE MAPPING
# ──────────────────────────────────────────────────────────────────────────────

EFFECT_CATEGORY_TO_HOUSE: dict[str, str] = {
    "wealth":       "HOUSE_2",
    "family":       "HOUSE_2",
    "communication":"HOUSE_3",
    "siblings":     "HOUSE_3",
    "property":     "HOUSE_4",
    "mother":       "HOUSE_4",
    "children":     "HOUSE_5",
    "intelligence": "HOUSE_5",
    "education":    "HOUSE_5",
    "enemies":      "HOUSE_6",
    "health":       "HOUSE_6",
    "disease":      "HOUSE_6",
    "marriage":     "HOUSE_7",
    "partner":      "HOUSE_7",
    "longevity":    "HOUSE_8",
    "obstacles":    "HOUSE_8",
    "fortune":      "HOUSE_9",
    "dharma":       "HOUSE_9",
    "career":       "HOUSE_10",
    "status":       "HOUSE_10",
    "gains":        "HOUSE_11",
    "income":       "HOUSE_11",
    "loss":         "HOUSE_12",
    "spirituality": "HOUSE_12",
    "fame":         "HOUSE_1",
    "self":         "HOUSE_1",
    "personality":  "HOUSE_1",
    "sons":         "HOUSE_5",
}


def map_effect_to_house(category: str | None) -> str | None:
    if not category:
        return None
    return EFFECT_CATEGORY_TO_HOUSE.get(category.lower().strip())


# ──────────────────────────────────────────────────────────────────────────────
# 3.  FINGERPRINT GENERATION
# ──────────────────────────────────────────────────────────────────────────────

def _extract_canonical_entities_from_conditions(logic_block: dict) -> list[str]:
    """Recursively collect all canonical entity references from a logic block."""
    entities: list[str] = []
    if not logic_block:
        return entities

    clauses = logic_block.get("clauses", [])
    for clause in clauses:
        # Recurse into nested logic blocks
        if "operator" in clause:
            entities.extend(_extract_canonical_entities_from_conditions(clause))
            continue

        for key in ("planet", "planet_a", "planet_b", "sign", "house"):
            val = clause.get(key)
            if val:
                norm = normalise(val)
                if norm:
                    entities.append(norm)

    return entities


def generate_fingerprint(rule: dict) -> str:
    """
    Deterministic fingerprint from canonical condition entities.
    Rules with the same fingerprint are the same logical rule from different books.
    """
    logic_block = rule.get("conditions", {}).get("logic_block", {})
    entities = sorted(set(_extract_canonical_entities_from_conditions(logic_block)))
    effects = sorted(
        e.get("category", "").upper()
        for e in rule.get("effects", [])
        if e.get("category")
    )
    raw = "_".join(entities + effects)
    if not raw:
        # Fallback: hash the original text
        raw = rule.get("original_text", rule.get("id", "unknown"))
    return hashlib.md5(raw.encode()).hexdigest()[:16].upper()


# ──────────────────────────────────────────────────────────────────────────────
# 4.  CLAUSE NORMALISATION
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class NormResult:
    normalised_clause: dict
    unknowns: list[str] = field(default_factory=list)


def normalise_clause(clause: dict) -> NormResult:
    """Normalise all entity fields in a single clause dict. Returns raw as fallback."""
    c = dict(clause)
    unknowns: list[str] = []

    entity_fields = ("planet", "planet_a", "planet_b", "sign", "house")
    raw_prefix = "raw_"

    for field_name in entity_fields:
        raw_val = c.get(field_name)
        if raw_val is None:
            continue
        canonical = normalise(raw_val)
        if canonical:
            c[raw_prefix + field_name] = raw_val   # preserve original
            c[field_name] = canonical
        else:
            unknowns.append(f"{field_name}:{raw_val}")

    # Recurse into nested logic
    if "clauses" in c:
        nested_unknowns: list[str] = []
        new_clauses = []
        for sub in c["clauses"]:
            r = normalise_clause(sub)
            new_clauses.append(r.normalised_clause)
            nested_unknowns.extend(r.unknowns)
        c["clauses"] = new_clauses
        unknowns.extend(nested_unknowns)

    return NormResult(normalised_clause=c, unknowns=unknowns)


def normalise_conditions(conditions: dict) -> tuple[dict, list[str]]:
    logic_block = conditions.get("logic_block", {})
    all_unknowns: list[str] = []

    if "clauses" in logic_block:
        new_clauses = []
        for clause in logic_block["clauses"]:
            r = normalise_clause(clause)
            new_clauses.append(r.normalised_clause)
            all_unknowns.extend(r.unknowns)
        logic_block = {**logic_block, "clauses": new_clauses}

    new_conditions = {**conditions, "logic_block": logic_block}
    return new_conditions, all_unknowns


def normalise_effects(effects: list[dict]) -> list[dict]:
    """Uppercase category/impact/intensity/probability and add life_area."""
    out = []
    for e in effects:
        ne = dict(e)
        for field_name in ("category", "impact", "intensity", "probability"):
            if ne.get(field_name):
                ne[field_name] = str(ne[field_name]).upper()
        if not ne.get("life_area"):
            ne["life_area"] = map_effect_to_house(ne.get("category"))
        out.append(ne)
    return out


# ──────────────────────────────────────────────────────────────────────────────
# 5.  NEO4J RELATIONSHIP BUILDER
# ──────────────────────────────────────────────────────────────────────────────

def build_neo4j_hints(rule: dict) -> dict:
    """
    Pre-compute every Neo4j relationship this rule needs so the loader
    doesn't have to re-parse conditions.
    """
    logic_block = rule.get("conditions", {}).get("logic_block", {})
    entities = set(_extract_canonical_entities_from_conditions(logic_block))

    relationships: list[dict[str, str]] = []

    for entity in entities:
        if entity in VALID_PLANETS:
            relationships.append({"type": "INVOLVES_PLANET", "target": entity})
        elif entity in VALID_SIGNS:
            relationships.append({"type": "INVOLVES_SIGN",   "target": entity})
        elif entity in VALID_HOUSES:
            relationships.append({"type": "INVOLVES_HOUSE",  "target": entity})

    for effect in rule.get("effects", []):
        cat = effect.get("category")
        if cat:
            relationships.append({"type": "AFFECTS_LIFE_AREA", "target": cat})
        area = effect.get("life_area")
        if area:
            relationships.append({"type": "PRIMARILY_AFFECTS_HOUSE", "target": area})

    confidence = rule.get("confidence", {})
    sources = confidence.get("sources", [{}])
    source = sources[0] if sources else {}
    book_id = source.get("book_id") or "unknown_source"
    relationships.append({"type": "SOURCE", "target": book_id})

    # Deduplicate
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for r in relationships:
        key = f"{r['type']}:{r['target']}"
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return {"node_label": "Rule", "relationships": unique}


# ──────────────────────────────────────────────────────────────────────────────
# 6.  FULL RULE TRANSFORMER
# ──────────────────────────────────────────────────────────────────────────────

def transform_rule(raw_rule: dict) -> dict:
    """
    Transform a single raw rule dict into the canonical schema.
    Returns the enriched rule dict.
    """
    new_rule = dict(raw_rule)
    
    # Standardize input keys
    if "original_text" not in new_rule and "source_text" in new_rule:
        new_rule["original_text"] = new_rule["source_text"]
    
    if "original_text" not in new_rule:
        new_rule["original_text"] = "No source text provided"

    # ── Normalise conditions ─────────────────────────────────────────────────
    conditions = new_rule.get("conditions", {})
    if not conditions:
        conditions = {"logic_block": {"operator": "AND", "clauses": []}}
    
    norm_conditions, unknowns = normalise_conditions(conditions)
    new_rule["conditions"] = norm_conditions

    # ── Normalise effects ────────────────────────────────────────────────────
    new_rule["effects"] = normalise_effects(new_rule.get("effects", []))

    # ── Uppercase tags ───────────────────────────────────────────────────────
    new_rule["tags"] = [str(t).upper() for t in new_rule.get("tags", [])]

    # ── Confidence block ─────────────────────────────────────────────────────
    meta = new_rule.get("metadata", {})
    existing_confidence = new_rule.get("confidence", {})

    if not existing_confidence:
        book_title = meta.get("source", "UNKNOWN")
        book_id = (
            str(book_title).lower()
            .replace(" ", "_")
            .replace("by", "")
            .strip("_")[:40]
        )
        new_rule["confidence"] = {
            "score": 0.3,
            "level": "LOW",
            "source_count": 1,
            "sources": [
                {
                    "book_id":    book_id,
                    "book_title": book_title,
                    "author":     meta.get("author", ""),
                    "stanza":     meta.get("stanza"),
                    "chapter":    meta.get("chapter"),
                    "tier":       meta.get("tier", 2),
                }
            ],
            "empirically_validated": False,
            "validation_status": "UNTESTED",
        }

    # ── Fingerprint ──────────────────────────────────────────────────────────
    new_rule["rule_fingerprint"] = generate_fingerprint(new_rule)

    # ── Neo4j hints ──────────────────────────────────────────────────────────
    new_rule["neo4j"] = build_neo4j_hints(new_rule)

    # ── Entities summary on conditions ───────────────────────────────────────
    logic_block = new_rule["conditions"].get("logic_block", {})
    canon_entities = list(set(_extract_canonical_entities_from_conditions(logic_block)))
    new_rule["conditions"]["entities_involved"] = canon_entities

    # ── Normalisation metadata ───────────────────────────────────────────────
    new_rule["normalization_meta"] = {
        "normalized":              True,
        "normalizer_version":      "1.0",
        "unknown_entities":        unknowns,
        "normalization_warnings":  [f"Unknown entity: {u}" for u in unknowns],
    }

    return new_rule


# ──────────────────────────────────────────────────────────────────────────────
# 7.  FILE FLATTENER  (handles multiple nesting patterns)
# ──────────────────────────────────────────────────────────────────────────────

def flatten_rules_from_file(path: Path) -> list[dict]:
    """
    Extract a flat list of raw rule dicts from a JSON file.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        log.warning(f"JSON parse error in {path.name}: {exc}")
        return []

    rules: list[dict] = []

    def _drain(obj: Any) -> None:
        if isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict) and "conditions" in item:
                    rules.append(item)
                elif isinstance(item, dict):
                    _drain(item)
        elif isinstance(obj, dict):
            if "rules" in obj:
                _drain(obj["rules"])
            elif "chunks" in obj:
                _drain(obj["chunks"])
            elif "conditions" in obj:
                rules.append(obj)
            else:
                for v in obj.values():
                    if isinstance(v, (list, dict)):
                        _drain(v)

    _drain(data)
    return rules


# ──────────────────────────────────────────────────────────────────────────────
# 8.  NEO4J LOADER
# ──────────────────────────────────────────────────────────────────────────────

UPSERT_RULE_CYPHER = """
MERGE (r:Rule {rule_fingerprint: $fingerprint})
ON CREATE SET
    r.id                  = $rule_id,
    r.original_text       = $original_text,
    r.confidence_score    = $confidence_score,
    r.confidence_level    = $confidence_level,
    r.source_count        = $source_count,
    r.validation_status   = $validation_status,
    r.full_json           = $full_json,
    r.created_at          = timestamp()
ON MATCH SET
    r.confidence_score    = CASE
        WHEN $confidence_score > r.confidence_score
        THEN $confidence_score
        ELSE r.confidence_score
    END,
    r.source_count        = r.source_count + 1,
    r.updated_at          = timestamp()
RETURN r.rule_fingerprint AS fp, (r.source_count > 1) AS was_merged
"""

LINK_ENTITY_CYPHER = """
MATCH  (r:Rule {rule_fingerprint: $fingerprint})
MATCH  (e {name: $entity_name})
MERGE  (r)-[:{rel_type}]->(e)
"""


def load_rule_to_neo4j(tx, rule: dict) -> bool:
    """Execute all Cypher for one rule inside a transaction. Returns True on success."""
    if "rule_fingerprint" not in rule:
        log.error(f"Rule missing fingerprint! Keys: {list(rule.keys())}")
        return False
    try:
        confidence = rule.get("confidence", {})
        tx.run(
            UPSERT_RULE_CYPHER,
            fingerprint=rule["rule_fingerprint"],
            rule_id=rule.get("id", ""),
            original_text=rule.get("original_text", ""),
            confidence_score=confidence.get("score", 0.3),
            confidence_level=confidence.get("level", "LOW"),
            source_count=confidence.get("source_count", 1),
            validation_status=confidence.get("validation_status", "UNTESTED"),
            full_json=json.dumps(rule),
        )

        # Link to ontology entities
        for rel in rule.get("neo4j", {}).get("relationships", []):
            rel_type = rel["type"]
            target   = rel["target"]
            # Only link to entities already in graph
            if rel_type in ("INVOLVES_PLANET", "INVOLVES_SIGN", "INVOLVES_HOUSE"):
                tx.run(
                    LINK_ENTITY_CYPHER.format(rel_type=rel_type),
                    fingerprint=rule["rule_fingerprint"],
                    entity_name=target,
                )
        return True

    except Exception as exc:
        log.error(f"Neo4j error for rule {rule.get('id')}: {exc}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# 9.  MIGRATION REPORT
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class MigrationStats:
    total_files:      int = 0
    total_raw_rules:  int = 0
    transformed_ok:   int = 0
    with_unknowns:    int = 0
    neo4j_loaded:     int = 0
    neo4j_failed:     int = 0
    unknown_entities: dict = field(default_factory=dict)   # entity → count
    failed_rule_ids:  list = field(default_factory=list)

    def record_unknowns(self, unknowns: list[str]) -> None:
        for u in unknowns:
            self.unknown_entities[u] = self.unknown_entities.get(u, 0) + 1

    def to_dict(self) -> dict:
        return {
            "summary": {
                "total_files":      self.total_files,
                "total_raw_rules":  self.total_raw_rules,
                "transformed_ok":   self.transformed_ok,
                "with_unknowns":    self.with_unknowns,
                "neo4j_loaded":     self.neo4j_loaded,
                "neo4j_failed":     self.neo4j_failed,
                "unknown_rate_pct": round(
                    self.with_unknowns / max(self.total_raw_rules, 1) * 100, 2
                ),
            },
            "unknown_entities_ranked": sorted(
                [{"entity": k, "count": v}
                 for k, v in self.unknown_entities.items()],
                key=lambda x: -x["count"],
            ),
            "failed_rule_ids": self.failed_rule_ids,
            "action_required": (
                "Add these to normaliser/ontology files, then re-run."
                if self.unknown_entities else "None — all entities resolved."
            ),
        }


# ──────────────────────────────────────────────────────────────────────────────
# 10.  MAIN ENTRYPOINT
# ──────────────────────────────────────────────────────────────────────────────

def main(input_path_str: str, report_path: str, dry_run: bool) -> None:
    input_path = Path(input_path_str)
    if not input_path.exists():
        log.error(f"Input path not found: {input_path}")
        sys.exit(1)

    if input_path.is_dir():
        json_files = sorted(input_path.rglob("*.json"))
    else:
        json_files = [input_path]

    if not json_files:
        log.error(f"No JSON files found at {input_path}")
        sys.exit(1)

    log.info(f"Found {len(json_files)} JSON file(s)")

    driver = None
    if not dry_run:
        neo4j_uri  = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_pass = os.getenv("NEO4J_PASSWORD", "password")
        try:
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
            driver.verify_connectivity()
            log.info(f"Connected to Neo4j at {neo4j_uri}")
        except Exception as exc:
            log.error(f"Neo4j connection failed: {exc}")
            sys.exit(1)

    stats = MigrationStats(total_files=len(json_files))
    transformed_rules: list[dict] = []

    for json_file in json_files:
        log.info(f"Processing: {json_file.name}")
        raw_rules = flatten_rules_from_file(json_file)
        log.info(f"  → {len(raw_rules)} rules extracted")
        stats.total_raw_rules += len(raw_rules)

        for raw in raw_rules:
            try:
                rule = transform_rule(raw)
                # Ensure fingerprint is present for Neo4j
                if "rule_fingerprint" not in rule:
                    rule["rule_fingerprint"] = generate_fingerprint(rule)
                
                unknowns = rule["normalization_meta"]["unknown_entities"]

                stats.transformed_ok += 1
                if unknowns:
                    stats.with_unknowns += 1
                    stats.record_unknowns(unknowns)

                transformed_rules.append(rule)
            except Exception as exc:
                log.warning(f"Transform failed for rule {raw.get('id', '?')}: {exc}")
                stats.failed_rule_ids.append(raw.get("id", "unknown"))

    if not dry_run and driver:
        log.info("Loading rules into Neo4j...")
        with driver.session() as session:
            for rule in transformed_rules:
                success = session.execute_write(load_rule_to_neo4j, rule)
                if success:
                    stats.neo4j_loaded += 1
                else:
                    stats.neo4j_failed += 1
                    stats.failed_rule_ids.append(rule.get("id", "?"))
        driver.close()
    else:
        stats.neo4j_loaded = stats.transformed_ok

    report = stats.to_dict()
    report["transformed_rules_sample"] = transformed_rules[:3]

    report_file = Path(report_path)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    log.info(f"Migration report written to: {report_file}")

    s = report["summary"]
    log.info("\n" + "=" * 55)
    log.info(f"  Raw rules found       : {s['total_raw_rules']}")
    log.info(f"  Successfully transformed: {s['transformed_ok']}")
    log.info(f"  Rules with unknowns   : {s['with_unknowns']}  ({s['unknown_rate_pct']}%)")
    log.info(f"  Target Neo4j Load     : {s['neo4j_loaded']}")
    log.info("=" * 55)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate rules to canonical schema")
    parser.add_argument("--input", default="data/extracted/all_rules_merged.json")
    parser.add_argument("--report", default="data/migration_report.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(args.input, args.report, args.dry_run)
