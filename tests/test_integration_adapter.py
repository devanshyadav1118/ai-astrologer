"""Integration coverage for hybrid extractor schema support."""

from __future__ import annotations

from extractor.adapter import adapt_extraction_payload
from normaliser.post_processor import PostProcessor


def test_external_schema_passes_end_to_end_through_adapter_and_post_processor() -> None:
    payload = {
        "rules": [
            {
                "id": "rule_001",
                "original_text": "Should Venus be in Pisces along with Jupiter and the Moon, the native will acquire kingly fortunes.",
                "conditions": {
                    "logic_block": {
                        "operator": "AND",
                        "clauses": [
                            {"type": "placement", "planet": "Venus", "sign": "Pisces"},
                            {"type": "conjunction", "planets": ["Venus", "Jupiter", "Moon"]},
                        ],
                    }
                },
                "effects": [
                    {
                        "category": "status",
                        "description": "kingly fortunes",
                        "impact": "Positive",
                        "intensity": "High",
                        "probability": "Certain",
                    }
                ],
                "metadata": {"source": "Garga Hora"},
            }
        ],
        "yogas": [],
        "descriptions": [],
        "calculation_methods": [],
    }

    adapted = adapt_extraction_payload(payload, {"chunk_id": "chunk_001", "book_id": "garga_hora"})
    processed = PostProcessor().normalise_book_data({"book_id": "garga_hora", **adapted})

    assert processed["normalised_rules"][0]["validation_status"] == "valid"
