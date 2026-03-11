Context Checklist for Codex
Before starting each task, ensure Codex has:

AGENTS.md — updated with current architecture
Ontology files — planets.json, signs.json, houses.json, nakshatras.json
normaliser.py — with working normalise() function
Neo4j schema — Cypher constraints from Phase 1
Your existing extraction prompt v2.0 — keep unchanged
Example chunk output — show Codex what Gemini currently returns


Critical Rules to Enforce
Tell Codex explicitly:

Never modify ontology automatically — unknown entities must be human-reviewed
Always normalise before storing — raw entity names never touch Neo4j
Track everything in SQLite — processing status, warnings, unknown entities
Resume capability required — if pipeline crashes, must resume from last checkpoint
Single source of truth — Neo4j is authoritative, flat JSON files are archival only