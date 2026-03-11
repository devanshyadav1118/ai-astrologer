"""Prompt builder coverage."""

from __future__ import annotations

from extractor.prompt import EXTRACTION_PROMPT_V2, get_extraction_prompt


def test_get_extraction_prompt_without_metadata_returns_base_prompt() -> None:
    assert get_extraction_prompt() == EXTRACTION_PROMPT_V2


def test_get_extraction_prompt_includes_metadata_context() -> None:
    prompt = get_extraction_prompt({"book_id": "saravali", "chapter": "Chapter 1"})

    assert "Context for this extraction:" in prompt
    assert "saravali" in prompt
    assert "Chapter 1" in prompt


def test_prompt_contains_production_schema_and_guardrails() -> None:
    assert "Return exactly one JSON object and nothing else." in EXTRACTION_PROMPT_V2
    assert "Format A: Predictive Rules" in EXTRACTION_PROMPT_V2
    assert "Format H: Yogas" in EXTRACTION_PROMPT_V2
    assert '"calculation_methods"' in EXTRACTION_PROMPT_V2
    assert '"rules": [...]' in EXTRACTION_PROMPT_V2
