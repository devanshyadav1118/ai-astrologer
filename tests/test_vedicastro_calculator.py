"""Phase 4 calculator coverage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from chart.vedicastro_calculator import VedicAstroCalculator


@dataclass
class FakeHouse:
    number: int
    sign: str
    degree: float


@dataclass
class FakePlanet:
    name: str
    sign: str
    degree: float
    longitude: float
    house: int
    nakshatra: str | None = None
    pada: int = 0
    sublord: str | None = None
    is_retrograde: bool = False


class FakeChart:
    def __init__(self, houses: list[FakeHouse], planets: list[FakePlanet]) -> None:
        self._houses = houses
        self._planets = planets

    def get_houses(self) -> list[FakeHouse]:
        return self._houses

    def get_planets(self) -> list[FakePlanet]:
        return self._planets


def build_fake_chart(**_: Any) -> FakeChart:
    houses = [
        FakeHouse(number=1, sign="Mesha", degree=0.0),
        FakeHouse(number=2, sign="Vrishabha", degree=0.0),
        FakeHouse(number=3, sign="Mithuna", degree=0.0),
        FakeHouse(number=4, sign="Karka", degree=0.0),
        FakeHouse(number=5, sign="Simha", degree=0.0),
        FakeHouse(number=6, sign="Kanya", degree=0.0),
        FakeHouse(number=7, sign="Tula", degree=0.0),
        FakeHouse(number=8, sign="Vrischika", degree=0.0),
        FakeHouse(number=9, sign="Dhanu", degree=0.0),
        FakeHouse(number=10, sign="Makara", degree=0.0),
        FakeHouse(number=11, sign="Kumbha", degree=0.0),
        FakeHouse(number=12, sign="Meena", degree=0.0),
    ]
    planets = [
        FakePlanet(name="Sun", sign="Mesha", degree=10.0, longitude=10.0, house=1, nakshatra="Ashwini", pada=1),
        FakePlanet(name="Mars", sign="Makara", degree=15.0, longitude=285.0, house=10, nakshatra="Shravana", pada=2),
        FakePlanet(name="Jupiter", sign="Karka", degree=5.0, longitude=95.0, house=4, nakshatra="Pushya", pada=3),
        FakePlanet(name="Mercury", sign="Mesha", degree=14.0, longitude=14.0, house=1, nakshatra="Ashwini", pada=2),
        FakePlanet(name="Saturn", sign="Tula", degree=20.0, longitude=200.0, house=7, nakshatra="Swati", pada=1),
    ]
    return FakeChart(houses=houses, planets=planets)


def test_calculate_chart_normalises_houses_and_planets() -> None:
    calculator = VedicAstroCalculator(chart_factory=build_fake_chart)

    chart = calculator.calculate_chart(
        date="1990-05-15",
        time="14:30:00",
        latitude=26.9124,
        longitude=75.7873,
        timezone=5.5,
    )

    assert chart["houses"][0]["sign"] == "ARIES"
    assert chart["houses"][9]["lord"] == "SATURN"
    assert chart["planets"][0]["name"] == "SUN"
    assert chart["planets"][1]["sign"] == "CAPRICORN"
    assert chart["planets"][1]["nakshatra"] == "SHRAVANA"


def test_calculate_chart_assigns_dignity_and_combustion() -> None:
    calculator = VedicAstroCalculator(chart_factory=build_fake_chart)

    chart = calculator.calculate_chart(
        date="1990-05-15",
        time="14:30:00",
        latitude=26.9124,
        longitude=75.7873,
        timezone=5.5,
    )
    planets = {planet["name"]: planet for planet in chart["planets"]}

    assert planets["SUN"]["dignity"]["status"] == "exalted"
    assert planets["MARS"]["dignity"]["status"] == "exalted"
    assert planets["JUPITER"]["dignity"]["status"] == "exalted"
    assert planets["MERCURY"]["combustion"] is True
    assert planets["SATURN"]["combustion"] is False


def test_calculate_chart_builds_vedic_aspects() -> None:
    calculator = VedicAstroCalculator(chart_factory=build_fake_chart)

    chart = calculator.calculate_chart(
        date="1990-05-15",
        time="14:30:00",
        latitude=26.9124,
        longitude=75.7873,
        timezone=5.5,
    )

    aspect_signatures = {
        (aspect["from_planet"], aspect["to_planet"], aspect["house_offset"], aspect["type"])
        for aspect in chart["aspects"]
    }
    assert ("MARS", "JUPITER", 7, "OPPOSITION") in aspect_signatures
    assert ("JUPITER", "MARS", 7, "OPPOSITION") in aspect_signatures
    assert ("SATURN", "JUPITER", 10, "SATURN_SPECIAL_ASPECT") in aspect_signatures


def test_calculate_chart_builds_house_aspects_conjunctions_and_dispositors() -> None:
    calculator = VedicAstroCalculator(chart_factory=build_fake_chart)

    chart = calculator.calculate_chart(
        date="1990-05-15",
        time="14:30:00",
        latitude=26.9124,
        longitude=75.7873,
        timezone=5.5,
    )

    house_aspects = {
        (aspect["from_planet"], aspect["to_house"], aspect["type"])
        for aspect in chart["house_aspects"]
    }
    conjunctions = {
        (conjunction["planet_1"], conjunction["planet_2"], conjunction["same_nakshatra"])
        for conjunction in chart["conjunctions"]
    }
    dispositors = {
        (item["planet"], item["dispositor"], item["same_planet"])
        for item in chart["dispositors"]
    }

    assert ("MARS", 4, "OPPOSITION") in house_aspects
    assert ("SATURN", 4, "SATURN_SPECIAL_ASPECT") in house_aspects
    assert ("SUN", "MERCURY", True) in conjunctions
    assert ("MARS", "SATURN", False) in dispositors
    assert all(item[0] != "SATURN" for item in dispositors)
