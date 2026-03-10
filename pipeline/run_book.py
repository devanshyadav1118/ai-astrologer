"""Book-level pipeline entry points."""

from pathlib import Path


def validate_book_path(pdf_path: Path) -> None:
    """Fail fast if a PDF path is not usable."""
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("book input must be a PDF file")
