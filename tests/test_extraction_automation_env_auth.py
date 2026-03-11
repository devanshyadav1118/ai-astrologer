"""Coverage for env-based auth in Extraction Automation scripts."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType


def _load_module(module_name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_process_pdf_chapters_prefers_env_api(monkeypatch, tmp_path: Path) -> None:
    script_path = Path("Extraction Automation/scripts/process_pdf_chapters.py")
    module = _load_module("ea_process_pdf_chapters_test", script_path)
    output_path = tmp_path / "out.json"

    def fake_api(prompt_text: str, api_key: str) -> str:
        assert api_key == "test-key"
        return json.dumps(
            {
                "rules": [],
                "descriptions": [],
                "calculation_methods": [],
                "yogas": [],
            }
        )

    def fail_subprocess(*args, **kwargs):
        raise AssertionError("CLI path should not be used when GEMINI_API_KEY is set")

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(module, "run_gemini_via_api", fake_api)
    monkeypatch.setattr(subprocess, "run", fail_subprocess)

    module.run_gemini("prompt text", output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["rules"] == []


def test_cli_extract_command_accepts_env_key(monkeypatch, tmp_path: Path, capsys) -> None:
    script_path = Path("Extraction Automation/scripts/cli.py")
    module = _load_module("ea_cli_test", script_path)
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True)
    input_dir = tmp_path / "input"
    input_dir.mkdir(parents=True)
    (input_dir / "astrology_full_book.pdf").write_text("pdf", encoding="utf-8")
    monkeypatch.chdir(scripts_dir)

    args = type("Args", (), {"validate": False})()
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(module, "run_command", lambda cmd, description: True)

    ok = module.extract_command(args)

    stdout = capsys.readouterr().out
    assert ok is True
    assert "Using GEMINI_API_KEY from environment" in stdout
