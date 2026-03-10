"""Phase 0 Gemini connectivity check."""

from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv


def test_gemini_connection() -> None:
    genai = pytest.importorskip("google.generativeai")
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        pytest.skip("GEMINI_API_KEY is not configured")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content('Say "Gemini connected" and nothing else.')
    assert response.text
