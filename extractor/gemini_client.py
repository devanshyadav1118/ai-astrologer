"""Gemini API configuration helpers."""

from __future__ import annotations

import os

from dotenv import load_dotenv


def load_gemini_api_key() -> str:
    """Load the Gemini API key from the environment."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return api_key
