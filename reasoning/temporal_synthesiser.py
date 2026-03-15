"""Phase 9 Temporal Synthesiser.

Combines Natal themes, Dasha periods, and Transit events into a unified 
temporal interpretation (TemporalPrediction).
"""

from __future__ import annotations

from typing import Any


class TemporalSynthesiser:
    """Orchestrates the three-layer temporal model: Natal, Dasha, Transit."""

    # Weights from Roadmap
    W_DASHA = 0.50
    W_TRANSIT = 0.30
    W_YOGA = 0.20

    def synthesize_prediction(
        self, 
        active_dasha_stack: list[dict[str, Any]], 
        active_transits: list[dict[str, Any]],
        theme_importance: dict[str, float]
    ) -> list[dict[str, Any]]:
        """Combine all temporal layers to identify high-probability windows/events."""
        predictions = []
        
        # dasha_stack is usually [Mahadasha, Antardasha]
        # For each theme (Career, wealth etc), calculate 'Temporal Intensity'
        for theme, importance in theme_importance.items():
            # 1. Dasha Contribution
            # Average activation weight of active planets
            dasha_contrib = sum(p.get("activation_weight", 0.5) for p in active_dasha_stack) / len(active_dasha_stack)
            
            # 2. Transit Contribution
            # Find transits targeting planets/houses relevant to this theme
            theme_transits = [t for t in active_transits if self._is_transit_relevant(t, theme)]
            transit_contrib = sum(t["strength"] for t in theme_transits) / max(1, len(theme_transits)) if theme_transits else 0.0
            
            # 3. Yoga Contribution
            # Count yoga activations in the current dasha period
            yoga_activations = sum(len(p.get("yogas_activated", [])) for p in active_dasha_stack)
            yoga_contrib = min(1.0, yoga_activations * 0.2)
            
            # Weighted Synthesis
            intensity = (
                (dasha_contrib * self.W_DASHA) +
                (transit_contrib * self.W_TRANSIT) +
                (yoga_contrib * self.W_YOGA)
            ) * importance / 10.0 # Scale by theme importance
            
            if intensity > 0.3: # Significance threshold
                predictions.append({
                    "theme": theme,
                    "intensity": round(intensity, 3),
                    "confidence": "high" if intensity > 0.7 else "medium",
                    "reasoning": {
                        "dasha_planets": [p["planet"] for p in active_dasha_stack],
                        "active_transits": [t["transit_planet"] for t in theme_transits],
                        "yogas": list(set([y for p in active_dasha_stack for y in p.get("yogas_activated", [])]))
                    }
                })
                
        return sorted(predictions, key=lambda x: x["intensity"], reverse=True)

    def _is_transit_relevant(self, transit: dict[str, Any], theme: str) -> bool:
        """Stub for mapping transit targets to life themes."""
        # Ideally this uses the 'houses' mapped to themes from Phase 8
        return True # Simplified for now
