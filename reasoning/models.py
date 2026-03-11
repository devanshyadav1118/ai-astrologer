"""Typed reasoning models for Phase 5 outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ReasoningFact:
    """Atomic fact collected during chart traversal."""

    id: str
    type: str
    source_step: str
    entities_involved: list[str]
    content: str
    strength_weight: float
    confidence: float
    supporting_rules: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SupportingFact:
    """Traceable supporting evidence for a reasoning node."""

    fact: str
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ReasoningNode:
    """Explainable reasoning tree node."""

    statement: str
    confidence: float
    strength_score: float
    supporting_facts: list[SupportingFact] = field(default_factory=list)
    classical_rules_applied: list[dict[str, Any]] = field(default_factory=list)
    novel_synthesis: bool = False
    children: list["ReasoningNode"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["supporting_facts"] = [fact.to_dict() for fact in self.supporting_facts]
        payload["children"] = [child.to_dict() for child in self.children]
        return payload
