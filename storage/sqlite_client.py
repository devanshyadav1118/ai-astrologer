"""SQLite metadata storage for the extraction pipeline."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterator


def default_sqlite_path(project_root: Path) -> Path:
    """Return the default metadata database path."""
    return project_root / "data" / "db" / "extraction.db"


class SQLiteClient:
    """SQLite wrapper for book progress, chunk checkpoints, and review queues."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else default_sqlite_path(Path.cwd())
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def register_book(self, book_id: str, metadata: dict[str, Any]) -> None:
        """Register or update a book record."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO books (
                    book_id, title, author, tradition, language, tier, status, notes, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(book_id) DO UPDATE SET
                    title=excluded.title,
                    author=excluded.author,
                    tradition=excluded.tradition,
                    language=excluded.language,
                    tier=excluded.tier,
                    status=excluded.status,
                    notes=excluded.notes,
                    updated_at=excluded.updated_at
                """,
                (
                    book_id,
                    metadata.get("title", book_id.replace("_", " ").title()),
                    metadata.get("author"),
                    metadata.get("tradition"),
                    metadata.get("language", "english"),
                    int(metadata.get("tier", 1)),
                    metadata.get("status", "pending"),
                    metadata.get("notes"),
                    _utc_now(),
                    _utc_now(),
                ),
            )

    def register_chunks(self, book_id: str, chunks: list[dict[str, Any]]) -> None:
        """Register all chunks for a book."""
        with self._connect() as conn:
            for chunk in chunks:
                conn.execute(
                    """
                    INSERT INTO chunks (
                        chunk_id, book_id, chunk_number, chapter, page_range, word_count, status, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                    ON CONFLICT(chunk_id) DO UPDATE SET
                        chapter=excluded.chapter,
                        page_range=excluded.page_range,
                        word_count=excluded.word_count,
                        updated_at=excluded.updated_at
                    """,
                    (
                        chunk["chunk_id"],
                        book_id,
                        int(chunk.get("chunk_number", 0)),
                        chunk.get("chapter"),
                        chunk.get("page_range"),
                        int(chunk.get("metadata", {}).get("word_count", 0)),
                        _utc_now(),
                        _utc_now(),
                    ),
                )
            conn.execute(
                "UPDATE books SET total_chunks = ?, updated_at = ? WHERE book_id = ?",
                (len(chunks), _utc_now(), book_id),
            )

    def update_chunk_status(
        self,
        chunk_id: str,
        status: str,
        warnings: list[str] | None = None,
        error_message: str | None = None,
        tokens_used: int | None = None,
        extraction_time: float | None = None,
    ) -> None:
        """Update chunk status and recompute book progress."""
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE chunks
                SET status = ?,
                    warnings = ?,
                    error_message = ?,
                    tokens_used = ?,
                    extraction_time = ?,
                    updated_at = ?
                WHERE chunk_id = ?
                """,
                (
                    status,
                    json.dumps(warnings, ensure_ascii=True) if warnings else None,
                    error_message,
                    tokens_used,
                    extraction_time,
                    _utc_now(),
                    chunk_id,
                ),
            )
            row = conn.execute("SELECT book_id FROM chunks WHERE chunk_id = ?", (chunk_id,)).fetchone()
            if row is not None:
                self._refresh_book_progress(conn, str(row["book_id"]))

    def log_unknown_entity(self, entity: str, book_id: str, chunk_id: str, context: str) -> None:
        """Insert or increment an unknown-entity review item."""
        with self._connect() as conn:
            existing = conn.execute(
                """
                SELECT id FROM unknown_entities
                WHERE entity_text = ? AND book_id = ? AND COALESCE(chunk_id, '') = COALESCE(?, '')
                """,
                (entity, book_id, chunk_id or None),
            ).fetchone()
            if existing is None:
                conn.execute(
                    """
                    INSERT INTO unknown_entities (
                        entity_text, book_id, chunk_id, context, frequency, review_status, created_at
                    )
                    VALUES (?, ?, ?, ?, 1, 'pending', ?)
                    """,
                    (entity, book_id, chunk_id or None, context, _utc_now()),
                )
            else:
                conn.execute(
                    "UPDATE unknown_entities SET frequency = frequency + 1 WHERE id = ?",
                    (existing["id"],),
                )

    def get_book_progress(self, book_id: str) -> dict[str, Any]:
        """Return progress and chunk breakdown for a book."""
        with self._connect() as conn:
            book = conn.execute("SELECT * FROM books WHERE book_id = ?", (book_id,)).fetchone()
            if book is None:
                raise KeyError(f"unknown book_id: {book_id}")
            progress = dict(book)
            rows = conn.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM chunks
                WHERE book_id = ?
                GROUP BY status
                """,
                (book_id,),
            ).fetchall()
            progress["chunk_stats"] = {str(row["status"]): int(row["count"]) for row in rows}
            return progress

    def get_chunk_status(self, chunk_id: str) -> str:
        """Return a chunk's persisted status."""
        with self._connect() as conn:
            row = conn.execute("SELECT status FROM chunks WHERE chunk_id = ?", (chunk_id,)).fetchone()
            return "pending" if row is None else str(row["status"])

    def mark_book_status(
        self,
        book_id: str,
        status: str,
        total_rules: int | None = None,
        total_yogas: int | None = None,
        total_descriptions: int | None = None,
    ) -> None:
        """Update aggregate counts and lifecycle state for a book."""
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE books
                SET status = ?,
                    total_rules = COALESCE(?, total_rules),
                    total_yogas = COALESCE(?, total_yogas),
                    total_descriptions = COALESCE(?, total_descriptions),
                    extraction_started = COALESCE(extraction_started, ?),
                    extraction_completed = CASE WHEN ? IN ('complete', 'partial') THEN ? ELSE extraction_completed END,
                    updated_at = ?
                WHERE book_id = ?
                """,
                (
                    status,
                    total_rules,
                    total_yogas,
                    total_descriptions,
                    _utc_now(),
                    status,
                    _utc_now(),
                    _utc_now(),
                    book_id,
                ),
            )

    def log_event(
        self,
        book_id: str,
        event_type: str,
        message: str,
        chunk_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Persist a structured processing event."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO processing_log (book_id, chunk_id, event_type, message, details, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    book_id,
                    chunk_id,
                    event_type,
                    message,
                    json.dumps(details, ensure_ascii=True, sort_keys=True) if details else None,
                    _utc_now(),
                ),
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_database(self) -> None:
        schema_path = Path(__file__).with_name("schema.sql")
        with schema_path.open(encoding="utf-8") as handle:
            schema = handle.read()
        with self._connect() as conn:
            conn.executescript(schema)

    def _refresh_book_progress(self, conn: sqlite3.Connection, book_id: str) -> None:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_chunks,
                SUM(CASE WHEN status IN ('extracted', 'normalised', 'stored') THEN 1 ELSE 0 END) AS processed_chunks
            FROM chunks
            WHERE book_id = ?
            """,
            (book_id,),
        ).fetchone()
        conn.execute(
            """
            UPDATE books
            SET total_chunks = ?, processed_chunks = ?, updated_at = ?
            WHERE book_id = ?
            """,
            (
                int(row["total_chunks"] or 0),
                int(row["processed_chunks"] or 0),
                _utc_now(),
                book_id,
            ),
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
