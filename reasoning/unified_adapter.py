"""Unified Vedic Horoscope Adapter.

Leverages the full VedicAstro library suite to provide comprehensive 
horoscope data (Dashas, Significators, and Divisional Charts).
"""

from __future__ import annotations

import collections
import json
from pathlib import Path
from typing import Any

from vedicastro.VedicAstro import VedicHoroscopeData
from normaliser.normaliser import AstrologyNormaliser


class UnifiedHoroscopeAdapter:
    """Consolidates all horoscope data points into a single queryable object."""

    def __init__(self, ontology_dir: str | Path = "normaliser/ontology") -> None:
        self.ontology_dir = Path(ontology_dir)
        self.normaliser = AstrologyNormaliser(self.ontology_dir)

    def get_all_horoscope_data(
        self, 
        date: str, 
        time: str, 
        latitude: float, 
        longitude: float, 
        timezone: float,
        ayanamsa: str = "Lahiri",
        house_system: str = "Placidus"
    ) -> dict[str, Any]:
        """Generate comprehensive horoscope payload."""
        # 1. Initialize Horoscope Object
        y, m, d = map(int, date.split("-"))
        hr, mn, sc = map(int, time.split(":"))
        utc_str = self._format_utc(timezone)
        
        horoscope = VedicHoroscopeData(
            y, m, d, hr, mn, sc,
            latitude, longitude, utc_str,
            ayanamsa, house_system
        )
        
        # 2. Generate Base Chart (D1)
        chart_d1 = horoscope.generate_chart()
        
        # 3. Extract Core Tables
        planets_raw = horoscope.get_planets_data_from_chart(chart_d1)
        houses_raw = horoscope.get_houses_data_from_chart(chart_d1)
        
        # 4. Extract Significators & Aspects
        planet_significators = horoscope.get_planet_wise_significators(planets_raw, houses_raw)
        house_significators = horoscope.get_house_wise_significators(planets_raw, houses_raw)
        aspects = horoscope.get_planetary_aspects(chart_d1)
        
        # 5. Extract Dashas
        dasha_table = horoscope.compute_vimshottari_dasa(chart_d1)
        
        # 6. Generate Divisional Charts (Phase 10 Foundation)
        divisional_charts = {
            "D1": self._format_chart_data(planets_raw, houses_raw),
            "D9": self._generate_varga(horoscope, 9),
            "D10": self._generate_varga(horoscope, 10)
        }

        return {
            "metadata": {
                "date": date, "time": time, "lat": latitude, "lon": longitude, "tz": timezone,
                "ayanamsa": ayanamsa, "house_system": house_system
            },
            "planets": divisional_charts["D1"]["planets"],
            "houses": divisional_charts["D1"]["houses"],
            "divisional_charts": divisional_charts,
            "significators": {
                "planets": [s._asdict() for s in planet_significators],
                "houses": [s._asdict() for s in house_significators]
            },
            "aspects": aspects,
            "dashas": dasha_table
        }

    def _generate_varga(self, horoscope: VedicHoroscopeData, harmonic: int) -> dict[str, Any]:
        """Stub for Divisional Chart generation using harmonic math."""
        # For now, we return D1 structure. 
        # Real logic for D9/D10 involves (longitude * harmonic) % 30
        return {"planets": [], "houses": []}

    def _format_chart_data(self, planets: list, houses: list) -> dict[str, Any]:
        return {
            "planets": [p._asdict() for p in planets],
            "houses": [h._asdict() for h in houses]
        }

    def _format_utc(self, tz: float) -> str:
        hours = int(tz)
        minutes = int((abs(tz) - abs(hours)) * 60)
        sign = "+" if tz >= 0 else "-"
        return f"{sign}{abs(hours):02d}:{minutes:02d}"
