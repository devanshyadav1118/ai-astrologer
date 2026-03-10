"""Helpers for combining chunk-level extraction results."""

from __future__ import annotations

from typing import Any


def stitch_chunk_payloads(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge chunk payloads into a single dictionary."""
    return {"chunks": payloads, "chunk_count": len(payloads)}
