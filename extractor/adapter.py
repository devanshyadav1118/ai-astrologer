"""Compatibility adapter for extractor payload variants."""

from __future__ import annotations

from copy import deepcopy
import json
import re
from typing import Any


CATEGORY_ALIASES = {
    "status": "social_status",
    "intelligence": "education",
}
IMPACT_ALIASES = {
    "positive": "positive",
    "negative": "negative",
    "mixed": "neutral",
    "neutral": "neutral",
}
INTENSITY_ALIASES = {
    "high": "high",
    "medium": "medium",
    "low": "low",
    "variable": "medium",
}
PROBABILITY_ALIASES = {
    "certain": "certain",
    "likely": "likely",
    "possible": "possible",
    "conditional": "conditional",
}
CLAUSE_TYPE_ALIASES = {
    "placement": "planet_state",
    "conjunction": "conjunction",
    "yoga_check": "other",
    "relative_placement": "other",
    "logic_block": "other",
}


def adapt_extraction_payload(
    payload: dict[str, Any],
    chunk_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convert extractor payload variants into the canonical downstream contract."""
    canonical = deepcopy(payload)
    calculations = canonical.pop("calculation_methods", canonical.get("calculations", []))
    canonical["rules"] = [
        adapt_rule(rule, index=index, chunk_metadata=chunk_metadata)
        for index, rule in enumerate(canonical.get("rules", []), start=1)
        if isinstance(rule, dict)
    ]
    canonical["yogas"] = [
        adapt_yoga(yoga, index=index, chunk_metadata=chunk_metadata)
        for index, yoga in enumerate(canonical.get("yogas", []), start=1)
        if isinstance(yoga, dict)
    ]
    canonical["descriptions"] = [
        adapt_description(description, index=index, chunk_metadata=chunk_metadata)
        for index, description in enumerate(canonical.get("descriptions", []), start=1)
        if isinstance(description, dict)
    ]
    canonical["calculations"] = [
        adapt_calculation(calculation, index=index, chunk_metadata=chunk_metadata)
        for index, calculation in enumerate(calculations or [], start=1)
        if isinstance(calculation, dict)
    ]
    return canonical


def adapt_rule(
    rule: dict[str, Any],
    index: int = 1,
    chunk_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convert either canonical or external extractor rule schema to canonical schema."""
    source_book = _source_book(rule, chunk_metadata)
    if not _looks_external_rule(rule):
        canonical = deepcopy(rule)
    else:
        logic = _extract_logic_block(rule.get("conditions", {}))
        canonical = {
            "schema_version": "2.0",
            "rule_id": str(rule.get("id") or _generated_id(chunk_metadata, "rule", index)),
            "type": str(rule.get("type") or "prediction").casefold(),
            "source_text": str(rule.get("original_text") or rule.get("source_text") or ""),
            "condition_text": str(rule.get("condition_text") or _derive_condition_text(logic, rule)),
            "conditions": adapt_logic_block(logic),
            "effects": [adapt_effect(effect) for effect in rule.get("effects", []) if isinstance(effect, dict)],
            "metadata": {
                "source_book": source_book,
                "confidence": _coerce_confidence(rule.get("metadata", {}).get("confidence", 1.0)),
                "author": rule.get("metadata", {}).get("author"),
                "stanza": rule.get("metadata", {}).get("stanza"),
            },
            "tags": list(rule.get("tags", [])) if isinstance(rule.get("tags"), list) else [],
        }
    canonical.setdefault("schema_version", "2.0")
    canonical["conditions"] = adapt_logic_block(canonical.get("conditions", {}))
    canonical["effects"] = [
        adapt_effect(effect) for effect in canonical.get("effects", []) if isinstance(effect, dict)
    ]
    canonical.setdefault("metadata", {})
    canonical["metadata"]["source_book"] = canonical["metadata"].get("source_book") or source_book
    canonical["metadata"]["confidence"] = _coerce_confidence(canonical["metadata"].get("confidence", 1.0))
    return canonical


def adapt_yoga(
    yoga: dict[str, Any],
    index: int = 1,
    chunk_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize yoga payload variants."""
    name = str(yoga.get("name") or yoga.get("canonical_name") or yoga.get("id") or f"yoga_{index}")
    yoga_id = str(yoga.get("yoga_id") or yoga.get("id") or _generated_id(chunk_metadata, "yoga", index))
    formation_logic = adapt_logic_block(yoga.get("formation_logic", yoga.get("conditions", {})))
    standard_effects = yoga.get("standard_effects", yoga.get("effects", []))
    return {
        "yoga_id": yoga_id,
        "name": name,
        "description": str(yoga.get("original_text") or yoga.get("description") or ""),
        "formation_logic": formation_logic,
        "effects": [adapt_effect(effect) for effect in standard_effects if isinstance(effect, dict)],
        "metadata": {
            "source_book": _source_book(yoga, chunk_metadata),
            "author": yoga.get("metadata", {}).get("author"),
        },
    }


def adapt_description(
    description: dict[str, Any],
    index: int = 1,
    chunk_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize description payload variants."""
    return {
        "description_id": str(description.get("id") or _generated_id(chunk_metadata, "description", index)),
        "text": str(description.get("original_text") or description.get("text") or ""),
        "topic": str(description.get("entity_name") or description.get("topic") or description.get("entity_type") or ""),
        "entity_type": description.get("entity_type"),
        "attributes": deepcopy(description.get("attributes", {})),
        "metadata": {
            "source_book": _source_book(description, chunk_metadata),
            "author": description.get("metadata", {}).get("author"),
        },
    }


def adapt_calculation(
    calculation: dict[str, Any],
    index: int = 1,
    chunk_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize calculation payload variants."""
    return {
        "calculation_id": str(calculation.get("id") or _generated_id(chunk_metadata, "calculation", index)),
        "text": str(calculation.get("original_text") or calculation.get("text") or ""),
        "formula_or_method": str(calculation.get("name") or calculation.get("formula_or_method") or calculation.get("purpose") or ""),
        "inputs": deepcopy(calculation.get("steps", calculation.get("inputs", []))),
        "metadata": {
            "source_book": _source_book(calculation, chunk_metadata),
            "author": calculation.get("metadata", {}).get("author"),
        },
    }


def adapt_logic_block(logic: Any) -> dict[str, Any]:
    """Normalize external logic blocks into canonical conditions."""
    if not isinstance(logic, dict):
        return {"operator": "AND", "clauses": []}
    operator = str(logic.get("operator", "AND")).upper()
    raw_clauses = logic.get("clauses", [])
    clauses: list[dict[str, Any]] = []
    if isinstance(raw_clauses, list):
        for clause in raw_clauses:
            adapted = adapt_clause(clause)
            if adapted is not None:
                clauses.append(adapted)
    elif isinstance(raw_clauses, dict):
        adapted = adapt_clause(raw_clauses)
        if adapted is not None:
            clauses.append(adapted)
    return {"operator": operator if operator in {"AND", "OR"} else "AND", "clauses": clauses}


def adapt_clause(clause: Any) -> dict[str, Any] | None:
    """Normalize one clause object."""
    if not isinstance(clause, dict):
        return None
    if "raw_text" in clause and "type" in clause:
        canonical = deepcopy(clause)
        canonical["type"] = _canonical_clause_type(str(canonical.get("type")))
        if "house" in canonical:
            canonical["house"] = _canonical_house(canonical["house"])
        if "planets" in canonical and isinstance(canonical["planets"], list):
            canonical["planets"] = [str(planet) for planet in canonical["planets"]]
        return canonical

    clause_type = _canonical_clause_type(str(clause.get("type", "other")))
    if clause.get("type") == "logic_block" or "clauses" in clause:
        return {
            "type": "other",
            "raw_text": json.dumps(clause, ensure_ascii=True, sort_keys=True),
        }

    raw_text = _clause_raw_text(clause)
    canonical: dict[str, Any] = {"type": clause_type, "raw_text": raw_text}
    if clause_type == "planet_state":
        if "planet" in clause:
            canonical["planet"] = str(clause["planet"])
        if "sign" in clause:
            canonical["sign"] = str(clause["sign"])
        if "house" in clause:
            canonical["house"] = _canonical_house(clause["house"])
        if "relation_to_sign" in clause:
            canonical["type"] = "dignity"
            canonical["dignity_state"] = str(clause["relation_to_sign"])
    elif clause_type == "conjunction":
        planets = clause.get("planets", [])
        canonical["planets"] = [str(planet) for planet in planets] if isinstance(planets, list) else []
        if canonical["planets"]:
            canonical["planet"] = canonical["planets"][0]
    elif clause_type == "aspect":
        canonical["aspect_type"] = str(clause.get("aspect_type") or clause.get("conditions") or "aspect")
        if "planet" in clause:
            canonical["planet"] = str(clause["planet"])
        if "house" in clause:
            canonical["house"] = _canonical_house(clause["house"])
    else:
        for key in ("planet", "sign", "house", "nakshatra", "yoga_id"):
            if key in clause:
                canonical[key] = _canonical_house(clause[key]) if key == "house" else str(clause[key])
    return canonical


def adapt_effect(effect: dict[str, Any]) -> dict[str, Any]:
    """Normalize one effect object to canonical validator enums."""
    category = str(effect.get("category", "")).strip().casefold()
    impact = str(effect.get("impact", "")).strip().casefold()
    intensity = str(effect.get("intensity", "")).strip().casefold()
    probability = str(effect.get("probability", "likely")).strip().casefold()
    return {
        "category": CATEGORY_ALIASES.get(category, category),
        "description": str(effect.get("description", "")).strip(),
        "impact": IMPACT_ALIASES.get(impact, impact),
        "intensity": INTENSITY_ALIASES.get(intensity, intensity),
        "probability": PROBABILITY_ALIASES.get(probability, probability),
        **({"context": effect.get("context")} if effect.get("context") is not None else {}),
    }


def _extract_logic_block(conditions: Any) -> dict[str, Any]:
    if not isinstance(conditions, dict):
        return {"operator": "AND", "clauses": []}
    if "logic_block" in conditions and isinstance(conditions["logic_block"], dict):
        return conditions["logic_block"]
    return conditions


def _clause_raw_text(clause: dict[str, Any]) -> str:
    if isinstance(clause.get("raw_text"), str):
        return str(clause["raw_text"])
    parts: list[str] = []
    for key in ("planet", "sign", "house", "relation_to_sign", "conditions"):
        value = clause.get(key)
        if value is not None:
            parts.append(f"{key}={value}")
    if isinstance(clause.get("planets"), list):
        parts.append("planets=" + ",".join(str(planet) for planet in clause["planets"]))
    return "; ".join(parts) if parts else json.dumps(clause, ensure_ascii=True, sort_keys=True)


def _canonical_clause_type(value: str) -> str:
    return CLAUSE_TYPE_ALIASES.get(value.casefold(), value.casefold() or "other")


def _canonical_house(value: Any) -> str:
    if isinstance(value, int):
        return f"HOUSE_{value}"
    if not isinstance(value, str):
        return str(value)
    stripped = value.strip()
    if re.fullmatch(r"\d+", stripped):
        return f"HOUSE_{stripped}"
    ordinal_match = re.fullmatch(r"(\d+)(?:st|nd|rd|th)(?:\s+house)?", stripped.casefold())
    if ordinal_match:
        return f"HOUSE_{ordinal_match.group(1)}"
    return stripped


def _coerce_confidence(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 1.0
    return max(0.0, min(1.0, numeric))


def _source_book(item: dict[str, Any], chunk_metadata: dict[str, Any] | None) -> str:
    metadata = item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {}
    return str(
        metadata.get("source_book")
        or metadata.get("source")
        or (chunk_metadata or {}).get("book_id")
        or "unknown"
    )


def _generated_id(chunk_metadata: dict[str, Any] | None, prefix: str, index: int) -> str:
    chunk_id = (chunk_metadata or {}).get("chunk_id", "chunk")
    return f"{chunk_id}_{prefix}_{index}"


def _derive_condition_text(logic: dict[str, Any], rule: dict[str, Any]) -> str:
    clauses = logic.get("clauses", []) if isinstance(logic, dict) else []
    if isinstance(clauses, list) and clauses:
        texts = [_clause_raw_text(clause) for clause in clauses if isinstance(clause, dict)]
        if texts:
            return " and ".join(texts)
    return str(rule.get("original_text") or rule.get("source_text") or "")


def _looks_external_rule(rule: dict[str, Any]) -> bool:
    return any(
        key in rule
        for key in ("id", "original_text")
    ) or (
        isinstance(rule.get("conditions"), dict)
        and "logic_block" in rule.get("conditions", {})
    )
 