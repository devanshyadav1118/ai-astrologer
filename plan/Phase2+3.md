# Phase 2+3 — Extraction Pipeline
## Complete Detailed Roadmap (Weeks 5-16)

---

# 📋 PRE-FLIGHT CHECK

Before starting Phase 2+3, verify you have completed:

```bash
# Phase 0 Verification
✓ Python 3.11 installed
✓ Neo4j Desktop running (localhost:7474)
✓ Gemini API key in .env
✓ Folder structure created (extractor/, normaliser/, storage/, pipeline/)
✓ AGENTS.md exists at project root
✓ Git initialized

# Phase 1 Verification
✓ planets.json (9 planets) loaded in Neo4j
✓ signs.json (12 signs) loaded in Neo4j
✓ houses.json (12 houses) loaded in Neo4j
✓ nakshatras.json (27 nakshatras) loaded in Neo4j
✓ normaliser.py with normalise() function passing tests
✓ validator.py with validate_rule() function working

# Test commands
python -c "from normaliser.normaliser import AstrologyNormaliser; n = AstrologyNormaliser(); print(n.normalise('Surya'))"
# Expected output: SUN
```

---

# 🗓 WEEK 5: Module Reorganization & Foundation

## Day 1 (Monday): Audit Existing Pipeline

### Morning: Document Current State

**Task 1.1: Create inventory of existing code**

Create `PIPELINE_AUDIT.md`:

```markdown
# Current Extraction Pipeline Inventory

## Existing Scripts
- [ ] PDF chunking script (location: _______)
- [ ] Gemini API caller (location: _______)
- [ ] Extraction prompt v2.0 (location: _______)
- [ ] Stitching/merging logic (location: _______)
- [ ] Output format: JSON / Text / Other: _______

## Existing Data
- [ ] Number of books already processed: _____
- [ ] Location of processed outputs: _____
- [ ] Format of outputs: _____

## Known Issues
- [ ] List any current bugs or limitations
- [ ] List any manual steps currently required
```

**Task 1.2: Test existing pipeline on one sample book**

```bash
# Run your current pipeline on a small test book
# Document exact steps and time taken
# Save output for comparison later
```

### Afternoon: Design Module Interfaces

**Task 1.3: Define all function signatures**

Create `MODULE_INTERFACES.md`:

```python
# extractor/chunker.py
def chunk_pdf(
    pdf_path: str,
    output_dir: str,
    tokens_per_chunk: int = 500
) -> list[dict]:
    """
    Returns: [
        {
            "chunk_id": "saravali_ch01_001",
            "text": "...",
            "page_range": "1-3",
            "chapter": "Chapter 1",
            "metadata": {
                "book_id": "saravali",
                "word_count": 487,
                "has_sanskrit": True
            }
        },
        ...
    ]
    """
    pass

# extractor/gemini_client.py
def extract_from_chunk(
    chunk_text: str,
    chunk_metadata: dict
) -> dict:
    """
    Returns: {
        "rules": [...],
        "yogas": [...],
        "descriptions": [...],
        "calculations": [...],
        "chunk_id": "...",
        "extraction_metadata": {
            "model": "gemini-pro",
            "timestamp": "...",
            "tokens_used": 1234
        }
    }
    """
    pass

# extractor/stitcher.py
def stitch_book_chunks(
    chunk_outputs: list[dict],
    book_id: str
) -> dict:
    """
    Returns: {
        "book_id": "saravali",
        "total_rules": 1247,
        "total_yogas": 83,
        "rules": [...],
        "yogas": [...],
        "descriptions": [...],
        "metadata": {...}
    }
    """
    pass

# normaliser/post_processor.py
def normalise_book_data(
    raw_book_data: dict
) -> dict:
    """
    Returns: {
        "book_id": "saravali",
        "normalised_rules": [...],
        "normalised_yogas": [...],
        "warnings": [
            {
                "type": "unknown_entity",
                "entity": "Dhruva",
                "context": "...",
                "rule_id": "..."
            }
        ],
        "stats": {
            "entities_normalised": 1523,
            "unknown_entities": 12
        }
    }
    """
    pass

# storage/neo4j_client.py
class Neo4jClient:
    def load_rule(self, rule: dict, book_id: str) -> str:
        """Returns: rule_id in Neo4j"""
        pass
    
    def load_yoga(self, yoga: dict, book_id: str) -> str:
        """Returns: yoga_id in Neo4j"""
        pass
    
    def check_duplicate_rule(self, rule: dict) -> Optional[str]:
        """Returns: existing rule_id if duplicate found, else None"""
        pass
    
    def increment_confidence(self, rule_id: str, book_id: str) -> None:
        pass

# storage/sqlite_client.py
class SQLiteClient:
    def register_book(self, book_id: str, metadata: dict) -> None:
        pass
    
    def register_chunks(self, book_id: str, chunks: list[dict]) -> None:
        pass
    
    def update_chunk_status(
        self, 
        chunk_id: str, 
        status: str,
        warnings: list[str] = None
    ) -> None:
        pass
    
    def log_unknown_entity(
        self, 
        entity: str, 
        book_id: str, 
        chunk_id: str,
        context: str
    ) -> None:
        pass
```

---

## Day 2 (Tuesday): Build Chunker Module

### Task 2.1: Create `extractor/chunker.py`

**Instructions for Codex:**

```
Create extractor/chunker.py with the following requirements:

1. Input: PDF file path
2. Output: List of text chunks with metadata
3. Chunking strategy:
   - Split by natural boundaries (chapter > section > paragraph)
   - Target ~500 tokens per chunk (not strict - keep semantic units intact)
   - Preserve chapter metadata
   - Track page ranges
4. Handle edge cases:
   - Multi-column layouts
   - Sanskrit text mixed with English
   - Footnotes and references
5. Use PyPDF2 or pdfplumber for extraction
6. Add logging for progress tracking

Dependencies needed: pip install PyPDF2 pdfplumber tiktoken

Function signature must match MODULE_INTERFACES.md
```

**Test file to create:**

```python
# tests/test_chunker.py
from extractor.chunker import chunk_pdf

def test_chunker_basic():
    chunks = chunk_pdf(
        pdf_path="data/raw/test_sample.pdf",
        output_dir="data/chunks/test/"
    )
    
    assert len(chunks) > 0
    assert all("chunk_id" in c for c in chunks)
    assert all("text" in c for c in chunks)
    assert all(len(c["text"]) > 0 for c in chunks)
    print(f"✓ Chunker created {len(chunks)} chunks")

if __name__ == "__main__":
    test_chunker_basic()
```

**Verification:**
```bash
python tests/test_chunker.py
# Expected: ✓ Chunker created 15 chunks (or similar)
```

### Task 2.2: Create chunk storage structure

```bash
# Create organized folder structure for chunks
mkdir -p data/chunks/{tier1,tier2,tier3}
```

Create `data/chunks/README.md`:
```markdown
# Chunk Storage Structure

## Organization
- tier1/ - Foundational texts (Saravali, Brihat Jataka, etc.)
- tier2/ - Major Nadi texts
- tier3/ - Commentaries and supplementary texts

## Naming Convention
{book_id}/chunk_{chapter}_{number}.json

Example: saravali/chunk_01_001.json
```

---

## Day 3 (Wednesday): Build Gemini Client Module

### Task 3.1: Create `extractor/gemini_client.py`

**Instructions for Codex:**

```
Create extractor/gemini_client.py with:

1. Load Gemini API key from .env
2. Implement retry logic (3 attempts with exponential backoff)
3. Handle rate limits (wait and retry)
4. Track token usage
5. Structured error handling
6. Logging for all API calls

Dependencies: pip install google-generativeai python-dotenv

Function signature must match MODULE_INTERFACES.md
```

**Implementation hints for Codex:**

