"""Helpers for combining chunk-level extraction results."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from typing import Any


def stitch_chunk_payloads(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge chunk payloads into a single dictionary."""
    return {"chunks": payloads, "chunk_count": len(payloads)}


def stitch_book_chunks(chunk_outputs: list[dict[str, Any]], book_id: str) -> dict[str, Any]:
    """Merge chunk outputs into one deduplicated book payload."""
    buckets: dict[str, list[dict[str, Any]]] = {
        "rules": [],
        "yogas": [],
        "descriptions": [],
        "calculations": [],
    }
    seen: dict[str, dict[str, Any]] = {}
    duplicate_count = 0

    for chunk_output in chunk_outputs:
        chunk_id = str(chunk_output.get("chunk_id", "unknown"))
        for bucket_name, bucket in buckets.items():
            for item in chunk_output.get(bucket_name, []):
                merged = deepcopy(item)
                source_chunks = list(merged.get("source_chunks", []))
                if chunk_id not in source_chunks:
                    source_chunks.append(chunk_id)
                merged["source_chunks"] = source_chunks
                signature = _signature(bucket_name, merged)
                existing = seen.get(signature)
                if existing is None:
                    seen[signature] = merged
                    bucket.append(merged)
                    continue
                duplicate_count += 1
                for source_chunk in source_chunks:
                    if source_chunk not in existing["source_chunks"]:
                        existing["source_chunks"].append(source_chunk)

    return {
        "book_id": book_id,
        "total_rules": len(buckets["rules"]),
        "total_yogas": len(buckets["yogas"]),
        "total_descriptions": len(buckets["descriptions"]),
        "total_calculations": len(buckets["calculations"]),
        "rules": buckets["rules"],
        "yogas": buckets["yogas"],
        "descriptions": buckets["descriptions"],
        "calculations": buckets["calculations"],
        "metadata": {
            "chunks_processed": len(chunk_outputs),
            "duplicates_removed": duplicate_count,
            "stitched_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def _signature(item_type: str, item: dict[str, Any]) -> str:
    payload = {key: value for key, value in item.items() if key not in {"rule_id", "yoga_id", "source_chunks"}}
    encoded = json.dumps({"type": item_type, "payload": payload}, ensure_ascii=True, sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
