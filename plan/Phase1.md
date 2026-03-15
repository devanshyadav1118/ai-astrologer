# Phase 1 — Formal Ontology Design
**AI Astrologer · v3.0 · MacBook Air M2 · Python 3.11 · Gemini Pro**
**Duration:** Weeks 3–4
**Goal:** Complete controlled vocabulary + synonym map + working normaliser. Every extracted rule from every book passes through this before touching Neo4j.

---

## Why This Phase Cannot Be Skipped

When extracting from 200–300 books you will encounter the same concept named dozens of ways:
- `Surya`, `Ravi`, `Arka`, `Aditya`, `Sun` → all mean the same planet
- `Lagna`, `Ascendant`, `1st house`, `Tanu Bhava` → all mean the same house
- `Guru`, `Brihaspati`, `Jupiter` → same planet

Without this phase, your knowledge graph becomes fragmented — `Surya` and `Sun` become two different nodes, and no rule ever connects correctly.

> ⚠️ Hard stop: do NOT begin Phase 2 extraction until `pytest tests/test_normaliser.py` passes 100%.

---

## Files to Create in This Phase

```
normaliser/
├── ontology/
│   ├── planets.json        ← Task 1.1
│   ├── signs.json          ← Task 1.2
│   ├── houses.json         ← Task 1.3
│   ├── nakshatras.json     ← Task 1.4
│   └── yogas.json          ← Task 1.5
├── normaliser.py           ← Task 1.6
└── validator.py            ← Task 1.7

storage/
└── neo4j_client.py         ← Task 1.8 (base ontology loader)

pipeline/
└── load_ontology.py        ← Task 1.9 (run-once seeder)

tests/
└── test_normaliser.py      ← Task 1.6 (write alongside normaliser)
```

---

## 1.1 — `normaliser/ontology/planets.json`

Define all 9 grahas. Use this exact schema — every field is needed by the reasoning engine in later phases.

