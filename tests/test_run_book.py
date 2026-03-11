"""Phase 2 book processor coverage."""

from __future__ import annotations

from pathlib import Path

from pipeline.run_book import BookProcessor
from storage.sqlite_client import SQLiteClient


class StubExtractor:
    def extract_from_chunk(self, chunk_text: str, chunk_metadata: dict[str, str]) -> dict[str, object]:
        return {
            "chunk_id": chunk_metadata["chunk_id"],
            "rules": [
                {
                    "id": f"{chunk_metadata['chunk_id']}_r1",
                    "original_text": "Surya in Lagna gives strength.",
                    "conditions": {
                        "logic_block": {
                            "operator": "AND",
                            "clauses": [
                                {
                                    "type": "placement",
                                    "planet": "Surya",
                                    "house": 1,
                                }
                            ],
                        },
                    },
                    "effects": [
                        {
                            "category": "character",
                            "description": "strong self",
                            "impact": "Positive",
                            "intensity": "Medium",
                            "probability": "Likely",
                        }
                    ],
                    "metadata": {"source": "Stub Book"},
                }
            ],
            "yogas": [],
            "descriptions": [],
            "calculation_methods": [],
            "extraction_metadata": {"tokens_used": 12},
        }


class StubNeo4j:
    def __init__(self) -> None:
        self.loaded_rules: list[tuple[str, str]] = []
        self.loaded_yogas: list[tuple[str, str]] = []

    def load_rule(self, rule: dict[str, object], book_id: str) -> str:
        self.loaded_rules.append((str(rule["rule_id"]), book_id))
        return str(rule["rule_id"])

    def load_yoga(self, yoga: dict[str, object], book_id: str) -> str:
        yoga_id = str(yoga.get("yoga_id", "yoga"))
        self.loaded_yogas.append((yoga_id, book_id))
        return yoga_id


def test_book_processor_runs_end_to_end_with_stubs(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(
        b"%PDF-1.4\n"
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
        b"2 0 obj<< /Type /Pages /Count 1 /Kids [3 0 R] >>endobj\n"
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] /Contents 4 0 R /Resources<<>> >>endobj\n"
        b"4 0 obj<< /Length 67 >>stream\nBT /F1 12 Tf 72 200 Td (Chapter 1) Tj T* (Surya in Lagna gives strength.) Tj ET\nendstream endobj\n"
        b"xref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000061 00000 n \n0000000118 00000 n \n0000000224 00000 n \n"
        b"trailer<< /Root 1 0 R /Size 5 >>\nstartxref\n340\n%%EOF\n"
    )

    processor = BookProcessor(
        book_id="sample",
        pdf_path=pdf_path,
        tier=1,
        sqlite_client=SQLiteClient(tmp_path / "metadata.db"),
        neo4j_client=StubNeo4j(),
        extractor_client=StubExtractor(),
    )

    summary = processor.run(max_chunks=1)

    assert summary["rules_loaded"] == 1
    assert summary["run_status"] == "complete"
    assert processor.neo4j.loaded_rules
