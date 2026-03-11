"""Phase 2 chunker coverage."""

from __future__ import annotations

from extractor.chunker import build_chunks_from_pages


def test_build_chunks_from_pages_preserves_metadata() -> None:
    pages = [
        {
            "page_number": 1,
            "text": "Chapter 1\n\nSurya in Lagna gives strength.\n\nGuru in Mesha gives wisdom.",
        },
        {
            "page_number": 2,
            "text": "Chapter 1\n\nChandra in 4th gives comfort.",
        },
    ]
    chunks = build_chunks_from_pages(pages=pages, book_id="sample_book", tokens_per_chunk=12)

    assert len(chunks) >= 2
    assert chunks[0]["chunk_id"] == "sample_book_001"
    assert chunks[0]["chapter"] == "Chapter 1"
    assert chunks[0]["metadata"]["book_id"] == "sample_book"
    assert chunks[0]["metadata"]["word_count"] > 0


def test_build_chunks_from_pages_tracks_page_ranges() -> None:
    pages = [
        {"page_number": 3, "text": "Chapter 2\n\nOne paragraph with enough words to fill a chunk."},
        {"page_number": 4, "text": "Another paragraph with enough words to force another chunk."},
    ]
    chunks = build_chunks_from_pages(pages=pages, book_id="sample_book", tokens_per_chunk=8)

    assert all(chunk["page_range"] for chunk in chunks)
    assert chunks[0]["page_range"] == "3"


def test_build_chunks_from_pages_splits_oversized_single_block() -> None:
    long_text = " ".join(
        [f"Sentence {index} ends here." for index in range(1, 61)]
    )
    pages = [{"page_number": 1, "text": f"Chapter 1\n\n{long_text}"}]

    chunks = build_chunks_from_pages(pages=pages, book_id="sample_book", tokens_per_chunk=80)

    assert len(chunks) > 1
    assert all(chunk["metadata"]["word_count"] < 220 for chunk in chunks)