```json
{
  "planets": [
    {
      "canonical_name": "SUN",
      "synonyms": [
        "Sun", "Surya", "Ravi", "Arka", "Aditya",
        "Bhanu", "Dinakara", "Bhaskar", "Mitra", "Vivaswat"
      ],
      "nature": "malefic",
      "element": "fire",
      "gender": "masculine",
      "exaltation_sign": "ARIES",
      "exaltation_degree": 10,
      "debilitation_sign": "LIBRA",
      "debilitation_degree": 10,
      "moolatrikona_sign": "LEO",
      "moolatrikona_degrees": [0, 20],
      "own_signs": ["LEO"],
      "friends": ["MOON", "MARS", "JUPITER"],
      "enemies": ["VENUS", "SATURN"],
      "neutrals": ["MERCURY"],
      "natural_karakatvam": ["soul", "father", "authority", "government", "vitality"],
      "body_parts": ["heart", "eyes", "bones", "spine"],
      "dasha_years": 6,
      "weekday": "Sunday",
      "direction": "east"
    },
    {
      "canonical_name": "MOON",
      "synonyms": [
        "Moon", "Chandra", "Soma", "Indu", "Nisha",
        "Mriganka", "Himanshu", "Shashi", "Nishapati"
      ],
      "nature": "benefic",
      "element": "water",
      "gender": "feminine",
      "exaltation_sign": "TAURUS",
      "exaltation_degree": 3,
      "debilitation_sign": "SCORPIO",
      "debilitation_degree": 3,
      "moolatrikona_sign": "TAURUS",
      "moolatrikona_degrees": [4, 20],
      "own_signs": ["CANCER"],
      "friends": ["SUN", "MERCURY"],
      "enemies": [],
      "neutrals": ["MARS", "JUPITER", "VENUS", "SATURN"],
      "natural_karakatvam": ["mind", "mother", "emotions", "public", "memory"],
      "body_parts": ["chest", "lungs", "blood", "fluids"],
      "dasha_years": 10,
      "weekday": "Monday",
      "direction": "northwest"
    },
    {
      "canonical_name": "MARS",
      "synonyms": [
        "Mars", "Mangala", "Kuja", "Bhouma", "Angaraka",
        "Lohitanga", "Ara", "Vakra", "Angarak"
      ],
      "nature": "malefic",
      "element": "fire",
      "gender": "masculine",
      "exaltation_sign": "CAPRICORN",
      "exaltation_degree": 28,
      "debilitation_sign": "CANCER",
      "debilitation_degree": 28,
      "moolatrikona_sign": "ARIES",
      "moolatrikona_degrees": [0, 12],
      "own_signs": ["ARIES", "SCORPIO"],
      "friends": ["SUN", "MOON", "JUPITER"],
      "enemies": ["MERCURY"],
      "neutrals": ["VENUS", "SATURN"],
      "natural_karakatvam": ["courage", "energy", "siblings", "land", "conflict"],
      "body_parts": ["blood", "muscles", "head", "marrow"],
      "dasha_years": 7,
      "weekday": "Tuesday",
      "direction": "south",
      "special_aspects": [4, 7, 8]
    },
    {
      "canonical_name": "MERCURY",
      "synonyms": [
        "Mercury", "Budha", "Saumya", "Gna", "Kumar",
        "Hemno", "Rohineyya", "Bodhana"
      ],
      "nature": "neutral",
      "element": "earth",
      "gender": "neutral",
      "exaltation_sign": "VIRGO",
      "exaltation_degree": 15,
      "debilitation_sign": "PISCES",
      "debilitation_degree": 15,
      "moolatrikona_sign": "VIRGO",
      "moolatrikona_degrees": [16, 20],
      "own_signs": ["GEMINI", "VIRGO"],
      "friends": ["SUN", "VENUS"],
      "enemies": ["MOON"],
      "neutrals": ["MARS", "JUPITER", "SATURN"],
      "natural_karakatvam": ["intellect", "communication", "trade", "skills", "education"],
      "body_parts": ["nervous_system", "skin", "arms", "tongue"],
      "dasha_years": 17,
      "weekday": "Wednesday",
      "direction": "north"
    },
    {
      "canonical_name": "JUPITER",
      "synonyms": [
        "Jupiter", "Guru", "Brihaspati", "Jeeva", "Devaguru",
        "Suracharya", "Angiras", "Vachaspati", "Brahmanaspati"
      ],
      "nature": "benefic",
      "element": "ether",
      "gender": "masculine",
      "exaltation_sign": "CANCER",
      "exaltation_degree": 5,
      "debilitation_sign": "CAPRICORN",
      "debilitation_degree": 5,
      "moolatrikona_sign": "SAGITTARIUS",
      "moolatrikona_degrees": [0, 10],
      "own_signs": ["SAGITTARIUS", "PISCES"],
      "friends": ["SUN", "MOON", "MARS"],
      "enemies": ["MERCURY", "VENUS"],
      "neutrals": ["SATURN"],
      "natural_karakatvam": ["wisdom", "children", "husband", "dharma", "wealth", "teacher"],
      "body_parts": ["liver", "hips", "thighs", "fat"],
      "dasha_years": 16,
      "weekday": "Thursday",
      "direction": "northeast",
      "special_aspects": [5, 7, 9]
    },
    {
      "canonical_name": "VENUS",
      "synonyms": [
        "Venus", "Shukra", "Bhrigu", "Kavi", "Sita",
        "Asuracharya", "Daityaguru", "Usanas", "Shukracharya"
      ],
      "nature": "benefic",
      "element": "water",
      "gender": "feminine",
      "exaltation_sign": "PISCES",
      "exaltation_degree": 27,
      "debilitation_sign": "VIRGO",
      "debilitation_degree": 27,
      "moolatrikona_sign": "LIBRA",
      "moolatrikona_degrees": [0, 15],
      "own_signs": ["TAURUS", "LIBRA"],
      "friends": ["MERCURY", "SATURN"],
      "enemies": ["SUN", "MOON"],
      "neutrals": ["MARS", "JUPITER"],
      "natural_karakatvam": ["wife", "beauty", "pleasure", "arts", "vehicles", "luxury"],
      "body_parts": ["kidneys", "reproductive_system", "throat", "face"],
      "dasha_years": 20,
      "weekday": "Friday",
      "direction": "southeast"
    },
    {
      "canonical_name": "SATURN",
      "synonyms": [
        "Saturn", "Shani", "Sanaischara", "Manda", "Krura",
        "Asita", "Yama", "Arkaja", "Saurya", "Shanaischar"
      ],
      "nature": "malefic",
      "element": "air",
      "gender": "neutral",
      "exaltation_sign": "LIBRA",
      "exaltation_degree": 20,
      "debilitation_sign": "ARIES",
      "debilitation_degree": 20,
      "moolatrikona_sign": "AQUARIUS",
      "moolatrikona_degrees": [0, 20],
      "own_signs": ["CAPRICORN", "AQUARIUS"],
      "friends": ["MERCURY", "VENUS"],
      "enemies": ["SUN", "MOON", "MARS"],
      "neutrals": ["JUPITER"],
      "natural_karakatvam": ["longevity", "discipline", "karma", "servants", "loss", "delays"],
      "body_parts": ["bones", "teeth", "joints", "nerves"],
      "dasha_years": 19,
      "weekday": "Saturday",
      "direction": "west",
      "special_aspects": [3, 7, 10]
    },
    {
      "canonical_name": "RAHU",
      "synonyms": [
        "Rahu", "Sarpa", "Dragon's Head", "North Node", "Tamas",
        "Svarbhanu", "Abhrak", "Caput Draconis"
      ],
      "nature": "malefic",
      "element": "air",
      "gender": "neutral",
      "exaltation_sign": "GEMINI",
      "debilitation_sign": "SAGITTARIUS",
      "own_signs": ["AQUARIUS"],
      "natural_karakatvam": ["foreigners", "material_desire", "obsession", "technology", "ambition"],
      "dasha_years": 18
    },
    {
      "canonical_name": "KETU",
      "synonyms": [
        "Ketu", "Dragon's Tail", "South Node", "Sikhi", "Dhvaja",
        "Mokshakaraka", "Cauda Draconis"
      ],
      "nature": "malefic",
      "element": "fire",
      "gender": "neutral",
      "exaltation_sign": "SAGITTARIUS",
      "debilitation_sign": "GEMINI",
      "own_signs": ["SCORPIO"],
      "natural_karakatvam": ["liberation", "spirituality", "past_life", "detachment", "occult"],
      "dasha_years": 7
    }
  ]
}
```

---

## 1.2 — `normaliser/ontology/signs.json`

