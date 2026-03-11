"""Gemini API configuration helpers."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import os
import re
import time
from typing import Any

from dotenv import load_dotenv

from extractor.adapter import adapt_extraction_payload
from extractor.prompt import get_extraction_prompt

LOGGER = logging.getLogger(__name__)


def load_gemini_api_key() -> str:
    """Load the Gemini API key from the environment."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return api_key


DEFAULT_GEMINI_MODEL = "models/gemini-flash-lite-latest"


class GeminiClient:
    """Minimal Gemini wrapper with retries and structured JSON parsing."""

    def __init__(self, model_name: str = DEFAULT_GEMINI_MODEL, max_attempts: int = 3) -> None:
        self.model_name = model_name
        self.max_attempts = max_attempts
        self._model: Any | None = None

    def extract_from_chunk(self, chunk_text: str, chunk_metadata: dict[str, Any]) -> dict[str, Any]:
        """Extract structured output from a chunk."""
        prompt = self._build_prompt(chunk_text, chunk_metadata)
        return self.extract_from_prompt(prompt, chunk_metadata)

    def extract_from_prompt(self, prompt: str, chunk_metadata: dict[str, Any]) -> dict[str, Any]:
        """Extract structured output from a prebuilt prompt."""
        model = self._get_model()
        last_error: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                started = time.perf_counter()
                response = model.generate_content(prompt)
                elapsed = time.perf_counter() - started
                payload = self._parse_response(response)
                metadata = payload.setdefault("extraction_metadata", {})
                metadata.setdefault("model", self.model_name)
                metadata.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
                metadata.setdefault("latency_seconds", round(elapsed, 3))
                payload.setdefault("chunk_id", chunk_metadata.get("chunk_id"))
                payload.setdefault("rules", [])
                payload.setdefault("yogas", [])
                payload.setdefault("descriptions", [])
                payload.setdefault("calculations", [])
                return payload
            except Exception as exc:  # pragma: no cover
                last_error = exc
                LOGGER.warning("Gemini attempt %s failed: %s", attempt, exc)
                if self._is_quota_exhausted(exc):
                    break
                if attempt < self.max_attempts:
                    time.sleep(min(2 ** attempt, 30))
        raise RuntimeError(f"Gemini extraction failed after {self.max_attempts} attempts") from last_error

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            import google.generativeai as genai
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("google-generativeai is not installed") from exc
        genai.configure(api_key=load_gemini_api_key())
        self._model = genai.GenerativeModel(self.model_name)
        return self._model

    def _build_prompt(self, chunk_text: str, chunk_metadata: dict[str, Any]) -> str:
        return f"{get_extraction_prompt(chunk_metadata)}\n\nSource chunk:\n{chunk_text}"

    def _parse_response(self, response: Any) -> dict[str, Any]:
        text = getattr(response, "text", "") or ""
        if not text:
            raise RuntimeError("Gemini returned an empty response")
        candidate = self._extract_json_text(text)
        payload = json.loads(candidate)
        return self._normalise_payload(payload)

    def _extract_json_text(self, text: str) -> str:
        fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
        if fenced:
            return fenced.group(1)
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise RuntimeError("Gemini response did not contain a JSON object")
        return text[start : end + 1]

    def _normalise_payload(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise RuntimeError("Gemini response JSON must be an object")
        normalised = adapt_extraction_payload(payload)
        for key in ("rules", "yogas", "descriptions", "calculations"):
            value = normalised.get(key, [])
            normalised[key] = value if isinstance(value, list) else []
        return normalised

    def _is_quota_exhausted(self, exc: Exception) -> bool:
        message = str(exc).lower()
        return "quota exceeded" in message or "current quota" in message or "resource_exhausted" in message


def extract_from_chunk(chunk_text: str, chunk_metadata: dict[str, Any]) -> dict[str, Any]:
    """Compatibility wrapper matching the roadmap API."""
    return GeminiClient().extract_from_chunk(chunk_text=chunk_text, chunk_metadata=chunk_metadata)
