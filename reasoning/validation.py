"""Validation helpers for Phase 5 reasoning outputs."""

from __future__ import annotations

from time import perf_counter
import json
from pathlib import Path
from typing import Any, Callable


class Phase5Validator:
    """Measure output quality against the Phase 5 roadmap targets."""

    def compute_metrics(
        self,
        analysis: dict[str, Any],
        expected_rule_ids: set[str] | None = None,
        expected_contradiction_houses: set[int] | None = None,
        novel_review_scores: list[bool] | None = None,
        elapsed_seconds: float | None = None,
    ) -> dict[str, float]:
        houses = analysis.get("house_analyses", [])
        ranked = analysis.get("ranked_interpretations", [])
        expected_rule_ids = expected_rule_ids or set()
        expected_contradiction_houses = expected_contradiction_houses or set()
        novel_review_scores = novel_review_scores or []
        reasoning_chain_completeness = self._reasoning_chain_completeness(houses)
        classical_rule_coverage = self._classical_rule_coverage(houses, expected_rule_ids)
        contradiction_handling = self._contradiction_handling(houses, expected_contradiction_houses)
        novel_synthesis_quality = self._novel_synthesis_quality(houses, novel_review_scores)
        response_time_seconds = float(elapsed_seconds or 0.0)
        return {
            "reasoning_chain_completeness": reasoning_chain_completeness,
            "classical_rule_coverage": classical_rule_coverage,
            "contradiction_handling": contradiction_handling,
            "novel_synthesis_quality": novel_synthesis_quality,
            "response_time_seconds": round(response_time_seconds, 3),
            "ranked_output_count": float(len(ranked)),
        }

    def measure_analysis(
        self,
        analysis_fn: Callable[[], dict[str, Any]],
        expected_rule_ids: set[str] | None = None,
        expected_contradiction_houses: set[int] | None = None,
        novel_review_scores: list[bool] | None = None,
    ) -> dict[str, Any]:
        start = perf_counter()
        analysis = analysis_fn()
        elapsed = perf_counter() - start
        return {
            "analysis": analysis,
            "metrics": self.compute_metrics(
                analysis=analysis,
                expected_rule_ids=expected_rule_ids,
                expected_contradiction_houses=expected_contradiction_houses,
                novel_review_scores=novel_review_scores,
                elapsed_seconds=elapsed,
            ),
        }

    def evaluate_library(
        self,
        library_path: str | Path,
        analysis_provider: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> dict[str, Any]:
        with Path(library_path).open(encoding="utf-8") as handle:
            payload = json.load(handle)
        cases = payload.get("cases", [])
        reports: list[dict[str, Any]] = []
        aggregate = {
            "reasoning_chain_completeness": 0.0,
            "classical_rule_coverage": 0.0,
            "contradiction_handling": 0.0,
            "novel_synthesis_quality": 0.0,
            "response_time_seconds": 0.0,
        }
        for case in cases:
            measured = self.measure_analysis(
                lambda case=case: analysis_provider(case),
                expected_rule_ids=set(case.get("expected_rule_ids", [])),
                expected_contradiction_houses={int(item) for item in case.get("expected_contradiction_houses", [])},
                novel_review_scores=[bool(item) for item in case.get("novel_review_scores", [])],
            )
            reports.append(
                {
                    "case_id": case.get("case_id"),
                    "title": case.get("title"),
                    "metrics": measured["metrics"],
                }
            )
            for key in aggregate:
                aggregate[key] += float(measured["metrics"][key])
        total = len(reports) or 1
        for key in aggregate:
            aggregate[key] = round(aggregate[key] / total, 3)
        return {"case_count": len(reports), "reports": reports, "aggregate_metrics": aggregate}

    def _reasoning_chain_completeness(self, houses: list[dict[str, Any]]) -> float:
        if not houses:
            return 0.0
        completed = 0
        for house in houses:
            tree = house.get("reasoning_tree", {})
            if house.get("facts") and tree.get("children") and tree.get("supporting_facts"):
                completed += 1
        return round(completed / len(houses), 3)

    def _classical_rule_coverage(self, houses: list[dict[str, Any]], expected_rule_ids: set[str]) -> float:
        if not expected_rule_ids:
            applicable = [house for house in houses if house.get("supporting_rules")]
            if not applicable:
                return 0.0
            return round(len(applicable) / len(houses), 3)
        seen = {
            str(rule["rule_id"])
            for house in houses
            for rule in house.get("supporting_rules", [])
            if rule.get("rule_id") is not None
        }
        return round(len(seen & expected_rule_ids) / len(expected_rule_ids), 3)

    def _contradiction_handling(
        self,
        houses: list[dict[str, Any]],
        expected_contradiction_houses: set[int],
    ) -> float:
        detected = {int(house["house"]) for house in houses if house.get("contradictions")}
        if not expected_contradiction_houses:
            return round(len(detected) / len(houses), 3) if houses else 0.0
        return round(len(detected & expected_contradiction_houses) / len(expected_contradiction_houses), 3)

    def _novel_synthesis_quality(self, houses: list[dict[str, Any]], review_scores: list[bool]) -> float:
        if review_scores:
            return round(sum(1 for score in review_scores if score) / len(review_scores), 3)
        novel = [
            house for house in houses if house.get("reasoning_tree", {}).get("novel_synthesis")
        ]
        if not novel:
            return 1.0
        complete = [house for house in novel if house.get("reasoning_tree", {}).get("children")]
        return round(len(complete) / len(novel), 3)