```json
{
  "signs": [
    {
      "canonical_name": "ARIES",
      "number": 1,
      "synonyms": ["Aries", "Mesha", "Mesh"],
      "sanskrit_name": "Mesha",
      "ruler": "MARS",
      "element": "fire",
      "modality": "cardinal",
      "gender": "masculine",
      "exaltation_planet": "SUN",
      "debilitation_planet": "SATURN",
      "primary_meanings": ["self", "initiative", "courage", "beginnings"]
    },
    {
      "canonical_name": "TAURUS",
      "number": 2,
      "synonyms": ["Taurus", "Vrishabha", "Vrishab"],
      "sanskrit_name": "Vrishabha",
      "ruler": "VENUS",
      "element": "earth",
      "modality": "fixed",
      "gender": "feminine",
      "exaltation_planet": "MOON",
      "debilitation_planet": null,
      "primary_meanings": ["wealth", "speech", "food", "stability"]
    },
    {
      "canonical_name": "GEMINI",
      "number": 3,
      "synonyms": ["Gemini", "Mithuna", "Mithun"],
      "sanskrit_name": "Mithuna",
      "ruler": "MERCURY",
      "element": "air",
      "modality": "mutable",
      "gender": "masculine",
      "exaltation_planet": null,
      "debilitation_planet": null,
      "primary_meanings": ["communication", "skills", "siblings", "adaptability"]
    },
    {
      "canonical_name": "CANCER",
      "number": 4,
      "synonyms": ["Cancer", "Karka", "Karkata", "Kataka"],
      "sanskrit_name": "Karka",
      "ruler": "MOON",
      "element": "water",
      "modality": "cardinal",
      "gender": "feminine",
      "exaltation_planet": "JUPITER",
      "debilitation_planet": "MARS",
      "primary_meanings": ["home", "mother", "emotions", "nurturing"]
    },
    {
      "canonical_name": "LEO",
      "number": 5,
      "synonyms": ["Leo", "Simha", "Singh"],
      "sanskrit_name": "Simha",
      "ruler": "SUN",
      "element": "fire",
      "modality": "fixed",
      "gender": "masculine",
      "exaltation_planet": null,
      "debilitation_planet": null,
      "primary_meanings": ["authority", "creativity", "children", "pride"]
    },
    {
      "canonical_name": "VIRGO",
      "number": 6,
      "synonyms": ["Virgo", "Kanya"],
      "sanskrit_name": "Kanya",
      "ruler": "MERCURY",
      "element": "earth",
      "modality": "mutable",
      "gender": "feminine",
      "exaltation_planet": "MERCURY",
      "debilitation_planet": "VENUS",
      "primary_meanings": ["service", "health", "analysis", "purity"]
    },
    {
      "canonical_name": "LIBRA",
      "number": 7,
      "synonyms": ["Libra", "Tula"],
      "sanskrit_name": "Tula",
      "ruler": "VENUS",
      "element": "air",
      "modality": "cardinal",
      "gender": "masculine",
      "exaltation_planet": "SATURN",
      "debilitation_planet": "SUN",
      "primary_meanings": ["marriage", "partnerships", "trade", "balance"]
    },
    {
      "canonical_name": "SCORPIO",
      "number": 8,
      "synonyms": ["Scorpio", "Vrishchika", "Vrischika"],
      "sanskrit_name": "Vrishchika",
      "ruler": "MARS",
      "element": "water",
      "modality": "fixed",
      "gender": "feminine",
      "exaltation_planet": null,
      "debilitation_planet": "MOON",
      "primary_meanings": ["transformation", "research", "occult", "secrets"]
    },
    {
      "canonical_name": "SAGITTARIUS",
      "number": 9,
      "synonyms": ["Sagittarius", "Dhanu", "Dhanus"],
      "sanskrit_name": "Dhanu",
      "ruler": "JUPITER",
      "element": "fire",
      "modality": "mutable",
      "gender": "masculine",
      "exaltation_planet": null,
      "debilitation_planet": "KETU",
      "primary_meanings": ["dharma", "fortune", "higher_learning", "teacher"]
    },
    {
      "canonical_name": "CAPRICORN",
      "number": 10,
      "synonyms": ["Capricorn", "Makara", "Makar"],
      "sanskrit_name": "Makara",
      "ruler": "SATURN",
      "element": "earth",
      "modality": "cardinal",
      "gender": "feminine",
      "exaltation_planet": "MARS",
      "debilitation_planet": "JUPITER",
      "primary_meanings": ["career", "status", "discipline", "ambition"]
    },
    {
      "canonical_name": "AQUARIUS",
      "number": 11,
      "synonyms": ["Aquarius", "Kumbha"],
      "sanskrit_name": "Kumbha",
      "ruler": "SATURN",
      "element": "air",
      "modality": "fixed",
      "gender": "masculine",
      "exaltation_planet": null,
      "debilitation_planet": null,
      "primary_meanings": ["gains", "networks", "idealism", "mass_causes"]
    },
    {
      "canonical_name": "PISCES",
      "number": 12,
      "synonyms": ["Pisces", "Meena", "Meen"],
      "sanskrit_name": "Meena",
      "ruler": "JUPITER",
      "element": "water",
      "modality": "mutable",
      "gender": "feminine",
      "exaltation_planet": "VENUS",
      "debilitation_planet": "MERCURY",
      "primary_meanings": ["liberation", "spirituality", "loss", "foreign"]
    }
  ]
}
```

---

## 1.3 — `normaliser/ontology/houses.json`

