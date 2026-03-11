"""Gemini client parsing coverage."""

from __future__ import annotations

from extractor.gemini_client import GeminiClient


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text


def test_gemini_client_parses_fenced_json() -> None:
    client = GeminiClient()
    response = _FakeResponse(
        """```json
        {"rules": [{"id": "r1", "original_text": "If Sun is in the 10th house.", "conditions": {"logic_block": {"operator": "AND", "clauses": [{"type": "placement", "planet": "Sun", "house": 10}]}}, "effects": [{"category": "status", "description": "fame", "impact": "Positive", "intensity": "High", "probability": "Likely"}], "metadata": {"source": "Test"}}], "yogas": [], "descriptions": [], "calculation_methods": []}
        ```"""
    )

    payload = client._parse_response(response)

    assert payload["rules"][0]["rule_id"] == "r1"
    assert payload["rules"][0]["effects"][0]["category"] == "social_status"


def test_gemini_client_normalises_missing_arrays() -> None:
    client = GeminiClient()
    response = _FakeResponse('{"rules": [{"rule_id": "r1", "source_text": "x", "conditions": {"operator": "AND", "clauses": []}, "effects": [], "metadata": {"source_book": "x"}}]}')

    payload = client._parse_response(response)

    assert payload["yogas"] == []
    assert payload["descriptions"] == []
    assert payload["calculations"] == []


def test_gemini_client_extract_from_prompt_uses_prebuilt_prompt(monkeypatch) -> None:
    client = GeminiClient()

    class _FakeModel:
        def generate_content(self, prompt: str) -> _FakeResponse:
            assert prompt == "prebuilt prompt"
            return _FakeResponse(
                '{"rules": [{"id": "r1", "original_text": "If Sun is in the 10th house.", "conditions": {"logic_block": {"operator": "AND", "clauses": [{"type": "placement", "planet": "Sun", "house": 10}]}}, "effects": [{"category": "status", "description": "fame", "impact": "Positive", "intensity": "High", "probability": "Likely"}], "metadata": {"source": "Test"}}], "yogas": [], "descriptions": [], "calculation_methods": []}'
            )

    monkeypatch.setattr(client, "_get_model", lambda: _FakeModel())

    payload = client.extract_from_prompt("prebuilt prompt", {"chunk_id": "c1"})

    assert payload["chunk_id"] == "c1"
    assert payload["rules"][0]["rule_id"] == "r1"


def test_gemini_client_stops_retrying_on_quota_error(monkeypatch) -> None:
    client = GeminiClient(max_attempts=3)
    call_count = {"count": 0}

    class _QuotaModel:
        def generate_content(self, prompt: str) -> _FakeResponse:
            call_count["count"] += 1
            raise RuntimeError("429 quota exceeded for current quota")

    monkeypatch.setattr(client, "_get_model", lambda: _QuotaModel())

    try:
        client.extract_from_prompt("prebuilt prompt", {"chunk_id": "c1"})
    except RuntimeError:
        pass

    assert call_count["count"] == 1