```python
# Key features to include:

import google.generativeai as genai
import time
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

class GeminiClient:
    def __init__(self):
        # Load API key from .env
        # Configure Gemini model
        # Set up logging
        pass
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    def extract_from_chunk(self, chunk_text: str, chunk_metadata: dict) -> dict:
        # Call Gemini API
        # Parse JSON response
        # Handle malformed JSON
        # Return structured output
        pass
```

### Task 3.2: Create `extractor/prompt.py`

**Instructions for Codex:**

```
Create extractor/prompt.py that stores your existing extraction prompt v2.0.

Requirements:
1. Store prompt as a string constant
2. Add function to inject chunk metadata into prompt
3. Keep all Format A-H schemas exactly as they are now
4. Do NOT modify the extraction logic - just organize the code

Copy your current working prompt exactly.
```

**Template structure:**

```python
# extractor/prompt.py

EXTRACTION_PROMPT_V2 = """
[Your existing full prompt here - Formats A through H]
"""

def get_extraction_prompt(chunk_metadata: dict = None) -> str:
    """
    Returns the extraction prompt, optionally with metadata injected.
    """
    prompt = EXTRACTION_PROMPT_V2
    
    if chunk_metadata:
        context = f"""
        Book: {chunk_metadata.get('book_id', 'unknown')}
        Chapter: {chunk_metadata.get('chapter', 'unknown')}
        Page Range: {chunk_metadata.get('page_range', 'unknown')}
        """
        prompt = context + "\n\n" + prompt
    
    return prompt
```

**Test:**
```python
# tests/test_gemini_client.py
from extractor.gemini_client import GeminiClient

def test_gemini_basic():
    client = GeminiClient()
    
    test_chunk = """
    If Sun is placed in the 10th house, the native will have authority,
    fame, and success in career. This placement grants leadership abilities.
    """
    
    result = client.extract_from_chunk(
        chunk_text=test_chunk,
        chunk_metadata={"book_id": "test", "chapter": "test"}
    )
    
    assert "rules" in result
    assert len(result["rules"]) > 0
    print(f"✓ Gemini extracted {len(result['rules'])} rules")

if __name__ == "__main__":
    test_gemini_basic()
```

---

## Day 4 (Thursday): Build Stitcher Module

### Task 4.1: Create `extractor/stitcher.py`

**Instructions for Codex:**

```
Create extractor/stitcher.py that merges all chunk outputs into one unified book output.

Requirements:
1. Input: List of chunk extraction results (from Gemini)
2. Output: Single unified JSON file with all rules/yogas/descriptions
3. Remove duplicates within the same book
4. Preserve source chunk information for traceability
5. Generate summary statistics

Function signature must match MODULE_INTERFACES.md
```

**Key logic to specify:**

```python
def stitch_book_chunks(chunk_outputs: list[dict], book_id: str) -> dict:
    """
    Merging logic:
    1. Combine all rules from all chunks
    2. Check for duplicates within book (same condition+result)
    3. Keep track of which chunk each rule came from
    4. Generate counts and statistics
    """
    
    all_rules = []
    all_yogas = []
    all_descriptions = []
    
    for chunk_output in chunk_outputs:
        # Extract rules from this chunk
        # Add source chunk_id to each rule
        # Check for duplicates
        pass
    
    return {
        "book_id": book_id,
        "total_rules": len(all_rules),
        "total_yogas": len(all_yogas),
        "total_descriptions": len(all_descriptions),
        "rules": all_rules,
        "yogas": all_yogas,
        "descriptions": all_descriptions,
        "metadata": {
            "chunks_processed": len(chunk_outputs),
            "extraction_date": datetime.now().isoformat()
        }
    }
```

**Test:**
```python
# tests/test_stitcher.py
from extractor.stitcher import stitch_book_chunks

def test_stitcher():
    chunk1 = {
        "chunk_id": "test_001",
        "rules": [{"rule_id": "r1", "condition": "Sun in 10th", "result": "fame"}],
        "yogas": []
    }
    
    chunk2 = {
        "chunk_id": "test_002",
        "rules": [{"rule_id": "r2", "condition": "Moon in 4th", "result": "happiness"}],
        "yogas": []
    }
    
    result = stitch_book_chunks([chunk1, chunk2], "test_book")
    
    assert result["total_rules"] == 2
    print("✓ Stitcher merged chunks correctly")

if __name__ == "__main__":
    test_stitcher()
```

---

## Day 5 (Friday): Build Normalisation Module

### Task 5.1: Create `normaliser/post_processor.py`

**Instructions for Codex:**

```
Create normaliser/post_processor.py that normalises all entity names in extracted data.

Requirements:
1. Walk through all rules/yogas/descriptions
2. Find entity mentions (planets, signs, houses, nakshatras)
3. Replace with canonical names using normaliser.normalise()
4. Track which entities were normalised
5. Flag unknown entities (where normalise() returns None)
6. Preserve original text for reference

Dependencies: Uses normaliser/normaliser.py (already exists from Phase 1)
```

**Implementation pattern:**

```python
# normaliser/post_processor.py

import re
from typing import Dict, List
from .normaliser import AstrologyNormaliser

class PostProcessor:
    def __init__(self):
        self.normaliser = AstrologyNormaliser()
        self.unknown_entities = []
    
    def normalise_book_data(self, raw_book_data: dict) -> dict:
        """
        Main entry point for normalisation.
        """
        normalised_rules = []
        
        for rule in raw_book_data.get("rules", []):
            normalised_rule = self._normalise_rule(rule)
            normalised_rules.append(normalised_rule)
        
        # Same for yogas, descriptions, etc.
        
        return {
            "book_id": raw_book_data["book_id"],
            "normalised_rules": normalised_rules,
            "warnings": self._generate_warnings(),
            "stats": self._generate_stats()
        }
    
    def _normalise_rule(self, rule: dict) -> dict:
        """
        Normalise a single rule.
        """
        original_condition = rule["condition"]
        original_result = rule["result"]
        
        normalised_condition = self._normalise_text(original_condition)
        normalised_result = self._normalise_text(original_result)
        
        return {
            **rule,
            "condition": normalised_condition,
            "result": normalised_result,
            "original_condition": original_condition,
            "original_result": original_result,
            "normalised": True
        }
    
    def _normalise_text(self, text: str) -> str:
        """
        Find and replace entity names in text.
        
        Strategy:
        1. Extract potential entity words (capitalized words, known patterns)
        2. Try to normalise each
        3. Replace if canonical form found
        4. Flag if unknown
        """
        # Find capitalised words (likely entities)
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        normalised_text = text
        
        for word in words:
            canonical = self.normaliser.normalise(word)
            
            if canonical:
                # Replace with canonical form
                normalised_text = normalised_text.replace(word, canonical)
            else:
                # Unknown entity - flag it
                self.unknown_entities.append({
                    "entity": word,
                    "context": text,
                    "type": "unknown_entity"
                })
        
        return normalised_text
```

**Test:**
```python
# tests/test_post_processor.py
from normaliser.post_processor import PostProcessor

def test_normalisation():
    processor = PostProcessor()
    
    raw_data = {
        "book_id": "test",
        "rules": [
            {
                "rule_id": "r1",
                "condition": "If Surya is in Lagna",
                "result": "strong personality"
            }
        ]
    }
    
    normalised = processor.normalise_book_data(raw_data)
    
    rule = normalised["normalised_rules"][0]
    assert "SUN" in rule["condition"]
    assert "HOUSE_1" in rule["condition"]
    print("✓ Entity normalisation working")

if __name__ == "__main__":
    test_normalisation()
```

---

# 🗓 WEEK 6: Storage Layer & Database Integration

## Day 1 (Monday): SQLite Schema & Client

### Task 6.1: Create database schema

Create `storage/schema.sql`:

