"""Phase 1 normaliser coverage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from normaliser.normaliser import AstrologyNormaliser


@pytest.fixture(scope="module")
def n() -> AstrologyNormaliser:
    return AstrologyNormaliser()


class TestOntologyCounts:
    def test_planets_count(self) -> None:
        with Path("normaliser/ontology/planets.json").open(encoding="utf-8") as handle:
            assert len(json.load(handle)["planets"]) == 9

    def test_signs_count(self) -> None:
        with Path("normaliser/ontology/signs.json").open(encoding="utf-8") as handle:
            assert len(json.load(handle)["signs"]) == 12

    def test_houses_count(self) -> None:
        with Path("normaliser/ontology/houses.json").open(encoding="utf-8") as handle:
            assert len(json.load(handle)["houses"]) == 12

    def test_nakshatras_count(self) -> None:
        with Path("normaliser/ontology/nakshatras.json").open(encoding="utf-8") as handle:
            assert len(json.load(handle)["nakshatras"]) == 27

    def test_yogas_count(self) -> None:
        with Path("normaliser/ontology/yogas.json").open(encoding="utf-8") as handle:
            assert len(json.load(handle)["yogas"]) >= 50


class TestPlanetSynonyms:
    def test_sun_canonical(self, n: AstrologyNormaliser) -> None: assert n.normalise("SUN") == "SUN"
    def test_sun_english(self, n: AstrologyNormaliser) -> None: assert n.normalise("Sun") == "SUN"
    def test_sun_surya(self, n: AstrologyNormaliser) -> None: assert n.normalise("Surya") == "SUN"
    def test_sun_ravi(self, n: AstrologyNormaliser) -> None: assert n.normalise("Ravi") == "SUN"
    def test_sun_aditya(self, n: AstrologyNormaliser) -> None: assert n.normalise("Aditya") == "SUN"
    def test_moon_chandra(self, n: AstrologyNormaliser) -> None: assert n.normalise("Chandra") == "MOON"
    def test_moon_soma(self, n: AstrologyNormaliser) -> None: assert n.normalise("Soma") == "MOON"
    def test_mars_kuja(self, n: AstrologyNormaliser) -> None: assert n.normalise("Kuja") == "MARS"
    def test_mars_bhouma(self, n: AstrologyNormaliser) -> None: assert n.normalise("Bhouma") == "MARS"
    def test_mars_mangala(self, n: AstrologyNormaliser) -> None: assert n.normalise("Mangala") == "MARS"
    def test_jupiter_guru(self, n: AstrologyNormaliser) -> None: assert n.normalise("Guru") == "JUPITER"
    def test_jupiter_brihaspati(self, n: AstrologyNormaliser) -> None: assert n.normalise("Brihaspati") == "JUPITER"
    def test_saturn_shani(self, n: AstrologyNormaliser) -> None: assert n.normalise("Shani") == "SATURN"
    def test_saturn_manda(self, n: AstrologyNormaliser) -> None: assert n.normalise("Manda") == "SATURN"
    def test_venus_shukra(self, n: AstrologyNormaliser) -> None: assert n.normalise("Shukra") == "VENUS"
    def test_mercury_budha(self, n: AstrologyNormaliser) -> None: assert n.normalise("Budha") == "MERCURY"
    def test_rahu_node(self, n: AstrologyNormaliser) -> None: assert n.normalise("Dragon's Head") == "RAHU"
    def test_ketu_node(self, n: AstrologyNormaliser) -> None: assert n.normalise("Dragon's Tail") == "KETU"


class TestHouseSynonyms:
    def test_lagna(self, n: AstrologyNormaliser) -> None: assert n.normalise("Lagna") == "HOUSE_1"
    def test_ascendant(self, n: AstrologyNormaliser) -> None: assert n.normalise("Ascendant") == "HOUSE_1"
    def test_tanu_bhava(self, n: AstrologyNormaliser) -> None: assert n.normalise("Tanu Bhava") == "HOUSE_1"
    def test_kalatra_bhava(self, n: AstrologyNormaliser) -> None: assert n.normalise("Kalatra Bhava") == "HOUSE_7"
    def test_karma_bhava(self, n: AstrologyNormaliser) -> None: assert n.normalise("Karma Bhava") == "HOUSE_10"
    def test_dhana_bhava(self, n: AstrologyNormaliser) -> None: assert n.normalise("Dhana Bhava") == "HOUSE_2"


class TestSignSynonyms:
    def test_mesha(self, n: AstrologyNormaliser) -> None: assert n.normalise("Mesha") == "ARIES"
    def test_mesh(self, n: AstrologyNormaliser) -> None: assert n.normalise("Mesh") == "ARIES"
    def test_vrishabha(self, n: AstrologyNormaliser) -> None: assert n.normalise("Vrishabha") == "TAURUS"
    def test_karka(self, n: AstrologyNormaliser) -> None: assert n.normalise("Karka") == "CANCER"
    def test_simha(self, n: AstrologyNormaliser) -> None: assert n.normalise("Simha") == "LEO"
    def test_dhanu(self, n: AstrologyNormaliser) -> None: assert n.normalise("Dhanu") == "SAGITTARIUS"
    def test_makara(self, n: AstrologyNormaliser) -> None: assert n.normalise("Makara") == "CAPRICORN"
    def test_meena(self, n: AstrologyNormaliser) -> None: assert n.normalise("Meena") == "PISCES"


class TestNakshatraAndYogaSynonyms:
    def test_ashwini(self, n: AstrologyNormaliser) -> None: assert n.normalise("Ashwini") == "ASHWINI"
    def test_sravana_variant(self, n: AstrologyNormaliser) -> None: assert n.normalise("Sravana") == "SHRAVANA"
    def test_gaja_kesari(self, n: AstrologyNormaliser) -> None: assert n.normalise("Gaja Kesari Yoga") == "GAJA_KESARI"
    def test_shasha_alias(self, n: AstrologyNormaliser) -> None: assert n.normalise("Shasha Yoga") == "SASA"


class TestEdgeCases:
    def test_unknown_returns_none(self, n: AstrologyNormaliser) -> None: assert n.normalise("gibberish") is None
    def test_empty_string_returns_none(self, n: AstrologyNormaliser) -> None: assert n.normalise("") is None
    def test_case_insensitive(self, n: AstrologyNormaliser) -> None: assert n.normalise("SURYA") == "SUN"
    def test_case_insensitive_lower(self, n: AstrologyNormaliser) -> None: assert n.normalise("surya") == "SUN"
    def test_whitespace_stripped(self, n: AstrologyNormaliser) -> None: assert n.normalise("  Guru  ") == "JUPITER"
    def test_extract_known_terms(self, n: AstrologyNormaliser) -> None:
        found = n.extract_known_terms("Guru in Mesha with Lagna forms Raja Yoga.")
        assert "guru" in found
        assert "mesha" in found
        assert "lagna" in found
        assert "raja yoga" in found
