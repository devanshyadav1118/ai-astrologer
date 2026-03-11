"""Wrapper around the standalone Extraction Automation tool."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any

from PyPDF2 import PdfReader

from extractor.adapter import adapt_extraction_payload
from extractor.gemini_client import DEFAULT_GEMINI_MODEL, GeminiClient


class ExternalAutomationExtractor:
    """Invoke the external extractor without rewriting its internals."""

    def __init__(
        self,
        automation_root: str | Path = "Extraction Automation",
        python_bin: str | None = None,
        timeout_seconds: int = 240,
        max_attempts: int = 3,
        gemini_model: str = DEFAULT_GEMINI_MODEL,
        gemini_timeout_seconds: int = 180,
        debug_output_dir: str | Path = "data/debug/external_automation",
        audit_output_dir: str | Path = "data/external_automation",
        runtime: str = "python_api",
        gemini_client: GeminiClient | None = None,
    ) -> None:
        self.automation_root = Path(automation_root)
        self.script_path = self.automation_root / "scripts" / "process_pdf_chapters.py"
        self.prompt_path = self.automation_root / "Prompt.txt"
        self.python_bin = python_bin or sys.executable
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts
        self.gemini_model = os.getenv("GEMINI_MODEL", gemini_model)
        self.gemini_timeout_seconds = int(os.getenv("GEMINI_TIMEOUT", str(gemini_timeout_seconds)))
        self.debug_output_dir = Path(debug_output_dir)
        self.audit_output_dir = Path(audit_output_dir)
        self.runtime = runtime
        self.gemini_client = gemini_client or GeminiClient(model_name=self.gemini_model, max_attempts=max_attempts)

    def build_chunks(
        self,
        pdf_path: str | Path,
        book_id: str,
        max_chunks: int | None = None,
    ) -> list[dict[str, Any]]:
        """Create page-based chunk descriptors for the external extractor."""
        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)
        if max_chunks is not None:
            total_pages = min(total_pages, max_chunks)
        return [
            {
                "chunk_id": f"{book_id}_page_{page_number:03d}",
                "chunk_number": page_number,
                "text": "",
                "page_range": str(page_number),
                "chapter": f"Page {page_number}",
                "metadata": {
                    "book_id": book_id,
                    "page_start": page_number,
                    "page_end": page_number,
                    "source_pdf": str(Path(pdf_path).resolve()),
                },
            }
            for page_number in range(1, total_pages + 1)
        ]

    def extract_from_chunk(self, chunk_text: str, chunk_metadata: dict[str, Any]) -> dict[str, Any]:
        """Run the external extractor for one page-based chunk and adapt the output."""
        source_pdf = Path(str(chunk_metadata["source_pdf"]))
        page_start = int(chunk_metadata["page_start"]) - 1
        page_end = int(chunk_metadata["page_end"]) - 1
        batch_size = page_end - page_start + 1

        if self.runtime == "python_api":
            return self._run_api_extraction(
                source_pdf=source_pdf,
                page_start=page_start,
                page_end=page_end,
                chunk_metadata=chunk_metadata,
            )

        last_error: RuntimeError | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return self._run_single_cli_extraction(
                    source_pdf=source_pdf,
                    page_start=page_start,
                    page_end=page_end,
                    batch_size=batch_size,
                    chunk_metadata=chunk_metadata,
                )
            except RuntimeError as exc:
                last_error = exc
                if attempt == self.max_attempts:
                    break
                if "No output from Gemini" not in str(exc):
                    break
                time.sleep(min(5 * attempt, 15))
        raise last_error or RuntimeError(f"Extraction Automation failed for {chunk_metadata['chunk_id']}")

    def _run_api_extraction(
        self,
        source_pdf: Path,
        page_start: int,
        page_end: int,
        chunk_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        chunk_text = self._extract_pdf_text(source_pdf, page_start, page_end)
        if not chunk_text.strip():
            raise RuntimeError(f"Extraction Automation found no text for {chunk_metadata['chunk_id']}")

        prompt = self._build_external_prompt(chunk_text, chunk_metadata)
        try:
            raw_payload = self.gemini_client.extract_from_prompt(prompt, chunk_metadata)
        except Exception as exc:
            self._write_debug_artifact(
                chunk_id=str(chunk_metadata["chunk_id"]),
                attempt_error="python_api_error",
                command=[self.gemini_model, "python_api"],
                stdout="",
                stderr=str(exc),
                payload={"prompt_preview": prompt[:4000]},
            )
            raise
        payload = adapt_extraction_payload(raw_payload, chunk_metadata)
        payload["chunk_id"] = chunk_metadata["chunk_id"]
        metadata = payload.setdefault("extraction_metadata", {})
        metadata["runtime"] = "extraction_automation_python_api"
        metadata["prompt_source"] = str(self.prompt_path)
        self._write_audit_bundle(
            chunk_id=str(chunk_metadata["chunk_id"]),
            chunk_metadata=chunk_metadata,
            prompt=prompt,
            payload=payload,
        )
        return payload

    def _run_single_cli_extraction(
        self,
        source_pdf: Path,
        page_start: int,
        page_end: int,
        batch_size: int,
        chunk_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        with tempfile.TemporaryDirectory(prefix=f"ext_auto_{chunk_metadata['chunk_id']}_") as temp_dir:
            runtime_root = Path(temp_dir)
            scripts_dir = runtime_root / "scripts"
            input_dir = scripts_dir / "input"
            output_dir = runtime_root / "output"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            input_dir.mkdir(parents=True, exist_ok=True)
            output_dir.mkdir(parents=True, exist_ok=True)

            self._link_or_copy(self.script_path, scripts_dir / "process_pdf_chapters.py")
            self._link_or_copy(self.prompt_path, scripts_dir / "Prompt.txt")
            self._link_or_copy(source_pdf, input_dir / "astrology_full_book.pdf")

            command = [
                self.python_bin,
                "process_pdf_chapters.py",
                "--start-page",
                str(page_start),
                "--batch-size",
                str(batch_size),
            ]
            env = {
                **os.environ,
                "GEMINI_MODEL": self.gemini_model,
                "GEMINI_TIMEOUT": str(self.gemini_timeout_seconds),
            }
            try:
                result = subprocess.run(
                    command,
                    cwd=scripts_dir,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    env=env,
                )
            except subprocess.TimeoutExpired as exc:
                self._write_debug_artifact(
                    chunk_id=str(chunk_metadata["chunk_id"]),
                    attempt_error="external_wrapper_timeout",
                    command=command,
                    stdout=(exc.stdout or ""),
                    stderr=(exc.stderr or ""),
                )
                raise RuntimeError(
                    f"Extraction Automation timed out for {chunk_metadata['chunk_id']} "
                    f"after {self.timeout_seconds}s"
                ) from exc
            if result.returncode != 0:
                self._write_debug_artifact(
                    chunk_id=str(chunk_metadata["chunk_id"]),
                    attempt_error="external_wrapper_nonzero_exit",
                    command=command,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )
                raise RuntimeError(
                    f"Extraction Automation failed for {chunk_metadata['chunk_id']}: "
                    f"{result.stderr.strip() or result.stdout.strip()}"
                )

            output_path = output_dir / f"Pages_{page_start:02d}-{page_end:02d}" / "extracted_data.json"
            if not output_path.exists():
                self._write_debug_artifact(
                    chunk_id=str(chunk_metadata["chunk_id"]),
                    attempt_error="missing_output_file",
                    command=command,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )
                raise RuntimeError(f"Expected extractor output not found: {output_path}")

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict) and "error" in payload:
                self._write_debug_artifact(
                    chunk_id=str(chunk_metadata["chunk_id"]),
                    attempt_error="extractor_error_payload",
                    command=command,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    payload=payload,
                )
                raise RuntimeError(f"Extraction Automation error for {chunk_metadata['chunk_id']}: {payload['error']}")

            adapted = adapt_extraction_payload(payload, chunk_metadata)
            adapted["chunk_id"] = chunk_metadata["chunk_id"]
            adapted["extraction_metadata"] = {
                "runtime": "extraction_automation_cli",
                "stdout": result.stdout.strip()[:1000],
            }
            self._write_audit_bundle(
                chunk_id=str(chunk_metadata["chunk_id"]),
                chunk_metadata=chunk_metadata,
                prompt=(scripts_dir / "Prompt.txt").read_text(encoding="utf-8"),
                payload=adapted,
            )
            return adapted

    def _extract_pdf_text(self, source_pdf: Path, page_start: int, page_end: int) -> str:
        reader = PdfReader(str(source_pdf))
        texts: list[str] = []
        for page_index in range(page_start, page_end + 1):
            page = reader.pages[page_index]
            texts.append(page.extract_text() or "")
        return "\n".join(texts).strip()

    def _build_external_prompt(self, chunk_text: str, chunk_metadata: dict[str, Any]) -> str:
        template = self.prompt_path.read_text(encoding="utf-8")
        prompt = template.replace("[Paste the full text from _Saravali_ or another source here.]", chunk_text)
        context = (
            "\n\n### 6. EXTRACTION CONTEXT\n"
            f'- book_id: "{chunk_metadata.get("book_id", "unknown")}"\n'
            f'- chunk_id: "{chunk_metadata.get("chunk_id", "unknown")}"\n'
            f'- page_start: "{chunk_metadata.get("page_start", "unknown")}"\n'
            f'- page_end: "{chunk_metadata.get("page_end", "unknown")}"\n'
            "\nReturn exactly one JSON object and nothing else."
        )
        return f"{prompt}{context}"

    def _link_or_copy(self, source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            destination.symlink_to(source.resolve())
        except OSError:
            shutil.copy2(source, destination)

    def _write_debug_artifact(
        self,
        chunk_id: str,
        attempt_error: str,
        command: list[str],
        stdout: str,
        stderr: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.debug_output_dir.mkdir(parents=True, exist_ok=True)
        debug_path = self.debug_output_dir / f"{chunk_id}.json"
        debug_payload = {
            "chunk_id": chunk_id,
            "error": attempt_error,
            "command": command,
            "stdout": stdout[:4000],
            "stderr": stderr[:4000],
        }
        if payload is not None:
            debug_payload["payload"] = payload
        debug_path.write_text(json.dumps(debug_payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def _write_audit_bundle(
        self,
        chunk_id: str,
        chunk_metadata: dict[str, Any],
        prompt: str,
        payload: dict[str, Any],
    ) -> None:
        bundle_dir = self.audit_output_dir / chunk_id
        bundle_dir.mkdir(parents=True, exist_ok=True)
        (bundle_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
        (bundle_dir / "metadata.json").write_text(
            json.dumps(
                {
                    "chunk_id": chunk_id,
                    "chunk_metadata": chunk_metadata,
                    "runtime": payload.get("extraction_metadata", {}).get("runtime"),
                    "model": payload.get("extraction_metadata", {}).get("model", self.gemini_model),
                },
                ensure_ascii=True,
                indent=2,
            ),
            encoding="utf-8",
        )
        (bundle_dir / "extracted_data.json").write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
