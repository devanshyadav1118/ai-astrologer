"""Coverage for the Node-backed rules extraction bridge."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from extractor.rules_extraction import RulesExtractionExtractor


def test_rules_extraction_build_chunks_uses_pages(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(
        b"%PDF-1.4\n"
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
        b"2 0 obj<< /Type /Pages /Count 2 /Kids [3 0 R 5 0 R] >>endobj\n"
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] /Contents 4 0 R /Resources<<>> >>endobj\n"
        b"4 0 obj<< /Length 36 >>stream\nBT /F1 12 Tf 72 200 Td (Page 1) Tj ET\nendstream endobj\n"
        b"5 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] /Contents 6 0 R /Resources<<>> >>endobj\n"
        b"6 0 obj<< /Length 36 >>stream\nBT /F1 12 Tf 72 200 Td (Page 2) Tj ET\nendstream endobj\n"
        b"xref\n0 7\n0000000000 65535 f \n0000000010 00000 n \n0000000061 00000 n \n0000000124 00000 n \n0000000230 00000 n \n0000000316 00000 n \n0000000422 00000 n \n"
        b"trailer<< /Root 1 0 R /Size 7 >>\nstartxref\n508\n%%EOF\n"
    )

    extractor = RulesExtractionExtractor(cli_script=tmp_path / "extract-chunk-cli.js")
    chunks = extractor.build_chunks(pdf_path, "sample")

    assert len(chunks) == 2
    assert chunks[0]["metadata"]["page_start"] == 1
    assert chunks[1]["chunk_id"] == "sample_page_002"


def test_rules_extraction_extract_from_chunk_adapts_output(monkeypatch, tmp_path: Path) -> None:
    cli_script = tmp_path / "extract-chunk-cli.js"
    cli_script.write_text("// stub\n", encoding="utf-8")
    source_pdf = tmp_path / "source.pdf"
    source_pdf.write_text("pdf", encoding="utf-8")

    def fake_run(
        cmd: list[str],
        cwd: Path,
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        assert cmd[0] == "node"
        assert cmd[1] == str(cli_script)
        payload = {
            "rules": [
                {
                    "id": "rule_001",
                    "original_text": "If Saturn is in the 7th house, there is delay.",
                    "conditions": {
                        "logic_block": {
                            "operator": "AND",
                            "clauses": [{"type": "placement", "planet": "Saturn", "house": 7}],
                        }
                    },
                    "effects": [
                        {
                            "category": "status",
                            "description": "delay",
                            "impact": "Negative",
                            "intensity": "High",
                            "probability": "Likely",
                        }
                    ],
                    "metadata": {"source": "Test Book"},
                }
            ],
            "yogas": [],
            "descriptions": [],
            "calculation_methods": [],
        }
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    extractor = RulesExtractionExtractor(
        cli_script=cli_script,
        audit_output_dir=tmp_path / "audit",
    )
    monkeypatch.setattr(
        extractor,
        "_extract_pdf_text",
        lambda source_pdf, page_start, page_end: "Saturn in 7th gives delay.",
    )

    payload = extractor.extract_from_chunk(
        "",
        {
            "chunk_id": "sample_page_001",
            "page_start": 1,
            "page_end": 1,
            "source_pdf": str(source_pdf),
            "book_id": "sample",
        },
    )

    assert payload["rules"][0]["rule_id"] == "rule_001"
    assert payload["rules"][0]["effects"][0]["category"] == "social_status"
    assert payload["extraction_metadata"]["runtime"] == "rules_extraction_node_cli"
    assert (tmp_path / "audit" / "sample_page_001" / "chunk.txt").exists()
