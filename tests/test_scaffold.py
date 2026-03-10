"""Basic scaffold verification for Phase 0."""

from __future__ import annotations

from pathlib import Path

from extractor.chunker import ChunkRequest, validate_chunk_request
from normaliser.normaliser import NormalisationError, canonicalise_token
from pipeline.load_ontology import ontology_directory
from storage.sqlite_client import default_sqlite_path


def test_validate_chunk_request_accepts_valid_values() -> None:
    validate_chunk_request(ChunkRequest(pdf_path=Path("sample.pdf")))


def test_canonicalise_token_maps_case_insensitively() -> None:
    synonym_map = {"surya": "SUN", "sun": "SUN"}
    assert canonicalise_token(" Surya ", synonym_map) == "SUN"


def test_canonicalise_token_rejects_unknown_value() -> None:
    try:
        canonicalise_token("unknown", {})
    except NormalisationError:
        return
    raise AssertionError("expected NormalisationError")


def test_project_paths_follow_phase_zero_layout() -> None:
    project_root = Path.cwd()
    assert ontology_directory(project_root) == project_root / "normaliser" / "ontology"
    assert default_sqlite_path(project_root) == project_root / "data" / "db" / "metadata.sqlite3"
