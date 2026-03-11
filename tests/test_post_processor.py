"""Phase 2 post-processor coverage."""

from __future__ import annotations

from normaliser.post_processor import PostProcessor


def test_normalise_book_data_normalises_rule_entities() -> None:
    processor = PostProcessor()
    raw_data = {
        "book_id": "test_book",
        "rules": [
            {
                "schema_version": "2.0",
                "rule_id": "R-1",
                "type": "prediction",
                "source_text": "If Surya is in Lagna, the native is strong.",
                "conditions": {
                    "operator": "AND",
                    "clauses": [
                        {"raw_text": "Surya is in Lagna", "type": "planet_state", "planet": "Surya", "house": "Lagna"}
                    ],
                },
                "effects": [
                    {
                        "category": "character",
                        "description": "strong nature",
                        "impact": "positive",
                        "intensity": "medium",
                        "probability": "likely",
                    }
                ],
                "metadata": {"source_book": "Test Book"},
            }
        ],
        "yogas": [],
    }

    normalised = processor.normalise_book_data(raw_data)
    rule = normalised["normalised_rules"][0]

    assert rule["conditions"]["clauses"][0]["planet"] == "SUN"
    assert rule["conditions"]["clauses"][0]["house"] == "HOUSE_1"
    assert "SUN" in rule["source_text"]
    assert rule["validation_status"] == "valid"


def test_normalise_book_data_tracks_unknown_entities() -> None:
    processor = PostProcessor()
    raw_data = {
        "book_id": "test_book",
        "rules": [
            {
                "schema_version": "2.0",
                "rule_id": "R-2",
                "type": "prediction",
                "source_text": "FooBar with Guru gives mixed results.",
                "conditions": {
                    "operator": "AND",
                    "clauses": [
                        {"raw_text": "FooBar with Guru", "type": "other", "planet": "FooBar"},
                    ],
                },
                "effects": [
                    {
                        "category": "fortune",
                        "description": "mixed",
                        "impact": "neutral",
                        "intensity": "low",
                        "probability": "possible",
                    }
                ],
                "metadata": {"source_book": "Test Book"},
            }
        ],
    }

    normalised = processor.normalise_book_data(raw_data)

    assert normalised["stats"]["unknown_entities"] == 1
    assert normalised["warnings"][0]["entity"] == "FooBar"


def test_normalise_book_data_handles_external_conjunction_planets() -> None:
    processor = PostProcessor()
    raw_data = {
        "book_id": "test_book",
        "rules": [
            {
                "id": "ext_1",
                "original_text": "Mercury and Mars together in the Ascendant cause trouble.",
                "conditions": {
                    "logic_block": {
                        "operator": "AND",
                        "clauses": [
                            {"type": "conjunction", "planets": ["Mercury", "Mars"]},
                            {"type": "placement", "planet": "Mercury", "house": 1},
                        ]
                    }
                },
                "effects": [
                    {
                        "category": "character",
                        "description": "trouble",
                        "impact": "Negative",
                        "intensity": "High",
                        "probability": "Likely",
                    }
                ],
                "metadata": {"source": "Test Book"},
            }
        ],
    }

    normalised = processor.normalise_book_data(raw_data)
    clauses = normalised["normalised_rules"][0]["conditions"]["clauses"]

    assert clauses[0]["planets"] == ["MERCURY", "MARS"]
    assert clauses[1]["house"] == "HOUSE_1"
