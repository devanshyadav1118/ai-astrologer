"""Phase 2 stitcher coverage."""

from __future__ import annotations

from extractor.stitcher import stitch_book_chunks


def test_stitch_book_chunks_deduplicates_rules() -> None:
    chunk_outputs = [
        {
            "chunk_id": "book_001",
            "rules": [{"rule_id": "r1", "source_text": "SUN in HOUSE_10 gives fame", "effects": []}],
            "yogas": [],
        },
        {
            "chunk_id": "book_002",
            "rules": [{"rule_id": "r2", "source_text": "SUN in HOUSE_10 gives fame", "effects": []}],
            "yogas": [],
        },
    ]

    stitched = stitch_book_chunks(chunk_outputs, "book")

    assert stitched["total_rules"] == 1
    assert stitched["metadata"]["duplicates_removed"] == 1
    assert stitched["rules"][0]["source_chunks"] == ["book_001", "book_002"]