```json
{
  "houses": [
    {
      "canonical_name": "HOUSE_1", "number": 1,
      "synonyms": ["1st house", "First house", "Lagna", "Ascendant", "Tanu Bhava", "Udaya Lagna", "Tanur"],
      "house_type": "kendra", "secondary_types": ["trikona"],
      "natural_karaka": "SUN",
      "primary_meanings": ["self", "personality", "appearance", "health", "vitality"],
      "secondary_meanings": ["fame", "head", "early childhood", "complexion"]
    },
    {
      "canonical_name": "HOUSE_2", "number": 2,
      "synonyms": ["2nd house", "Second house", "Dhana Bhava", "Kutumba Bhava"],
      "house_type": "maraka", "secondary_types": [],
      "natural_karaka": "JUPITER",
      "primary_meanings": ["wealth", "speech", "family", "food"],
      "secondary_meanings": ["right eye", "accumulated assets", "early education"]
    },
    {
      "canonical_name": "HOUSE_3", "number": 3,
      "synonyms": ["3rd house", "Third house", "Sahaja Bhava", "Parakrama Bhava"],
      "house_type": "upachaya", "secondary_types": [],
      "natural_karaka": "MARS",
      "primary_meanings": ["siblings", "communication", "courage", "skills"],
      "secondary_meanings": ["short travel", "right ear", "writing", "neighbours"]
    },
    {
      "canonical_name": "HOUSE_4", "number": 4,
      "synonyms": ["4th house", "Fourth house", "Sukha Bhava", "Matru Bhava", "Bandhu Bhava"],
      "house_type": "kendra", "secondary_types": [],
      "natural_karaka": "MOON",
      "primary_meanings": ["mother", "home", "happiness", "education"],
      "secondary_meanings": ["land", "vehicles", "chest", "fixed assets"]
    },
    {
      "canonical_name": "HOUSE_5", "number": 5,
      "synonyms": ["5th house", "Fifth house", "Putra Bhava", "Suta Bhava"],
      "house_type": "trikona", "secondary_types": [],
      "natural_karaka": "JUPITER",
      "primary_meanings": ["children", "intellect", "creativity", "past merit"],
      "secondary_meanings": ["speculation", "romance", "stomach", "mantras"]
    },
    {
      "canonical_name": "HOUSE_6", "number": 6,
      "synonyms": ["6th house", "Sixth house", "Ripu Bhava", "Shatru Bhava", "Roga Bhava"],
      "house_type": "trik", "secondary_types": ["upachaya"],
      "natural_karaka": "MARS",
      "primary_meanings": ["enemies", "disease", "debt", "service"],
      "secondary_meanings": ["obstacles", "litigation", "maternal uncle", "digestion"]
    },
    {
      "canonical_name": "HOUSE_7", "number": 7,
      "synonyms": ["7th house", "Seventh house", "Kalatra Bhava", "Jaya Bhava", "Jamitra"],
      "house_type": "kendra", "secondary_types": ["maraka"],
      "natural_karaka": "VENUS",
      "primary_meanings": ["marriage", "spouse", "partnerships", "business"],
      "secondary_meanings": ["foreign travel", "trade", "lower abdomen", "legal contracts"]
    },
    {
      "canonical_name": "HOUSE_8", "number": 8,
      "synonyms": ["8th house", "Eighth house", "Ayur Bhava", "Mritu Bhava", "Randhra Bhava"],
      "house_type": "trik", "secondary_types": [],
      "natural_karaka": "SATURN",
      "primary_meanings": ["longevity", "transformation", "research", "occult"],
      "secondary_meanings": ["inheritance", "chronic illness", "sudden events", "in-laws"]
    },
    {
      "canonical_name": "HOUSE_9", "number": 9,
      "synonyms": ["9th house", "Ninth house", "Dharma Bhava", "Bhagya Bhava", "Pitru Bhava"],
      "house_type": "trikona", "secondary_types": [],
      "natural_karaka": "JUPITER",
      "primary_meanings": ["fortune", "guru", "dharma", "father", "higher learning"],
      "secondary_meanings": ["long travel", "religion", "philosophy", "luck"]
    },
    {
      "canonical_name": "HOUSE_10", "number": 10,
      "synonyms": ["10th house", "Tenth house", "Karma Bhava", "Rajya Bhava", "Kirtisthana"],
      "house_type": "kendra", "secondary_types": [],
      "natural_karaka": "SUN",
      "primary_meanings": ["career", "status", "authority", "public image"],
      "secondary_meanings": ["government", "father", "knees", "profession"]
    },
    {
      "canonical_name": "HOUSE_11", "number": 11,
      "synonyms": ["11th house", "Eleventh house", "Labha Bhava", "Ayaya Bhava"],
      "house_type": "upachaya", "secondary_types": [],
      "natural_karaka": "JUPITER",
      "primary_meanings": ["gains", "income", "networks", "elder siblings"],
      "secondary_meanings": ["fulfilment of desires", "left ear", "friends"]
    },
    {
      "canonical_name": "HOUSE_12", "number": 12,
      "synonyms": ["12th house", "Twelfth house", "Vyaya Bhava", "Moksha Bhava", "Antya Bhava"],
      "house_type": "trik", "secondary_types": [],
      "natural_karaka": "SATURN",
      "primary_meanings": ["loss", "liberation", "foreign", "spiritual practices"],
      "secondary_meanings": ["expenses", "sleep", "left eye", "imprisonment", "hospitals"]
    }
  ]
}
```

---

## 1.4 — `normaliser/ontology/nakshatras.json`

Define all 27. Schema for each entry — fill in all 27 following this pattern:

```json
{
  "nakshatras": [
    {
      "canonical_name": "ASHWINI",
      "number": 1,
      "synonyms": ["Ashwini", "Asvini", "Ashvini", "Aswini"],
      "lord": "KETU",
      "deity": "Ashwini Kumaras",
      "shakti": "healing_power",
      "symbol": "horse_head",
      "gana": "deva",
      "gender": "masculine",
      "rashi": "ARIES",
      "degrees": [0, 13.2],
      "padas": [
        {"pada": 1, "navamsa_sign": "ARIES"},
        {"pada": 2, "navamsa_sign": "TAURUS"},
        {"pada": 3, "navamsa_sign": "GEMINI"},
        {"pada": 4, "navamsa_sign": "CANCER"}
      ],
      "primary_qualities": ["speed", "healing", "initiation", "divine_grace"]
    },
    {
      "canonical_name": "BHARANI",
      "number": 2,
      "synonyms": ["Bharani", "Bharni"],
      "lord": "VENUS",
      "deity": "Yama",
      "shakti": "apabharani_shakti",
      "symbol": "yoni",
      "gana": "manushya",
      "gender": "feminine",
      "rashi": "ARIES",
      "degrees": [13.2, 26.4],
      "padas": [
        {"pada": 1, "navamsa_sign": "LEO"},
        {"pada": 2, "navamsa_sign": "VIRGO"},
        {"pada": 3, "navamsa_sign": "LIBRA"},
        {"pada": 4, "navamsa_sign": "SCORPIO"}
      ],
      "primary_qualities": ["restraint", "purification", "fertility", "karma"]
    }
    // ... continue for KRITTIKA through REVATI (all 27)
    // Lords follow Vimshottari sequence: KETU, VENUS, SUN, MOON, MARS,
    // RAHU, JUPITER, SATURN, MERCURY (repeating 3 times across 27 nakshatras)
  ]
}
```

