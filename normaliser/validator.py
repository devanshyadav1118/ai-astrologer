"""Validation helpers for normalised payloads."""

from __future__ import annotations

from typing import Iterable


def validate_required_entities(values: Iterable[str]) -> None:
    """Reject empty canonical entity values."""
    for value in values:
        if not value or not value.strip():
            raise ValueError("canonical entity values must be non-empty")
