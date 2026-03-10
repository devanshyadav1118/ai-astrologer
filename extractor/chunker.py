"""PDF chunking primitives for the extraction pipeline."""

from dataclasses import dataclass
from pathlib import Path


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
