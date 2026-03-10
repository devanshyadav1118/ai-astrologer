# AI Astrologer — Phase 1–5 Codex Roadmap
**Version: 3.0 | Stack: MacBook Air M2 · Python 3.11 · Gemini Pro · Neo4j Desktop**

---

## HOW TO USE THIS FILE

Place this file at your project root as `AGENTS.md` OR keep it as a reference alongside your existing `AGENTS.md`. Each phase has:
- A clear **goal**
- Exact **folder/file targets**
- **Task list** Codex can execute step by step
- **Verification checks** before moving to the next phase

---

## PROJECT CONTEXT (For Codex)

This is a Vedic astrology knowledge extraction and reasoning engine. 200–300 classical books are processed into a structured knowledge graph (Neo4j), which powers an explainable AI prediction system.

**Core Data Flow:**
```
PDF → Chunker → Gemini Pro API → Structured JSON → Normaliser → Validator → Neo4j Graph
```

**Key Rule:** Every entity name (planet, sign, house) must be normalised to its canonical form (e.g. `Surya` → `SUN`) BEFORE anything touches Neo4j.

**Existing Assets (Do NOT rebuild):**
- Extraction prompt v2.0 (multi-format JSON schema)
- Chunking pipeline (PDF → chunks → Gemini Pro → structured JSON)
- Continuation + stitching logic for large books
- 1–5 books already processed and validated
- 200–300 books downloaded locally in `data/raw/`

---

## PROJECT FOLDER STRUCTURE

```
ai-astrologer/
├── extractor/
│   ├── chunker.py          # PDF → chunks with metadata
│   ├── gemini_client.py    # Gemini API wrapper
│   ├── prompt.py           # Extraction prompt v2.0
│   └── stitcher.py         # Merges chunk outputs into single JSON
├── normaliser/
│   ├── ontology/           # JSON entity definition files
│   │   ├── planets.json
│   │   ├── signs.json
│   │   ├── houses.json
│   │   ├── nakshatras.json
│   │   └── yogas.json
│   ├── normaliser.py       # Surya→SUN, Lagna→HOUSE_1 etc.
│   └── validator.py        # Validates extracted rules against ontology
├── storage/
│   ├── neo4j_client.py     # Knowledge graph operations
│   └── sqlite_client.py    # Chunk index + book metadata
├── pipeline/
│   └── run_book.py         # Single command: book PDF → Neo4j
├── reasoning/              # Built in Phases 5+
├── data/
│   ├── raw/                # Original PDFs — NEVER MODIFY
│   ├── extracted/          # JSON rule files per book
│   └── db/                 # SQLite databases
├── tests/                  # pytest test suite
├── AGENTS.md               # This file (Codex context)
├── .env                    # API keys — never commit
└── requirements.txt
```

---

## CODING STANDARDS (Apply to every file)

- Type hints on all function signatures
- Single responsibility per file — one module does one thing
- All entity names must be canonical before Neo4j storage
- Never modify files in `data/raw/`
- All secrets via `.env` using `python-dotenv`, never hardcoded
- Every new function gets a corresponding test in `tests/`

---

---

# PHASE 0 — Foundation & Infrastructure
**Duration:** Weeks 1–2  
**Goal:** Clean Mac environment. All tools installed, tested, and verified before any data work begins.

## Tasks

### 0.1 — Mac Environment Setup
```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install python@3.11 git

# Create project + virtual environment
mkdir ~/ai-astrologer && cd ~/ai-astrologer
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

### 0.2 — Install All Dependencies
```bash
pip install google-generativeai          # Gemini Pro API
pip install neo4j                         # Neo4j Python driver
pip install chromadb                      # Vector store
pip install pyswisseph                    # Swiss Ephemeris (chart calc)
pip install fastapi uvicorn               # API layer
pip install streamlit                     # UI
pip install pandas sqlite-utils           # Data handling
pip install pytest black ruff jupyter    # Dev tools
pip install python-dotenv
pip freeze > requirements.txt
```

### 0.3 — Neo4j Desktop
- Install Neo4j Desktop from neo4j.com/download (native Mac app, no Docker needed)
- Create a new project + local database named `ai-astrologer`
- Set password, note it for `.env`
- Verify browser loads at `localhost:7474`

### 0.4 — Environment Config Files
**`.env` (never commit)**
```
GEMINI_API_KEY=your_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
```

**`.gitignore`**
```
.env
data/
.venv/
__pycache__/
*.pyc
.DS_Store
```

### 0.5 — Create Folder Structure
```bash
mkdir -p ai-astrologer/{extractor,normaliser/ontology,storage,pipeline,reasoning,data/{raw,extracted,db},tests}
```

### 0.6 — Git Init
```bash
git init
git add .
git commit -m "Phase 0: project scaffold and environment"
```

## ✅ Phase 0 Verification Checklist
| Check | Command | Expected |
|-------|---------|----------|
| Python version | `python --version` | 3.11.x |
| Neo4j running | Open browser | Loads at localhost:7474 |
| Gemini API | Run test script | Returns response |
| .env loads | `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('GEMINI_API_KEY'))"` | Key printed |
| Folder structure | `ls extractor normaliser storage pipeline` | All exist |

---

---

# PHASE 1 — Formal Ontology Design
**Duration:** Weeks 3–4  
**Goal:** Complete controlled vocabulary + synonym map. The DNA of the entire system. Every rule, every graph node, every reasoning step depends on this being correct first.

> ⚠️ Do NOT begin Phase 2 extraction until the normaliser passes ALL tests and all entities are loaded in Neo4j.

## Tasks

### 1.1 — Create `normaliser/ontology/planets.json`

Define all 9 grahas. Each entry must include:

```json
{
  "planets": [
    {
      "canonical_name": "SUN",
      "synonyms": ["Sun", "Surya", "Ravi", "Arka", "Aditya", "Bhanu", "Dinakara", "Bhaskar", "Mitra", "Vivaswat"],
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
      "natural_karakatvam": ["soul", "father", "authority", "vitality"],
      "dasha_years": 6
    }
    // ... MOON, MARS, MERCURY, JUPITER, VENUS, SATURN, RAHU, KETU
  ]
}
```

**All 9 canonical names:** `SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN, RAHU, KETU`

**Full synonym targets:**
| Canonical | All Synonyms to Map |
|-----------|---------------------|
| SUN | Sun, Surya, Ravi, Arka, Aditya, Bhanu, Dinakara, Bhaskar |
| MOON | Moon, Chandra, Soma, Indu, Nisha, Mriganka, Himanshu, Shashi |
| MARS | Mars, Mangala, Kuja, Bhouma, Angaraka, Lohitanga, Ara |
| MERCURY | Mercury, Budha, Saumya, Gna, Kumar |
| JUPITER | Jupiter, Guru, Brihaspati, Jeeva, Devaguru, Angiras, Vachaspati |
| VENUS | Venus, Shukra, Bhrigu, Kavi, Sita, Usanas, Daityaguru |
| SATURN | Saturn, Shani, Sanaischara, Manda, Krura, Asita, Arkaja, Saurya |
| RAHU | Rahu, Sarpa, Dragon's Head, North Node, Tamas, Svarbhanu |
| KETU | Ketu, Dragon's Tail, South Node, Sikhi, Dhvaja, Mokshakaraka |

