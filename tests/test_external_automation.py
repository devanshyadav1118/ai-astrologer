"""External automation wrapper coverage."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import pytest

from extractor.external_automation import ExternalAutomationExtractor


def test_external_automation_build_chunks_uses_pages(tmp_path: Path) -> None:
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

    extractor = ExternalAutomationExtractor(timeout_seconds=1)
    chunks = extractor.build_chunks(pdf_path, "sample")

    assert len(chunks) == 2
    assert chunks[0]["metadata"]["page_start"] == 1
    assert chunks[1]["chunk_id"] == "sample_page_002"


def test_external_automation_extract_from_chunk_adapts_output(monkeypatch, tmp_path: Path) -> None:
    automation_root = tmp_path / "Extraction Automation"
    scripts_dir = automation_root / "scripts"
    scripts_dir.mkdir(parents=True)
    (scripts_dir / "process_pdf_chapters.py").write_text("# stub\n", encoding="utf-8")
    (automation_root / "Prompt.txt").write_text("prompt", encoding="utf-8")
    source_pdf = tmp_path / "source.pdf"
    source_pdf.write_text("pdf", encoding="utf-8")

    def fake_run(
        cmd: list[str],
        cwd: Path,
        capture_output: bool,
        text: bool,
        timeout: int,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        output_path = cwd.parent / "output" / "Pages_00-00" / "extracted_data.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(
                {
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
                    ]
                }
            ),
            encoding="utf-8",
        )
        assert env["GEMINI_MODEL"] == "models/gemini-flash-lite-latest"
        assert env["GEMINI_TIMEOUT"] == "180"
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    extractor = ExternalAutomationExtractor(automation_root=automation_root, runtime="cli")
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


def test_external_automation_retries_no_output_error(monkeypatch, tmp_path: Path) -> None:
    automation_root = tmp_path / "Extraction Automation"
    scripts_dir = automation_root / "scripts"
    scripts_dir.mkdir(parents=True)
    (scripts_dir / "process_pdf_chapters.py").write_text("# stub\n", encoding="utf-8")
    (automation_root / "Prompt.txt").write_text("prompt", encoding="utf-8")
    source_pdf = tmp_path / "source.pdf"
    source_pdf.write_text("pdf", encoding="utf-8")
    call_count = {"count": 0}

    def fake_run(
        cmd: list[str],
        cwd: Path,
        capture_output: bool,
        text: bool,
        timeout: int,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        call_count["count"] += 1
        output_path = cwd.parent / "output" / "Pages_00-00" / "extracted_data.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if call_count["count"] == 1:
            output_path.write_text(json.dumps({"error": "No output from Gemini"}), encoding="utf-8")
        else:
            output_path.write_text(
                json.dumps(
                    {
                        "rules": [
                            {
                                "id": "rule_001",
                                "original_text": "If Saturn is in the 7th house, there is delay.",
                                "conditions": {"logic_block": {"operator": "AND", "clauses": [{"type": "placement", "planet": "Saturn", "house": 7}]}},
                                "effects": [{"category": "status", "description": "delay", "impact": "Negative", "intensity": "High", "probability": "Likely"}],
                                "metadata": {"source": "Test Book"},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    extractor = ExternalAutomationExtractor(automation_root=automation_root, max_attempts=2, runtime="cli")
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

    assert call_count["count"] == 2
    assert payload["rules"][0]["rule_id"] == "rule_001"


def test_external_automation_writes_debug_artifact_on_timeout(monkeypatch, tmp_path: Path) -> None:
    automation_root = tmp_path / "Extraction Automation"
    scripts_dir = automation_root / "scripts"
    scripts_dir.mkdir(parents=True)
    (scripts_dir / "process_pdf_chapters.py").write_text("# stub\n", encoding="utf-8")
    (automation_root / "Prompt.txt").write_text("prompt", encoding="utf-8")
    source_pdf = tmp_path / "source.pdf"
    source_pdf.write_text("pdf", encoding="utf-8")
    debug_dir = tmp_path / "debug"

    def fake_run(
        cmd: list[str],
        cwd: Path,
        capture_output: bool,
        text: bool,
        timeout: int,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout, output="slow", stderr="still running")

    monkeypatch.setattr(subprocess, "run", fake_run)

    extractor = ExternalAutomationExtractor(
        automation_root=automation_root,
        timeout_seconds=5,
        debug_output_dir=debug_dir,
        max_attempts=1,
        runtime="cli",
    )

    with pytest.raises(RuntimeError, match="timed out"):
        extractor.extract_from_chunk(
            "",
            {
                "chunk_id": "sample_page_001",
                "page_start": 1,
                "page_end": 1,
                "source_pdf": str(source_pdf),
                "book_id": "sample",
            },
        )

    debug_payload = json.loads((debug_dir / "sample_page_001.json").read_text(encoding="utf-8"))
    assert debug_payload["error"] == "external_wrapper_timeout"
    assert "process_pdf_chapters.py" in " ".join(debug_payload["command"])


def test_external_automation_python_api_uses_prompt_template(monkeypatch, tmp_path: Path) -> None:
    automation_root = tmp_path / "Extraction Automation"
    scripts_dir = automation_root / "scripts"
    scripts_dir.mkdir(parents=True)
    (scripts_dir / "process_pdf_chapters.py").write_text("# stub\n", encoding="utf-8")
    (automation_root / "Prompt.txt").write_text(
        "PREFIX\n[Paste the full text from _Saravali_ or another source here.]\nSUFFIX",
        encoding="utf-8",
    )
    pdf_path = tmp_path / "source.pdf"
    pdf_path.write_text("pdf", encoding="utf-8")

    class StubGeminiClient:
        def __init__(self) -> None:
            self.prompt: str | None = None

        def extract_from_prompt(self, prompt: str, chunk_metadata: dict[str, str]) -> dict[str, object]:
            self.prompt = prompt
            return {
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

    stub_client = StubGeminiClient()
    extractor = ExternalAutomationExtractor(
        automation_root=automation_root,
        audit_output_dir=tmp_path / "audit",
        runtime="python_api",
        gemini_client=stub_client,  # type: ignore[arg-type]
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
            "source_pdf": str(pdf_path),
            "book_id": "sample",
        },
    )

    assert stub_client.prompt is not None
    assert "PREFIX" in stub_client.prompt
    assert "Saturn in 7th gives delay." in stub_client.prompt
    assert payload["rules"][0]["rule_id"] == "rule_001"
    assert payload["extraction_metadata"]["runtime"] == "extraction_automation_python_api"
    assert (tmp_path / "audit" / "sample_page_001" / "prompt.txt").exists()
    assert (tmp_path / "audit" / "sample_page_001" / "metadata.json").exists()
    assert (tmp_path / "audit" / "sample_page_001" / "extracted_data.json").exists()