**Nakshatra lord sequence (for reference):**
| # | Name | Lord | Rashi |
|---|------|------|-------|
| 1 | ASHWINI | KETU | ARIES |
| 2 | BHARANI | VENUS | ARIES |
| 3 | KRITTIKA | SUN | ARIES/TAURUS |
| 4 | ROHINI | MOON | TAURUS |
| 5 | MRIGASHIRA | MARS | TAURUS/GEMINI |
| 6 | ARDRA | RAHU | GEMINI |
| 7 | PUNARVASU | JUPITER | GEMINI/CANCER |
| 8 | PUSHYA | SATURN | CANCER |
| 9 | ASHLESHA | MERCURY | CANCER |
| 10 | MAGHA | KETU | LEO |
| 11 | PURVA_PHALGUNI | VENUS | LEO |
| 12 | UTTARA_PHALGUNI | SUN | LEO/VIRGO |
| 13 | HASTA | MOON | VIRGO |
| 14 | CHITRA | MARS | VIRGO/LIBRA |
| 15 | SWATI | RAHU | LIBRA |
| 16 | VISHAKHA | JUPITER | LIBRA/SCORPIO |
| 17 | ANURADHA | SATURN | SCORPIO |
| 18 | JYESHTHA | MERCURY | SCORPIO |
| 19 | MULA | KETU | SAGITTARIUS |
| 20 | PURVA_ASHADHA | VENUS | SAGITTARIUS |
| 21 | UTTARA_ASHADHA | SUN | SAGITTARIUS/CAPRICORN |
| 22 | SHRAVANA | MOON | CAPRICORN |
| 23 | DHANISHTHA | MARS | CAPRICORN/AQUARIUS |
| 24 | SHATABHISHA | RAHU | AQUARIUS |
| 25 | PURVA_BHADRAPADA | JUPITER | AQUARIUS/PISCES |
| 26 | UTTARA_BHADRAPADA | SATURN | PISCES |
| 27 | REVATI | MERCURY | PISCES |

---

## 1.5 — `normaliser/ontology/yogas.json`

Define 50+ classical yogas. **Each yoga must have machine-readable conditions** — not just text descriptions — because the yoga detection engine in Phase 7 will run these as graph queries.

```json
{
  "yogas": [
    {
      "canonical_name": "GAJA_KESARI",
      "synonyms": ["Gaja Kesari Yoga", "Gajakesari", "Elephant-Lion Yoga"],
      "type": "dhana_raja_yoga",
      "conditions": {
        "logic": "AND",
        "rules": [
          {"planet": "JUPITER", "relation": "in_kendra_from", "reference": "MOON"},
          {"planet": "JUPITER", "not_in": ["HOUSE_6", "HOUSE_8", "HOUSE_12"]}
        ]
      },
      "effects": ["wisdom", "fame", "benevolence", "wealth", "leadership"],
      "classical_sources": ["Brihat Parashara Hora Shastra", "Phaladeepika"],
      "confidence": "very_high"
    },
    {
      "canonical_name": "RAJA_YOGA",
      "synonyms": ["Raja Yoga", "Royal Combination"],
      "type": "raja_yoga",
      "conditions": {
        "logic": "OR",
        "rules": [
          {"conjunction_between": ["trikona_lord", "kendra_lord"]},
          {"aspect_between": ["trikona_lord", "kendra_lord"]},
          {"mutual_reception_between": ["trikona_lord", "kendra_lord"]}
        ]
      },
      "effects": ["authority", "fame", "political_success", "leadership"],
      "classical_sources": ["Brihat Parashara Hora Shastra"],
      "confidence": "classical"
    },
    {
      "canonical_name": "DHANA_YOGA",
      "synonyms": ["Dhana Yoga", "Wealth Combination"],
      "type": "dhana_yoga",
      "conditions": {
        "logic": "OR",
        "rules": [
          {"conjunction_between": ["HOUSE_2_lord", "HOUSE_11_lord"]},
          {"aspect_between": ["HOUSE_2_lord", "HOUSE_11_lord"]},
          {"conjunction_between": ["HOUSE_1_lord", "HOUSE_2_lord"]}
        ]
      },
      "effects": ["wealth", "financial_prosperity", "material_gains"],
      "classical_sources": ["Brihat Parashara Hora Shastra"],
      "confidence": "high"
    },
    {
      "canonical_name": "BUDHA_ADITYA",
      "synonyms": ["Budha Aditya Yoga", "Nipuna Yoga"],
      "type": "graha_yoga",
      "conditions": {
        "logic": "AND",
        "rules": [
          {"conjunction_between": ["SUN", "MERCURY"]},
          {"planet": "SUN", "not_in_sign": ["GEMINI", "VIRGO"]}
        ]
      },
      "effects": ["intelligence", "communication skills", "career success", "recognition"],
      "classical_sources": ["Phaladeepika"],
      "confidence": "high"
    },
    {
      "canonical_name": "CHANDRA_MANGALA",
      "synonyms": ["Chandra Mangala Yoga", "Moon Mars Yoga"],
      "type": "dhana_yoga",
      "conditions": {
        "logic": "OR",
        "rules": [
          {"conjunction_between": ["MOON", "MARS"]},
          {"mutual_aspect_between": ["MOON", "MARS"]}
        ]
      },
      "effects": ["wealth through trade", "bold temperament", "independent earning"],
      "classical_sources": ["Brihat Jataka"],
      "confidence": "high"
    }
    // ... continue to 50+ yogas
    // Include: PANCHA_MAHAPURUSHA (5 yogas), NEECHA_BHANGA,
    // VIPARITA_RAJA_YOGA, KEMADRUMA, SUNAPHA, ANAPHA, DURUDHURA,
    // VESI, VOSI, UBHAYACHARI, HAMSA, MALAVYA, RUCHAKA,
    // BHADRA, SASA, SHASHA, and others from your classical texts
  ]
}
```

---

## 1.6 — `normaliser/normaliser.py`

This is the most critical function in the entire pipeline. Every entity name from every book passes through `normalise()` before storage.

