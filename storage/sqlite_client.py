"""SQLite path helpers for local metadata storage."""

from pathlib import Path


def default_sqlite_path(project_root: Path) -> Path:
    """Return the default metadata database path."""
    return project_root / "data" / "db" / "metadata.sqlite3"