```sql
-- Books table
CREATE TABLE IF NOT EXISTS books (
    book_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT,
    tradition TEXT,  -- 'parashari', 'jaimini', 'nadi', etc.
    language TEXT,   -- 'english', 'sanskrit', 'hindi'
    tier INTEGER NOT NULL,  -- 1, 2, or 3
    status TEXT DEFAULT 'pending',  -- 'pending', 'processing', 'complete', 'error'
    total_chunks INTEGER DEFAULT 0,
    processed_chunks INTEGER DEFAULT 0,
    total_rules INTEGER DEFAULT 0,
    total_yogas INTEGER DEFAULT 0,
    total_descriptions INTEGER DEFAULT 0,
    extraction_started TIMESTAMP,
    extraction_completed TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chunks table
CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL,
    chunk_number INTEGER NOT NULL,
    chapter TEXT,
    page_range TEXT,
    word_count INTEGER,
    status TEXT DEFAULT 'pending',  -- 'pending', 'extracted', 'normalised', 'stored', 'error'
    extraction_time REAL,  -- seconds
    tokens_used INTEGER,
    warnings TEXT,  -- JSON array
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(book_id)
);

-- Unknown entities table
CREATE TABLE IF NOT EXISTS unknown_entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_text TEXT NOT NULL,
    book_id TEXT NOT NULL,
    chunk_id TEXT,
    context TEXT,  -- surrounding text for review
    frequency INTEGER DEFAULT 1,
    review_status TEXT DEFAULT 'pending',  -- 'pending', 'added_to_ontology', 'false_positive', 'ignored'
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(book_id),
    FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id)
);

-- Processing log table
CREATE TABLE IF NOT EXISTS processing_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id TEXT NOT NULL,
    chunk_id TEXT,
    event_type TEXT NOT NULL,  -- 'chunking_started', 'extraction_complete', 'error', etc.
    message TEXT,
    details TEXT,  -- JSON for structured data
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(book_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_books_status ON books(status);
CREATE INDEX IF NOT EXISTS idx_books_tier ON books(tier);
CREATE INDEX IF NOT EXISTS idx_chunks_book_status ON chunks(book_id, status);
CREATE INDEX IF NOT EXISTS idx_unknown_entities_status ON unknown_entities(review_status);
CREATE INDEX IF NOT EXISTS idx_unknown_entities_frequency ON unknown_entities(entity_text, frequency);
```

### Task 6.2: Create `storage/sqlite_client.py`

**Instructions for Codex:**

```
Create storage/sqlite_client.py that implements all database operations.

Requirements:
1. Initialize database from schema.sql
2. All CRUD operations for books, chunks, unknown_entities
3. Transaction support for batch operations
4. Query helpers for common operations
5. Thread-safe (use connection pooling)

Database location: data/db/extraction.db

Use MODULE_INTERFACES.md for function signatures.
```

**Implementation skeleton:**

```python
# storage/sqlite_client.py

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import json

class SQLiteClient:
    def __init__(self, db_path: str = "data/db/extraction.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database from schema.sql"""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path) as f:
            schema = f.read()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema)
    
    def register_book(
        self, 
        book_id: str, 
        title: str,
        tier: int,
        author: str = None,
        tradition: str = None,
        language: str = "english"
    ) -> None:
        """Register a new book in the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO books (book_id, title, author, tradition, language, tier, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """, (book_id, title, author, tradition, language, tier))
    
    def register_chunks(self, book_id: str, chunks: List[Dict]) -> None:
        """Register all chunks for a book."""
        with sqlite3.connect(self.db_path) as conn:
            for chunk in chunks:
                conn.execute("""
                    INSERT INTO chunks (
                        chunk_id, book_id, chunk_number, chapter, 
                        page_range, word_count, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'pending')
                """, (
                    chunk["chunk_id"],
                    book_id,
                    chunk.get("chunk_number", 0),
                    chunk.get("chapter"),
                    chunk.get("page_range"),
                    chunk.get("metadata", {}).get("word_count", 0)
                ))
            
            # Update book's total_chunks
            conn.execute("""
                UPDATE books 
                SET total_chunks = ?
                WHERE book_id = ?
            """, (len(chunks), book_id))
    
    def update_chunk_status(
        self,
        chunk_id: str,
        status: str,
        warnings: List[str] = None,
        error_message: str = None,
        tokens_used: int = None,
        extraction_time: float = None
    ) -> None:
        """Update chunk processing status."""
        with sqlite3.connect(self.db_path) as conn:
            warnings_json = json.dumps(warnings) if warnings else None
            
            conn.execute("""
                UPDATE chunks
                SET status = ?,
                    warnings = ?,
                    error_message = ?,
                    tokens_used = ?,
                    extraction_time = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE chunk_id = ?
            """, (status, warnings_json, error_message, tokens_used, extraction_time, chunk_id))
    
    def log_unknown_entity(
        self,
        entity: str,
        book_id: str,
        chunk_id: str,
        context: str
    ) -> None:
        """Log an unknown entity for review."""
        with sqlite3.connect(self.db_path) as conn:
            # Check if entity already exists for this book
            cursor = conn.execute("""
                SELECT id, frequency FROM unknown_entities
                WHERE entity_text = ? AND book_id = ?
            """, (entity, book_id))
            
            row = cursor.fetchone()
            
            if row:
                # Increment frequency
                conn.execute("""
                    UPDATE unknown_entities
                    SET frequency = frequency + 1
                    WHERE id = ?
                """, (row[0],))
            else:
                # Insert new
                conn.execute("""
                    INSERT INTO unknown_entities (
                        entity_text, book_id, chunk_id, context, review_status
                    )
                    VALUES (?, ?, ?, ?, 'pending')
                """, (entity, book_id, chunk_id, context))
    
    def get_book_progress(self, book_id: str) -> Dict:
        """Get current processing progress for a book."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM books WHERE book_id = ?
            """, (book_id,))
            
            book = dict(cursor.fetchone())
            
            # Get chunk statistics
            cursor = conn.execute("""
                SELECT 
                    status,
                    COUNT(*) as count
                FROM chunks
                WHERE book_id = ?
                GROUP BY status
            """, (book_id,))
            
            chunk_stats = {row["status"]: row["count"] for row in cursor}
            book["chunk_stats"] = chunk_stats
            
            return book
    
    def get_unknown_entities(
        self, 
        book_id: str = None, 
        min_frequency: int = 1,
        review_status: str = "pending"
    ) -> List[Dict]:
        """Get unknown entities for review."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = """
                SELECT * FROM unknown_entities
                WHERE frequency >= ? AND review_status = ?
            """
            params = [min_frequency, review_status]
            
            if book_id:
                query += " AND book_id = ?"
                params.append(book_id)
            
            query += " ORDER BY frequency DESC"
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor]
```

**Test:**
```bash
python -c "
from storage.sqlite_client import SQLiteClient
client = SQLiteClient()
client.register_book('test_book', 'Test Book', tier=1)
progress = client.get_book_progress('test_book')
print('✓ SQLite client working:', progress)
"
```

---

## Day 2 (Tuesday): Neo4j Schema & Client

### Task 6.3: Create Neo4j extended schema

Create `storage/neo4j_schema.cypher`:

