# AI Astrologer

Vedic astrology knowledge extraction and reasoning engine.

This project turns classical Jyotish source material into a structured knowledge graph, then uses chart calculations plus graph reasoning to generate explainable interpretations.

## Current Scope

Implemented through Phase 5:

- book extraction pipeline
- ontology normalisation
- Neo4j knowledge graph loading
- natal chart calculation and ingestion
- chart graph queries
- house-level symbolic reasoning
- full-chart reasoning orchestration
- novel-combination synthesis
- validation metrics and test-chart library

## Project Structure

- [extractor/](/Users/devanshydv/Desktop/Astrology%20final%20boss/extractor): PDF chunking, extraction, stitching, validation
- [normaliser/](/Users/devanshydv/Desktop/Astrology%20final%20boss/normaliser): ontology mapping and validation
- [storage/](/Users/devanshydv/Desktop/Astrology%20final%20boss/storage): Neo4j and SQLite persistence
- [chart/](/Users/devanshydv/Desktop/Astrology%20final%20boss/chart): natal chart calculation and astrology-specific derived data
- [reasoning/](/Users/devanshydv/Desktop/Astrology%20final%20boss/reasoning): Phase 5 reasoning engine
- [pipeline/](/Users/devanshydv/Desktop/Astrology%20final%20boss/pipeline): CLI entry points for books, charts, and validation
- [tests/](/Users/devanshydv/Desktop/Astrology%20final%20boss/tests): automated coverage

## Main Flows

### Book to Rules

`PDF -> chunker -> Gemini extraction -> stitcher -> normaliser -> validator -> Neo4j`

Main entry point:

- [pipeline/run_book.py](/Users/devanshydv/Desktop/Astrology%20final%20boss/pipeline/run_book.py)

### Birth Data to Chart Graph

`birth data -> chart calculator -> chart JSON -> Neo4j chart subgraph`

Main entry point:

- [pipeline/run_chart.py](/Users/devanshydv/Desktop/Astrology%20final%20boss/pipeline/run_chart.py)

### Chart Graph to Reasoning

`chart graph -> house analysis -> full chart synthesis -> validation`

Main entry points:

- [pipeline/analyze_house.py](/Users/devanshydv/Desktop/Astrology%20final%20boss/pipeline/analyze_house.py)
- [pipeline/analyze_chart.py](/Users/devanshydv/Desktop/Astrology%20final%20boss/pipeline/analyze_chart.py)
- [pipeline/validate_phase5.py](/Users/devanshydv/Desktop/Astrology%20final%20boss/pipeline/validate_phase5.py)

## Phase Status

### Completed

- Phase 0-4 base system
- Phase 5 implementation

### Phase 5 Caveat

Phase 5 is implementation-complete, but not fully validation-complete in the strict roadmap sense.

What is already done:

- reasoning facts
- reasoning tree output
- full-chart orchestration
- ranking
- dependency mapping
- novel synthesis
- 20-case validation library

What still depends on project data:

- loading more processed books and rules into Neo4j
- ingesting more real charts
- running the 20-case validator against real chart ids
- checking whether the target metrics are met

See:

- [Phase5.md](/Users/devanshydv/Desktop/Astrology%20final%20boss/Phase5.md)
- [reasoning/PHASE5_DELIVERABLES.md](/Users/devanshydv/Desktop/Astrology%20final%20boss/reasoning/PHASE5_DELIVERABLES.md)
- [reasoning/PHASE5_VALIDATION_REPORT.md](/Users/devanshydv/Desktop/Astrology%20final%20boss/reasoning/PHASE5_VALIDATION_REPORT.md)

## Useful Commands

Run targeted Phase 5 tests:

```bash
./.venv/bin/pytest tests/test_house_reasoner.py tests/test_chart_reasoner.py tests/test_reasoning_models.py tests/test_chart_queries.py tests/test_validation.py tests/test_novel_synthesizer.py tests/test_phase5_library.py
```

Run one chart calculation:

```bash
./.venv/bin/python pipeline/run_chart.py --chart-id demo_chart --date 1990-05-15 --time 14:30:00 --latitude 26.9124 --longitude 75.7873 --timezone 5.5 --dry-run
```

Analyze one stored chart:

```bash
./.venv/bin/python pipeline/analyze_chart.py --chart-id demo_chart --focus-area Career
```

Validate Phase 5 library:

```bash
./.venv/bin/python pipeline/validate_phase5.py --library reasoning/test_chart_library.json
```

## Recommended Next Step

Tomorrow’s highest-value work:

1. Process 2-3 more books and load their rules into Neo4j.
2. Ingest 5-10 real charts.
3. Replace placeholder validation cases with actual chart ids and expected outcomes.
4. Run the Phase 5 validator on those real charts.
