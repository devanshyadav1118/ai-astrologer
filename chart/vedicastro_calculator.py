"""Phase 4 chart calculation and ontology normalisation."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from normaliser.normaliser import AstrologyNormaliser
from chart.strength_engine import StrengthEngine


class VedicAstroCalculator:
    """Wrap chart calculation and adapt results to the project ontology."""

    def __init__(
        self,
        ontology_dir: str | Path = "normaliser/ontology",
        chart_factory: Callable[..., Any] | None = None,
        normaliser: AstrologyNormaliser | None = None,
        strength_engine: StrengthEngine | None = None,
    ) -> None:
        self.ontology_dir = Path(ontology_dir)
        self.normaliser = normaliser or AstrologyNormaliser(self.ontology_dir)
        self.strength_engine = strength_engine or StrengthEngine(self.ontology_dir)
        self.chart_factory = chart_factory or self._build_chart
        self.planets = self._load_ontology_map("planets.json", "planets")
        self.signs = self._load_ontology_map("signs.json", "signs")

    def calculate_chart(
        self,
        date: str,
        time: str,
        latitude: float,
        longitude: float,
        timezone: float,
    ) -> dict[str, Any]:
        """Calculate a chart and return normalized graph-ready data."""
        chart = self.chart_factory(
            date=date,
            time=time,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
        )
        houses = self._extract_houses(chart)
        planets = self._extract_planets(chart)

        # Phase 6: Calculate sophisticated strength scores for each planet
        # Pass 1: Initial strength without dispositor contribution
        chart_data_pre = {"planets": planets, "houses": houses, "aspects": self._calculate_aspects(planets)}
        initial_scores = {}
        for planet in planets:
            strength_data = self.strength_engine.calculate_planet_strength(
                planet["name"], chart_data_pre, dispositor_score=5.0
            )
            initial_scores[planet["name"]] = strength_data["total_strength"]

        # Pass 2: Final strength including dispositor contribution
        for planet in planets:
            # Find the dispositor (ruler of the sign the planet is in)
            ruler_name = self.signs[planet["sign"]]["ruler"]
            dispositor_score = initial_scores.get(ruler_name, 5.0)
            
            final_strength_data = self.strength_engine.calculate_planet_strength(
                planet["name"], chart_data_pre, dispositor_score=dispositor_score
            )
            planet["strength_scores"] = final_strength_data
            # Overwrite the simple dignity-based modifier with the total strength
            planet["dignity"]["strength_modifier"] = final_strength_data["total_strength"]

        aspects = self._calculate_aspects(planets)
        house_aspects = self._calculate_house_aspects(planets)
        conjunctions = self._calculate_conjunctions(planets)
        dispositors = self._calculate_dispositors(planets)
        return {
            "metadata": {
                "date": date,
                "time": time,
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone,
            },
            "houses": houses,
            "planets": planets,
            "aspects": aspects,
            "house_aspects": house_aspects,
            "conjunctions": conjunctions,
            "dispositors": dispositors,
        }

    def _build_chart(self, **kwargs: Any) -> Any:
        try:
            from vedicastro.VedicAstro import VedicHoroscopeData  # type: ignore
            year, month, day = (int(part) for part in str(kwargs["date"]).split("-"))
            hour, minute, second = (int(part) for part in str(kwargs["time"]).split(":"))
            horoscope = VedicHoroscopeData(
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                second=second,
                utc=self._timezone_to_utc_string(float(kwargs["timezone"])),
                latitude=float(kwargs["latitude"]),
                longitude=float(kwargs["longitude"]),
                house_system="Whole Sign",
            )
            raw_chart = horoscope.generate_chart()
            return _VedicAstroChartAdapter(
                planets=horoscope.get_planets_data_from_chart(raw_chart),
                houses=horoscope.get_houses_data_from_chart(raw_chart),
            )
        except Exception:
            return self._build_chart_with_swisseph(**kwargs)

    def _build_chart_with_swisseph(self, **kwargs: Any) -> Any:
        try:
            import swisseph as swe  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "Neither a working vedicastro stack nor swisseph is available for chart calculation."
            ) from exc
        year, month, day = (int(part) for part in str(kwargs["date"]).split("-"))
        hour, minute, second = (int(part) for part in str(kwargs["time"]).split(":"))
        timezone = float(kwargs["timezone"])
        ut_hours = hour + (minute / 60.0) + (second / 3600.0) - timezone
        julian_day = swe.julday(year, month, day, ut_hours)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        house_cusps, _ = swe.houses_ex(
            julian_day,
            float(kwargs["latitude"]),
            float(kwargs["longitude"]),
            b"W",
            flags,
        )
        sign_names = [
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
        ]
        nakshatra_names = [
            "Ashwini",
            "Bharani",
            "Krittika",
            "Rohini",
            "Mrigashira",
            "Ardra",
            "Punarvasu",
            "Pushya",
            "Ashlesha",
            "Magha",
            "Purva Phalguni",
            "Uttara Phalguni",
            "Hasta",
            "Chitra",
            "Swati",
            "Vishakha",
            "Anuradha",
            "Jyeshtha",
            "Mula",
            "Purva Ashadha",
            "Uttara Ashadha",
            "Shravana",
            "Dhanishta",
            "Shatabhisha",
            "Purva Bhadrapada",
            "Uttara Bhadrapada",
            "Revati",
        ]
        houses = [
            SimpleNamespace(
                number=index,
                sign=sign_names[int(cusp // 30) % 12],
                degree=round(cusp % 30, 6),
            )
            for index, cusp in enumerate(house_cusps, start=1)
        ]
        asc_longitude = float(house_cusps[0])
        planet_ids = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mars": swe.MARS,
            "Mercury": swe.MERCURY,
            "Jupiter": swe.JUPITER,
            "Venus": swe.VENUS,
            "Saturn": swe.SATURN,
            "Rahu": swe.MEAN_NODE,
        }
        planets: list[Any] = []
        for name, planet_id in planet_ids.items():
            values, _ = swe.calc_ut(julian_day, planet_id, flags)
            longitude = float(values[0]) % 360.0
            latitude = float(values[1])
            speed = float(values[3])
            planets.append(
                SimpleNamespace(
                    name=name,
                    sign=sign_names[int(longitude // 30) % 12],
                    degree=round(longitude % 30, 6),
                    longitude=round(longitude, 6),
                    latitude=round(latitude, 6),
                    house=int(((longitude - asc_longitude) % 360.0) // 30) + 1,
                    nakshatra=nakshatra_names[int(longitude // (360.0 / 27.0)) % 27],
                    pada=int(((longitude % (360.0 / 27.0)) // (360.0 / 108.0)) + 1),
                    sublord=None,
                    is_retrograde=speed < 0,
                )
            )
        ketu_longitude = (next(planet.longitude for planet in planets if planet.name == "Rahu") + 180.0) % 360.0
        ketu_latitude = -next(planet.latitude for planet in planets if planet.name == "Rahu")
        planets.append(
            SimpleNamespace(
                name="Ketu",
                sign=sign_names[int(ketu_longitude // 30) % 12],
                degree=round(ketu_longitude % 30, 6),
                longitude=round(ketu_longitude, 6),
                latitude=round(ketu_latitude, 6),
                house=int(((ketu_longitude - asc_longitude) % 360.0) // 30) + 1,
                nakshatra=nakshatra_names[int(ketu_longitude // (360.0 / 27.0)) % 27],
                pada=int(((ketu_longitude % (360.0 / 27.0)) // (360.0 / 108.0)) + 1),
                sublord=None,
                is_retrograde=True,
            )
        )
        return _ComputedChartAdapter(planets=planets, houses=houses)

    def _load_ontology_map(self, filename: str, top_key: str) -> dict[str, dict[str, Any]]:
        with (self.ontology_dir / filename).open(encoding="utf-8") as handle:
            payload = json.load(handle)
        return {
            item["canonical_name"]: item
            for item in payload[top_key]
            if isinstance(item, dict) and item.get("canonical_name")
        }

    def _extract_houses(self, chart: Any) -> list[dict[str, Any]]:
        houses: list[dict[str, Any]] = []
        for index, house in enumerate(chart.get_houses(), start=1):
            house_number = int(getattr(house, "number", index))
            sign = self.normaliser.normalise(str(getattr(house, "sign", "")))
            if sign is None or sign not in self.signs:
                raise ValueError(f"unknown sign for house {house_number}: {getattr(house, 'sign', None)}")
            houses.append(
                {
                    "number": house_number,
                    "house": f"HOUSE_{house_number}",
                    "sign": sign,
                    "degree": float(getattr(house, "degree", 0.0)),
                    "lord": self.signs[sign]["ruler"],
                }
            )
        return houses

    def _extract_planets(self, chart: Any) -> list[dict[str, Any]]:
        planets: list[dict[str, Any]] = []
        raw_planets = list(chart.get_planets())
        for planet in raw_planets:
            name = self.normaliser.normalise(str(getattr(planet, "name", "")))
            sign = self.normaliser.normalise(str(getattr(planet, "sign", "")))
            nakshatra_value = getattr(planet, "nakshatra", None)
            nakshatra = self.normaliser.normalise(str(nakshatra_value)) if nakshatra_value else None
            if name is None or name not in self.planets:
                raise ValueError(f"unknown planet: {getattr(planet, 'name', None)}")
            if sign is None or sign not in self.signs:
                raise ValueError(f"unknown sign for planet {name}: {getattr(planet, 'sign', None)}")
            degree = float(getattr(planet, "degree", 0.0))
            longitude = float(getattr(planet, "longitude", degree))
            latitude = float(getattr(planet, "latitude", 0.0))
            planets.append(
                {
                    "name": name,
                    "sign": sign,
                    "degree": degree,
                    "longitude": longitude,
                    "latitude": latitude,
                    "house": int(getattr(planet, "house")),
                    "nakshatra": nakshatra,
                    "nakshatra_pada": int(getattr(planet, "pada", 0) or 0),
                    "sublord": self.normaliser.normalise(str(getattr(planet, "sublord", "")))
                    if getattr(planet, "sublord", None)
                    else None,
                    "retrograde": bool(getattr(planet, "is_retrograde", False)),
                    "dignity": self._determine_dignity(name, sign, degree),
                }
            )
        sun_longitude = next(
            (planet["longitude"] for planet in planets if planet["name"] == "SUN"),
            None,
        )
        for planet in planets:
            planet["combustion"] = self._check_combustion(planet["name"], planet["longitude"], sun_longitude)
        return planets

    def _determine_dignity(self, planet: str, sign: str, degree: float) -> dict[str, Any]:
        planet_data = self.planets[planet]
        sign_data = self.signs[sign]
        dignity = {
            "exalted": False,
            "debilitated": False,
            "own_sign": False,
            "moolatrikona": False,
            "friend_sign": False,
            "enemy_sign": False,
            "status": "neutral",
            "strength_modifier": 0.0,
        }
        if sign == planet_data.get("exaltation_sign"):
            dignity["exalted"] = True
            dignity["status"] = "exalted"
            dignity["strength_modifier"] = 5.0
            return dignity
        if sign == planet_data.get("debilitation_sign"):
            dignity["debilitated"] = True
            dignity["status"] = "debilitated"
            dignity["strength_modifier"] = -5.0
            return dignity
        if sign in planet_data.get("own_signs", []):
            dignity["own_sign"] = True
            dignity["status"] = "own_sign"
            dignity["strength_modifier"] = 4.0
            return dignity
        moolatrikona_sign = planet_data.get("moolatrikona_sign")
        moolatrikona_degrees = planet_data.get("moolatrikona_degrees")
        if (
            sign == moolatrikona_sign
            and isinstance(moolatrikona_degrees, list)
            and len(moolatrikona_degrees) == 2
            and float(moolatrikona_degrees[0]) <= degree <= float(moolatrikona_degrees[1])
        ):
            dignity["moolatrikona"] = True
            dignity["status"] = "moolatrikona"
            dignity["strength_modifier"] = 3.5
            return dignity
        if planet in sign_data.get("friendly_planets", []):
            dignity["friend_sign"] = True
            dignity["status"] = "friend"
            dignity["strength_modifier"] = 2.0
            return dignity
        if planet in sign_data.get("enemy_planets", []):
            dignity["enemy_sign"] = True
            dignity["status"] = "enemy"
            dignity["strength_modifier"] = -2.0
        return dignity

    def _calculate_aspects(self, planets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        aspects: list[dict[str, Any]] = []
        for source in planets:
            supported_offsets = set(self.planets[source["name"]].get("special_aspects", []))
            for target in planets:
                if source["name"] == target["name"]:
                    continue
                house_offset = ((target["house"] - source["house"]) % 12) + 1
                if house_offset not in supported_offsets:
                    continue
                aspects.append(
                    {
                        "from_planet": source["name"],
                        "to_planet": target["name"],
                        "to_house": target["house"],
                        "type": "OPPOSITION" if house_offset == 7 else f"{source['name']}_SPECIAL_ASPECT",
                        "house_offset": house_offset,
                        "strength": 1.0,
                    }
                )
        return aspects

    def _check_combustion(self, planet: str, longitude: float, sun_longitude: float | None) -> bool:
        if planet in {"SUN", "RAHU", "KETU"} or sun_longitude is None:
            return False
        separation = abs(longitude - sun_longitude)
        angular_distance = min(separation, 360.0 - separation)
        return angular_distance <= 6.0

    def _calculate_house_aspects(self, planets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        house_aspects: list[dict[str, Any]] = []
        for source in planets:
            supported_offsets = set(self.planets[source["name"]].get("special_aspects", []))
            for house_offset in sorted(supported_offsets):
                target_house = ((source["house"] + house_offset - 2) % 12) + 1
                house_aspects.append(
                    {
                        "from_planet": source["name"],
                        "to_house": target_house,
                        "type": "OPPOSITION" if house_offset == 7 else f"{source['name']}_SPECIAL_ASPECT",
                        "house_offset": house_offset,
                        "strength": 1.0,
                    }
                )
        return house_aspects

    def _calculate_conjunctions(self, planets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        conjunctions: list[dict[str, Any]] = []
        for index, left in enumerate(planets):
            for right in planets[index + 1:]:
                if left["house"] != right["house"]:
                    continue
                orb = abs(left["longitude"] - right["longitude"])
                orb = min(orb, 360.0 - orb)
                if orb > 8.0:
                    continue
                conjunctions.append(
                    {
                        "planet_1": left["name"],
                        "planet_2": right["name"],
                        "orb": round(orb, 3),
                        "same_nakshatra": left.get("nakshatra") == right.get("nakshatra"),
                        "house": left["house"],
                    }
                )
        return conjunctions

    def _calculate_dispositors(self, planets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        planets_by_name = {planet["name"]: planet for planet in planets}
        dispositors: list[dict[str, Any]] = []
        for planet in planets:
            ruler = self.signs[planet["sign"]]["ruler"]
            if ruler not in planets_by_name:
                continue
            dispositors.append(
                {
                    "planet": planet["name"],
                    "dispositor": ruler,
                    "same_planet": planet["name"] == ruler,
                }
            )
        return dispositors

    def _timezone_to_utc_string(self, timezone: float) -> str:
        sign = "+" if timezone >= 0 else "-"
        absolute = abs(timezone)
        hours = int(absolute)
        minutes = int(round((absolute - hours) * 60))
        if minutes == 60:
            hours += 1
            minutes = 0
        return f"{sign}{hours:02d}:{minutes:02d}"


class _VedicAstroChartAdapter:
    """Compatibility wrapper over the installed `vedicastro` package output."""

    def __init__(self, planets: list[Any], houses: list[Any]) -> None:
        self._planets = planets
        self._houses = houses

    def get_planets(self) -> list[Any]:
        canonical_planets = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        return [
            SimpleNamespace(
                name=planet.Object,
                sign=planet.Rasi,
                degree=planet.SignLonDecDeg,
                longitude=planet.LonDecDeg,
                latitude=getattr(planet, "LatDecDeg", 0.0),
                house=planet.HouseNr,
                nakshatra=planet.Nakshatra,
                pada=None,
                sublord=planet.SubLord,
                is_retrograde=bool(planet.isRetroGrade),
            )
            for planet in self._planets
            if getattr(planet, "Object", None) in canonical_planets
        ]

    def get_houses(self) -> list[Any]:
        return [
            SimpleNamespace(
                number=house.HouseNr,
                sign=house.Rasi,
                degree=house.SignLonDecDeg,
            )
            for house in self._houses
        ]


class _ComputedChartAdapter:
    """Simple adapter for internally computed chart objects."""

    def __init__(self, planets: list[Any], houses: list[Any]) -> None:
        self._planets = planets
        self._houses = houses

    def get_planets(self) -> list[Any]:
        return self._planets

    def get_houses(self) -> list[Any]:
        return self._houses