```cypher
// ============================================
// EXTENDED SCHEMA FOR EXTRACTED KNOWLEDGE
// ============================================

// --- Node Constraints (ontology nodes already exist from Phase 1) ---

// Rule nodes
CREATE CONSTRAINT rule_id IF NOT EXISTS 
FOR (r:Rule) REQUIRE r.rule_id IS UNIQUE;

// Yoga nodes
CREATE CONSTRAINT yoga_id IF NOT EXISTS 
FOR (y:Yoga) REQUIRE y.yoga_id IS UNIQUE;

// Description nodes  
CREATE CONSTRAINT description_id IF NOT EXISTS 
FOR (d:Description) REQUIRE d.description_id IS UNIQUE;

// Book nodes
CREATE CONSTRAINT book_id IF NOT EXISTS 
FOR (b:Book) REQUIRE b.book_id IS UNIQUE;

// --- Indexes for Performance ---

CREATE INDEX rule_confidence IF NOT EXISTS 
FOR (r:Rule) ON (r.confidence);

CREATE INDEX rule_book IF NOT EXISTS 
FOR (r:Rule) ON (r.source_books);

CREATE INDEX yoga_confidence IF NOT EXISTS 
FOR (y:Yoga) ON (y.confidence);

// ============================================
// SAMPLE RULE NODE STRUCTURE
// ============================================

// Example Rule node:
// (:Rule {
//     rule_id: "saravali_ch03_r045",
//     type: "prediction",  // Format A
//     condition: "SUN in HOUSE_10",
//     result: "authority, fame, government position",
//     impact: "strong",
//     intensity: 8,
//     probability: "high",
//     source_books: ["saravali", "brihat_jataka"],
//     source_chunks: ["saravali_ch03_014", "brihat_jataka_ch08_023"],
//     confidence: 2,  // found in 2 books
//     original_condition: "If Sun is placed in the tenth house",
//     original_result: "the native will have authority and fame",
//     created_at: "2024-03-15T10:23:45Z"
// })

// Example relationships:
// (r:Rule)-[:INVOLVES]->(p:Planet {name: "SUN"})
// (r:Rule)-[:AFFECTS]->(h:House {number: 10})
// (r:Rule)-[:EXTRACTED_FROM]->(b:Book {book_id: "saravali"})

// ============================================
// SAMPLE YOGA NODE STRUCTURE
// ============================================

// Example Yoga node:
// (:Yoga {
//     yoga_id: "gaja_kesari_001",
//     name: "GAJA_KESARI_YOGA",
//     formation_logic: "JUPITER in kendra from MOON",
//     conditions: [{...}],  // JSON structure
//     effects: ["wisdom", "fame", "benevolence"],
//     source_books: ["saravali", "phala_deepika"],
//     confidence: 2,
//     classical_reference: "Brihat Parashara Hora Shastra, Chapter 41"
// })

// Yoga relationships:
// (y:Yoga)-[:REQUIRES]->(p:Planet {name: "JUPITER"})
// (y:Yoga)-[:REQUIRES]->(m:Planet {name: "MOON"})
// (y:Yoga)-[:EXTRACTED_FROM]->(b:Book)
```

### Task 6.4: Create `storage/neo4j_client.py`

**Instructions for Codex:**

```
Create storage/neo4j_client.py for all Neo4j operations.

Requirements:
1. Connect to Neo4j (credentials from .env)
2. Load rules, yogas, descriptions as nodes
3. Create relationships to ontology entities
4. Check for duplicates before creating
5. Increment confidence scores for duplicates
6. Batch loading for efficiency (500 rules at a time)

Use MODULE_INTERFACES.md for function signatures.
```

**Implementation:**

```python
# storage/neo4j_client.py

from neo4j import GraphDatabase
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv
from datetime import datetime
import hashlib

load_dotenv()

class Neo4jClient:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")
        
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._verify_connection()
    
    def _verify_connection(self):
        with self.driver.session() as session:
            result = session.run("RETURN 'Connected' AS message")
            print(f"✓ Neo4j: {result.single()['message']}")
    
    def load_rule(self, rule: dict, book_id: str) -> str:
        """
        Load a rule into Neo4j.
        Returns the rule_id (existing or new).
        """
        with self.driver.session() as session:
            # Check if duplicate exists
            existing_id = self._check_duplicate_rule(session, rule)
            
            if existing_id:
                # Increment confidence and add book to sources
                self._increment_rule_confidence(session, existing_id, book_id)
                return existing_id
            else:
                # Create new rule
                return self._create_new_rule(session, rule, book_id)
    
    def _check_duplicate_rule(self, session, rule: dict) -> Optional[str]:
        """
        Check if a rule with the same condition+result already exists.
        Uses hash of normalised condition+result for exact matching.
        """
        rule_hash = self._compute_rule_hash(
            rule.get("condition", ""),
            rule.get("result", "")
        )
        
        result = session.run("""
            MATCH (r:Rule {rule_hash: $hash})
            RETURN r.rule_id AS rule_id
            LIMIT 1
        """, hash=rule_hash)
        
        record = result.single()
        return record["rule_id"] if record else None
    
    def _create_new_rule(self, session, rule: dict, book_id: str) -> str:
        """Create a new rule node with all relationships."""
        rule_id = rule.get("rule_id", self._generate_rule_id(book_id))
        rule_hash = self._compute_rule_hash(
            rule.get("condition", ""),
            rule.get("result", "")
        )
        
        # Create Rule node
        session.run("""
            MERGE (r:Rule {rule_id: $rule_id})
            SET r.type = $type,
                r.condition = $condition,
                r.result = $result,
                r.impact = $impact,
                r.intensity = $intensity,
                r.probability = $probability,
                r.source_books = [$book_id],
                r.source_chunks = $source_chunks,
                r.confidence = 1,
                r.rule_hash = $hash,
                r.original_condition = $original_condition,
                r.original_result = $original_result,
                r.created_at = datetime()
        """, 
            rule_id=rule_id,
            type=rule.get("type", "prediction"),
            condition=rule.get("condition", ""),
            result=rule.get("result", ""),
            impact=rule.get("impact"),
            intensity=rule.get("intensity"),
            probability=rule.get("probability"),
            book_id=book_id,
            source_chunks=rule.get("source_chunks", []),
            hash=rule_hash,
            original_condition=rule.get("original_condition", ""),
            original_result=rule.get("original_result", "")
        )
        
        # Create relationship to Book node
        session.run("""
            MATCH (r:Rule {rule_id: $rule_id})
            MERGE (b:Book {book_id: $book_id})
            MERGE (r)-[:EXTRACTED_FROM]->(b)
        """, rule_id=rule_id, book_id=book_id)
        
        # Extract and link entities (planets, houses, signs)
        self._link_rule_entities(session, rule_id, rule)
        
        return rule_id
    
    def _increment_rule_confidence(self, session, rule_id: str, book_id: str):
        """
        Increment confidence when same rule found in another book.
        """
        session.run("""
            MATCH (r:Rule {rule_id: $rule_id})
            SET r.confidence = r.confidence + 1,
                r.source_books = r.source_books + $book_id
            
            WITH r
            MERGE (b:Book {book_id: $book_id})
            MERGE (r)-[:EXTRACTED_FROM]->(b)
        """, rule_id=rule_id, book_id=book_id)
    
    def _link_rule_entities(self, session, rule_id: str, rule: dict):
        """
        Extract entity mentions from condition and create relationships.
        """
        condition = rule.get("condition", "")
        
        # Find planet mentions
        planets = self._extract_entity_mentions(condition, "Planet")
        for planet in planets:
            session.run("""
                MATCH (r:Rule {rule_id: $rule_id})
                MATCH (p:Planet {name: $planet})
                MERGE (r)-[:INVOLVES]->(p)
            """, rule_id=rule_id, planet=planet)
        
        # Find house mentions
        houses = self._extract_entity_mentions(condition, "House")
        for house in houses:
            session.run("""
                MATCH (r:Rule {rule_id: $rule_id})
                MATCH (h:House {canonical_name: $house})
                MERGE (r)-[:AFFECTS]->(h)
            """, rule_id=rule_id, house=house)
    
    def _extract_entity_mentions(self, text: str, entity_type: str) -> List[str]:
        """
        Extract entity mentions from text.
        Looks for canonical names (SUN, MOON, HOUSE_1, etc.)
        """
        import re
        
        if entity_type == "Planet":
            planets = ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN", "RAHU", "KETU"]
            return [p for p in planets if p in text]
        
        elif entity_type == "House":
            pattern = r'HOUSE_(\d+)'
            matches = re.findall(pattern, text)
            return [f"HOUSE_{m}" for m in matches]
        
        return []
    
    def _compute_rule_hash(self, condition: str, result: str) -> str:
        """Compute hash for duplicate detection."""
        combined = f"{condition}|{result}".lower().strip()
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _generate_rule_id(self, book_id: str) -> str:
        """Generate unique rule ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"{book_id}_r_{timestamp}"
    
    def load_yoga(self, yoga: dict, book_id: str) -> str:
        """Load yoga into Neo4j (similar pattern to rules)."""
        # Implementation similar to load_rule
        pass
    
    def get_rule_count(self) -> int:
        """Get total number of rules in database."""
        with self.driver.session() as session:
            result = session.run("MATCH (r:Rule) RETURN count(r) AS count")
            return result.single()["count"]
    
    def get_confidence_distribution(self) -> Dict[int, int]:
        """Get distribution of confidence scores."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (r:Rule)
                RETURN r.confidence AS confidence, count(*) AS count
                ORDER BY confidence
            """)
            return {record["confidence"]: record["count"] for record in result}
    
    def close(self):
        self.driver.close()
```

