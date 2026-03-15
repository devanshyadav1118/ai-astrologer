"""Phase 8 House Influence Propagation Engine.

Implements a PageRank-adapted algorithm to compute house importance scores
based on lordship, aspect, and yoga connections.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np


class PropagationEngine:
    """Computes house importance scores through iterative influence propagation."""

    DAMPING_FACTOR = 0.85
    CONVERGENCE_THRESHOLD = 0.001
    MAX_ITERATIONS = 100
    LAGNA_SEED_BOOST = 0.3
    YOGA_EDGE_CAP = 0.8

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def compute_house_importance(
        self, 
        chart_data: dict[str, Any], 
        detected_yogas: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Run the propagation algorithm and return ranked house scores and themes."""
        # 1. Construct Edges
        edges = self._construct_edges(chart_data, detected_yogas)
        
        # 2. Initialize Scores (1.0 base, 1.3 for House 1)
        scores = np.ones(12)
        scores[0] += self.LAGNA_SEED_BOOST
        
        # 3. Iterative Propagation
        for i in range(self.MAX_ITERATIONS):
            new_scores = np.zeros(12)
            for h_idx in range(12):
                incoming_influence = 0.0
                for (sender_idx, target_idx), weight in edges.items():
                    if target_idx == h_idx:
                        incoming_influence += scores[sender_idx] * weight
                
                base_val = 1.3 if h_idx == 0 else 1.0
                new_scores[h_idx] = (self.DAMPING_FACTOR * incoming_influence) + \
                                   ((1 - self.DAMPING_FACTOR) * base_val)
            
            delta = np.max(np.abs(new_scores - scores))
            scores = new_scores
            if delta < self.CONVERGENCE_THRESHOLD:
                break
        
        # 4. Normalization (0-10 scale)
        max_score = np.max(scores)
        normalized = (scores / max_score) * 10.0
        
        # 5. Theme Identification
        results = []
        for i in range(12):
            results.append({
                "house": i + 1,
                "importance_score": round(float(normalized[i]), 2),
            })
            
        ranked_houses = sorted(results, key=lambda x: x["importance_score"], reverse=True)
        for rank, item in enumerate(ranked_houses, 1):
            item["rank"] = rank

        dominant_themes = self._identify_dominant_themes(normalized, chart_data, detected_yogas)
            
        return {
            "house_importance": sorted(ranked_houses, key=lambda x: x["house"]),
            "dominant_themes": dominant_themes,
            "convergence_delta": float(delta),
            "iterations": i + 1,
            "edges": [{"from": k[0]+1, "to": k[1]+1, "weight": v} for k, v in edges.items()]
        }

    def _identify_dominant_themes(self, scores: np.ndarray, chart_data: dict[str, Any], yogas: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Identify life themes based on clusters of important houses."""
        theme_map = {
            "CAREER": [10, 6, 2, 11],
            "RELATIONSHIPS": [7, 5, 11, 4],
            "SPIRITUALITY": [9, 12, 5],
            "HEALTH": [1, 6, 8],
            "WEALTH": [2, 11, 9, 5],
        }
        
        themes = []
        for name, houses in theme_map.items():
            cluster_scores = [scores[h-1] for h in houses]
            avg_score = sum(cluster_scores) / len(cluster_scores)
            
            # Find key planets/yogas for this theme
            key_planets = set()
            yoga_contributors = []
            
            for h_num in houses:
                # Planet in house
                p_in_h = [p["name"] for p in chart_data["planets"] if p["house"] == h_num]
                key_planets.update(p_in_h)
                
                # Lord of house
                lord = next((h["lord"] for h in chart_data["houses"] if h["number"] == h_num), None)
                if lord: key_planets.add(lord)
                
            for y in yogas:
                # If yoga involves houses in this theme
                y_planets = y.get("participating_planets", [])
                y_houses = [p["house"] for p in chart_data["planets"] if p["name"] in y_planets]
                if any(h in houses for h in y_houses):
                    yoga_contributors.append(y["name"])

            themes.append({
                "theme_name": name,
                "theme_score": round(avg_score, 2),
                "key_houses": houses,
                "key_planets": list(key_planets)[:5],
                "yoga_contributors": list(set(yoga_contributors))[:3]
            })
            
        ranked_themes = sorted(themes, key=lambda x: x["theme_score"], reverse=True)
        for i, t in enumerate(ranked_themes, 1):
            t["theme_rank"] = i
            
        return ranked_themes

    def _construct_edges(
        self, 
        chart_data: dict[str, Any], 
        detected_yogas: list[dict[str, Any]]
    ) -> dict[tuple[int, int], float]:
        """Build the weighted edge dictionary (sender_idx, target_idx) -> weight."""
        edges: dict[tuple[int, int], float] = {}

        # 1. Lordship Edges (Owned House -> Placement House)
        # Weight = Lord Strength (0-1)
        for p_data in chart_data["planets"]:
            p_name = p_data["name"]
            placement_house = p_data["house"]
            strength = p_data["dignity"].get("strength_modifier", 5.0) / 10.0
            
            # Find which houses this planet rules
            owned_houses = [h["number"] for h in chart_data["houses"] if h["lord"] == p_name]
            for oh in owned_houses:
                key = (oh - 1, placement_house - 1)
                edges[key] = edges.get(key, 0.0) + strength

        # 2. Aspect Edges (Planet's House -> Aspected House)
        # Weight = Planet Strength * Aspect Strength
        for aspect in chart_data.get("aspects", []):
            from_p = aspect["from_planet"]
            to_p = aspect["to_planet"]
            strength_p = next((p["dignity"].get("strength_modifier", 5.0) / 10.0) 
                             for p in chart_data["planets"] if p["name"] == from_p)
            
            from_data = next(p for p in chart_data["planets"] if p["name"] == from_p)
            to_data = next(p for p in chart_data["planets"] if p["name"] == to_p)
            
            # Note: The roadmap says aspects go from planet's house to target house.
            # Here we model house-to-house influence.
            key = (from_data["house"] - 1, to_data["house"] - 1)
            weight = strength_p * aspect.get("strength", 1.0)
            edges[key] = edges.get(key, 0.0) + weight

        # 3. Yoga Edges (Bidirectional)
        # Weight = Yoga strength (0-1)
        for yoga in detected_yogas:
            planets = yoga.get("participating_planets", [])
            if len(planets) < 2: continue
            
            # Get houses of participants
            houses = []
            for p_name in planets:
                p_data = next((p for p in chart_data["planets"] if p["name"] == p_name), None)
                if p_data:
                    houses.append(p_data["house"])
            
            # Create bidirectional edges between all pairs of houses involved
            y_strength = min(self.YOGA_EDGE_CAP, yoga.get("strength_score", 0.5))
            for i in range(len(houses)):
                for j in range(i + 1, len(houses)):
                    h1, h2 = houses[i], houses[j]
                    if h1 == h2: continue
                    
                    edges[(h1-1, h2-1)] = edges.get((h1-1, h2-1), 0.0) + y_strength
                    edges[(h2-1, h1-1)] = edges.get((h2-1, h1-1), 0.0) + y_strength

        # Cap all edges at 1.0
        return {k: min(1.0, v) for k, v in edges.items()}
