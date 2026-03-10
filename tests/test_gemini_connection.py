"""Phase 0 Gemini connectivity check."""

from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv


def _pick_generate_content_model(genai: object) -> str:
    """Pick an available text generation model from the API at runtime."""
    preferred_models = (
        "models/gemini-2.5-flash",
        "models/gemini-3-flash-preview",
        "models/gemini-2.0-flash",
    )
    supported_models: list[str] = []
    for model in genai.list_models():
        methods = set(getattr(model, "supported_generation_methods", []))
        if "generateContent" in methods:
            supported_models.append(model.name)
    for model_name in preferred_models:
        if model_name in supported_models:
            return model_name.removeprefix("models/")
    if supported_models:
        return supported_models[0].removeprefix("models/")
    raise RuntimeError("No generateContent model is available for this API key")


def test_gemini_connection() -> None:
    genai = pytest.importorskip("google.generativeai")
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        pytest.skip("GEMINI_API_KEY is not configured")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(_pick_generate_content_model(genai))
    response = model.generate_content('Say "Gemini connected" and nothing else.')
    assert response.text
