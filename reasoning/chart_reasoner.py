"""Full-chart orchestration for Phase 5 & 7."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reasoning.house_reasoner import HouseReasoner
from reasoning.yoga_detector import YogaDetector
from reasoning.propagation import PropagationEngine


class ChartReasoner:
    """Combine twelve house analyses and detected yogas into chart-level themes."""

    def __init__(
        self, 
        house_reasoner: HouseReasoner, 
        ontology_dir: str | Path = "normaliser/ontology",
        yoga_detector: YogaDetector | None = None,
        propagation_engine: PropagationEngine | None = None
    ) -> None:
        self.house_reasoner = house_reasoner
        self.ontology_dir = Path(ontology_dir)
        self.yoga_detector = yoga_detector or YogaDetector(self.ontology_dir)
        self.propagation_engine = propagation_engine or PropagationEngine()
        self.concepts = self._load_concepts()

    def analyze_full_chart(self, chart_id: str, focus_areas: list[str] | None = None) -> dict[str, Any]:
        normalized_focus = {area.strip().lower() for area in (focus_areas or []) if area.strip()}
        
        # 1. House-by-House Analysis (Phase 5)
        houses: list[dict[str, Any]] = []
        for house_number in range(1, 13):
            analysis = self.house_reasoner.analyze_house(chart_id, house_number)
            if analysis is not None:
                houses.append(analysis)
        
        # 2. Yoga Detection (Phase 7)
        full_chart_data = self.house_reasoner.queries.get_full_chart_data(chart_id)
        detected_yogas = self.yoga_detector.detect_yogas(full_chart_data)
        
        # 3. House Influence Propagation (Phase 8)
        propagation_results = self.propagation_engine.compute_house_importance(full_chart_data, detected_yogas)
        
        ranked = sorted(houses, key=lambda item: float(item.get("rank_score", 0.0)), reverse=True)
        dependency_graph = self._dependency_graph(houses)
        
        return {
            "chart_id": chart_id,
            "focus_areas": sorted(normalized_focus),
            "house_analyses": houses,
            "detected_yogas": detected_yogas,
            "house_importance": propagation_results["house_importance"],
            "dominant_themes": propagation_results["dominant_themes"],
            "propagation_metadata": {
                "iterations": propagation_results["iterations"],
                "convergence_delta": propagation_results["convergence_delta"],
                "edges": propagation_results.get("edges", [])
            },
            "dependency_map": dependency_graph["dependency_map"],
            "dependency_resolution": {
                "order": dependency_graph["order"],
                "circular_dependencies": dependency_graph["cycles"],
            },
            "ranked_interpretations": self._rank_interpretations(ranked, normalized_focus),
            "dominant_patterns": self._dominant_patterns(houses),
            "life_theme_reports": self._life_theme_reports(houses),
            "chart_fingerprint": self._chart_fingerprint(houses),
        }

    def _load_concepts(self) -> list[dict[str, Any]]:
        with (self.ontology_dir / "concepts.json").open(encoding="utf-8") as handle:
            payload = json.load(handle)
        return [item for item in payload["concepts"] if isinstance(item, dict)]

    def _rank_interpretations(
        self,
        analyses: list[dict[str, Any]],
        focus_areas: set[str],
    ) -> list[dict[str, Any]]:
        cross_verification = self._cross_verification_scores(analyses)
        max_rank_score = max((float(item.get("rank_score", 0.0)) for item in analyses), default=1.0)
        total = len(analyses) or 1
        ranked: list[dict[str, Any]] = []
        for index, analysis in enumerate(analyses, start=1):
            house_key = int(analysis["house"])
            focus_boost = 1.0 if str(analysis["theme"]).lower() in focus_areas else 0.0
            normalized_rank = float(analysis["rank_score"]) / max_rank_score if max_rank_score else 0.0
            final_score = round(
                (normalized_rank * 10.0 * 0.4)
                + (float(analysis["confidence"]) * 10.0 * 0.3)
                + (focus_boost * 10.0 * 0.2)
                + (cross_verification[house_key] * 10.0 * 0.1),
                3,
            )
            percentile = index / total
            ranked.append(
                {
                    "house": house_key,
                    "theme": analysis["theme"],
                    "score": final_score,
                    "base_rank_score": analysis["rank_score"],
                    "confidence": analysis["confidence"],
                    "cross_verification": cross_verification[house_key],
                    "focus_match": focus_boost > 0.0,
                    "summary": analysis["synthesis"],
                }
            )
        return sorted(ranked, key=lambda item: float(item["score"]), reverse=True)

    def _dominant_patterns(self, analyses: list[dict[str, Any]]) -> dict[str, Any]:
        planet_scores: dict[str, float] = {}
        theme_scores: dict[str, float] = {}
        for analysis in analyses:
            planet = str(analysis["lord"])
            planet_scores[planet] = planet_scores.get(planet, 0.0) + float(analysis.get("rank_score", 0.0))
            theme = str(analysis["theme"])
            theme_scores[theme] = theme_scores.get(theme, 0.0) + float(analysis.get("confidence", 0.0))
        top_planets = sorted(planet_scores.items(), key=lambda item: item[1], reverse=True)[:3]
        top_themes = sorted(theme_scores.items(), key=lambda item: item[1], reverse=True)[:5]
        return {
            "strongest_planets": [{"planet": name, "score": round(score, 3)} for name, score in top_planets],
            "emphasized_themes": [{"theme": name, "score": round(score, 3)} for name, score in top_themes],
        }

    def _life_theme_reports(self, analyses: list[dict[str, Any]]) -> list[dict[str, Any]]:
        reports: list[dict[str, Any]] = []
        themes = {
            "Career": [10, 6, 2, 11],
            "Relationships": [7, 5, 11, 4],
            "Spirituality": [9, 12, 5],
            "Health": [1, 6, 8],
            "Wealth": [2, 11, 9, 5],
        }
        by_house = {int(item["house"]): item for item in analyses}
        for label, houses in themes.items():
            related = [by_house[house] for house in houses if house in by_house]
            if not related:
                continue
            ranked = sorted(related, key=lambda item: float(item.get("rank_score", 0.0)), reverse=True)
            reports.append(
                {
                    "theme": label,
                    "houses": houses,
                    "confidence": round(
                        sum(float(item.get("confidence", 0.0)) for item in related) / len(related), 3
                    ),
                    "summary": " ".join(item["synthesis"] for item in ranked[:2]),
                }
            )
        return reports

    def _chart_fingerprint(self, analyses: list[dict[str, Any]]) -> str:
        top = sorted(analyses, key=lambda item: float(item.get("rank_score", 0.0)), reverse=True)[:3]
        if not top:
            return "No chart fingerprint available."
        return "; ".join(f"{item['theme']} via {item['lord']}" for item in top)

    def _dependency_graph(self, analyses: list[dict[str, Any]]) -> dict[str, Any]:
        dependency_map = {
            f"HOUSE_{item['house']}": [item["lord_placement"].replace("House ", "HOUSE_")] for item in analyses
        }
        order: list[str] = []
        cycles: list[list[str]] = []
        visited: set[str] = set()
        stack: set[str] = set()

        def visit(node: str, path: list[str]) -> None:
            if node in stack:
                cycle_start = path.index(node) if node in path else 0
                cycles.append(path[cycle_start:] + [node])
                return
            if node in visited:
                return
            visited.add(node)
            stack.add(node)
            for child in dependency_map.get(node, []):
                visit(child, path + [child])
            stack.remove(node)
            order.append(node)

        for node in dependency_map:
            visit(node, [node])
        return {
            "dependency_map": dependency_map,
            "order": order,
            "cycles": cycles,
        }

    def _cross_verification_scores(self, analyses: list[dict[str, Any]]) -> dict[int, float]:
        lord_counts: dict[str, int] = {}
        theme_counts: dict[str, int] = {}
        for analysis in analyses:
            lord = str(analysis["lord"])
            theme = str(analysis["theme"])
            lord_counts[lord] = lord_counts.get(lord, 0) + 1
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        scores: dict[int, float] = {}
        for analysis in analyses:
            house = int(analysis["house"])
            lord_score = min(lord_counts[str(analysis["lord"])] / 3.0, 1.0)
            theme_score = min(theme_counts[str(analysis["theme"])] / 3.0, 1.0)
            scores[house] = round((lord_score + theme_score) / 2.0, 3)
        return scores