---

### 1.2 — Create `normaliser/ontology/signs.json`

Define all 12 rashis. Each entry:

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
      "exaltation_degree": 10,
      "debilitation_planet": "SATURN",
      "debilitation_degree": 20,
      "primary_meanings": ["self", "initiative", "courage", "beginnings"]
    }
    // ... TAURUS through PISCES
  ]
}
```

**All 12 canonical names:** `ARIES, TAURUS, GEMINI, CANCER, LEO, VIRGO, LIBRA, SCORPIO, SAGITTARIUS, CAPRICORN, AQUARIUS, PISCES`

---

### 1.3 — Create `normaliser/ontology/houses.json`

Define all 12 bhavas. Each entry:

```json
{
  "houses": [
    {
      "canonical_name": "HOUSE_1",
      "number": 1,
      "synonyms": ["1st house", "First house", "Lagna", "Ascendant", "Tanu Bhava", "Udaya Lagna"],
      "house_type": "kendra",
      "secondary_types": ["trikona"],
      "natural_karaka": "SUN",
      "primary_meanings": ["self", "personality", "appearance", "health", "vitality"],
      "secondary_meanings": ["fame", "head", "early childhood"]
    }
    // ... HOUSE_2 through HOUSE_12
  ]
}
```

**House type reference:**
| Houses | Type |
|--------|------|
| 1, 4, 7, 10 | kendra |
| 1, 5, 9 | trikona |
| 6, 8, 12 | trik (dusthana) |
| 3, 6, 10, 11 | upachaya |
| 2, 7 | maraka |

**Key synonyms to include:**
- HOUSE_1: Lagna, Ascendant, Tanu Bhava, Udaya Lagna
- HOUSE_7: Kalatra Bhava, Jaya Bhava, Jamitra
- HOUSE_10: Karma Bhava, Rajya Bhava

---

### 1.4 — Create `normaliser/ontology/nakshatras.json`

Define all 27 nakshatras. Each entry:

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
      "rashi": "ARIES",
      "degrees": [0, 13.2],
      "padas": [
        {"pada": 1, "navamsa_sign": "ARIES"},
        {"pada": 2, "navamsa_sign": "TAURUS"},
        {"pada": 3, "navamsa_sign": "GEMINI"},
        {"pada": 4, "navamsa_sign": "CANCER"}
      ],
      "primary_qualities": ["speed", "healing", "initiation"]
    }
    // ... all 27
  ]
}
```

---

### 1.5 — Create `normaliser/ontology/yogas.json`

Define 50+ classical yogas with **machine-readable conditions** (not just text descriptions):

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
      "effects": ["wisdom", "fame", "benevolence", "wealth"],
      "classical_sources": ["Brihat Parashara Hora Shastra"],
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
          {"aspect_between": ["trikona_lord", "kendra_lord"]}
        ]
      },
      "effects": ["authority", "fame", "political_success"],
      "confidence": "classical"
    }
    // ... 50+ total
  ]
}
```

---

### 1.6 — Build `normaliser/normaliser.py`

This is the most critical function in the entire project. Every entity name from every book passes through `normalise()` before storage.

```python
# normaliser/normaliser.py
import json
import re
from pathlib import Path

class AstrologyNormaliser:
    """
    Maps any astrological term to its canonical form.
    normalise('Surya') -> 'SUN'
    normalise('Lagna') -> 'HOUSE_1'
    normalise('Guru')  -> 'JUPITER'
    normalise('unknown') -> None  (flagged for review)
    """

    def __init__(self, ontology_dir: str = 'normaliser/ontology'):
        self.ontology_dir = Path(ontology_dir)
        self.synonym_map: dict[str, str] = {}
        self._build_synonym_map()

    def _build_synonym_map(self) -> None:
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
                    self.synonym_map[canonical.lower()] = canonical
                    for synonym in entity.get('synonyms', []):
                        self.synonym_map[synonym.lower()] = canonical

    def normalise(self, term: str) -> str | None:
        if not term:
            return None
        cleaned = term.strip().lower()
        if cleaned in self.synonym_map:
            return self.synonym_map[cleaned]
        # Fuzzy suffix patterns
        patterns = [
            (r'\b(\w+)ine\b', r'\1'),   # saturnine → saturn
            (r'\b(\w+)ian\b', r'\1'),   # jupiterian → jupiter
        ]
        for pattern, replacement in patterns:
            fuzzy = re.sub(pattern, replacement, cleaned)
            if fuzzy in self.synonym_map:
                return self.synonym_map[fuzzy]
        return None  # Unknown — will be flagged for review
```

**Normaliser test suite — `tests/test_normaliser.py`:**

```python
from normaliser.normaliser import AstrologyNormaliser

def test_planet_synonyms():
    n = AstrologyNormaliser()
    assert n.normalise('Surya') == 'SUN'
    assert n.normalise('Ravi') == 'SUN'
    assert n.normalise('Guru') == 'JUPITER'
    assert n.normalise('Brihaspati') == 'JUPITER'
    assert n.normalise('Kuja') == 'MARS'
    assert n.normalise('Bhouma') == 'MARS'
    assert n.normalise('Shani') == 'SATURN'
    assert n.normalise('Chandra') == 'MOON'

def test_house_synonyms():
    n = AstrologyNormaliser()
    assert n.normalise('Lagna') == 'HOUSE_1'
    assert n.normalise('Ascendant') == 'HOUSE_1'
    assert n.normalise('Tanu Bhava') == 'HOUSE_1'

def test_sign_synonyms():
    n = AstrologyNormaliser()
    assert n.normalise('Mesha') == 'ARIES'
    assert n.normalise('Mesh') == 'ARIES'

def test_unknown_returns_none():
    n = AstrologyNormaliser()
    assert n.normalise('gibberish') is None
    assert n.normalise('') is None
```

---

### 1.7 — Build `normaliser/validator.py`

```python
# normaliser/validator.py
import re
from normaliser.normaliser import AstrologyNormaliser

class RuleValidator:
    """Validates extracted rules against the formal ontology."""

    def __init__(self):
        self.normaliser = AstrologyNormaliser()

    def validate_rule(self, rule: dict) -> dict:
        errors = []
        warnings = []
        required = ['rule_id', 'type', 'condition', 'result', 'source_text']
        for field in required:
            if field not in rule or not rule[field]:
                errors.append(f'Missing required field: {field}')

        valid_types = ['prediction', 'description', 'yoga', 'calculation', 'modification']
        if rule.get('type') not in valid_types:
            warnings.append(f'Unknown rule type: {rule.get("type")}')

        condition = rule.get('condition', '')
        entities = self._extract_entities(condition)
        normalised = {}
        for entity in entities:
            canonical = self.normaliser.normalise(entity)
            if canonical is None:
                warnings.append(f'Unknown entity: "{entity}" — needs review')
            else:
                normalised[entity] = canonical

        status = 'invalid' if errors else ('warning' if warnings else 'valid')
        return {**rule, 'normalised_entities': normalised,
                'validation_errors': errors, 'validation_warnings': warnings,
                'validation_status': status}

    def validate_batch(self, rules: list[dict]) -> dict:
        results: dict[str, list] = {'valid': [], 'warning': [], 'invalid': []}
        for rule in rules:
            validated = self.validate_rule(rule)
            results[validated['validation_status']].append(validated)
        total = len(rules)
        return {
            'results': results,
            'summary': {
                'total': total,
                'valid': len(results['valid']),
                'warning': len(results['warning']),
                'invalid': len(results['invalid']),
                'valid_pct': round(len(results['valid']) / total * 100, 1) if total else 0
            }
        }

    def _extract_entities(self, text: str) -> list[str]:
        tokens = re.findall(r'[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*', text)
        return [t.strip() for t in tokens if len(t) > 2]