```python
# normaliser/normaliser.py
import json
import re
from pathlib import Path


class AstrologyNormaliser:
    """
    Maps any astrological term to its canonical form.

    Examples:
        normalise('Surya')      -> 'SUN'
        normalise('Lagna')      -> 'HOUSE_1'
        normalise('Guru')       -> 'JUPITER'
        normalise('Mesha')      -> 'ARIES'
        normalise('gibberish')  -> None  (flagged for human review)
    """

    def __init__(self, ontology_dir: str = 'normaliser/ontology') -> None:
        self.ontology_dir = Path(ontology_dir)
        self.synonym_map: dict[str, str] = {}
        self._build_synonym_map()

    def _build_synonym_map(self) -> None:
        """Load all entity JSON files and build reverse synonym lookup."""
        files = ['planets.json', 'signs.json', 'houses.json',
                 'nakshatras.json', 'yogas.json']
        for filename in files:
            filepath = self.ontology_dir / filename
            if not filepath.exists():
                continue
            with open(filepath) as f:
                data = json.load(f)
            for category_key in data:
                for entity in data[category_key]:
                    canonical = entity['canonical_name']
                    # Map canonical name to itself
                    self.synonym_map[canonical.lower()] = canonical
                    # Map all synonyms
                    for synonym in entity.get('synonyms', []):
                        self.synonym_map[synonym.lower()] = canonical

    def normalise(self, term: str) -> str | None:
        """
        Returns canonical name for any known astrological term.
        Returns None if term is not in ontology — caller must flag for review.
        """
        if not term:
            return None
        cleaned = term.strip().lower()

        # Direct lookup
        if cleaned in self.synonym_map:
            return self.synonym_map[cleaned]

        # Fuzzy: common adjectival suffix patterns
        patterns = [
            (r'\b(\w+)ine\b', r'\1'),    # saturnine → saturn
            (r'\b(\w+)ian\b', r'\1'),    # jupiterian → jupiter
            (r'\b(\w+)al\b', r'\1'),     # martial → marti → no match, ok
        ]
        for pattern, replacement in patterns:
            fuzzy = re.sub(pattern, replacement, cleaned)
            if fuzzy != cleaned and fuzzy in self.synonym_map:
                return self.synonym_map[fuzzy]

        return None  # Unknown — must be flagged for human review

    def normalise_batch(self, terms: list[str]) -> dict[str, str | None]:
        """Normalise a list of terms. Returns {term: canonical_or_None}."""
        return {term: self.normalise(term) for term in terms}

    def get_all_canonicals(self) -> list[str]:
        """Returns all unique canonical names in the ontology."""
        return list(set(self.synonym_map.values()))
```

**`tests/test_normaliser.py` — write this alongside the normaliser:**

```python
# tests/test_normaliser.py
import pytest
from normaliser.normaliser import AstrologyNormaliser


@pytest.fixture
def n():
    return AstrologyNormaliser()


class TestPlanetSynonyms:
    def test_sun_canonical(self, n): assert n.normalise('SUN') == 'SUN'
    def test_sun_english(self, n): assert n.normalise('Sun') == 'SUN'
    def test_sun_surya(self, n): assert n.normalise('Surya') == 'SUN'
    def test_sun_ravi(self, n): assert n.normalise('Ravi') == 'SUN'
    def test_sun_aditya(self, n): assert n.normalise('Aditya') == 'SUN'

    def test_moon_chandra(self, n): assert n.normalise('Chandra') == 'MOON'
    def test_moon_soma(self, n): assert n.normalise('Soma') == 'MOON'

    def test_mars_kuja(self, n): assert n.normalise('Kuja') == 'MARS'
    def test_mars_bhouma(self, n): assert n.normalise('Bhouma') == 'MARS'
    def test_mars_mangala(self, n): assert n.normalise('Mangala') == 'MARS'

    def test_jupiter_guru(self, n): assert n.normalise('Guru') == 'JUPITER'
    def test_jupiter_brihaspati(self, n): assert n.normalise('Brihaspati') == 'JUPITER'

    def test_saturn_shani(self, n): assert n.normalise('Shani') == 'SATURN'
    def test_saturn_manda(self, n): assert n.normalise('Manda') == 'SATURN'

    def test_venus_shukra(self, n): assert n.normalise('Shukra') == 'VENUS'
    def test_mercury_budha(self, n): assert n.normalise('Budha') == 'MERCURY'
    def test_rahu_node(self, n): assert n.normalise("Dragon's Head") == 'RAHU'
    def test_ketu_node(self, n): assert n.normalise("Dragon's Tail") == 'KETU'


class TestHouseSynonyms:
    def test_lagna(self, n): assert n.normalise('Lagna') == 'HOUSE_1'
    def test_ascendant(self, n): assert n.normalise('Ascendant') == 'HOUSE_1'
    def test_tanu_bhava(self, n): assert n.normalise('Tanu Bhava') == 'HOUSE_1'
    def test_kalatra_bhava(self, n): assert n.normalise('Kalatra Bhava') == 'HOUSE_7'
    def test_karma_bhava(self, n): assert n.normalise('Karma Bhava') == 'HOUSE_10'
    def test_dhana_bhava(self, n): assert n.normalise('Dhana Bhava') == 'HOUSE_2'


class TestSignSynonyms:
    def test_mesha(self, n): assert n.normalise('Mesha') == 'ARIES'
    def test_mesh(self, n): assert n.normalise('Mesh') == 'ARIES'
    def test_vrishabha(self, n): assert n.normalise('Vrishabha') == 'TAURUS'
    def test_karka(self, n): assert n.normalise('Karka') == 'CANCER'
    def test_simha(self, n): assert n.normalise('Simha') == 'LEO'
    def test_dhanu(self, n): assert n.normalise('Dhanu') == 'SAGITTARIUS'
    def test_makara(self, n): assert n.normalise('Makara') == 'CAPRICORN'
    def test_meena(self, n): assert n.normalise('Meena') == 'PISCES'


class TestEdgeCases:
    def test_unknown_returns_none(self, n): assert n.normalise('gibberish') is None
    def test_empty_string_returns_none(self, n): assert n.normalise('') is None
    def test_case_insensitive(self, n): assert n.normalise('SURYA') == 'SUN'
    def test_case_insensitive_lower(self, n): assert n.normalise('surya') == 'SUN'
    def test_whitespace_stripped(self, n): assert n.normalise('  Guru  ') == 'JUPITER'
```