**Test:**
```python
# tests/test_neo4j_client.py
from storage.neo4j_client import Neo4jClient

def test_neo4j_rule_loading():
    client = Neo4jClient()
    
    test_rule = {
        "rule_id": "test_001",
        "type": "prediction",
        "condition": "SUN in HOUSE_10",
        "result": "authority and fame",
        "impact": "strong",
        "intensity": 8,
        "probability": "high"
    }
    
    rule_id = client.load_rule(test_rule, "test_book")
    print(f"✓ Rule loaded: {rule_id}")
    
    # Load same rule again (should increment confidence)
    rule_id2 = client.load_rule(test_rule, "another_book")
    assert rule_id == rule_id2
    print("✓ Duplicate detection working")
    
    count = client.get_rule_count()
    print(f"✓ Total rules in Neo4j: {count}")
    
    client.close()

if __name__ == "__main__":
    test_neo4j_rule_loading()
```

---

## Days 3-5 (Wed-Fri): Integration Testing

### Task 6.5: End-to-end module integration test

Create `tests/test_integration.py`:

```python
"""
End-to-end test: PDF → Neo4j

Tests the complete pipeline with one small sample book.
"""

from extractor.chunker import chunk_pdf
from extractor.gemini_client import GeminiClient
from extractor.stitcher import stitch_book_chunks
from normaliser.post_processor import PostProcessor
from storage.sqlite_client import SQLiteClient
from storage.neo4j_client import Neo4jClient

def test_end_to_end():
    print("\n" + "="*60)
    print("END-TO-END INTEGRATION TEST")
    print("="*60 + "\n")
    
    # Setup
    book_id = "test_sample"
    pdf_path = "data/raw/test_sample.pdf"  # Small test PDF
    
    sqlite = SQLiteClient()
    neo4j = Neo4jClient()
    gemini = GeminiClient()
    processor = PostProcessor()
    
    # Step 1: Register book
    print("Step 1: Registering book in SQLite...")
    sqlite.register_book(book_id, "Test Sample Book", tier=1)
    print("✓ Book registered\n")
    
    # Step 2: Chunk PDF
    print("Step 2: Chunking PDF...")
    chunks = chunk_pdf(pdf_path, f"data/chunks/{book_id}/")
    print(f"✓ Created {len(chunks)} chunks\n")
    
    # Step 3: Register chunks
    print("Step 3: Registering chunks...")
    sqlite.register_chunks(book_id, chunks)
    print("✓ Chunks registered\n")
    
    # Step 4: Extract from each chunk
    print("Step 4: Extracting with Gemini...")
    chunk_outputs = []
    
    for i, chunk in enumerate(chunks[:3]):  # Test with first 3 chunks only
        print(f"  Processing chunk {i+1}/{min(3, len(chunks))}...")
        
        result = gemini.extract_from_chunk(
            chunk_text=chunk["text"],
            chunk_metadata=chunk["metadata"]
        )
        
        chunk_outputs.append(result)
        
        # Update chunk status
        sqlite.update_chunk_status(
            chunk["chunk_id"],
            status="extracted",
            tokens_used=result.get("extraction_metadata", {}).get("tokens_used")
        )
    
    print(f"✓ Extracted from {len(chunk_outputs)} chunks\n")
    
    # Step 5: Stitch chunks
    print("Step 5: Stitching chunks...")
    book_data = stitch_book_chunks(chunk_outputs, book_id)
    print(f"✓ Stitched: {book_data['total_rules']} rules, {book_data['total_yogas']} yogas\n")
    
    # Step 6: Normalise
    print("Step 6: Normalising entities...")
    normalised_data = processor.normalise_book_data(book_data)
    print(f"✓ Normalised {normalised_data['stats']['entities_normalised']} entities")
    print(f"  Warnings: {len(normalised_data['warnings'])}\n")
    
    # Step 7: Load into Neo4j
    print("Step 7: Loading into Neo4j...")
    rules_loaded = 0
    
    for rule in normalised_data["normalised_rules"]:
        rule_id = neo4j.load_rule(rule, book_id)
        rules_loaded += 1
    
    print(f"✓ Loaded {rules_loaded} rules into Neo4j\n")
    
    # Step 8: Verify
    print("Step 8: Verification...")
    progress = sqlite.get_book_progress(book_id)
    print(f"  Book status: {progress['status']}")
    print(f"  Chunks processed: {progress.get('processed_chunks', 0)}/{progress['total_chunks']}")
    
    rule_count = neo4j.get_rule_count()
    print(f"  Total rules in Neo4j: {rule_count}")
    
    print("\n" + "="*60)
    print("✓ END-TO-END TEST PASSED")
    print("="*60 + "\n")
    
    neo4j.close()

if __name__ == "__main__":
    test_end_to_end()
```

**Run test:**
```bash
python tests/test_integration.py
```

**Expected output:**
```
============================================================
END-TO-END INTEGRATION TEST
============================================================

Step 1: Registering book in SQLite...
✓ Book registered

Step 2: Chunking PDF...
✓ Created 5 chunks

Step 3: Registering chunks...
✓ Chunks registered

Step 4: Extracting with Gemini...
  Processing chunk 1/3...
  Processing chunk 2/3...
  Processing chunk 3/3...
✓ Extracted from 3 chunks

Step 5: Stitching chunks...
✓ Stitched: 47 rules, 3 yogas

Step 6: Normalising entities...
✓ Normalised 89 entities
  Warnings: 2

Step 7: Loading into Neo4j...
✓ Loaded 47 rules into Neo4j

Step 8: Verification...
  Book status: processing
  Chunks processed: 3/5
  Total rules in Neo4j: 47

============================================================
✓ END-TO-END TEST PASSED
============================================================
```

---

# 🗓 WEEK 7: Master Pipeline & Orchestration

## Day 1 (Monday): Create Master Pipeline Script

### Task 7.1: Create `pipeline/run_book.py`

**Instructions for Codex:**

```
Create pipeline/run_book.py - the master orchestration script.

Requirements:
1. Command-line interface with argparse
2. Processes entire book from PDF to Neo4j
3. Progress tracking with progress bars
4. Error handling and recovery (resume from failures)
5. Detailed logging to file
6. Summary report at end

Command format:
python pipeline/run_book.py --pdf data/raw/saravali.pdf --book-id saravali --tier 1

Optional flags:
--resume : Resume from last checkpoint
--dry-run : Show what would be done without executing
--max-chunks : Limit number of chunks (for testing)
```

**Implementation:**

