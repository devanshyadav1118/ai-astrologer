# Phase 0 — Foundation & Infrastructure
**AI Astrologer · v3.0 · MacBook Air M2 · Python 3.11 · Gemini Pro**
**Duration:** Weeks 1–2
**Goal:** Clean Mac environment. Every tool installed, tested, and verified before any data work begins. Nothing proceeds until this checklist is 100% complete.

---

## Project Context (Read First)

This is a Vedic astrology knowledge extraction and reasoning engine.

**Core data flow:**
```
PDF → Chunker → Gemini Pro API → Structured JSON → Normaliser → Validator → Neo4j Graph
```

**Stack:**
- MacBook Air M2 — all development Phases 0–12
- Python 3.11 + pip + venv
- Gemini Pro API (not local LLM — no CUDA/Docker needed until Phase 13)
- Neo4j Desktop (native Mac app — no Docker needed)
- ChromaDB via pip

---

## 0.1 — Homebrew & Python

```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11 and git
brew install python@3.11 git

# Verify
python3.11 --version   # Expected: Python 3.11.x
git --version
```

---

## 0.2 — Project Folder & Virtual Environment

```bash
# Create project root
mkdir ~/ai-astrologer && cd ~/ai-astrologer

# Create and activate venv
python3.11 -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

**Exact folder structure to create now:**
```
ai-astrologer/
├── extractor/
│   ├── __init__.py
│   ├── chunker.py
│   ├── gemini_client.py
│   ├── prompt.py
│   └── stitcher.py
├── normaliser/
│   ├── __init__.py
│   ├── ontology/          ← JSON entity files go here in Phase 1
│   ├── normaliser.py
│   └── validator.py
├── storage/
│   ├── __init__.py
│   ├── neo4j_client.py
│   └── sqlite_client.py
├── pipeline/
│   ├── __init__.py
│   ├── run_book.py
│   └── load_ontology.py
├── reasoning/             ← Built in Phases 5+
├── data/
│   ├── raw/               ← PDFs go here — NEVER MODIFY CONTENTS
│   ├── extracted/         ← JSON rule files per book
│   └── db/                ← SQLite databases
├── tests/
│   └── __init__.py
├── AGENTS.md
├── .env
├── .gitignore
└── requirements.txt
```

```bash
# Create all folders in one command
mkdir -p extractor normaliser/ontology storage pipeline reasoning \
         data/{raw,extracted,db} tests

# Create empty __init__.py files
touch extractor/__init__.py normaliser/__init__.py storage/__init__.py \
      pipeline/__init__.py tests/__init__.py
```

---

## 0.3 — Install All Dependencies

```bash
# Activate venv first
source .venv/bin/activate

# Gemini Pro API
pip install google-generativeai

# Knowledge graph
pip install neo4j

# Vector store
pip install chromadb

# Chart calculation (Swiss Ephemeris)
pip install pyswisseph

# API layer
pip install fastapi uvicorn

# UI
pip install streamlit

# Data handling
pip install pandas sqlite-utils

# PDF processing
pip install pypdf2 pdfplumber

# Dev tools
pip install pytest black ruff jupyter

# Environment management
pip install python-dotenv

# Save
pip freeze > requirements.txt
```

---

## 0.4 — Neo4j Desktop Setup

1. Download and install Neo4j Desktop from **neo4j.com/download** (native Mac `.dmg`)
2. Open Neo4j Desktop → Create New Project → name it `ai-astrologer`
3. Add a Local DBMS → name it `ai-astrologer-db`
4. Set a password (e.g. `astrologer2024`) — note it for `.env`
5. Click **Start** to launch the database
6. Click **Open Browser** → verify it loads at `http://localhost:7474`
7. In the browser, run: `RETURN 'Connected' AS msg` → should return the string

---

## 0.5 — Config Files

**Create `.env` (NEVER commit this file):**
```
GEMINI_API_KEY=your_gemini_api_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=astrologer2024
```

**Create `.gitignore`:**
```
.env
data/
.venv/
__pycache__/
*.pyc
*.pyo
.DS_Store
*.egg-info/
dist/
.pytest_cache/
```

