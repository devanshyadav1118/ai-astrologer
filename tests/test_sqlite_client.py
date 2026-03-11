"""Phase 2 SQLite client coverage."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from storage.sqlite_client import SQLiteClient


def test_sqlite_client_tracks_chunk_progress(tmp_path: Path) -> None:
    client = SQLiteClient(tmp_path / "extraction.db")
    client.register_book("sample", {"title": "Sample", "tier": 1})
    client.register_chunks(
        "sample",
        [
            {
                "chunk_id": "sample_001",
                "chunk_number": 1,
                "chapter": "Chapter 1",
                "page_range": "1-2",
                "metadata": {"word_count": 20},
            }
        ],
    )
    client.update_chunk_status("sample_001", "extracted", warnings=["minor"], tokens_used=42)
    progress = client.get_book_progress("sample")

    assert progress["total_chunks"] == 1
    assert progress["processed_chunks"] == 1
    assert progress["chunk_stats"]["extracted"] == 1


def test_sqlite_client_increments_unknown_entity_frequency(tmp_path: Path) -> None:
    db_path = tmp_path / "extraction.db"
    client = SQLiteClient(db_path)
    client.register_book("sample", {"title": "Sample", "tier": 1})
    client.log_unknown_entity("Dhruva", "sample", "sample_001", "Dhruva in Lagna")
    client.log_unknown_entity("Dhruva", "sample", "sample_001", "Dhruva in Lagna")

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT frequency FROM unknown_entities WHERE entity_text = 'Dhruva' AND book_id = 'sample'"
        ).fetchone()

    assert row[0] == 2
