"""Partial-run bookkeeping coverage."""

from __future__ import annotations

from pathlib import Path

from pipeline.run_book import BookProcessor
from storage.sqlite_client import SQLiteClient


class PartialExtractor:
    def build_chunks(self, pdf_path: str | Path, book_id: str, max_chunks: int | None = None) -> list[dict[str, object]]:
        chunks = [
            {
                "chunk_id": f"{book_id}_{index:03d}",
                "chunk_number": index,
                "text": "",
                "page_range": str(index),
                "chapter": f"Page {index}",
                "metadata": {"book_id": book_id},
            }
            for index in range(1, 4)
        ]
        return chunks if max_chunks is None else chunks[:max_chunks]

    def extract_from_chunk(self, chunk_text: str, chunk_metadata: dict[str, str]) -> dict[str, object]:
        return {
            "rules": [
                {
                    "schema_version": "2.0",
                    "rule_id": f"{chunk_metadata['chunk_id']}_r1",
                    "type": "prediction",
                    "source_text": "Surya in Lagna gives strength.",
                    "conditions": {
                        "operator": "AND",
                        "clauses": [{"raw_text": "Surya in Lagna", "type": "planet_state", "planet": "Surya", "house": "Lagna"}],
                    },
                    "effects": [
                        {
                            "category": "character",
                            "description": "strong self",
                            "impact": "positive",
                            "intensity": "medium",
                            "probability": "likely",
                        }
                    ],
                    "metadata": {"source_book": "Stub Book"},
                }
            ],
            "yogas": [],
            "descriptions": [],
            "calculations": [],
        }


class StubNeo4j:
    def load_rule(self, rule: dict[str, object], book_id: str) -> str:
        return str(rule["rule_id"])

    def load_yoga(self, yoga: dict[str, object], book_id: str) -> str:
        return str(yoga.get("yoga_id", "yoga"))


class FlakyExtractor(PartialExtractor):
    def extract_from_chunk(self, chunk_text: str, chunk_metadata: dict[str, str]) -> dict[str, object]:
        if chunk_metadata["chunk_id"].endswith("002"):
            raise RuntimeError("temporary extraction failure")
        return super().extract_from_chunk(chunk_text, chunk_metadata)


def test_book_processor_marks_partial_when_capped(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")
    sqlite_client = SQLiteClient(tmp_path / "metadata.db")

    processor = BookProcessor(
        book_id="sample",
        pdf_path=pdf_path,
        tier=1,
        sqlite_client=sqlite_client,
        neo4j_client=StubNeo4j(),
        extractor_client=PartialExtractor(),
    )

    summary = processor.run(max_chunks=1)
    progress = sqlite_client.get_book_progress("sample")

    assert summary["run_status"] == "partial"
    assert progress["status"] == "partial"
    assert progress["total_chunks"] == 3
    assert progress["processed_chunks"] == 1


def test_book_processor_continues_after_chunk_error(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")
    sqlite_client = SQLiteClient(tmp_path / "metadata.db")

    processor = BookProcessor(
        book_id="sample",
        pdf_path=pdf_path,
        tier=1,
        sqlite_client=sqlite_client,
        neo4j_client=StubNeo4j(),
        extractor_client=FlakyExtractor(),
    )

    summary = processor.run(max_chunks=3)
    progress = sqlite_client.get_book_progress("sample")

    assert summary["chunk_errors"] == 1
    assert summary["rules_loaded"] == 1
    assert progress["status"] == "partial"
    assert progress["chunk_stats"]["error"] == 1
