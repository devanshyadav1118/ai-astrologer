"""Canonical entity normalisation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
import unicodedata


class NormalisationError(ValueError):
    """Raised when a value cannot be mapped to a canonical form."""


def canonicalise_token(token: str, synonym_map: dict[str, str]) -> str:
    """Map a token to its canonical uppercase identifier."""
    cleaned = token.strip().casefold()
    if not cleaned:
        raise NormalisationError("token cannot be empty")
    try:
        return synonym_map[cleaned]
    except KeyError as exc:
        raise NormalisationError(f"unknown token: {token}") from exc


class AstrologyNormaliser:
    """Maps astrological terms and synonyms to canonical ontology identifiers.

    Supports all 9 ontology files. Each file has its own JSON shape, so the
    loader handles them individually rather than assuming a uniform structure.

    File shapes handled:
        Flat lists   — planets, signs, houses, nakshatras, yogas, concepts
                       Each item has canonical_name + synonyms at the top level.

        Nested dicts — aspects, dignity, dashas
                       Contain several named sub-lists, each with their own
                       canonical_name / synonyms entries. Only sub-lists that
                       carry canonical entity terms are indexed.
    """

    def __init__(self, ontology_dir: str | Path = "normaliser/ontology") -> None:
        self.ontology_dir = Path(ontology_dir)
        self.synonym_map: dict[str, str] = {}
        self._phrase_keys: list[str] = []
        self._build_synonym_map()

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def normalise(self, term: str) -> str | None:
        """Return the canonical entity for *term*, or ``None`` if unknown."""
        if not term:
            return None
        cleaned = self._clean_term(term)
        if not cleaned:
            return None
        direct = self.synonym_map.get(cleaned)
        if direct is not None:
            return direct
        for fuzzy in self._generate_fuzzy_candidates(cleaned):
            canonical = self.synonym_map.get(fuzzy)
            if canonical is not None:
                return canonical
        return None

    def normalise_batch(self, terms: list[str]) -> dict[str, str | None]:
        """Normalise a list of terms, preserving the original keys."""
        return {term: self.normalise(term) for term in terms}

    def get_all_canonicals(self) -> list[str]:
        """Return all unique canonical identifiers present in the ontology."""
        return sorted(set(self.synonym_map.values()))

    def extract_known_terms(self, text: str) -> list[str]:
        """Return matched ontology terms from *text* using normalised source phrases."""
        if not text:
            return []
        normalised_text = self._normalise_text_for_search(text)
        found: set[str] = set()
        for phrase in self._phrase_keys:
            pattern = rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])"
            if re.search(pattern, normalised_text):
                found.add(phrase)
        return sorted(found)

    # ------------------------------------------------------------------ #
    # Loading                                                              #
    # ------------------------------------------------------------------ #

    def _build_synonym_map(self) -> None:
        """Populate synonym_map from all 9 ontology files."""
        loaders = [
            # Flat list files — each item has canonical_name + synonyms
            self._load_flat_list_file("planets.json",    top_key="planets"),
            self._load_flat_list_file("signs.json",      top_key="signs"),
            self._load_flat_list_file("houses.json",     top_key="houses"),
            self._load_flat_list_file("nakshatras.json", top_key="nakshatras"),
            self._load_flat_list_file("yogas.json",      top_key="yogas"),
            self._load_flat_list_file("concepts.json",   top_key="concepts"),
            # Nested dict files — each requires targeted sub-list extraction
            self._load_aspects(),
            self._load_dignity(),
            self._load_dashas(),
        ]
        for entry_set in loaders:
            for canonical, synonyms in entry_set:
                self._register(canonical, synonyms)

        self._phrase_keys = sorted(self.synonym_map.keys(), key=len, reverse=True)

    def _load_flat_list_file(
        self, filename: str, top_key: str
    ) -> list[tuple[str, list[str]]]:
        """Load a simple ``{top_key: [{canonical_name, synonyms, ...}]}`` file."""
        data = self._read_json(filename)
        if data is None:
            return []
        entries = []
        for item in data.get(top_key, []):
            canonical = item.get("canonical_name")
            if canonical:
                entries.append((canonical, item.get("synonyms", [])))
        return entries

    def _load_aspects(self) -> list[tuple[str, list[str]]]:
        """aspects.json has two sub-lists with canonical_name+synonyms:
            aspects.aspect_types       — CONJUNCTION, OPPOSITION, etc.
            aspects.aspect_modification_rules — keyed by 'rule', no synonyms, skip.
            aspects.special_aspects    — keyed by 'planet', not canonical entities.
        Only aspect_types carries canonical entity terms.
        """
        data = self._read_json("aspects.json")
        if data is None:
            return []
        entries = []
        aspects_block = data.get("aspects", {})
        for item in aspects_block.get("aspect_types", []):
            canonical = item.get("canonical_name")
            if canonical:
                entries.append((canonical, item.get("synonyms", [])))
        return entries

    def _load_dignity(self) -> list[tuple[str, list[str]]]:
        """dignity.json has three sub-lists with canonical_name+synonyms:
            dignity.dignity_types          — EXALTATION, OWN_SIGN, etc.
            dignity.house_position_modifiers — KENDRA, TRIKONA, etc.
            dignity.special_conditions     — COMBUSTION, RETROGRADE, etc.
        aspect_dignity_modifiers and strength_interpretation have no canonical_name.
        """
        data = self._read_json("dignity.json")
        if data is None:
            return []
        entries = []
        dignity_block = data.get("dignity", {})
        for sub_key in ("dignity_types", "house_position_modifiers", "special_conditions"):
            for item in dignity_block.get(sub_key, []):
                canonical = item.get("canonical_name")
                if canonical:
                    entries.append((canonical, item.get("synonyms", [])))
        return entries

    def _load_dashas(self) -> list[tuple[str, list[str]]]:
        """dashas.json has no canonical_name/synonyms lists — it holds dasha
        system metadata. We don't register any entity terms from it, but we
        *do* expose the nakshatra→dasha_lord mapping as a standalone lookup.

        This method returns an empty list so the main build loop stays uniform.
        The nakshatra mapping is available via ``nakshatra_dasha_lord()``.
        """
        data = self._read_json("dashas.json")
        if data is None:
            return []
        # Store nakshatra→lord mapping for runtime use (Phase 9)
        self._nakshatra_to_dasha_lord: dict[str, str] = (
            data.get("dashas", {}).get("nakshatra_to_dasha_lord", {})
        )
        return []

    # ------------------------------------------------------------------ #
    # Runtime helpers exposed for Phase 9                                  #
    # ------------------------------------------------------------------ #

    def nakshatra_dasha_lord(self, nakshatra_canonical: str) -> str | None:
        """Return the Vimshottari dasha lord for a given nakshatra canonical name."""
        mapping = getattr(self, "_nakshatra_to_dasha_lord", {})
        return mapping.get(nakshatra_canonical.upper())

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _register(self, canonical: str, synonyms: list[str]) -> None:
        """Add a canonical name and all its synonyms to the map."""
        self.synonym_map[canonical.casefold()] = canonical
        for synonym in synonyms:
            key = synonym.strip().casefold()
            if key:
                self.synonym_map[key] = canonical

    def _read_json(self, filename: str) -> dict[str, Any] | None:
        filepath = self.ontology_dir / filename
        if not filepath.exists():
            return None
        with filepath.open(encoding="utf-8") as handle:
            return json.load(handle)

    def _clean_term(self, term: str) -> str:
        normalized = unicodedata.normalize("NFKD", term)
        stripped = "".join(char for char in normalized if not unicodedata.combining(char))
        return " ".join(stripped.strip().casefold().split())

    def _normalise_text_for_search(self, text: str) -> str:
        lowered = self._clean_term(text)
        lowered = re.sub(r"[_/]", " ", lowered)
        lowered = re.sub(r"[^a-z0-9'\s]", " ", lowered)
        return " ".join(lowered.split())

    def _generate_fuzzy_candidates(self, term: str) -> list[str]:
        candidates: set[str] = set()
        if term.endswith("ine") and len(term) > 4:
            candidates.add(term[:-3])
        if term.endswith("ian") and len(term) > 4:
            candidates.add(term[:-3])
        if term.endswith("ic") and len(term) > 3:
            candidates.add(term[:-2])
        if term.endswith("al") and len(term) > 3:
            candidates.add(term[:-2])
        if term.endswith("sh") and f"{term}a" in self.synonym_map:
            candidates.add(f"{term}a")
        return [c for c in candidates if c]


def load_ontology_file(filepath: str | Path) -> dict[str, list[dict[str, Any]]]:
    """Load a single ontology JSON file."""
    with Path(filepath).open(encoding="utf-8") as handle:
        return json.load(handle)
