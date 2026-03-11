"""PDF chunking primitives for the extraction pipeline."""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
import re
from typing import Any

from PyPDF2 import PdfReader

LOGGER = logging.getLogger(__name__)
CHAPTER_PATTERN = re.compile(r"(?im)^(chapter|adhyaya|canto|section)\s+[\w.\-:() ]+$")


@dataclass(slots=True)
class ChunkRequest:
    """Describes a source PDF that will be chunked later in the pipeline."""

    pdf_path: Path
    chunk_size: int = 2000
    overlap: int = 200


def validate_chunk_request(request: ChunkRequest) -> None:
    """Validate a chunk request before extraction work begins."""
    if request.chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if request.overlap < 0:
        raise ValueError("overlap cannot be negative")
    if request.overlap >= request.chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")


def chunk_pdf(
    pdf_path: str | Path,
    output_dir: str | Path,
    tokens_per_chunk: int = 500,
) -> list[dict[str, Any]]:
    """Extract a PDF into semantic text chunks and persist them as JSON."""
    pdf_file = Path(pdf_path)
    if pdf_file.suffix.lower() != ".pdf":
        raise ValueError("book input must be a PDF file")
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_file}")
    if tokens_per_chunk <= 0:
        raise ValueError("tokens_per_chunk must be greater than zero")

    reader = PdfReader(str(pdf_file))
    pages = [
        {
            "page_number": page_number,
            "text": _clean_page_text(page.extract_text() or ""),
        }
        for page_number, page in enumerate(reader.pages, start=1)
    ]
    chunks = build_chunks_from_pages(pages=pages, book_id=pdf_file.stem, tokens_per_chunk=tokens_per_chunk)
    _write_chunks(chunks, Path(output_dir))
    LOGGER.info("Created %s chunks for %s", len(chunks), pdf_file.stem)
    return chunks


def build_chunks_from_pages(
    pages: list[dict[str, Any]],
    book_id: str,
    tokens_per_chunk: int = 500,
) -> list[dict[str, Any]]:
    """Build chunk payloads from already extracted page text."""
    if tokens_per_chunk <= 0:
        raise ValueError("tokens_per_chunk must be greater than zero")

    units = _extract_semantic_units(pages)
    chunks: list[dict[str, Any]] = []
    current_units: list[dict[str, Any]] = []
    current_tokens = 0

    for unit in units:
        unit_tokens = _estimate_tokens(unit["text"])
        if current_units and current_tokens + unit_tokens > tokens_per_chunk:
            chunks.append(_build_chunk_payload(book_id, len(chunks) + 1, current_units))
            current_units = []
            current_tokens = 0
        current_units.append(unit)
        current_tokens += unit_tokens

    if current_units:
        chunks.append(_build_chunk_payload(book_id, len(chunks) + 1, current_units))
    return chunks


def _extract_semantic_units(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    current_chapter = "Unknown"

    for page in pages:
        text = page.get("text", "")
        if not text.strip():
            continue
        blocks = [block.strip() for block in re.split(r"\n{2,}", text) if block.strip()]
        if not blocks:
            blocks = [text.strip()]
        for block in blocks:
            current_chapter = _detect_chapter(block) or current_chapter
            for sub_block in _split_oversized_block(block):
                units.append(
                    {
                        "text": sub_block,
                        "page_number": int(page["page_number"]),
                        "chapter": current_chapter,
                    }
                )
    return units


def _build_chunk_payload(book_id: str, chunk_number: int, units: list[dict[str, Any]]) -> dict[str, Any]:
    text = "\n\n".join(unit["text"] for unit in units)
    page_numbers = [int(unit["page_number"]) for unit in units]
    chapter = units[0]["chapter"] if units else "Unknown"
    chunk_id = f"{book_id}_{chunk_number:03d}"
    return {
        "chunk_id": chunk_id,
        "chunk_number": chunk_number,
        "text": text,
        "page_range": _format_page_range(page_numbers),
        "chapter": chapter,
        "metadata": {
            "book_id": book_id,
            "word_count": len(text.split()),
            "has_sanskrit": _contains_sanskrit_markers(text),
            "page_start": min(page_numbers),
            "page_end": max(page_numbers),
        },
    }


def _clean_page_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _detect_chapter(text: str) -> str | None:
    for line in text.splitlines()[:3]:
        candidate = line.strip()
        if CHAPTER_PATTERN.match(candidate):
            return candidate
    return None


def _estimate_tokens(text: str) -> int:
    return max(1, round(len(re.findall(r"\S+", text)) * 1.3))


def _split_oversized_block(block: str, max_words: int = 180) -> list[str]:
    words = block.split()
    if len(words) <= max_words:
        return [block]

    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", block)
        if sentence.strip()
    ]
    if len(sentences) <= 1:
        return _split_by_word_window(words, max_words=max_words)

    parts: list[str] = []
    current: list[str] = []
    current_words = 0
    for sentence in sentences:
        sentence_words = sentence.split()
        if current and current_words + len(sentence_words) > max_words:
            parts.append(" ".join(current))
            current = []
            current_words = 0
        current.append(sentence)
        current_words += len(sentence_words)
    if current:
        parts.append(" ".join(current))
    return parts


def _split_by_word_window(words: list[str], max_words: int) -> list[str]:
    return [
        " ".join(words[index : index + max_words])
        for index in range(0, len(words), max_words)
    ]


def _contains_sanskrit_markers(text: str) -> bool:
    lowered = text.casefold()
    return any(marker in lowered for marker in ("shloka", "sloka", "lagna", "bhava", "graha"))


def _format_page_range(page_numbers: list[int]) -> str:
    start = min(page_numbers)
    end = max(page_numbers)
    return f"{start}" if start == end else f"{start}-{end}"


def _write_chunks(chunks: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for chunk in chunks:
        with (output_dir / f"{chunk['chunk_id']}.json").open("w", encoding="utf-8") as handle:
            json.dump(chunk, handle, ensure_ascii=True, indent=2)
