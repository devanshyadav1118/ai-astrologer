"""Validation helpers for external extraction audit bundles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ExternalAuditValidator:
    """Validate audit bundles emitted by the external extraction bridge."""

    def validate_bundle(self, bundle_dir: str | Path) -> dict[str, Any]:
        path = Path(bundle_dir)
        result = {
            "bundle_dir": str(path),
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {
                "rules": 0,
                "yogas": 0,
                "descriptions": 0,
                "calculations": 0,
            },
        }
        required = ["prompt.txt", "metadata.json", "extracted_data.json"]
        for name in required:
            if not (path / name).exists():
                result["errors"].append(f"missing required file: {name}")
                result["valid"] = False

        if not result["valid"]:
            return result

        payload = json.loads((path / "extracted_data.json").read_text(encoding="utf-8"))
        for key in ("rules", "yogas", "descriptions", "calculations"):
            value = payload.get(key, [])
            if not isinstance(value, list):
                result["errors"].append(f"{key} must be a list")
                result["valid"] = False
                continue
            result["stats"][key] = len(value)

        for rule in payload.get("rules", []):
            if "rule_id" not in rule or "source_text" not in rule:
                result["errors"].append("rule missing canonical fields")
                result["valid"] = False

        if result["stats"]["rules"] == 0 and result["stats"]["yogas"] == 0:
            result["warnings"].append("bundle has no extracted rules or yogas")

        return result
