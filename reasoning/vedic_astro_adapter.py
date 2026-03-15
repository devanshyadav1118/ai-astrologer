"""Phase 9 VedicAstro Adapter.

Bridges the VedicAstro library to the project's canonical schema.
Owned by Phase 9 Temporal Dynamics Engine.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from vedicastro.VedicAstro import VedicHoroscopeData
from normaliser.normaliser import AstrologyNormaliser


class VedicAstroAdapter:
    """Wrapper for VedicAstro library to normalize output formats."""

    def __init__(self, ontology_dir: str | Path = "normaliser/ontology") -> None:
        self.ontology_dir = Path(ontology_dir)
        self.normaliser = AstrologyNormaliser(self.ontology_dir)
        self.logger = logging.getLogger(__name__)

    def get_dasha_timeline(
        self, 
        birth_date: str, 
        birth_time: str, 
        lat: float, 
        lon: float, 
        tz: float
    ) -> list[dict[str, Any]]:
        """Compute Vimshottari Dasha timeline and return canonical period nodes."""
        # 1. Initialize VedicAstro
        y, m, d = map(int, birth_date.split("-"))
        hr, mn, sc = map(int, birth_time.split(":"))
        utc_str = self._format_utc(tz)
        
        va = VedicHoroscopeData(y, m, d, hr, mn, sc, utc_str, lat, lon, ayanamsa="Lahiri")
        chart = va.generate_chart()
        
        # 2. Compute Dashas (Nested Dict: Mahadasha -> Bhukti)
        raw_dashas = va.compute_vimshottari_dasa(chart)
        
        # 3. Flatten and Normalize
        periods = []
        for md_planet, md_data in raw_dashas.items():
            md_node = {
                "dasha_type": "mahadasha",
                "planet": self.normaliser.normalise(md_planet),
                "start_date": self._parse_va_date(md_data["start"]),
                "end_date": self._parse_va_date(md_data["end"]),
                "source": "vedic_astro_api"
            }
            periods.append(md_node)
            
            # Add Antardashas (Bhuktis)
            for ad_planet, ad_data in md_data.get("bhuktis", {}).items():
                ad_node = {
                    "dasha_type": "antardasha",
                    "planet": self.normaliser.normalise(ad_planet),
                    "start_date": self._parse_va_date(ad_data["start"]),
                    "end_date": self._parse_va_date(ad_data["end"]),
                    "parent_planet": md_node["planet"],
                    "source": "vedic_astro_api"
                }
                periods.append(ad_node)
                
        return periods

    def _format_utc(self, tz: float) -> str:
        """Convert float timezone to HH:MM string."""
        hours = int(tz)
        minutes = int((abs(tz) - abs(hours)) * 60)
        sign = "+" if tz >= 0 else "-"
        return f"{sign}{abs(hours):02d}:{minutes:02d}"

    def _parse_va_date(self, date_str: str) -> str:
        """Convert DD-MM-YYYY to ISO 8601 YYYY-MM-DD."""
        return datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")

    def verify_ayanamsa(self, birth_date: str, birth_time: str, lat: float, lon: float, tz: float, expected_moon_lon: float) -> bool:
        """Check if VedicAstro's Moon matches our internal Swiss Eph moon."""
        y, m, d = map(int, birth_date.split("-"))
        hr, mn, sc = map(int, birth_time.split(":"))
        utc_str = self._format_utc(tz)
        
        va = VedicHoroscopeData(y, m, d, hr, mn, sc, utc_str, lat, lon, ayanamsa="Lahiri")
        chart = va.generate_chart()
        va_planets = va.get_planets_data_from_chart(chart)
        
        va_moon_lon = next(p.LonDecDeg for p in va_planets if p.Object == 'Moon')
        diff = abs(expected_moon_lon - va_moon_lon)
        if diff > 180: diff = 360 - diff
        
        return diff < 0.1
