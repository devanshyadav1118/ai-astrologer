# AI Astrologer — Codex Context

## What This Project Is
A Vedic astrology knowledge extraction and reasoning engine.
200–300 classical Vedic texts → structured Neo4j knowledge graph → explainable AI predictions.

## Architecture: 4 Modules
- extractor/   : PDF chunking + Gemini Pro extraction
- normaliser/  : Maps Sanskrit/English synonyms to canonical ontology terms
- storage/     : Neo4j knowledge graph + SQLite chunk index
- pipeline/    : Orchestrates all modules — one command per book

## Core Data Flow
PDF → chunker.py → gemini_client.py → stitcher.py → normaliser.py → validator.py → neo4j_client.py

## Canonical Name Convention
All entity names MUST be normalised before Neo4j storage.
- Planets:    SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN, RAHU, KETU
- Signs:      ARIES, TAURUS, GEMINI, CANCER, LEO, VIRGO, LIBRA, SCORPIO,
              SAGITTARIUS, CAPRICORN, AQUARIUS, PISCES
- Houses:     HOUSE_1 through HOUSE_12
- Nakshatras: ASHWINI, BHARANI, KRITTIKA ... (all caps)
- Yogas:      GAJA_KESARI, RAJA_YOGA ... (all caps with underscores)

## Coding Standards
- Type hints on all function signatures
- Single responsibility per file
- All secrets via .env using python-dotenv — never hardcoded
- Never modify files in data/raw/
- Every new function gets a corresponding test in tests/

## Stack
- Python 3.11, MacBook Air M2
- Gemini Pro (google-generativeai) — primary extraction LLM
- Neo4j Desktop (localhost:7474) — knowledge graph
- ChromaDB — vector store for semantic search
- pyswisseph — Swiss Ephemeris for chart calculation
- FastAPI + Streamlit — API and UI (Phases 4+)