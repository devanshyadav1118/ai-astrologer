"""Compatibility adapter coverage."""

from __future__ import annotations

import json
from pathlib import Path

from extractor.adapter import adapt_extraction_payload, adapt_rule, adapt_yoga
from normaliser.validator import RuleValidator


def test_adapter_transforms_external_rule_to_canonical_schema() -> None:
    payload = {
        "rules": [
            {
                "id": "rule_001",
                "original_text": "If Saturn is in the 7th house, marriage is delayed.",
                "conditions": {
                    "logic_block": {
                        "operator": "AND",
                        "clauses": [
                            {"type": "placement", "planet": "Saturn", "house": 7},
                        ],
                    }
                },
                "effects": [
                    {
                        "category": "status",
                        "description": "Delayed marriage",
                        "impact": "Negative",
                        "intensity": "High",
                        "probability": "Likely",
                    }
                ],
                "metadata": {"source": "Test Book"},
            }
        ]
    }

    adapted = adapt_extraction_payload(payload, {"chunk_id": "chunk_001", "book_id": "test_book"})
    rule = adapted["rules"][0]

    assert rule["rule_id"] == "rule_001"
    assert rule["source_text"] == "If Saturn is in the 7th house, marriage is delayed."
    assert rule["conditions"]["clauses"][0]["type"] == "planet_state"
    assert rule["conditions"]["clauses"][0]["house"] == "HOUSE_7"
    assert rule["effects"][0]["category"] == "social_status"
    assert rule["effects"][0]["impact"] == "negative"


def test_adapter_maps_calculation_methods_to_calculations() -> None:
    payload = {
        "calculation_methods": [
            {"id": "calc_001", "name": "Ashtakavarga", "original_text": "Count bindus.", "steps": [{"step": 1}]}
        ]
    }

    adapted = adapt_extraction_payload(payload, {"chunk_id": "chunk_001", "book_id": "test_book"})

    assert adapted["calculations"][0]["calculation_id"] == "calc_001"
    assert adapted["calculations"][0]["formula_or_method"] == "Ashtakavarga"


def test_adapter_maps_yoga_standard_effects() -> None:
    yoga = {
        "id": "yoga_gajakesari_001",
        "name": "Gajakesari Yoga",
        "original_text": "When Jupiter and Moon are in kendras.",
        "formation_logic": {"operator": "AND", "clauses": [{"type": "relative_placement", "conditions": "Jupiter and Moon in kendras"}]},
        "standard_effects": [{"category": "intelligence", "description": "Enhanced wisdom", "impact": "Positive", "intensity": "High"}],
    }

    adapted = adapt_yoga(yoga, chunk_metadata={"chunk_id": "chunk_001", "book_id": "test_book"})

    assert adapted["yoga_id"] == "yoga_gajakesari_001"
    assert adapted["effects"][0]["category"] == "education"


def test_acceptance_transform_real_external_sample_validates() -> None:
    sample_path = Path("Extraction Automation/output/extracted_data.json")
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    payload = adapt_extraction_payload(sample, {"chunk_id": "acceptance_001", "book_id": "garga_hora"})

    validator = RuleValidator()
    validated = validator.validate_rule(payload["rules"][0])

    assert validated["validation_status"] in {"valid", "warning"}