**Create `AGENTS.md` (Codex reads this at the start of every session):**
```markdown
# AI Astrologer — Codex Context

## What This Project Is
A Vedic astrology knowledge extraction and reasoning engine.
200–300 classical Vedic texts → structured Neo4j knowledge graph → explainable AI predictions.

## Architecture: 4 Modules
- extractor/   : PDF chunking + Gemini Pro extraction
- normaliser/  : Maps Sanskrit/English synonyms to canonical ontology terms
- storage/     : Neo4j knowledge graph + SQLite chunk index
- pipeline/    : Orchestrates all modules — one command per book

## Core Data Flow
PDF → chunker.py → gemini_client.py → stitcher.py → normaliser.py → validator.py → neo4j_client.py

## Canonical Name Convention
All entity names MUST be normalised before Neo4j storage.
- Planets:    SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN, RAHU, KETU
- Signs:      ARIES, TAURUS, GEMINI, CANCER, LEO, VIRGO, LIBRA, SCORPIO,
              SAGITTARIUS, CAPRICORN, AQUARIUS, PISCES
- Houses:     HOUSE_1 through HOUSE_12
- Nakshatras: ASHWINI, BHARANI, KRITTIKA ... (all caps)
- Yogas:      GAJA_KESARI, RAJA_YOGA ... (all caps with underscores)

## Coding Standards
- Type hints on all function signatures
- Single responsibility per file
- All secrets via .env using python-dotenv — never hardcoded
- Never modify files in data/raw/
- Every new function gets a corresponding test in tests/

## Stack
- Python 3.11, MacBook Air M2
- Gemini Pro (google-generativeai) — primary extraction LLM
- Neo4j Desktop (localhost:7474) — knowledge graph
- ChromaDB — vector store for semantic search
- pyswisseph — Swiss Ephemeris for chart calculation
- FastAPI + Streamlit — API and UI (Phases 4+)
```

---

## 0.6 — Verify Gemini API

**Create `tests/test_gemini_connection.py`:**
```python
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

def test_gemini_connection():
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content('Say "Gemini connected" and nothing else.')
    assert response.text is not None
    assert len(response.text) > 0
    print(f'Response: {response.text}')
```

```bash
pytest tests/test_gemini_connection.py -v -s
# Expected: PASSED + "Gemini connected" printed
```

---

## 0.7 — Verify Neo4j Connection

**Create `tests/test_neo4j_connection.py`:**
```python
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

def test_neo4j_connection():
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
    )
    with driver.session() as session:
        result = session.run("RETURN 'Neo4j connected' AS msg")
        msg = result.single()['msg']
        assert msg == 'Neo4j connected'
        print(f'Result: {msg}')
    driver.close()
```

```bash
pytest tests/test_neo4j_connection.py -v -s
# Expected: PASSED + "Neo4j connected" printed
```

---

## 0.8 — Git Init

```bash
git init
git add .
git commit -m "Phase 0: project scaffold, environment, and verified connections"
```

---

## ✅ Phase 0 Completion Checklist

Do not proceed to Phase 1 until every item is checked.

| # | Check | Command | Expected |
|---|-------|---------|----------|
| 1 | Python 3.11 in venv | `python --version` | `3.11.x` |
| 2 | Neo4j Desktop running | Open browser | Loads at `localhost:7474` |
| 3 | Gemini API test passes | `pytest tests/test_gemini_connection.py -v` | PASSED |
| 4 | Neo4j connection test passes | `pytest tests/test_neo4j_connection.py -v` | PASSED |
| 5 | `.env` loads without error | `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('GEMINI_API_KEY')[:5])"` | First 5 chars of key |
| 6 | All folders exist | `ls extractor normaliser storage pipeline data/raw` | No errors |
| 7 | `AGENTS.md` at project root | `cat AGENTS.md` | Readable |
| 8 | `requirements.txt` saved | `cat requirements.txt` | Lists all packages |
| 9 | Git initialised | `git log --oneline` | 1 commit visible |

**When all 9 are green → proceed to Phase 1.**