```python
# pipeline/run_book.py

import argparse
import logging
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import json

from extractor.chunker import chunk_pdf
from extractor.gemini_client import GeminiClient
from extractor.stitcher import stitch_book_chunks
from normaliser.post_processor import PostProcessor
from storage.sqlite_client import SQLiteClient
from storage.neo4j_client import Neo4jClient

# Setup logging
def setup_logging(book_id: str):
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"{book_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return log_file

class BookProcessor:
    def __init__(self, book_id: str, pdf_path: str, tier: int, resume: bool = False):
        self.book_id = book_id
        self.pdf_path = Path(pdf_path)
        self.tier = tier
        self.resume = resume
        
        # Initialize clients
        self.sqlite = SQLiteClient()
        self.neo4j = Neo4jClient()
        self.gemini = GeminiClient()
        self.processor = PostProcessor()
        
        # Stats tracking
        self.stats = {
            "chunks_processed": 0,
            "rules_extracted": 0,
            "yogas_extracted": 0,
            "rules_loaded": 0,
            "unknown_entities": 0,
            "errors": 0
        }
    
    def run(self, max_chunks: int = None):
        """Main processing pipeline."""
        logging.info(f"Starting processing: {self.book_id}")
        logging.info(f"PDF: {self.pdf_path}")
        logging.info(f"Tier: {self.tier}")
        
        try:
            # Step 1: Register book (if not resuming)
            if not self.resume:
                self._register_book()
            
            # Step 2: Chunk PDF
            chunks = self._chunk_pdf()
            
            # Limit chunks if testing
            if max_chunks:
                chunks = chunks[:max_chunks]
                logging.info(f"Limited to {max_chunks} chunks for testing")
            
            # Step 3: Register chunks
            if not self.resume:
                self._register_chunks(chunks)
            else:
                logging.info("Resuming - checking for already processed chunks")
            
            # Step 4: Process each chunk
            chunk_outputs = self._process_chunks(chunks)
            
            # Step 5: Stitch results
            book_data = self._stitch_results(chunk_outputs)
            
            # Step 6: Normalise
            normalised_data = self._normalise_data(book_data)
            
            # Step 7: Load into Neo4j
            self._load_to_neo4j(normalised_data)
            
            # Step 8: Mark complete
            self._mark_complete()
            
            # Step 9: Generate report
            self._generate_report()
            
            logging.info("✓ Processing complete!")
            
        except Exception as e:
            logging.error(f"Processing failed: {e}", exc_info=True)
            self.stats["errors"] += 1
            raise
        
        finally:
            self.neo4j.close()
    
    def _register_book(self):
        logging.info("Registering book...")
        
        # Extract metadata from PDF if possible
        title = self.book_id.replace("_", " ").title()
        
        self.sqlite.register_book(
            book_id=self.book_id,
            title=title,
            tier=self.tier
        )
        
        logging.info(f"✓ Book registered: {title}")
    
    def _chunk_pdf(self):
        logging.info("Chunking PDF...")
        
        output_dir = f"data/chunks/{self.book_id}"
        chunks = chunk_pdf(self.pdf_path, output_dir)
        
        logging.info(f"✓ Created {len(chunks)} chunks")
        return chunks
    
    def _register_chunks(self, chunks):
        logging.info("Registering chunks...")
        self.sqlite.register_chunks(self.book_id, chunks)
        logging.info(f"✓ Registered {len(chunks)} chunks")
    
    def _process_chunks(self, chunks):
        logging.info("Processing chunks with Gemini...")
        
        chunk_outputs = []
        
        # Progress bar
        pbar = tqdm(chunks, desc="Extracting", unit="chunk")
        
        for chunk in pbar:
            chunk_id = chunk["chunk_id"]
            
            # Check if already processed (for resume)
            if self.resume:
                status = self._get_chunk_status(chunk_id)
                if status in ["extracted", "normalised", "stored"]:
                    logging.info(f"Skipping already processed chunk: {chunk_id}")
                    continue
            
            try:
                # Extract
                result = self.gemini.extract_from_chunk(
                    chunk_text=chunk["text"],
                    chunk_metadata=chunk.get("metadata", {})
                )
                
                chunk_outputs.append(result)
                
                # Update stats
                self.stats["chunks_processed"] += 1
                self.stats["rules_extracted"] += len(result.get("rules", []))
                self.stats["yogas_extracted"] += len(result.get("yogas", []))
                
                # Update status
                self.sqlite.update_chunk_status(
                    chunk_id,
                    status="extracted",
                    tokens_used=result.get("extraction_metadata", {}).get("tokens_used")
                )
                
                pbar.set_postfix({
                    "rules": self.stats["rules_extracted"],
                    "yogas": self.stats["yogas_extracted"]
                })
                
            except Exception as e:
                logging.error(f"Error processing chunk {chunk_id}: {e}")
                self.sqlite.update_chunk_status(
                    chunk_id,
                    status="error",
                    error_message=str(e)
                )
                self.stats["errors"] += 1
        
        logging.info(f"✓ Processed {len(chunk_outputs)} chunks")
        return chunk_outputs
    
    def _stitch_results(self, chunk_outputs):
        from extractor.stitcher import stitch_book_chunks
        
        logging.info("Stitching chunk outputs...")
        book_data = stitch_book_chunks(chunk_outputs, self.book_id)
        
        logging.info(f"✓ Stitched: {book_data['total_rules']} rules, {book_data['total_yogas']} yogas")
        
        # Save stitched output
        output_file = Path(f"data/extracted/{self.book_id}_stitched.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(book_data, f, indent=2)
        
        return book_data
    
    def _normalise_data(self, book_data):
        logging.info("Normalising entities...")
        
        normalised_data = self.processor.normalise_book_data(book_data)
        
        logging.info(f"✓ Normalised {normalised_data['stats']['entities_normalised']} entities")
        logging.info(f"  Warnings: {len(normalised_data['warnings'])}")
        
        # Log unknown entities
        for warning in normalised_data["warnings"]:
            if warning["type"] == "unknown_entity":
                self.sqlite.log_unknown_entity(
                    entity=warning["entity"],
                    book_id=self.book_id,
                    chunk_id=warning.get("rule_id", ""),
                    context=warning.get("context", "")
                )
                self.stats["unknown_entities"] += 1
        
        # Save normalised output
        output_file = Path(f"data/extracted/{self.book_id}_normalised.json")
        with open(output_file, 'w') as f:
            json.dump(normalised_data, f, indent=2)
        
        return normalised_data
    
    def _load_to_neo4j(self, normalised_data):
        logging.info("Loading into Neo4j...")
        
        # Load rules
        for rule in tqdm(normalised_data["normalised_rules"], desc="Loading rules"):
            try:
                self.neo4j.load_rule(rule, self.book_id)
                self.stats["rules_loaded"] += 1
            except Exception as e:
                logging.error(f"Error loading rule: {e}")
                self.stats["errors"] += 1
        
        # Load yogas
        for yoga in tqdm(normalised_data.get("normalised_yogas", []), desc="Loading yogas"):
            try:
                self.neo4j.load_yoga(yoga, self.book_id)
            except Exception as e:
                logging.error(f"Error loading yoga: {e}")
        
        logging.info(f"✓ Loaded {self.stats['rules_loaded']} rules")
    
    def _mark_complete(self):
        # Update book status in SQLite
        # (Add this method to SQLiteClient if not exists)
        logging.info("Marking book as complete...")
    
    def _generate_report(self):
        logging.info("\n" + "="*60)
        logging.info("PROCESSING COMPLETE - SUMMARY REPORT")
        logging.info("="*60)
        logging.info(f"Book: {self.book_id}")
        logging.info(f"Chunks processed: {self.stats['chunks_processed']}")
        logging.info(f"Rules extracted: {self.stats['rules_extracted']}")
        logging.info(f"Yogas extracted: {self.stats['yogas_extracted']}")
        logging.info(f"Rules loaded to Neo4j: {self.stats['rules_loaded']}")
        logging.info(f"Unknown entities: {self.stats['unknown_entities']}")
        logging.info(f"Errors: {self.stats['errors']}")
        logging.info("="*60 + "\n")
    
    def _get_chunk_status(self, chunk_id: str) -> str:
        # Query SQLite for chunk status
        # (Implement in SQLiteClient if needed)
        return "pending"

def main():
    parser = argparse.ArgumentParser(description="Process astrological book")
    parser.add_argument("--pdf", required=True, help="Path to PDF file")
    parser.add_argument("--book-id", required=True, help="Unique book identifier")
    parser.add_argument("--tier", type=int, required=True, choices=[1,2,3], help="Book tier (1-3)")
    parser.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--max-chunks", type=int, help="Limit number of chunks (for testing)")
    
    args = parser.parse_args()
    
    # Setup logging
    log_file = setup_logging(args.book_id)
    logging.info(f"Logging to: {log_file}")
    
    if args.dry_run:
        logging.info("DRY RUN MODE - No changes will be made")
        logging.info(f"Would process: {args.pdf}")
        logging.info(f"Book ID: {args.book_id}")
        logging.info(f"Tier: {args.tier}")
        return
    
    # Run processing
    processor = BookProcessor(
        book_id=args.book_id,
        pdf_path=args.pdf,
        tier=args.tier,
        resume=args.resume
    )
    
    processor.run(max_chunks=args.max_chunks)

if __name__ == "__main__":
    main()
```

