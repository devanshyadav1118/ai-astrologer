"""Validation coverage for external extraction audit bundles."""

from __future__ import annotations

import json
from pathlib import Path

from extractor.external_validation import ExternalAuditValidator


def test_external_audit_validator_accepts_canonical_bundle(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "chunk_001"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "prompt.txt").write_text("prompt", encoding="utf-8")
    (bundle_dir / "metadata.json").write_text(json.dumps({"chunk_id": "chunk_001"}), encoding="utf-8")
    (bundle_dir / "extracted_data.json").write_text(
        json.dumps(
            {
                "rules": [
                    {
                        "rule_id": "r1",
                        "source_text": "If Sun is in Lagna.",
                        "conditions": {"operator": "AND", "clauses": []},
                        "effects": [],
                        "metadata": {"source_book": "Test"},
                    }
                ],
                "yogas": [],
                "descriptions": [],
                "calculations": [],
            }
        ),
        encoding="utf-8",
    )

    result = ExternalAuditValidator().validate_bundle(bundle_dir)

    assert result["valid"] is True
    assert result["stats"]["rules"] == 1


def test_external_audit_validator_flags_missing_files(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "chunk_002"
    bundle_dir.mkdir(parents=True)

    result = ExternalAuditValidator().validate_bundle(bundle_dir)

    assert result["valid"] is False
    assert result["errors"]