---

## 1.7 — `normaliser/validator.py`

```python
# normaliser/validator.py
import re
from normaliser.normaliser import AstrologyNormaliser


class RuleValidator:
    """
    Validates extracted rules against the formal ontology.
    Every rule must pass through validate_rule() before Neo4j storage.
    """

    VALID_TYPES = {'prediction', 'description', 'yoga', 'calculation', 'modification'}

    def __init__(self) -> None:
        self.normaliser = AstrologyNormaliser()

    def validate_rule(self, rule: dict) -> dict:
        """
        Validates a single extracted rule.
        Returns the rule enriched with normalised_entities and validation_status.

        Status values:
            'valid'   — all fields present, all entities known
            'warning' — structurally valid but some entities unknown (needs review)
            'invalid' — missing required fields (do not store)
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Required field check
        required = ['rule_id', 'type', 'condition', 'result', 'source_text']
        for field in required:
            if not rule.get(field):
                errors.append(f'Missing required field: {field}')

        # Rule type check
        if rule.get('type') not in self.VALID_TYPES:
            warnings.append(f'Unknown rule type: {rule.get("type")} — expected one of {self.VALID_TYPES}')

        # Entity normalisation
        condition = rule.get('condition', '')
        entities_found = self._extract_entity_candidates(condition)
        normalised_entities: dict[str, str] = {}
        for entity in entities_found:
            canonical = self.normaliser.normalise(entity)
            if canonical is None:
                warnings.append(f'Unknown entity in condition: "{entity}" — needs manual review')
            else:
                normalised_entities[entity] = canonical

        status = 'invalid' if errors else ('warning' if warnings else 'valid')
        return {
            **rule,
            'normalised_entities': normalised_entities,
            'validation_errors': errors,
            'validation_warnings': warnings,
            'validation_status': status,
        }

    def validate_batch(self, rules: list[dict]) -> dict:
        """Validates a list of rules and returns categorised results + summary."""
        results: dict[str, list] = {'valid': [], 'warning': [], 'invalid': []}
        for rule in rules:
            validated = self.validate_rule(rule)
            results[validated['validation_status']].append(validated)

        total = len(rules)
        valid_pct = round(len(results['valid']) / total * 100, 1) if total else 0
        print(f'Validation: {valid_pct}% valid | '
              f'{len(results["valid"])} valid, '
              f'{len(results["warning"])} warning, '
              f'{len(results["invalid"])} invalid')
        return {'results': results, 'summary': {
            'total': total, 'valid': len(results['valid']),
            'warning': len(results['warning']), 'invalid': len(results['invalid']),
            'valid_pct': valid_pct
        }}

    def _extract_entity_candidates(self, text: str) -> list[str]:
        """Extract capitalised words/phrases that are likely entity names."""
        tokens = re.findall(r'[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*', text)
        return [t.strip() for t in tokens if len(t) > 2]
```

---

## 1.8 — `storage/neo4j_client.py` (Ontology Loader)

```python
# storage/neo4j_client.py
import json
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()


class Neo4jClient:

    def __init__(self) -> None:
        self.driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
        )

    def verify_connection(self) -> str:
        with self.driver.session() as session:
            return session.run("RETURN 'connected' AS msg").single()['msg']

    def create_constraints(self) -> None:
        constraints = [
            "CREATE CONSTRAINT planet_name IF NOT EXISTS FOR (p:Planet) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT sign_name   IF NOT EXISTS FOR (s:Sign)   REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT house_name  IF NOT EXISTS FOR (h:House)  REQUIRE h.name IS UNIQUE",
            "CREATE CONSTRAINT naksh_name  IF NOT EXISTS FOR (n:Nakshatra) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT rule_id     IF NOT EXISTS FOR (r:Rule)   REQUIRE r.rule_id IS UNIQUE",
            "CREATE CONSTRAINT yoga_name   IF NOT EXISTS FOR (y:Yoga)   REQUIRE y.name IS UNIQUE",
        ]
        with self.driver.session() as session:
            for cypher in constraints:
                session.run(cypher)

    def load_planets(self, filepath: str) -> int:
        with open(filepath) as f:
            data = json.load(f)
        with self.driver.session() as session:
            for p in data['planets']:
                session.run("""
                    MERGE (n:Planet {name: $name})
                    SET n.nature = $nature, n.element = $element,
                        n.exaltation_sign = $exalt, n.debilitation_sign = $debil,
                        n.dasha_years = $dasha, n.synonyms = $synonyms,
                        n.natural_karakatvam = $karakas
                """,
                name=p['canonical_name'], nature=p.get('nature'),
                element=p.get('element'), exalt=p.get('exaltation_sign'),
                debil=p.get('debilitation_sign'), dasha=p.get('dasha_years'),
                synonyms=p.get('synonyms', []),
                karakas=p.get('natural_karakatvam', []))
        return len(data['planets'])

    def load_signs(self, filepath: str) -> int:
        with open(filepath) as f:
            data = json.load(f)
        with self.driver.session() as session:
            for s in data['signs']:
                session.run("""
                    MERGE (n:Sign {name: $name})
                    SET n.number = $number, n.ruler = $ruler,
                        n.element = $element, n.modality = $modality,
                        n.synonyms = $synonyms,
                        n.primary_meanings = $meanings
                """,
                name=s['canonical_name'], number=s.get('number'),
                ruler=s.get('ruler'), element=s.get('element'),
                modality=s.get('modality'), synonyms=s.get('synonyms', []),
                meanings=s.get('primary_meanings', []))
        return len(data['signs'])

    def load_houses(self, filepath: str) -> int:
        with open(filepath) as f:
            data = json.load(f)
        with self.driver.session() as session:
            for h in data['houses']:
                session.run("""
                    MERGE (n:House {name: $name})
                    SET n.number = $number, n.house_type = $house_type,
                        n.natural_karaka = $karaka,
                        n.primary_meanings = $primary,
                        n.synonyms = $synonyms
                """,
                name=h['canonical_name'], number=h.get('number'),
                house_type=h.get('house_type'), karaka=h.get('natural_karaka'),
                primary=h.get('primary_meanings', []),
                synonyms=h.get('synonyms', []))
        return len(data['houses'])

    def load_nakshatras(self, filepath: str) -> int:
        with open(filepath) as f:
            data = json.load(f)
        with self.driver.session() as session:
            for nk in data['nakshatras']:
                session.run("""
                    MERGE (n:Nakshatra {name: $name})
                    SET n.number = $number, n.lord = $lord,
                        n.rashi = $rashi, n.shakti = $shakti,
                        n.gana = $gana, n.synonyms = $synonyms
                """,
                name=nk['canonical_name'], number=nk.get('number'),
                lord=nk.get('lord'), rashi=nk.get('rashi'),
                shakti=nk.get('shakti'), gana=nk.get('gana'),
                synonyms=nk.get('synonyms', []))
        return len(data['nakshatras'])

    def load_planet_relationships(self, filepath: str) -> None:
        with open(filepath) as f:
            data = json.load(f)
        with self.driver.session() as session:
            for p in data['planets']:
                pname = p['canonical_name']
                if p.get('exaltation_sign'):
                    session.run("""
                        MATCH (p:Planet {name:$pname}) MATCH (s:Sign {name:$sign})
                        MERGE (p)-[:IS_EXALTED_IN {degree:$deg}]->(s)
                    """, pname=pname, sign=p['exaltation_sign'],
                    deg=p.get('exaltation_degree', 0))
                if p.get('debilitation_sign'):
                    session.run("""
                        MATCH (p:Planet {name:$pname}) MATCH (s:Sign {name:$sign})
                        MERGE (p)-[:IS_DEBILITATED_IN {degree:$deg}]->(s)
                    """, pname=pname, sign=p['debilitation_sign'],
                    deg=p.get('debilitation_degree', 0))
                for own in p.get('own_signs', []):
                    session.run("""
                        MATCH (p:Planet {name:$pname}) MATCH (s:Sign {name:$sign})
                        MERGE (p)-[:OWNS]->(s)
                    """, pname=pname, sign=own)
                for friend in p.get('friends', []):
                    session.run("""
                        MATCH (p1:Planet {name:$p1}) MATCH (p2:Planet {name:$p2})
                        MERGE (p1)-[:NATURAL_FRIEND_OF]->(p2)
                    """, p1=pname, p2=friend)

    def verify_entity_counts(self) -> dict[str, int]:
        counts = {}
        with self.driver.session() as session:
            for label in ['Planet', 'Sign', 'House', 'Nakshatra']:
                c = session.run(f'MATCH (n:{label}) RETURN count(n) AS c').single()['c']
                counts[label] = c
        return counts

    def close(self) -> None:
        self.driver.close()
```

