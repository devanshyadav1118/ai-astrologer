"""Prompt templates used by the extraction layer."""

from __future__ import annotations

import json
from typing import Any

EXTRACTION_PROMPT_V2 = """
You are a highly specialized AI data extraction engine for classical astrology texts.
Your sole objective is to analyze the provided source text and convert every extractable rule,
description, yoga, and calculation method into structured JSON suitable for database ingestion.

Non-negotiable rules:
1. Return exactly one JSON object and nothing else.
2. Do not wrap the JSON in markdown fences.
3. Do not invent rules, entities, yogas, or calculations not supported by the chunk.
4. Prefer omission over hallucination.
5. Unknown or uncertain entities must remain in raw surface form for downstream review.
6. Use empty arrays instead of null.
7. If the chunk contains no extractable content, return all top-level keys with empty arrays.

Use these extraction sections:
- `rules`
- `descriptions`
- `calculation_methods`
- `yogas`

Format A: Predictive Rules (`rules`)
{
  "rules": [
    {
      "id": "unique identifier",
      "original_text": "exact source text",
      "conditions": {
        "ascendant_sign": "optional string",
        "logic_block": {
          "operator": "AND|OR",
          "clauses": [
            {
              "type": "placement|conjunction|yoga_check|logic_block|relative_placement",
              "planet": "optional",
              "sign": "optional",
              "house": "optional",
              "relation_to_sign": "optional",
              "planets": ["optional list"]
            }
          ]
        }
      },
      "effects": [
        {
          "category": "wealth|health|character|family|status|intelligence|marriage|fortune|longevity|career|children|spiritual|social_status",
          "description": "clear summary of the effect",
          "impact": "Positive|Negative|Mixed|Neutral",
          "intensity": "High|Medium|Low|Variable",
          "probability": "Certain|Likely|Possible|Conditional",
          "context": "optional"
        }
      ],
      "tags": ["flat list of terms/categories"],
      "metadata": {
        "source": "source title",
        "author": "author",
        "stanza": "optional"
      }
    }
  ]
}

Format B: Descriptions (`descriptions`)
{
  "descriptions": [
    {
      "id": "unique identifier",
      "entity_type": "zodiac_sign|planet|house|other",
      "entity_name": "entity name",
      "original_text": "exact source text",
      "attributes": {"key": "value"},
      "metadata": {
        "source": "source title",
        "author": "author"
      }
    }
  ]
}

Format C: Calculation Algorithms (`calculation_methods`)
{
  "calculation_methods": [
    {
      "id": "unique identifier",
      "name": "calculation name",
      "purpose": "what it is used for",
      "original_text": "exact source text",
      "steps": [
        {
          "step": 1,
          "logic": "instruction",
          "note": "optional"
        }
      ],
      "metadata": {
        "source": "source title",
        "author": "author"
      }
    }
  ]
}

Format H: Yogas (`yogas`)
{
  "yogas": [
    {
      "id": "unique identifier",
      "name": "yoga name",
      "original_text": "defining text",
      "formation_logic": {
        "operator": "AND|OR",
        "clauses": [
          {
            "type": "relative_placement|placement|conjunction|other",
            "conditions": "or structured fields"
          }
        ]
      },
      "standard_effects": [
        {
          "category": "effect category",
          "description": "effect text",
          "impact": "Positive|Negative|Mixed|Neutral",
          "intensity": "High|Medium|Low|Variable"
        }
      ],
      "metadata": {
        "source": "source title",
        "author": "author"
      }
    }
  ]
}

Extraction guidance:
- Prioritize named yoga definitions when a named yoga is explicitly introduced.
- Extract every clear cause-and-effect statement as a separate rule.
- Preserve nested logic when explicitly stated; otherwise use the simplest faithful structure.
- Reuse source wording in `original_text`.

Output contract:
Return exactly one JSON object with these keys:
{
  "rules": [...],
  "descriptions": [...],
  "calculation_methods": [...],
  "yogas": [...]
}
""".strip()


def get_extraction_prompt(chunk_metadata: dict[str, Any] | None = None) -> str:
    """Return the extraction prompt with optional chunk metadata context."""
    if not chunk_metadata:
        return EXTRACTION_PROMPT_V2

    context = {
        "book_id": chunk_metadata.get("book_id", "unknown"),
        "chapter": chunk_metadata.get("chapter", "unknown"),
        "page_range": chunk_metadata.get("page_range", "unknown"),
        "chunk_id": chunk_metadata.get("chunk_id", "unknown"),
    }
    metadata_block = json.dumps(context, ensure_ascii=True, sort_keys=True, indent=2)
    return (
        "Context for this extraction:\n"
        f"{metadata_block}\n\n"
        "Use the context above to populate metadata.source and create stable ids.\n\n"
        f"{EXTRACTION_PROMPT_V2}"
    )