**Test:**
```bash
# Dry run first
python pipeline/run_book.py \
    --pdf data/raw/test_sample.pdf \
    --book-id test_sample \
    --tier 1 \
    --dry-run

# Real run with limited chunks
python pipeline/run_book.py \
    --pdf data/raw/test_sample.pdf \
    --book-id test_sample \
    --tier 1 \
    --max-chunks 3
```

---

## Day 2 (Tuesday): Progress Monitoring Tools

### Task 7.2: Create `pipeline/monitor.py`

**Instructions for Codex:**

```
Create pipeline/monitor.py for real-time progress tracking.

Features:
1. Show processing status for a book
2. Show overall progress across all books
3. Show statistics (rules per book, confidence distribution)
4. Estimate time remaining

Command: python pipeline/monitor.py --book saravali
Command: python pipeline/monitor.py --all
```

**Implementation:**

```python
# pipeline/monitor.py

import argparse
from storage.sqlite_client import SQLiteClient
from storage.neo4j_client import Neo4jClient
from tabulate import tabulate  # pip install tabulate
from datetime import datetime

def show_book_progress(book_id: str):
    """Show progress for a specific book."""
    sqlite = SQLiteClient()
    progress = sqlite.get_book_progress(book_id)
    
    print(f"\n{'='*60}")
    print(f"Book: {progress['title']} ({book_id})")
    print(f"{'='*60}\n")
    
    print(f"Status: {progress['status']}")
    print(f"Tier: {progress['tier']}")
    
    print(f"\nProgress:")
    print(f"  Chunks: {progress.get('processed_chunks', 0)}/{progress['total_chunks']}")
    
    chunk_stats = progress.get('chunk_stats', {})
    if chunk_stats:
        print(f"\n  Chunk Status:")
        for status, count in chunk_stats.items():
            print(f"    {status}: {count}")
    
    print(f"\nExtracted:")
    print(f"  Rules: {progress.get('total_rules', 0)}")
    print(f"  Yogas: {progress.get('total_yogas', 0)}")
    print(f"  Descriptions: {progress.get('total_descriptions', 0)}")
    
    if progress.get('extraction_started'):
        print(f"\nStarted: {progress['extraction_started']}")
    if progress.get('extraction_completed'):
        print(f"Completed: {progress['extraction_completed']}")
    
    # Unknown entities
    unknown = sqlite.get_unknown_entities(book_id=book_id)
    if unknown:
        print(f"\n⚠️  Unknown Entities: {len(unknown)}")
        print("\nTop 5 Unknown Entities:")
        for entity in unknown[:5]:
            print(f"  '{entity['entity_text']}' (frequency: {entity['frequency']})")
    
    print(f"\n{'='*60}\n")

def show_all_books():
    """Show progress for all books."""
    sqlite = SQLiteClient()
    
    # Get all books
    with sqlite.db_path as db:
        conn = sqlite3.connect(db)
        cursor = conn.execute("""
            SELECT book_id, title, tier, status, 
                   total_chunks, processed_chunks,
                   total_rules, total_yogas
            FROM books
            ORDER BY tier, book_id
        """)
        
        rows = cursor.fetchall()
    
    if not rows:
        print("No books registered yet.")
        return
    
    # Format as table
    headers = ["Book ID", "Title", "Tier", "Status", "Chunks", "Rules", "Yogas"]
    table_data = []
    
    for row in rows:
        book_id, title, tier, status, total_chunks, processed_chunks, total_rules, total_yogas = row
        
        chunks_str = f"{processed_chunks or 0}/{total_chunks or 0}"
        table_data.append([
            book_id,
            title[:30],  # Truncate long titles
            tier,
            status,
            chunks_str,
            total_rules or 0,
            total_yogas or 0
        ])
    
    print(f"\n{'='*80}")
    print("ALL BOOKS OVERVIEW")
    print(f"{'='*80}\n")
    
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Summary statistics
    neo4j = Neo4jClient()
    total_rules = neo4j.get_rule_count()
    confidence_dist = neo4j.get_confidence_distribution()
    
    print(f"\n{'='*80}")
    print("NEO4J STATISTICS")
    print(f"{'='*80}\n")
    
    print(f"Total Rules in Knowledge Graph: {total_rules}")
    
    print("\nConfidence Distribution:")
    for conf, count in sorted(confidence_dist.items()):
        bar = "█" * (count // 10)  # Simple bar chart
        print(f"  {conf} books: {count:4d} rules {bar}")
    
    neo4j.close()
    
    print(f"\n{'='*80}\n")

def main():
    parser = argparse.ArgumentParser(description="Monitor book processing progress")
    parser.add_argument("--book", help="Show progress for specific book")
    parser.add_argument("--all", action="store_true", help="Show all books")
    
    args = parser.parse_args()
    
    if args.book:
        show_book_progress(args.book)
    elif args.all:
        show_all_books()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
```

**Test:**
```bash
python pipeline/monitor.py --all
python pipeline/monitor.py --book test_sample
```

---

## Days 3-5 (Wed-Fri): Quality Assurance Tools

### Task 7.3: Create `pipeline/review.py` (for unknown entities)

Create a tool for reviewing and resolving unknown entities:

```python
# pipeline/review.py

"""
Interactive tool for reviewing unknown entities.
Allows adding new synonyms to ontology.
"""

import argparse
from storage.sqlite_client import SQLiteClient
from normaliser.normaliser import AstrologyNormaliser
import json
from pathlib import Path

def review_unknown_entities(book_id: str = None, limit: int = 20):
    """
    Show unknown entities and allow resolution.
    """
    sqlite = SQLiteClient()
    unknown = sqlite.get_unknown_entities(
        book_id=book_id,
        min_frequency=1,
        review_status="pending"
    )
    
    if not unknown:
        print("✓ No unknown entities to review!")
        return
    
    print(f"\nFound {len(unknown)} unknown entities")
    print(f"Showing top {min(limit, len(unknown))}:\n")
    
    normaliser = AstrologyNormaliser()
    
    for i, entity in enumerate(unknown[:limit], 1):
        print(f"\n[{i}/{limit}] Entity: '{entity['entity_text']}'")
        print(f"    Frequency: {entity['frequency']}")
        print(f"    Book: {entity['book_id']}")
        print(f"    Context: {entity['context'][:100]}...")
        
        print("\n    Options:")
        print("    1. Add to ontology (specify canonical mapping)")
        print("    2. Mark as false positive")
        print("    3. Ignore")
        print("    4. Skip to next")
        print("    q. Quit")
        
        choice = input("\n    Your choice: ").strip()
        
        if choice == "1":
            canonical = input("    Map to canonical name (e.g., SUN): ").strip().upper()
            
            # Verify canonical exists
            # Add to ontology synonym map
            # Mark as resolved
            print(f"    ✓ Added '{entity['entity_text']}' → '{canonical}'")
        
        elif choice == "2":
            # Mark as false positive
            print("    ✓ Marked as false positive")
        
        elif choice == "3":
            # Mark as ignored
            print("    ✓ Ignored")
        
        elif choice == "q":
            break

def main():
    parser = argparse.ArgumentParser(description="Review unknown entities")
    parser.add_argument("--book", help="Review for specific book")
    parser.add_argument("--limit", type=int, default=20, help="Number of entities to show")
    
    args = parser.parse_args()
    
    review_unknown_entities(book_id=args.book, limit=args.limit)

if __name__ == "__main__":
    main()
```