---

## 1.9 — `pipeline/load_ontology.py`

Run this **once** after all JSON files are complete to seed Neo4j:

```python
# pipeline/load_ontology.py
"""
Run once to seed Neo4j with the complete ontology.
Usage: python pipeline/load_ontology.py
"""
from storage.neo4j_client import Neo4jClient


def main() -> None:
    db = Neo4jClient()
    print('Connection:', db.verify_connection())

    print('\nCreating constraints...')
    db.create_constraints()

    steps = [
        ('Planets',     lambda: db.load_planets('normaliser/ontology/planets.json')),
        ('Signs',       lambda: db.load_signs('normaliser/ontology/signs.json')),
        ('Houses',      lambda: db.load_houses('normaliser/ontology/houses.json')),
        ('Nakshatras',  lambda: db.load_nakshatras('normaliser/ontology/nakshatras.json')),
    ]
    for label, fn in steps:
        n = fn()
        print(f'  {label}: {n} loaded')

    print('\nLoading planet relationships...')
    db.load_planet_relationships('normaliser/ontology/planets.json')

    print('\nEntity counts in Neo4j:')
    counts = db.verify_entity_counts()
    expected = {'Planet': 9, 'Sign': 12, 'House': 12, 'Nakshatra': 27}
    all_ok = True
    for entity_type, count in counts.items():
        ok = count == expected.get(entity_type, 1)
        status = '✓' if ok else '✗'
        if not ok:
            all_ok = False
        print(f'  {status} {entity_type}: {count} (expected {expected.get(entity_type, "?")})')

    print('\n✓ Ontology loaded successfully!' if all_ok else '\n✗ Check counts above — something is wrong.')
    db.close()


if __name__ == '__main__':
    main()
```

---

## ✅ Phase 1 Completion Checklist

Do not proceed to Phase 2 until every item is checked.

| # | Check | Command | Expected |
|---|-------|---------|----------|
| 1 | `planets.json` valid — 9 planets | `python -c "import json; d=json.load(open('normaliser/ontology/planets.json')); assert len(d['planets'])==9; print('OK')"` | `OK` |
| 2 | `signs.json` valid — 12 signs | Same pattern, assert 12 | `OK` |
| 3 | `houses.json` valid — 12 houses | Same pattern, assert 12 | `OK` |
| 4 | `nakshatras.json` valid — 27 | Same pattern, assert 27 | `OK` |
| 5 | `yogas.json` valid — 50+ yogas | Same pattern, assert >= 50 | `OK` |
| 6 | All normaliser tests pass | `pytest tests/test_normaliser.py -v` | All PASSED |
| 7 | `normalise('gibberish')` is None | Included in test suite | PASSED |
| 8 | Ontology loaded into Neo4j | `python pipeline/load_ontology.py` | Planet:9, Sign:12, House:12, Nakshatra:27 |
| 9 | Relationships in Neo4j | `MATCH ()-[r:IS_EXALTED_IN]->() RETURN count(r)` in Neo4j Browser | 7+ results |
| 10 | Git commit | `git add . && git commit -m "Phase 1: ontology complete"` | Clean commit |

**When all 10 are green → proceed to Phase 2.**