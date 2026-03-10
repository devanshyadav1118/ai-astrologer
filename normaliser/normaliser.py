"""Canonical entity normalisation."""

from __future__ import annotations


class NormalisationError(ValueError):
    """Raised when a value cannot be mapped to a canonical form."""


def canonicalise_token(token: str, synonym_map: dict[str, str]) -> str:
    """Map a token to its canonical uppercase identifier."""
    cleaned = token.strip().casefold()
    if not cleaned:
        raise NormalisationError("token cannot be empty")
    try:
        return synonym_map[cleaned]
    except KeyError as exc:
        raise NormalisationError(f"unknown token: {token}") from exc