---

### Task 7.4: Create `pipeline/stats.py` (overall statistics)

```python
# pipeline/stats.py

"""
Generate comprehensive statistics about the extraction pipeline.
"""

from storage.sqlite_client import SQLiteClient
from storage.neo4j_client import Neo4jClient
from tabulate import tabulate

def generate_stats():
    sqlite = SQLiteClient()
    neo4j = Neo4jClient()
    
    print("\n" + "="*80)
    print("EXTRACTION PIPELINE STATISTICS")
    print("="*80 + "\n")
    
    # SQLite stats
    print("BOOKS PROCESSED:")
    # ... query counts by tier, status
    
    print("\nCHUNK STATISTICS:")
    # ... total chunks, avg per book, status distribution
    
    print("\nNEO4J KNOWLEDGE GRAPH:")
    print(f"  Total Rules: {neo4j.get_rule_count()}")
    print(f"  Total Yogas: ...")  # Add yoga count method
    
    print("\nCONFIDENCE DISTRIBUTION:")
    conf_dist = neo4j.get_confidence_distribution()
    for conf, count in sorted(conf_dist.items()):
        pct = (count / neo4j.get_rule_count()) * 100
        print(f"  {conf} source(s): {count:5d} rules ({pct:5.1f}%)")
    
    print("\nUNKNOWN ENTITIES:")
    unknown = sqlite.get_unknown_entities(review_status="pending")
    print(f"  Pending review: {len(unknown)}")
    
    neo4j.close()

if __name__ == "__main__":
    generate_stats()
```

---

# 🗓 WEEKS 8-10: Process Tier 1 Books

## Week 8: Saravali & Brihat Jataka

### Day 1-3: Process Saravali

```bash
# Full Saravali processing
python pipeline/run_book.py \
    --pdf data/raw/saravali.pdf \
    --book-id saravali \
    --tier 1

# Monitor progress
python pipeline/monitor.py --book saravali

# Review unknown entities
python pipeline/review.py --book saravali
```

**Daily tasks:**
- Day 1: Start processing, monitor for errors
- Day 2: Review first 50 unknown entities, add to ontology
- Day 3: Re-normalise if ontology updated, verify in Neo4j

### Day 4-5: Process Brihat Jataka

Same workflow as Saravali.

---

## Week 9: Phala Deepika & BPHS

Same pattern - one book every 2-3 days.

---

## Week 10: Tier 1 Cleanup & Validation

### Task 10.1: Cross-book duplicate detection

Create `pipeline/deduplicate.py`:

```python
# Find rules that appear in multiple Tier 1 books
# Merge them and update confidence scores
# Generate report of high-confidence rules
```

### Task 10.2: QA sampling

Create `pipeline/qa_check.py`:

```python
# Random sample 5% of rules from each book
# Show original text + extracted rule side-by-side
# Mark hallucinations
# Generate accuracy report
```

---

# 🗓 WEEKS 11-14: Process Tier 2 & 3 Books

## Weeks 11-12: Tier 2 Books (High-value sources)

- Jataka Parijata
- Sarvartha Chintamani
- Major Nadi texts

**Automation upgrade:**

Create `pipeline/batch_process.py`:

```bash
# Process multiple books in sequence
python pipeline/batch_process.py --tier 2
```

---

## Weeks 13-14: Tier 3 Books (Bulk processing)

Process remaining 200+ books.

**Key strategy:**
- Batch processing (3-5 books at a time)
- Automated unknown entity resolution (if frequency < 2, auto-ignore)
- Focus on quantity over perfect quality
- Weekly deduplication runs

---

# 🗓 WEEKS 15-16: Final QA & Reporting

## Week 15: Deduplication & Confidence Scoring

### Task 15.1: Final deduplication pass

```bash
python pipeline/deduplicate.py --all-books
```

**Logic:**
1. Find all rule clusters (same condition+result)
2. Merge into single rule
3. Update confidence = number of source books
4. Keep source book list for traceability

### Task 15.2: Confidence analysis

Generate report:
- How many rules have confidence 1, 2, 3, 4, 5+
- Which books contributed most unique vs shared knowledge
- Coverage analysis (which planets/houses have most rules)

---

## Week 16: Final Validation & Documentation

### Task 16.1: Statistical validation

Create `pipeline/validate_extraction.py`:

```python
"""
Validate extraction quality.
"""

# Metrics:
# - Average rules per book
# - Rules per chunk
# - Normalisation success rate
# - Unknown entity rate
# - Confidence distribution
# - Entity coverage (all planets covered?)
```

### Task 16.2: Create final documentation

Create `EXTRACTION_REPORT.md`:

```markdown
# Phase 2+3 Extraction Pipeline - Final Report

## Books Processed
- Tier 1: X books (foundational)
- Tier 2: Y books (major sources)
- Tier 3: Z books (supplementary)
- **Total: 200+ books**

## Knowledge Extracted
- Total Rules: 50,000+
- Total Yogas: 500+
- Total Descriptions: 2,000+

## Confidence Distribution
- 1 source: X rules
- 2 sources: Y rules
- 3+ sources: Z rules (high confidence)

## Entity Coverage
- Planets: 100% coverage
- Houses: 100% coverage
- Signs: 100% coverage
- Nakshatras: 95% coverage

## Unknown Entities
- Total flagged: 200
- Resolved: 150
- Added to ontology: 100
- False positives: 50

## Quality Metrics
- Normalisation success: 98%
- QA sample accuracy: 95%
- Hallucination rate: <2%

## Deliverables
✓ All books in Neo4j knowledge graph
✓ Cross-book confidence scores assigned
✓ All entities normalised to canonical form
✓ SQLite index complete
✓ Pipeline fully automated and tested
```

---

# 📊 FINAL DELIVERABLES CHECKLIST

By end of Week 16:

### Code Modules (All in Git)
- ✓ `extractor/` — chunker, gemini_client, prompt, stitcher
- ✓ `normaliser/` — normaliser, post_processor, validator
- ✓ `storage/` — neo4j_client, sqlite_client, schemas
- ✓ `pipeline/` — run_book, monitor, review, deduplicate, stats, batch_process

### Data Assets
- ✓ 200-300 books fully processed
- ✓ 50,000+ rules in Neo4j (deduplicated with confidence scores)
- ✓ All entities normalised to canonical names
- ✓ SQLite database with complete metadata and processing logs
- ✓ Unknown entities < 50 unresolved

### Documentation
- ✓ AGENTS.md updated with all modules
- ✓ PROCESSING_LOG.md — tracks which books processed when
- ✓ EXTRACTION_REPORT.md — final statistics and validation
- ✓ Individual log files per book in logs/

### Database State
- ✓ Neo4j: 50,000+ Rule nodes linked to ontology
- ✓ Neo4j: Yogas, Descriptions, Books nodes
- ✓ Neo4j: Confidence scores assigned
- ✓ SQLite: All books/chunks indexed
- ✓ SQLite: Unknown entities tracked

---

# 🎯 SUCCESS CRITERIA

Phase 2+3 is complete when:

1. **All 200-300 books processed** — SQLite shows "complete" status
2. **Neo4j has 50,000+ rules** — with confidence distribution matching expectations
3. **< 50 unresolved unknown entities** — 98%+ normalisation success rate
4. **QA validation passes** — random sample shows <5% error rate
5. **Pipeline is repeatable** — can process new book in < 2 hours
6. **All code is modular** — each module has single responsibility and tests

---
 
---

This roadmap should give you everything you need for Codex to implement Phase 2+3 systematically. Each week builds on the previous, all code is modular and testable, and you have clear verification points throughout.