```

---

### 1.8 — Build `storage/neo4j_client.py` (Base Ontology Loader)

```python
# storage/neo4j_client.py
import json
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

class Neo4jClient:
    def __init__(self):
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
            "CREATE CONSTRAINT sign_name IF NOT EXISTS FOR (s:Sign) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT house_number IF NOT EXISTS FOR (h:House) REQUIRE h.name IS UNIQUE",
            "CREATE CONSTRAINT nakshatra_name IF NOT EXISTS FOR (n:Nakshatra) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT rule_id IF NOT EXISTS FOR (r:Rule) REQUIRE r.rule_id IS UNIQUE",
            "CREATE CONSTRAINT yoga_name IF NOT EXISTS FOR (y:Yoga) REQUIRE y.name IS UNIQUE",
        ]
        with self.driver.session() as session:
            for cypher in constraints:
                session.run(cypher)

    def load_planets(self, filepath: str) -> int:
        with open(filepath) as f:
            data = json.load(f)
        with self.driver.session() as session:
            for planet in data['planets']:
                session.run("""
                    MERGE (p:Planet {name: $name})
                    SET p.nature = $nature,
                        p.element = $element,
                        p.exaltation_sign = $exaltation,
                        p.debilitation_sign = $debilitation,
                        p.dasha_years = $dasha_years,
                        p.synonyms = $synonyms
                """,
                name=planet['canonical_name'],
                nature=planet.get('nature'),
                element=planet.get('element'),
                exaltation=planet.get('exaltation_sign'),
                debilitation=planet.get('debilitation_sign'),
                dasha_years=planet.get('dasha_years'),
                synonyms=planet.get('synonyms', []))
        return len(data['planets'])

    def load_signs(self, filepath: str) -> int:
        with open(filepath) as f:
            data = json.load(f)
        with self.driver.session() as session:
            for sign in data['signs']:
                session.run("""
                    MERGE (s:Sign {name: $name})
                    SET s.number = $number,
                        s.ruler = $ruler,
                        s.element = $element,
                        s.modality = $modality,
                        s.synonyms = $synonyms
                """,
                name=sign['canonical_name'],
                number=sign.get('number'),
                ruler=sign.get('ruler'),
                element=sign.get('element'),
                modality=sign.get('modality'),
                synonyms=sign.get('synonyms', []))
        return len(data['signs'])

    def load_houses(self, filepath: str) -> int:
        with open(filepath) as f:
            data = json.load(f)
        with self.driver.session() as session:
            for house in data['houses']:
                session.run("""
                    MERGE (h:House {name: $name})
                    SET h.number = $number,
                        h.house_type = $house_type,
                        h.natural_karaka = $karaka,
                        h.primary_meanings = $primary,
                        h.synonyms = $synonyms
                """,
                name=house['canonical_name'],
                number=house.get('number'),
                house_type=house.get('house_type'),
                karaka=house.get('natural_karaka'),
                primary=house.get('primary_meanings', []),
                synonyms=house.get('synonyms', []))
        return len(data['houses'])

    def load_nakshatras(self, filepath: str) -> int:
        with open(filepath) as f:
            data = json.load(f)
        with self.driver.session() as session:
            for n in data['nakshatras']:
                session.run("""
                    MERGE (n:Nakshatra {name: $name})
                    SET n.number = $number,
                        n.lord = $lord,
                        n.rashi = $rashi,
                        n.shakti = $shakti,
                        n.synonyms = $synonyms
                """,
                name=n['canonical_name'],
                number=n.get('number'),
                lord=n.get('lord'),
                rashi=n.get('rashi'),
                shakti=n.get('shakti'),
                synonyms=n.get('synonyms', []))
        return len(data['nakshatras'])

    def load_planet_relationships(self, filepath: str) -> None:
        with open(filepath) as f:
            data = json.load(f)
        with self.driver.session() as session:
            for planet in data['planets']:
                pname = planet['canonical_name']
                if planet.get('exaltation_sign'):
                    session.run("""
                        MATCH (p:Planet {name: $planet})
                        MATCH (s:Sign {name: $sign})
                        MERGE (p)-[:IS_EXALTED_IN {degree: $deg}]->(s)
                    """, planet=pname, sign=planet['exaltation_sign'],
                    deg=planet.get('exaltation_degree', 0))

                if planet.get('debilitation_sign'):
                    session.run("""
                        MATCH (p:Planet {name: $planet})
                        MATCH (s:Sign {name: $sign})
                        MERGE (p)-[:IS_DEBILITATED_IN {degree: $deg}]->(s)
                    """, planet=pname, sign=planet['debilitation_sign'],
                    deg=planet.get('debilitation_degree', 0))

                for own_sign in planet.get('own_signs', []):
                    session.run("""
                        MATCH (p:Planet {name: $planet})
                        MATCH (s:Sign {name: $sign})
                        MERGE (p)-[:OWNS]->(s)
                    """, planet=pname, sign=own_sign)

                for friend in planet.get('friends', []):
                    session.run("""
                        MATCH (p1:Planet {name: $p1})
                        MATCH (p2:Planet {name: $p2})
                        MERGE (p1)-[:NATURAL_FRIEND_OF]->(p2)
                    """, p1=pname, p2=friend)

    def verify_entity_counts(self) -> dict:
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

### 1.9 — Build `pipeline/load_ontology.py` (Run Once)

```python
# pipeline/load_ontology.py
"""Run once after all ontology JSON files are complete to seed Neo4j."""
from storage.neo4j_client import Neo4jClient

def main():
    db = Neo4jClient()
    print('Connection:', db.verify_connection())

    print('Creating constraints...')
    db.create_constraints()

    print('Loading planets...')
    n = db.load_planets('normaliser/ontology/planets.json')
    print(f'  → {n} planets loaded')

    print('Loading signs...')
    n = db.load_signs('normaliser/ontology/signs.json')
    print(f'  → {n} signs loaded')

    print('Loading houses...')
    n = db.load_houses('normaliser/ontology/houses.json')
    print(f'  → {n} houses loaded')

    print('Loading nakshatras...')
    n = db.load_nakshatras('normaliser/ontology/nakshatras.json')
    print(f'  → {n} nakshatras loaded')

    print('Loading planet relationships...')
    db.load_planet_relationships('normaliser/ontology/planets.json')

    print('\nEntity counts:')
    counts = db.verify_entity_counts()
    for entity_type, count in counts.items():
        status = '✓' if count > 0 else '✗'
        print(f'  {status} {entity_type}: {count}')

    # Expected: Planet: 9, Sign: 12, House: 12, Nakshatra: 27
    db.close()

if __name__ == '__main__':
    main()
```

