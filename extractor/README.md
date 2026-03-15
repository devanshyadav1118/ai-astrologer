# AI Astrologer: Knowledge Extraction Pipeline

This folder contains the core logic for extracting structured astrological knowledge from PDF books using Gemini LLMs.

## Directory Structure

- `main.py`: Entry point for the pipeline.
- `core/`:
  - `config.py`: Central configuration, paths, and model rotation logic.
  - `chunker.py`: Handles PDF parsing and token-based chunking.
  - `extractor.py`: Core logic for Gemini API interaction, model rotation, and on-the-fly normalization.
  - `stitcher.py`: Merges and deduplicates rules from multiple chunks.
  - `inspector.py`: Generates quality reports and audits the extracted knowledge.

## Usage

### Run End-to-End Pipeline
```bash
python extractor/main.py all --book "Book Name"
```

### Individual Phases
- **Chunking Only:** `python extractor/main.py chunk --book "Book Name"`
- **Extraction Only:** `python extractor/main.py extract --book "Book Name"`
- **Stitching Only:** `python extractor/main.py stitch --book "Book Name"`
- **Inspection Only:** `python extractor/main.py inspect --book "Book Name"`

## Key Features

1. **Model Rotation:** Automatically switches between Gemini models (Flash, Pro) if quota limits are reached.
2. **On-the-fly Normalization:** Entities like "Surya" or "Lagna" are normalized to canonical forms (`SUN`, `HOUSE_1`) during extraction.
3. **Fuzzy Deduplication:** Identifies and merges overlapping or identical rules extracted from different chunks.
4. **Quality Reporting:** Generates a detailed audit of entity recognition rates and rule types.
