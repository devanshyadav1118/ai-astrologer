from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from normaliser.normaliser import AstrologyNormaliser
from chart.strength_engine import StrengthEngine
from chart.vedicastro_api_client import VedicAstroAPIClient

class VedicAstroAPICalculator:
    """Calculator that uses the VedicAstro API for chart data."""

    def __init__(
        self,
        ontology_dir: str | Path = "normaliser/ontology",
        api_url: str = "http://127.0.0.1:8088",
        normaliser: AstrologyNormaliser | None = None,
        strength_engine: StrengthEngine | None = None,
    ) -> None:
        self.ontology_dir = Path(ontology_dir)
        self.normaliser = normaliser or AstrologyNormaliser(self.ontology_dir)
        self.strength_engine = strength_engine or StrengthEngine(self.ontology_dir)
        self.api_client = VedicAstroAPIClient(base_url=api_url)
        self.planets_meta = self._load_ontology_map("planets.json", "planets")
        self.signs_meta = self._load_ontology_map("signs.json", "signs")
        self.logger = logging.getLogger(__name__)

    def calculate_chart(
        self,
        date: str,
        time: str,
        latitude: float,
        longitude: float,
        timezone: float,
    ) -> dict[str, Any]:
        """Fetch chart data from API and normalize to project format."""
        
        # 1. Fetch data from API
        raw_data = self.api_client.get_all_horoscope_data(
            date=date,
            time=time,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            ayanamsa="Lahiri",  # Defaulting to Lahiri for consistency
            house_system="Whole Sign" # Matching original calculator default
        )

        # 2. Extract and Normalize Houses
        houses = self._extract_houses(raw_data["houses_data"])
        
        # 3. Extract and Normalize Planets
        planets = self._extract_planets(raw_data["planets_data"])

        # 4. Phase 6 Strength Engine
        # Pass 1: Initial strength without dispositor contribution
        chart_data_pre = {
            "planets": planets, 
            "houses": houses, 
            "aspects": self._extract_aspects(raw_data["planetary_aspects"])
        }
        initial_scores = {}
        for planet in planets:
            strength_data = self.strength_engine.calculate_planet_strength(
                planet["name"], chart_data_pre, dispositor_score=5.0
            )
            initial_scores[planet["name"]] = strength_data["total_strength"]

        # Pass 2: Final strength including dispositor contribution
        for planet in planets:
            ruler_name = self.signs_meta[planet["sign"]]["ruler"]
            dispositor_score = initial_scores.get(ruler_name, 5.0)
            
            final_strength_data = self.strength_engine.calculate_planet_strength(
                planet["name"], chart_data_pre, dispositor_score=dispositor_score
            )
            planet["strength_scores"] = final_strength_data
            planet["dignity"]["strength_modifier"] = final_strength_data["total_strength"]

        # 5. Extract other derived data
        aspects = self._extract_aspects(raw_data["planetary_aspects"])
        house_aspects = self._calculate_house_aspects(planets)
        conjunctions = self._calculate_conjunctions(planets)
        dispositors = self._calculate_dispositors(planets)

        # Phase 9: Convert Dasha Table to canonical list format
        dasha_periods = self._convert_dasha_table(raw_data.get("vimshottari_dasa_table", {}))

        # Phase 10: Extract Divisional Charts from API
        divisional_charts = self._extract_divisional_charts(raw_data.get("divisional_charts", {}))

        return {
            "metadata": {
                "date": date,
                "time": time,
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone,
                "source": "VedicAstroAPI"
            },
            "houses": houses,
            "planets": planets,
            "aspects": aspects,
            "house_aspects": house_aspects,
            "conjunctions": conjunctions,
            "dispositors": dispositors,
            "dasha_periods": dasha_periods,
            "divisional_charts": divisional_charts,
            "api_raw": {
                "planet_significators": raw_data.get("planet_significators"),
                "house_significators": raw_data.get("house_significators"),
                "vimshottari_dasa_table": raw_data.get("vimshottari_dasa_table")
            }
        }

    def _extract_divisional_charts(self, div_raw: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
        """Maps raw API divisional data to canonical list of placements."""
        results = {}
        for code, planets_data in div_raw.items():
            placements = []
            for p in planets_data:
                # Filter to canonical planets
                if p["Object"] in {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}:
                    placements.append({
                        "name": self.normaliser.normalise(p["Object"]),
                        "divisional_sign": self.normaliser.normalise(p["Rasi"]),
                        "degree": float(p["SignLonDecDeg"])
                    })
            results[code] = placements
        return results

    def _convert_dasha_table(self, table: dict[str, Any]) -> list[dict[str, Any]]:
        """Convert API's nested dasha table to a flat list of period nodes."""
        from datetime import datetime
        periods = []
        
        def parse_date(d: str) -> str:
            # API returns DD-MM-YYYY, we need YYYY-MM-DD
            try:
                return datetime.strptime(d, "%d-%m-%Y").strftime("%Y-%m-%d")
            except Exception:
                return d

        for md_planet, md_data in table.items():
            md_node = {
                "dasha_type": "mahadasha",
                "planet": self.normaliser.normalise(md_planet),
                "start_date": parse_date(md_data["start"]),
                "end_date": parse_date(md_data["end"]),
                "source": "VedicAstroAPI"
            }
            periods.append(md_node)
            
            for ad_planet, ad_data in md_data.get("bhuktis", {}).items():
                periods.append({
                    "dasha_type": "antardasha",
                    "planet": self.normaliser.normalise(ad_planet),
                    "parent_planet": md_node["planet"],
                    "start_date": parse_date(ad_data["start"]),
                    "end_date": parse_date(ad_data["end"]),
                    "source": "VedicAstroAPI"
                })
        return periods

    def _load_ontology_map(self, filename: str, top_key: str) -> dict[str, dict[str, Any]]:
        with (self.ontology_dir / filename).open(encoding="utf-8") as handle:
            payload = json.load(handle)
        return {
            item["canonical_name"]: item
            for item in payload[top_key]
            if isinstance(item, dict) and item.get("canonical_name")
        }

    def _extract_houses(self, houses_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        houses = []
        for house in houses_data:
            house_number = house["HouseNr"]
            sign = self.normaliser.normalise(house["Rasi"])
            houses.append({
                "number": house_number,
                "house": f"HOUSE_{house_number}",
                "sign": sign,
                "degree": float(house["SignLonDecDeg"]),
                "lord": self.signs_meta[sign]["ruler"],
            })
        return sorted(houses, key=lambda x: x["number"])

    def _extract_planets(self, planets_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        planets = []
        canonical_planets = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        
        for p in planets_data:
            if p["Object"] not in canonical_planets:
                continue
                
            name = self.normaliser.normalise(p["Object"])
            sign = self.normaliser.normalise(p["Rasi"])
            nakshatra = self.normaliser.normalise(p["Nakshatra"])
            degree = float(p["SignLonDecDeg"])
            
            planets.append({
                "name": name,
                "sign": sign,
                "degree": degree,
                "longitude": float(p["LonDecDeg"]),
                "latitude": self._dms_to_dec(p.get("LatDMS")),
                "house": p["HouseNr"],
                "nakshatra": nakshatra,
                "nakshatra_pada": 0, # API doesn't seem to provide Pada directly in planets_data
                "sublord": self.normaliser.normalise(p.get("SubLord")),
                "retrograde": bool(p.get("isRetroGrade", False)),
                "dignity": self._determine_dignity(name, sign, degree),
            })
        
        # Calculate combustion
        sun_longitude = next((p["longitude"] for p in planets if p["name"] == "SUN"), None)
        for p in planets:
            p["combustion"] = self._check_combustion(p["name"], p["longitude"], sun_longitude)
            
        return planets

    def _dms_to_dec(self, dms_str: str | None) -> float:
        if not dms_str or not isinstance(dms_str, str):
            return 0.0
        # Format: "+DD:MM:SS"
        try:
            sign = 1 if dms_str[0] == "+" else -1
            parts = dms_str[1:].split(":")
            d = float(parts[0])
            m = float(parts[1]) if len(parts) > 1 else 0.0
            s = float(parts[2]) if len(parts) > 2 else 0.0
            return sign * (d + m/60.0 + s/3600.0)
        except (ValueError, IndexError):
            return 0.0

    def _determine_dignity(self, planet: str, sign: str, degree: float) -> dict[str, Any]:
        # Copy-pasted logic from VedicAstroCalculator for consistency
        planet_data = self.planets_meta[planet]
        sign_data = self.signs_meta[sign]
        dignity = {
            "exalted": False, "debilitated": False, "own_sign": False,
            "moolatrikona": False, "friend_sign": False, "enemy_sign": False,
            "status": "neutral", "strength_modifier": 0.0,
        }
        if sign == planet_data.get("exaltation_sign"):
            dignity.update({"exalted": True, "status": "exalted", "strength_modifier": 5.0})
            return dignity
        if sign == planet_data.get("debilitation_sign"):
            dignity.update({"debilitated": True, "status": "debilitated", "strength_modifier": -5.0})
            return dignity
        if sign in planet_data.get("own_signs", []):
            dignity.update({"own_sign": True, "status": "own_sign", "strength_modifier": 4.0})
            return dignity
        mt_sign = planet_data.get("moolatrikona_sign")
        mt_deg = planet_data.get("moolatrikona_degrees")
        if (sign == mt_sign and isinstance(mt_deg, list) and len(mt_deg) == 2 and 
            float(mt_deg[0]) <= degree <= float(mt_deg[1])):
            dignity.update({"moolatrikona": True, "status": "moolatrikona", "strength_modifier": 3.5})
            return dignity
        if planet in sign_data.get("friendly_planets", []):
            dignity.update({"friend_sign": True, "status": "friend", "strength_modifier": 2.0})
            return dignity
        if planet in sign_data.get("enemy_planets", []):
            dignity.update({"enemy_sign": True, "status": "enemy", "strength_modifier": -2.0})
        return dignity

    def _extract_aspects(self, raw_aspects: list[dict[str, Any]]) -> list[dict[str, Any]]:
        aspects = []
        canonical_planets = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        for a in raw_aspects:
            p1 = a["P1"]
            p2 = a["P2"]
            if p1 not in canonical_planets or p2 not in canonical_planets:
                continue
            
            # Map API aspect names to project format if needed
            # For now, we'll use the API's AspectType but normalize names
            aspects.append({
                "from_planet": self.normaliser.normalise(p1),
                "to_planet": self.normaliser.normalise(p2),
                "type": a["AspectType"].upper().replace(" ", "_"),
                "orb": a["AspectOrb"],
                "strength": 1.0 - (a["AspectOrb"] / 10.0) if a["AspectOrb"] < 10.0 else 0.1 # Simple strength formula
            })
        return aspects

    def _calculate_house_aspects(self, planets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # Copy-pasted from original calculator
        house_aspects: list[dict[str, Any]] = []
        for source in planets:
            supported_offsets = set(self.planets_meta[source["name"]].get("special_aspects", []))
            for house_offset in sorted(supported_offsets):
                target_house = ((source["house"] + house_offset - 2) % 12) + 1
                house_aspects.append({
                    "from_planet": source["name"],
                    "to_house": target_house,
                    "type": "OPPOSITION" if house_offset == 7 else f"{source['name']}_SPECIAL_ASPECT",
                    "house_offset": house_offset,
                    "strength": 1.0,
                })
        return house_aspects

    def _calculate_conjunctions(self, planets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # Copy-pasted from original calculator
        conjunctions: list[dict[str, Any]] = []
        for index, left in enumerate(planets):
            for right in planets[index + 1:]:
                if left["house"] != right["house"]:
                    continue
                orb = abs(left["longitude"] - right["longitude"])
                orb = min(orb, 360.0 - orb)
                if orb > 8.0:
                    continue
                conjunctions.append({
                    "planet_1": left["name"],
                    "planet_2": right["name"],
                    "orb": round(orb, 3),
                    "same_nakshatra": left.get("nakshatra") == right.get("nakshatra"),
                    "house": left["house"],
                })
        return conjunctions

    def _calculate_dispositors(self, planets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # Copy-pasted from original calculator
        planets_by_name = {planet["name"]: planet for planet in planets}
        dispositors: list[dict[str, Any]] = []
        for planet in planets:
            ruler = self.signs_meta[planet["sign"]]["ruler"]
            if ruler not in planets_by_name:
                continue
            dispositors.append({
                "planet": planet["name"],
                "dispositor": ruler,
                "same_planet": planet["name"] == ruler,
            })
        return dispositors

    def _check_combustion(self, planet: str, longitude: float, sun_longitude: float | None) -> bool:
        if planet in {"SUN", "RAHU", "KETU"} or sun_longitude is None:
            return False
        separation = abs(longitude - sun_longitude)
        angular_distance = min(separation, 360.0 - separation)
        return angular_distance <= 6.0