## ✅ Phase 1 Verification Checklist
| Check | Verification |
|-------|-------------|
| `planets.json` — 9 planets | `python -c "import json; d=json.load(open('normaliser/ontology/planets.json')); assert len(d['planets'])==9"` |
| `signs.json` — 12 signs | Same pattern, assert 12 |
| `houses.json` — 12 houses | Same pattern, assert 12 |
| `nakshatras.json` — 27 | Same pattern, assert 27 |
| `yogas.json` — 50+ yogas | Same pattern, assert >= 50 |
| Normaliser tests pass | `pytest tests/test_normaliser.py -v` — all pass |
| Entities in Neo4j | `python pipeline/load_ontology.py` → Planet:9, Sign:12, House:12, Nakshatra:27 |
| Unknown term returns None | `normalise('gibberish') == None` |

---

---

# PHASE 2+3 — Extraction Pipeline (Combined)
**Duration:** Weeks 5–16  
**Goal:** All 200–300 books → normalised JSON rules → Neo4j. These phases are merged because the existing chunker+Gemini+stitcher pipeline already handles both. The work here is: clean reorganisation, add normalisation, and process all books.

## What Changes vs Existing Pipeline
| Current | New (Clean Architecture) |
|---------|--------------------------|
| Random scripts in files | 4 clean modules, single responsibility each |
| Entity names raw (Surya, Ravi) | All normalised to canonical (SUN) before storage |
| Output: flat stitched JSON | Flat JSON + loaded into Neo4j + indexed in SQLite |
| No confidence tracking | Same rule from 2+ books → confidence increases |
| No unknown entity flagging | Entities not in ontology auto-flagged for review |
| Manual per-book runs | `pipeline/run_book.py` handles single command per book |

## Tasks

### 2.1 — Clean Up `extractor/chunker.py`

Reorganise existing chunking logic into this interface:

```python
# extractor/chunker.py
from pathlib import Path
import json

def chunk_pdf(pdf_path: str, output_dir: str, chunk_size_tokens: int = 500) -> list[dict]:
    """
    Split a PDF into ~500-token chunks with metadata.
    Returns list of chunk dicts.
    Each chunk: {chunk_id, book_id, chapter, page_range, text, token_count}
    """
    # Move your existing chunking logic here
    # Ensure each chunk carries: book_id, chapter, page_range, priority_tier
    pass
```

### 2.2 — Clean Up `extractor/gemini_client.py`

```python
# extractor/gemini_client.py
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

class GeminiClient:
    def __init__(self, model: str = 'gemini-pro'):
        self.model = genai.GenerativeModel(model)

    def extract_from_chunk(self, chunk_text: str, prompt: str) -> dict:
        """Send a chunk through extraction prompt. Returns parsed JSON."""
        full_prompt = f"{prompt}\n\n---\nTEXT:\n{chunk_text}"
        response = self.model.generate_content(full_prompt)
        # Parse JSON from response — handle ```json fences
        raw = response.text.strip()
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        import json
        return json.loads(raw.strip())
```

### 2.3 — Clean Up `extractor/prompt.py`

Move your existing v2.0 extraction prompt here as a constant:

```python
# extractor/prompt.py

EXTRACTION_PROMPT_V2 = """
[Your existing v2.0 prompt goes here — unchanged]

Return ONLY valid JSON. No preamble. No markdown fences. No explanation.
Schema formats A through H as defined.
"""
```

### 2.4 — Clean Up `extractor/stitcher.py`

```python
# extractor/stitcher.py
import json
from pathlib import Path

def stitch_chunks(chunk_outputs: list[dict], output_path: str) -> dict:
    """
    Merge all chunk extraction outputs into one unified JSON file per book.
    Deduplicate rules. Preserve all source references.
    """
    stitched = {'rules': [], 'yogas': [], 'descriptions': [], 'calculations': []}
    for chunk_output in chunk_outputs:
        for category in stitched:
            stitched[category].extend(chunk_output.get(category, []))
    with open(output_path, 'w') as f:
        json.dump(stitched, f, indent=2)
    return stitched
```

### 2.5 — Build `storage/sqlite_client.py`

```python
# storage/sqlite_client.py
import sqlite3
from pathlib import Path
import json

