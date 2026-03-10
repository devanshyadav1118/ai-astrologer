"""Canonical entity normalisation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


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
    """Maps astrological terms and synonyms to canonical ontology identifiers."""

    _ONTOLOGY_FILES = (
        "planets.json",
        "signs.json",
        "houses.json",
        "nakshatras.json",
        "yogas.json",
    )

    def __init__(self, ontology_dir: str | Path = "normaliser/ontology") -> None:
        self.ontology_dir = Path(ontology_dir)
        self.synonym_map: dict[str, str] = {}
        self._phrase_keys: list[str] = []
        self._build_synonym_map()

    def _build_synonym_map(self) -> None:
        for filename in self._ONTOLOGY_FILES:
            filepath = self.ontology_dir / filename
            if not filepath.exists():
                continue
            with filepath.open(encoding="utf-8") as handle:
                payload = json.load(handle)
            for entities in payload.values():
                for entity in entities:
                    canonical = entity["canonical_name"]
                    self.synonym_map[canonical.casefold()] = canonical
                    for synonym in entity.get("synonyms", []):
                        self.synonym_map[synonym.casefold()] = canonical
        self._phrase_keys = sorted(self.synonym_map.keys(), key=len, reverse=True)

    def normalise(self, term: str) -> str | None:
        """Return the canonical entity for a term or `None` if unknown."""
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
        """Normalise a list of terms while preserving the original keys."""
        return {term: self.normalise(term) for term in terms}

    def get_all_canonicals(self) -> list[str]:
        """Return all unique canonical identifiers in the ontology."""
        return sorted(set(self.synonym_map.values()))

    def extract_known_terms(self, text: str) -> list[str]:
        """Extract known ontology terms and synonyms found in arbitrary text."""
        if not text:
            return []
        normalised_text = self._normalise_text_for_search(text)
        matches: list[str] = []
        for phrase in self._phrase_keys:
            pattern = rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])"
            if re.search(pattern, normalised_text):
                matches.append(phrase)
        return matches

    def _clean_term(self, term: str) -> str:
        return " ".join(term.strip().casefold().split())

    def _normalise_text_for_search(self, text: str) -> str:
        lowered = text.casefold()
        lowered = re.sub(r"[_/]", " ", lowered)
        lowered = re.sub(r"[^a-z0-9'\s]", " ", lowered)
        return " ".join(lowered.split())

    def _generate_fuzzy_candidates(self, term: str) -> list[str]:
        candidates = {term}
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
        return [candidate for candidate in candidates if candidate]


def load_ontology_file(filepath: str | Path) -> dict[str, list[dict[str, Any]]]:
    """Load a single ontology JSON file."""
    with Path(filepath).open(encoding="utf-8") as handle:
        return json.load(handle)
