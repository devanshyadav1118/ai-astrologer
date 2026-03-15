"""Book-level pipeline entry points."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
from typing import Any, Protocol

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from extractor.core.extractor import extract_from_chunk
from extractor.core.chunker import chunk_pdf
from extractor.core.stitcher import stitch_book_chunks
from normaliser.post_processor import PostProcessor
from storage.neo4j_client import Neo4jClient
from storage.sqlite_client import SQLiteClient


class ChunkExtractor(Protocol):
    def build_chunks(
        self,
        pdf_path: str | Path,
        book_id: str,
        max_chunks: int | None = None,
    ) -> list[dict[str, Any]]:
        """Optionally build extractor-specific chunks."""

    def extract_from_chunk(self, chunk_text: str, chunk_metadata: dict[str, Any]) -> dict[str, Any]:
        """Extract structured content from one chunk."""


def validate_book_path(pdf_path: Path) -> None:
    """Fail fast if a PDF path is not usable."""
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("book input must be a PDF file")
    if not pdf_path.exists():
        raise FileNotFoundError(f"book input not found: {pdf_path}")


def setup_logging(book_id: str) -> Path:
    """Configure logging for a processing run."""
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{book_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)
    return log_path


class BookProcessor:
    """Orchestrate PDF chunking, extraction, post-processing, and persistence."""

    def __init__(
        self,
        book_id: str,
        pdf_path: str | Path,
        tier: int,
        resume: bool = False,
        sqlite_client: SQLiteClient | None = None,
        neo4j_client: Neo4jClient | None = None,
        extractor_client: ChunkExtractor | None = None,
        post_processor: PostProcessor | None = None,
    ) -> None:
        self.book_id = book_id
        self.pdf_path = Path(pdf_path)
        self.tier = tier
        self.resume = resume
        self.sqlite = sqlite_client or SQLiteClient()
        self.neo4j = neo4j_client or Neo4jClient()
        self.post_processor = post_processor or PostProcessor()
        self.output_dir = Path("data") / "extracted"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.chunk_errors = 0

    def run(self, max_chunks: int | None = None) -> dict[str, Any]:
        """Process a full book and return a summary."""
        validate_book_path(self.pdf_path)
        self.sqlite.register_book(
            self.book_id,
            {
                "title": self.book_id.replace("_", " ").title(),
                "tier": self.tier,
                "status": "processing",
            },
        )
        self.sqlite.log_event(self.book_id, "pipeline_started", "Book processing started")

        if hasattr(self.extractor, "build_chunks"):
            all_chunks = self.extractor.build_chunks(self.pdf_path, self.book_id, max_chunks=None)
        else:
            all_chunks = chunk_pdf(self.pdf_path, Path("data") / "chunks" / self.book_id)
        chunks = all_chunks[:max_chunks] if max_chunks is not None else all_chunks
        self.sqlite.register_chunks(self.book_id, all_chunks)

        chunk_outputs: list[dict[str, Any]] = []
        for chunk in chunks:
            chunk_id = chunk["chunk_id"]
            if self.resume and self.sqlite.get_chunk_status(chunk_id) in {"extracted", "normalised", "stored"}:
                self.logger.info("Skipping already processed chunk %s", chunk_id)
                continue

            started = datetime.now(timezone.utc)
            try:
                result = self.extractor.extract_from_chunk(
                    chunk_text=chunk["text"],
                    chunk_metadata={**chunk.get("metadata", {}), "chunk_id": chunk_id},
                )
                result = adapt_extraction_payload(result, {**chunk.get("metadata", {}), "chunk_id": chunk_id})
                result["chunk_id"] = chunk_id
                chunk_outputs.append(result)
                elapsed = (datetime.now(timezone.utc) - started).total_seconds()
                self.sqlite.update_chunk_status(
                    chunk_id=chunk_id,
                    status="extracted",
                    warnings=result.get("warnings"),
                    tokens_used=result.get("extraction_metadata", {}).get("tokens_used"),
                    extraction_time=elapsed,
                )
            except Exception as exc:
                self.chunk_errors += 1
                self.logger.exception("Chunk extraction failed for %s", chunk_id)
                elapsed = (datetime.now(timezone.utc) - started).total_seconds()
                self.sqlite.update_chunk_status(
                    chunk_id=chunk_id,
                    status="error",
                    error_message=str(exc),
                    extraction_time=elapsed,
                )
                self.sqlite.log_event(
                    self.book_id,
                    "chunk_extraction_error",
                    str(exc),
                    chunk_id=chunk_id,
                )

        if not chunk_outputs:
            self.sqlite.mark_book_status(self.book_id, "error")
            raise RuntimeError(f"No chunks were successfully extracted for {self.book_id}")

        stitched = stitch_book_chunks(chunk_outputs, self.book_id)
        normalised = self.post_processor.normalise_book_data(stitched)
        self._persist_unknown_entities(normalised)
        self._write_json(self.output_dir / f"{self.book_id}_stitched.json", stitched)
        self._write_json(self.output_dir / f"{self.book_id}_normalised.json", normalised)
        self._load_graph(normalised)

        if self.chunk_errors > 0:
            final_status = "partial"
        else:
            final_status = "complete" if len(chunks) == len(all_chunks) else "partial"
        self.sqlite.mark_book_status(
            self.book_id,
            final_status,
            total_rules=len(normalised["normalised_rules"]),
            total_yogas=len(normalised["normalised_yogas"]),
            total_descriptions=stitched.get("total_descriptions"),
        )
        self.sqlite.log_event(
            self.book_id,
            "pipeline_completed",
            "Book processing completed",
            details={"run_status": final_status, "processed_chunk_count": len(chunks), "total_chunk_count": len(all_chunks)},
        )
        return {
            "book_id": self.book_id,
            "chunks_processed": len(chunk_outputs),
            "rules_loaded": len(normalised["normalised_rules"]),
            "yogas_loaded": len(normalised["normalised_yogas"]),
            "warnings": len(normalised["warnings"]),
            "chunk_errors": self.chunk_errors,
            "run_status": final_status,
        }

    def _persist_unknown_entities(self, normalised: dict[str, Any]) -> None:
        for warning in normalised.get("warnings", []):
            if warning.get("type") != "unknown_entity":
                continue
            self.sqlite.log_unknown_entity(
                entity=str(warning.get("entity", "")),
                book_id=self.book_id,
                chunk_id=str(warning.get("chunk_id") or ""),
                context=str(warning.get("context", "")),
            )

    def _load_graph(self, normalised: dict[str, Any]) -> None:
        for rule in normalised.get("normalised_rules", []):
            self.neo4j.load_rule(rule, self.book_id)
        for yoga in normalised.get("normalised_yogas", []):
            self.neo4j.load_yoga(yoga, self.book_id)

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=True, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Process one astrological book")
    parser.add_argument("--pdf", required=True, help="Path to the source PDF")
    parser.add_argument("--book-id", required=True, help="Unique identifier for the book")
    parser.add_argument("--tier", required=True, type=int, choices=[1, 2, 3], help="Book tier")
    parser.add_argument("--resume", action="store_true", help="Resume from chunk checkpoints")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and exit")
    parser.add_argument("--max-chunks", type=int, help="Limit chunk count for testing")
    args = parser.parse_args()

    log_path = setup_logging(args.book_id)
    logging.info("Logging to %s", log_path)
    pdf_path = Path(args.pdf)
    validate_book_path(pdf_path)
    if args.dry_run:
        logging.info("Dry run complete for %s", args.book_id)
        return

    processor = BookProcessor(
        book_id=args.book_id,
        pdf_path=pdf_path,
        tier=args.tier,
        resume=args.resume,
    )
    summary = processor.run(max_chunks=args.max_chunks)
    logging.info("Summary: %s", json.dumps(summary, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