class SQLiteClient:
    def __init__(self, db_path: str = 'data/db/index.sqlite'):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS books (
                book_id TEXT PRIMARY KEY,
                title TEXT,
                author TEXT,
                tradition TEXT,
                language TEXT,
                priority_tier INTEGER,
                total_chunks INTEGER,
                processed_chunks INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending'
            );
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                book_id TEXT,
                chapter TEXT,
                page_range TEXT,
                token_count INTEGER,
                ocr_confidence REAL,
                processing_status TEXT DEFAULT 'pending',
                extraction_status TEXT DEFAULT 'pending',
                unknown_entities TEXT,
                FOREIGN KEY (book_id) REFERENCES books(book_id)
            );
        """)
        self.conn.commit()

    def register_book(self, book_meta: dict) -> None:
        self.conn.execute("""
            INSERT OR REPLACE INTO books
            (book_id, title, author, tradition, language, priority_tier, total_chunks)
            VALUES (:book_id, :title, :author, :tradition, :language, :priority_tier, :total_chunks)
        """, book_meta)
        self.conn.commit()

    def update_chunk_status(self, chunk_id: str, status: str,
                             unknown_entities: list | None = None) -> None:
        self.conn.execute("""
            UPDATE chunks SET extraction_status = ?, unknown_entities = ?
            WHERE chunk_id = ?
        """, (status, json.dumps(unknown_entities or []), chunk_id))
        self.conn.commit()
```

### 2.6 — Build `storage/neo4j_client.py` — Rule Ingestion (Add to existing)

Add these methods to your existing `Neo4jClient` class:

```python
def ingest_rule(self, rule: dict) -> None:
    """Store a single validated rule as a Neo4j node linked to its entities."""
    with self.driver.session() as session:
        session.run("""
            MERGE (r:Rule {rule_id: $rule_id})
            SET r.type = $type,
                r.condition = $condition,
                r.result = $result,
                r.source_text = $source_text,
                r.book_id = $book_id,
                r.confidence = $confidence
        """,
        rule_id=rule['rule_id'],
        type=rule['type'],
        condition=rule['condition'],
        result=rule['result'],
        source_text=rule.get('source_text', ''),
        book_id=rule.get('book_id', ''),
        confidence=rule.get('confidence', 'low'))

        # Link rule to normalised entity nodes
        for original, canonical in rule.get('normalised_entities', {}).items():
            label = self._get_label_for_canonical(canonical)
            if label:
                session.run(f"""
                    MATCH (r:Rule {{rule_id: $rule_id}})
                    MATCH (e:{label} {{name: $canonical}})
                    MERGE (r)-[:INVOLVES]->(e)
                """, rule_id=rule['rule_id'], canonical=canonical)

def _get_label_for_canonical(self, canonical: str) -> str | None:
    if canonical in ['SUN','MOON','MARS','MERCURY','JUPITER','VENUS','SATURN','RAHU','KETU']:
        return 'Planet'
    if canonical in ['ARIES','TAURUS','GEMINI','CANCER','LEO','VIRGO',
                     'LIBRA','SCORPIO','SAGITTARIUS','CAPRICORN','AQUARIUS','PISCES']:
        return 'Sign'
    if canonical.startswith('HOUSE_'):
        return 'House'
    return None

def update_rule_confidence(self, rule_id: str, new_confidence: str) -> None:
    """Upgrade confidence when same rule found in multiple books."""
    with self.driver.session() as session:
        session.run("""
            MATCH (r:Rule {rule_id: $rule_id})
            SET r.confidence = $confidence
        """, rule_id=rule_id, confidence=new_confidence)
```

### 2.7 — Build `pipeline/run_book.py`

The single command that processes one book end to end:

```python
# pipeline/run_book.py
"""
Usage: python pipeline/run_book.py --pdf data/raw/saravali.pdf --book-id saravali --tier 1
"""
import argparse
from extractor.chunker import chunk_pdf
from extractor.gemini_client import GeminiClient
from extractor.prompt import EXTRACTION_PROMPT_V2
from extractor.stitcher import stitch_chunks
from normaliser.normaliser import AstrologyNormaliser
from normaliser.validator import RuleValidator
from storage.neo4j_client import Neo4jClient
from storage.sqlite_client import SQLiteClient
import json
from pathlib import Path

def run_book(pdf_path: str, book_id: str, tier: int) -> None:
    print(f'\n=== Processing: {book_id} ===')

    # Init clients
    gemini = GeminiClient()
    normaliser = AstrologyNormaliser()
    validator = RuleValidator()
    neo4j = Neo4jClient()
    sqlite = SQLiteClient()

    # Step 1: Chunk
    print('Chunking...')
    chunks = chunk_pdf(pdf_path, f'data/extracted/{book_id}')
    print(f'  → {len(chunks)} chunks')

    # Step 2: Extract
    print('Extracting...')
    chunk_outputs = []
    for i, chunk in enumerate(chunks):
        print(f'  chunk {i+1}/{len(chunks)}', end='\r')
        try:
            output = gemini.extract_from_chunk(chunk['text'], EXTRACTION_PROMPT_V2)
            chunk_outputs.append(output)
        except Exception as e:
            print(f'  ✗ chunk {i+1} failed: {e}')

    # Step 3: Stitch
    print('\nStitching...')
    stitched_path = f'data/extracted/{book_id}/stitched.json'
    stitched = stitch_chunks(chunk_outputs, stitched_path)
    print(f'  → {len(stitched.get("rules", []))} rules extracted')

    # Step 4: Normalise + Validate + Store
    print('Normalising and storing...')
    all_rules = stitched.get('rules', []) + stitched.get('yogas', [])
    valid_count = 0
    flagged_count = 0

    for rule in all_rules:
        validated = validator.validate_rule(rule)
        if validated['validation_status'] == 'invalid':
            flagged_count += 1
            continue
        neo4j.ingest_rule(validated)
        valid_count += 1

    print(f'  → Stored: {valid_count} | Flagged: {flagged_count}')
    print(f'=== {book_id} complete ===\n')
    neo4j.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', required=True)
    parser.add_argument('--book-id', required=True)
    parser.add_argument('--tier', type=int, default=2)
    args = parser.parse_args()
    run_book(args.pdf, args.book_id, args.tier)
```

### 2.8 — Processing Priority Order

Process in this exact order to build confidence scores correctly:

| Tier | Books | Reason |
|------|-------|--------|
| **Tier 1** | Saravali, Brihat Jataka, Phala Deepika, Brihat Parashara Hora Shastra | Foundational — most rules cited across all other books |
| **Tier 2** | Major Nadi Granthas, Jataka Parijata, Sarvartha Chintamani | High rule density |
| **Tier 3** | Commentaries, regional texts, personal notes | Supplementary |

### 2.9 — Cross-Book Confidence Scoring

When a rule from Book A is found again in Book B, upgrade its confidence:

| Books containing rule | Confidence Level |
|----------------------|-----------------|
| 1 book | `low` |
| 2 books | `medium` |
| 3+ books | `high` |
| 5+ books | `very_high` |

Add a deduplication pass after each batch of books is loaded. Match rules by condition similarity and update confidence accordingly.

## ✅ Phase 2+3 Verification Checklist
| Check | Verification |
|-------|-------------|
| `run_book.py` processes Tier 1 book | `python pipeline/run_book.py --pdf data/raw/saravali.pdf --book-id saravali --tier 1` completes |
| Rules in Neo4j after first book | `MATCH (r:Rule) RETURN count(r)` → > 0 |
| Unknown entities flagged | Check logs for flagged terms |
| SQLite chunk index populated | `sqlite3 data/db/index.sqlite "SELECT count(*) FROM chunks"` → > 0 |
| All Tier 1 books processed | 4 books complete, Neo4j rule count grows |
| 50,000+ rules target | After all books: `MATCH (r:Rule) RETURN count(r)` → 50,000+ |
| Confidence scores present | `MATCH (r:Rule) WHERE r.confidence='high' RETURN count(r)` → > 0 |

---

---

# PHASE 4 — Knowledge Graph & Chart Ingestion
**Duration:** Weeks 17–20  
**Goal:** Swiss Ephemeris chart calculation engine + chart-specific Neo4j subgraph for any birth data.

## Tasks

### 4.1 — Chart Calculation Engine `reasoning/chart_calculator.py`

```python
# reasoning/chart_calculator.py
import swisseph as swe
from datetime import datetime
from dataclasses import dataclass

@dataclass
class ChartData:
    birth_dt: datetime
    latitude: float
    longitude: float
    planet_positions: dict    # {planet_name: {sign, degree, house, nakshatra, retrograde}}
    house_cusps: list         # 12 house cusp degrees
    house_lords: dict         # {house_number: planet_name}
    dignities: dict           # {planet_name: dignity_type}
    aspects: list             # [{aspecting, aspected, type, strength}]

class ChartCalculator:
    PLANET_IDS = {
        'SUN': swe.SUN, 'MOON': swe.MOON, 'MARS': swe.MARS,
        'MERCURY': swe.MERCURY, 'JUPITER': swe.JUPITER,
        'VENUS': swe.VENUS, 'SATURN': swe.SATURN,
        'RAHU': swe.MEAN_NODE, 'KETU': swe.MEAN_NODE  # Ketu = Rahu + 180
    }

    def calculate(self, birth_dt: datetime, lat: float, lon: float) -> ChartData:
        """Full chart calculation for any birth date/time/place."""
        jd = swe.julday(birth_dt.year, birth_dt.month, birth_dt.day,
                        birth_dt.hour + birth_dt.minute / 60.0)

        # Calculate planet positions
        planet_positions = {}
        for planet_name, planet_id in self.PLANET_IDS.items():
            pos, _ = swe.calc_ut(jd, planet_id)
            degree = pos[0]
            if planet_name == 'KETU':
                degree = (degree + 180) % 360
            sign_num = int(degree / 30)
            sign_degree = degree % 30
            retrograde = pos[3] < 0
            planet_positions[planet_name] = {
                'degree': degree,
                'sign_number': sign_num,
                'sign_degree': sign_degree,
                'retrograde': retrograde
            }

        # Whole Sign houses (standard for Jyotish)
        house_cusps, ascmc = swe.houses(jd, lat, lon, b'W')
        asc_sign = int(ascmc[0] / 30)  # Ascendant sign number
        house_lords = self._compute_house_lords(asc_sign)

        return ChartData(
            birth_dt=birth_dt,
            latitude=lat,
            longitude=lon,
            planet_positions=planet_positions,
            house_cusps=list(house_cusps),
            house_lords=house_lords,
            dignities=self._compute_dignities(planet_positions),
            aspects=self._compute_aspects(planet_positions, asc_sign)
        )

    def _compute_house_lords(self, asc_sign: int) -> dict:
        """Whole Sign: house N is ruled by the lord of the sign in that house."""
        SIGN_LORDS = {
            0: 'MARS', 1: 'VENUS', 2: 'MERCURY', 3: 'MOON',
            4: 'SUN', 5: 'MERCURY', 6: 'VENUS', 7: 'MARS',
            8: 'JUPITER', 9: 'SATURN', 10: 'SATURN', 11: 'JUPITER'
        }
        lords = {}
        for house_num in range(1, 13):
            sign_in_house = (asc_sign + house_num - 1) % 12
            lords[house_num] = SIGN_LORDS[sign_in_house]
        return lords

    def _compute_dignities(self, positions: dict) -> dict:
        EXALTATION = {'SUN': 0, 'MOON': 1, 'MARS': 9, 'MERCURY': 5,
                      'JUPITER': 3, 'VENUS': 11, 'SATURN': 6}
        DEBILITATION = {'SUN': 6, 'MOON': 7, 'MARS': 3, 'MERCURY': 11,
                        'JUPITER': 9, 'VENUS': 5, 'SATURN': 0}
        OWN_SIGNS = {
            'SUN': [4], 'MOON': [3], 'MARS': [0, 7], 'MERCURY': [2, 5],
            'JUPITER': [8, 11], 'VENUS': [1, 6], 'SATURN': [9, 10]
        }
        dignities = {}
        for planet, data in positions.items():
            sign = data['sign_number']
            if planet in EXALTATION and EXALTATION[planet] == sign:
                dignities[planet] = 'exalted'
            elif planet in DEBILITATION and DEBILITATION[planet] == sign:
                dignities[planet] = 'debilitated'
            elif planet in OWN_SIGNS and sign in OWN_SIGNS[planet]:
                dignities[planet] = 'own_sign'
            else:
                dignities[planet] = 'neutral'
        return dignities

    def _compute_aspects(self, positions: dict, asc_sign: int) -> list:
        """Jyotish sign-based aspects including special aspects."""
        SPECIAL_ASPECTS = {
            'MARS': [3, 6, 7],    # 4th, 7th, 8th from Mars
            'JUPITER': [4, 6, 8], # 5th, 7th, 9th from Jupiter
            'SATURN': [2, 6, 9],  # 3rd, 7th, 10th from Saturn
        }
        aspects = []
        for planet, data in positions.items():
            planet_sign = data['sign_number']
            # All planets aspect 7th sign
            aspect_signs = [(planet_sign + 6) % 12]
            # Special aspects
            if planet in SPECIAL_ASPECTS:
                for offset in SPECIAL_ASPECTS[planet]:
                    aspect_signs.append((planet_sign + offset) % 12)

            for aspected_planet, aspected_data in positions.items():
                if aspected_planet == planet:
                    continue
                if aspected_data['sign_number'] in aspect_signs:
                    aspects.append({
                        'aspecting': planet,
                        'aspected': aspected_planet,
                        'type': 'full'
                    })
        return aspects
```

### 4.2 — Chart Graph Builder `storage/neo4j_client.py` (Add chart methods)

```python
# Add to Neo4jClient class

def create_chart_subgraph(self, chart_id: str, chart_data: 'ChartData') -> None:
    """Creates a chart-specific subgraph in Neo4j for reasoning."""
    with self.driver.session() as session:
        # Create Chart node
        session.run("""
            MERGE (c:Chart {chart_id: $chart_id})
            SET c.birth_dt = $birth_dt,
                c.latitude = $lat,
                c.longitude = $lon
        """, chart_id=chart_id,
        birth_dt=str(chart_data.birth_dt),
        lat=chart_data.latitude,
        lon=chart_data.longitude)

        # Planet placements
        for planet_name, data in chart_data.planet_positions.items():
            house_num = self._degree_to_house(data['sign_number'],
                                               chart_data.house_cusps)
            session.run("""
                MATCH (c:Chart {chart_id: $chart_id})
                MATCH (p:Planet {name: $planet})
                MATCH (s:Sign {name: $sign})
                MATCH (h:House {name: $house})
                MERGE (cp:ChartPlanet {
                    chart_id: $chart_id, planet: $planet
                })
                SET cp.degree = $degree,
                    cp.retrograde = $retrograde,
                    cp.dignity = $dignity
                MERGE (c)-[:HAS_PLANET]->(cp)
                MERGE (cp)-[:IN_SIGN]->(s)
                MERGE (cp)-[:IN_HOUSE]->(h)
            """,
            chart_id=chart_id, planet=planet_name,
            sign=self._sign_number_to_name(data['sign_number']),
            house=f'HOUSE_{house_num}',
            degree=data['sign_degree'],
            retrograde=data['retrograde'],
            dignity=chart_data.dignities.get(planet_name, 'neutral'))

        # Aspect relationships
        for aspect in chart_data.aspects:
            session.run("""
                MATCH (cp1:ChartPlanet {chart_id: $chart_id, planet: $p1})
                MATCH (cp2:ChartPlanet {chart_id: $chart_id, planet: $p2})
                MERGE (cp1)-[:ASPECTS {type: $type}]->(cp2)
            """, chart_id=chart_id,
            p1=aspect['aspecting'], p2=aspect['aspected'],
            type=aspect['type'])

def _sign_number_to_name(self, sign_num: int) -> str:
    SIGNS = ['ARIES','TAURUS','GEMINI','CANCER','LEO','VIRGO',
             'LIBRA','SCORPIO','SAGITTARIUS','CAPRICORN','AQUARIUS','PISCES']
    return SIGNS[sign_num % 12]

def _degree_to_house(self, sign_number: int, house_cusps: list) -> int:
    # Whole sign: house number = sign offset from ascendant + 1
    asc_sign = int(house_cusps[0] / 30)
    return ((sign_number - asc_sign) % 12) + 1
```

### 4.3 — Test Chart Calculator `tests/test_chart_calculator.py`

```python
from reasoning.chart_calculator import ChartCalculator
from datetime import datetime

def test_chart_calculation_returns_9_planets():
    calc = ChartCalculator()
    dt = datetime(1990, 1, 15, 10, 30)
    chart = calc.calculate(dt, lat=28.6, lon=77.2)  # Delhi
    assert len(chart.planet_positions) == 9

def test_house_lords_returns_12_entries():
    calc = ChartCalculator()
    dt = datetime(1990, 1, 15, 10, 30)
    chart = calc.calculate(dt, lat=28.6, lon=77.2)
    assert len(chart.house_lords) == 12

def test_dignities_present_for_all_planets():
    calc = ChartCalculator()
    dt = datetime(1990, 1, 15, 10, 30)
    chart = calc.calculate(dt, lat=28.6, lon=77.2)
    for planet in ['SUN','MOON','MARS','MERCURY','JUPITER','VENUS','SATURN']:
        assert planet in chart.dignities
```

## ✅ Phase 4 Verification Checklist
| Check | Verification |
|-------|-------------|
| Chart calculator returns 9 planets | `pytest tests/test_chart_calculator.py` passes |
| Chart subgraph created in Neo4j | Run with test birth data → `MATCH (cp:ChartPlanet) RETURN count(cp)` → 9 |
| House lords computed | `chart.house_lords` has 12 entries |
| Aspects calculated | `chart.aspects` is non-empty |
| Dignities assigned | All planets have a dignity value |

---

---

# PHASE 5 — Core Logic Flow Engine
**Duration:** Weeks 21–24  
**Goal:** Graph traversal reasoning. Not rule lookup — logical propagation through causal chains. This is what makes the system reason like a Jyotishi instead of matching pre-written rules.

## Core Insight

> Mars in 5th aspected by Mercury — no such rule exists in any book.  
> Mars (action, courage) + 5th house (intelligence, creativity) + Mercury aspect (intellect, analysis) = **strategic intelligence**.  
> Pure logic propagation. No book needed.

## Tasks

### 5.1 — Build `reasoning/logic_engine.py`

```python
# reasoning/logic_engine.py
from storage.neo4j_client import Neo4jClient
from normaliser.ontology import HOUSE_MEANINGS, PLANET_NATURES  # define these constants

class LogicEngine:
    """
    Core reasoning engine. Traverses the Neo4j chart subgraph
    to produce a structured fact set for any house or theme.
    """

    def __init__(self, chart_id: str):
        self.chart_id = chart_id
        self.db = Neo4jClient()

    # ── Core Traversal Functions ────────────────────────────────

    def get_house_lord(self, house_number: int) -> str:
        """Returns the ruling planet of a given house for this chart."""
        with self.db.driver.session() as session:
            result = session.run("""
                MATCH (c:Chart {chart_id: $chart_id})-[:HAS_PLANET]->(cp:ChartPlanet)
                      -[:IN_HOUSE]->(h:House {name: $house})
                MATCH (cp)-[:IN_SIGN]->(s:Sign)
                MATCH (p:Planet)-[:OWNS]->(s)
                RETURN p.name AS lord
            """, chart_id=self.chart_id, house=f'HOUSE_{house_number}')
            row = result.single()
            return row['lord'] if row else None

    def get_planet_house(self, planet_name: str) -> int | None:
        """Returns which house a planet occupies in this chart."""
        with self.db.driver.session() as session:
            result = session.run("""
                MATCH (c:Chart {chart_id: $chart_id})-[:HAS_PLANET]->
                      (cp:ChartPlanet {planet: $planet})-[:IN_HOUSE]->(h:House)
                RETURN h.number AS house_num
            """, chart_id=self.chart_id, planet=planet_name)
            row = result.single()
            return row['house_num'] if row else None

    def get_aspects_to_planet(self, planet_name: str) -> list[dict]:
        """Returns all planets aspecting the given planet."""
        with self.db.driver.session() as session:
            result = session.run("""
                MATCH (c:Chart {chart_id: $chart_id})-[:HAS_PLANET]->
                      (cp_src:ChartPlanet)-[:ASPECTS]->
                      (cp_tgt:ChartPlanet {planet: $planet})
                RETURN cp_src.planet AS aspecting_planet
            """, chart_id=self.chart_id, planet=planet_name)
            return [{'aspecting': row['aspecting_planet']} for row in result]

    def get_conjunctions(self, planet_name: str) -> list[str]:
        """Returns planets co-located in the same house as the given planet."""
        with self.db.driver.session() as session:
            result = session.run("""
                MATCH (c:Chart {chart_id: $chart_id})-[:HAS_PLANET]->
                      (cp1:ChartPlanet {planet: $planet})-[:IN_HOUSE]->(h:House)
                MATCH (c)-[:HAS_PLANET]->(cp2:ChartPlanet)-[:IN_HOUSE]->(h)
                WHERE cp2.planet <> $planet
                RETURN cp2.planet AS conjunct
            """, chart_id=self.chart_id, planet=planet_name)
            return [row['conjunct'] for row in result]

    def get_planet_dignity(self, planet_name: str) -> str:
        """Returns the dignity of a planet in this chart."""
        with self.db.driver.session() as session:
            result = session.run("""
                MATCH (c:Chart {chart_id: $chart_id})-[:HAS_PLANET]->
                      (cp:ChartPlanet {planet: $planet})
                RETURN cp.dignity AS dignity
            """, chart_id=self.chart_id, planet=planet_name)
            row = result.single()
            return row['dignity'] if row else 'neutral'

    # ── Main Traversal Chain ────────────────────────────────────

    def interpret_house(self, house_number: int) -> dict:
        """
        Full 7-step traversal for a house. Returns structured fact set.

        Step 1: House primary meanings
        Step 2: Find house lord
        Step 3: Lord's placement (which house does the lord sit in?)
        Step 4: Lord's inherent nature
        Step 5: Aspects on the lord
        Step 6: Lord's dignity
        Step 7: Conjunctions with lord
        """
        facts = {
            'house': house_number,
            'steps': [],
            'synthesis': ''
        }

        # Step 1: House meaning
        house_meanings = self._get_house_meanings(house_number)
        facts['steps'].append({
            'step': 1,
            'label': 'House Meaning',
            'content': f'HOUSE_{house_number} primary themes: {", ".join(house_meanings)}'
        })

        # Step 2: Find lord
        lord = self.get_house_lord(house_number)
        if not lord:
            facts['synthesis'] = 'Could not determine house lord.'
            return facts
        facts['steps'].append({
            'step': 2,
            'label': 'House Lord',
            'content': f'{lord} rules HOUSE_{house_number}'
        })

        # Step 3: Lord's placement
        lord_house = self.get_planet_house(lord)
        if lord_house:
            lord_house_meanings = self._get_house_meanings(lord_house)
            facts['steps'].append({
                'step': 3,
                'label': "Lord's Placement",
                'content': f'{lord} is placed in HOUSE_{lord_house} ({", ".join(lord_house_meanings)})'
            })

        # Step 4: Lord's nature
        lord_nature = self._get_planet_nature(lord)
        facts['steps'].append({
            'step': 4,
            'label': "Lord's Nature",
            'content': f'{lord} nature: {lord_nature}'
        })

        # Step 5: Aspects on lord
        aspects = self.get_aspects_to_planet(lord)
        if aspects:
            aspecting = [a['aspecting_planet'] for a in aspects]
            facts['steps'].append({
                'step': 5,
                'label': 'Aspects on Lord',
                'content': f'{lord} is aspected by: {", ".join(aspecting)}'
            })

        # Step 6: Dignity
        dignity = self.get_planet_dignity(lord)
        facts['steps'].append({
            'step': 6,
            'label': 'Dignity',
            'content': f'{lord} dignity: {dignity}'
        })

        # Step 7: Conjunctions
        conjuncts = self.get_conjunctions(lord)
        if conjuncts:
            facts['steps'].append({
                'step': 7,
                'label': 'Conjunctions',
                'content': f'{lord} conjoins: {", ".join(conjuncts)}'
            })

        # Build synthesis string from all steps
        facts['synthesis'] = self._synthesise_facts(facts['steps'])
        return facts

    def interpret_all_houses(self) -> list[dict]:
        """Run interpret_house for all 12 houses."""
        return [self.interpret_house(i) for i in range(1, 13)]

    # ── Knowledge Graph Rule Lookup ─────────────────────────────

    def get_matching_rules(self, planet: str, house: int) -> list[dict]:
        """Fetch classical rules from Neo4j that match a planet+house combination."""
        with self.db.driver.session() as session:
            result = session.run("""
                MATCH (r:Rule)-[:INVOLVES]->(p:Planet {name: $planet})
                MATCH (r)-[:INVOLVES]->(h:House {name: $house})
                RETURN r.rule_id, r.condition, r.result, r.source_text,
                       r.confidence, r.book_id
                ORDER BY r.confidence DESC
                LIMIT 10
            """, planet=planet, house=f'HOUSE_{house}')
            return [dict(row) for row in result]

    # ── Internal Helpers ────────────────────────────────────────

    def _get_house_meanings(self, house_number: int) -> list[str]:
        HOUSE_MEANINGS = {
            1: ['self', 'personality', 'appearance', 'health'],
            2: ['wealth', 'speech', 'family', 'food'],
            3: ['siblings', 'communication', 'courage', 'skills'],
            4: ['mother', 'home', 'happiness', 'education'],
            5: ['children', 'intellect', 'creativity', 'past merit'],
            6: ['enemies', 'disease', 'debt', 'service'],
            7: ['marriage', 'partnerships', 'business', 'trade'],
            8: ['longevity', 'transformation', 'research', 'occult'],
            9: ['fortune', 'guru', 'dharma', 'father', 'higher learning'],
            10: ['career', 'status', 'authority', 'public image'],
            11: ['gains', 'income', 'networks', 'elder siblings'],
            12: ['loss', 'liberation', 'foreign', 'spiritual practices']
        }
        return HOUSE_MEANINGS.get(house_number, [])

    def _get_planet_nature(self, planet_name: str) -> str:
        NATURES = {
            'SUN': 'soul, authority, vitality, father — natural malefic',
            'MOON': 'mind, emotions, mother, nurturing — natural benefic',
            'MARS': 'action, courage, energy, conflict — natural malefic',
            'MERCURY': 'intellect, communication, analysis, adaptability — neutral',
            'JUPITER': 'wisdom, expansion, grace, teaching — natural benefic',
            'VENUS': 'beauty, pleasure, relationships, art — natural benefic',
            'SATURN': 'discipline, structure, delay, persistence — natural malefic',
            'RAHU': 'ambition, obsession, foreign, material desire — shadow planet',
            'KETU': 'detachment, spirituality, past life, liberation — shadow planet'
        }
        return NATURES.get(planet_name, 'unknown')

    def _synthesise_facts(self, steps: list[dict]) -> str:
        """Combine traversal steps into a readable synthesis string."""
        parts = [s['content'] for s in steps]
        return ' | '.join(parts)
```

### 5.2 — Build Reasoning Tree Output `reasoning/reasoning_tree.py`

```python
# reasoning/reasoning_tree.py
from reasoning.logic_engine import LogicEngine

def generate_reasoning_tree(chart_id: str, house_number: int) -> str:
    """
    Generates a human-readable reasoning tree for a house interpretation.
    Format matches the example in the masterplan.
    """
    engine = LogicEngine(chart_id)
    facts = engine.interpret_house(house_number)

    lines = [
        f"HOUSE {house_number} INTERPRETATION",
        "─" * 60
    ]
    for step in facts['steps']:
        lines.append(f"Step {step['step']} → {step['content']}")

    lines.append("─" * 60)
    lines.append(f"SYNTHESIS: {facts['synthesis']}")

    # Fetch matching classical rules
    lord_step = next((s for s in facts['steps'] if s['label'] == 'House Lord'), None)
    if lord_step:
        lord = lord_step['content'].split(' ')[0]
        rules = engine.get_matching_rules(lord, house_number)
        if rules:
            lines.append("\nClassical rules matched:")
            for rule in rules[:3]:
                lines.append(f"  • [{rule['book_id']}] {rule['result']}")

    return '\n'.join(lines)
```

### 5.3 — Test Logic Engine `tests/test_logic_engine.py`

```python
from reasoning.logic_engine import LogicEngine

def test_interpret_house_returns_steps():
    engine = LogicEngine(chart_id='test_chart')
    result = engine.interpret_house(10)
    assert 'steps' in result
    assert len(result['steps']) >= 2
    assert 'synthesis' in result

def test_house_meanings_complete():
    engine = LogicEngine(chart_id='test')
    for i in range(1, 13):
        meanings = engine._get_house_meanings(i)
        assert len(meanings) >= 2, f'House {i} has too few meanings'

def test_all_planet_natures_defined():
    engine = LogicEngine(chart_id='test')
    for planet in ['SUN','MOON','MARS','MERCURY','JUPITER','VENUS','SATURN','RAHU','KETU']:
        nature = engine._get_planet_nature(planet)
        assert nature != 'unknown', f'{planet} nature not defined'
```

## ✅ Phase 5 Verification Checklist
| Check | Verification |
|-------|-------------|
| Logic engine unit tests pass | `pytest tests/test_logic_engine.py -v` |
| `interpret_house(10)` returns 7 steps | Manual test with real chart data |
| House meanings for all 12 houses | `_get_house_meanings(i)` returns non-empty list for i=1..12 |
| Planet natures for all 9 planets | All return descriptive string, not 'unknown' |
| Classical rules linked in output | `get_matching_rules()` returns results after Phase 2+3 complete |
| Reasoning tree readable | `generate_reasoning_tree(chart_id, 10)` produces formatted output |
| Novel combination handled | Planet+house combo with no book rule → still produces synthesis from nature+meanings |

---

---

## RUNNING ORDER SUMMARY

```
Phase 0  →  Environment setup + AGENTS.md + folder structure
Phase 1  →  Build all ontology JSONs → normaliser → validator → load Neo4j
            ⛔ STOP: all normaliser tests must pass before proceeding
Phase 2+3 → Clean up extractor → build run_book.py → process all 200-300 books
            Start with Tier 1 books (Saravali first)
Phase 4  →  Build chart calculator → create chart subgraphs in Neo4j
Phase 5  →  Build logic engine → test with real charts
            Every house should produce a 7-step reasoning chain
```

## QUICK REFERENCE — CANONICAL NAMES

| Type | Canonical Format | Example |
|------|-----------------|---------|
| Planets | ALL_CAPS | `SUN`, `MOON`, `MARS` |
| Signs | ALL_CAPS | `ARIES`, `TAURUS` |
| Houses | `HOUSE_N` | `HOUSE_1`, `HOUSE_10` |
| Nakshatras | ALL_CAPS | `ASHWINI`, `BHARANI` |
| Yogas | ALL_CAPS with underscores | `GAJA_KESARI`, `RAJA_YOGA` |

---

*AI Astrologer · Phase 1–5 Codex Roadmap · v3.0*