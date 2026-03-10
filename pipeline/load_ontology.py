"""Ontology loading entry points."""

from pathlib import Path


def ontology_directory(project_root: Path) -> Path:
    """Return the ontology directory location."""
    return project_root / "normaliser" / "ontology"
