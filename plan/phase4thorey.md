# Phase 4: Knowledge Graph & Chart Ingestion Engine
## Complete Theoretical Framework (Updated for VedicAstro)

**Duration:** Weeks 17–20 (4 weeks)  
**Goal:** Transform any birth chart into a queryable Neo4j knowledge subgraph that connects to your Phase 1-3 knowledge base, enabling symbolic reasoning in Phase 5+

---

## 🎯 Core Concept: The Chart as a Living Graph

### **Traditional Approach (What You're NOT Building):**
```
Birth Data → Static Report → Text Interpretation
```
- Chart calculated once
- Interpretations pre-written
- No reasoning, just lookup
- Can't handle novel combinations

### **Your Approach (Knowledge Graph):**
```
Birth Data → VedicAstro → Normalized Data → Neo4j Subgraph → Connected to 50,000+ Rules
                                              ↓
                                    Reasoning Engine Queries
                                    (Phases 5-11)
```

**Why This Is Revolutionary:**
- Chart becomes **queryable graph structure**
- Every planet/house/aspect is a **node with relationships**
- Connected to **classical knowledge** from 200+ books
- Enables **logical reasoning chains** (house → lord → placement → aspects)
- Handles **infinite combinations** never written in any text

---

## 📐 The Three-Layer Architecture

### **Layer 1: Base Ontology (Phase 1)**
*Static knowledge — the universal truth of Vedic astrology*

```
Nodes:
- Planet (9 grahas with eternal properties)
- Sign (12 rashis with eternal qualities)
- House (12 bhavas with eternal meanings)
- Nakshatra (27 with lords, deities, qualities)
- Yoga (50+ classical combinations)
- Rule (50,000+ extracted from books)

These nodes are PERMANENT. Created once, never change.
```

**Example Planet Node:**
```
(:Planet {
    name: 'MARS',
    nature: 'malefic',
    element: 'fire',
    exaltation_sign: 'CAPRICORN',
    exaltation_degree: 28,
    debilitation_sign: 'CANCER',
    friends: ['SUN', 'MOON', 'JUPITER'],
    enemies: ['MERCURY'],
    karakatvam: ['courage', 'action', 'siblings', 'property'],
    dasha_years: 7
})
```

### **Layer 2: Chart Instance (Phase 4 — What You're Building)**
*Dynamic data — specific to one person's birth chart*

```
Nodes:
- Chart (master node for this person)
- ChartPlanet (where Mars sits in THIS chart)
- ChartHouse (what sign is on 10th cusp in THIS chart)

These nodes are TRANSIENT. Created per chart, connected to Layer 1.
```

**Example ChartPlanet Node:**
```
(:ChartPlanet {
    id: 'chart_abc123_MARS',
    planet_name: 'MARS',
    sign: 'CAPRICORN',
    degree: 15.23,
    house: 10,
    nakshatra: 'SHRAVANA',
    nakshatra_pada: 2,
    sublord: 'JUPITER',  // KP system bonus
    retrograde: false,
    combustion: false,
    dignity_status: 'exalted',
    strength_modifier: 5
})
```

**Connected via:**
```
(:ChartPlanet)-[:INSTANCE_OF]->(:Planet)  // Links to base Mars
(:ChartPlanet)-[:PLACED_IN_SIGN]->(:Sign {name: 'CAPRICORN'})
(:ChartPlanet)-[:IN_NAKSHATRA]->(:Nakshatra {name: 'SHRAVANA'})
(:Chart)-[:CONTAINS_PLANET]->(:ChartPlanet)
```

### **Layer 3: Reasoning Layer (Phases 5-11)**
*Computed relationships — derived through graph traversal*

```
Computed at query time:
- House lord chains (10th lord → where placed → what aspects it)
- Aspect webs (which planets aspect which)
- Yoga formations (pattern matching across chart)
- Strength scores (numerical evaluation)
- Influence propagation (energy flow across houses)
```

**Example Reasoning Query:**
```cypher
// "Analyze career prospects" (10th house analysis)
MATCH (c:Chart {chart_id: $chart_id})-[:CONTAINS_HOUSE]->
      (ch:ChartHouse {house_number: 10})-[:RULED_BY]->(lord:ChartPlanet)
MATCH (lord)-[:PLACED_IN_HOUSE]->(lord_house:ChartHouse)
MATCH (lord)-[:PLACED_IN_SIGN]->(lord_sign:Sign)
OPTIONAL MATCH (lord)<-[:ASPECTS]-(aspector:ChartPlanet)
RETURN 
    ch.sign AS career_sign,
    lord.planet_name AS career_lord,
    lord_house.house_number AS lord_placement,
    lord.dignity_status AS lord_dignity,
    collect(aspector.planet_name) AS aspects_to_lord
```

**This query answers:** "What does the 10th house reveal about career?"

---

## 🧩 What Phase 4 Actually Does

### **Week 17: Calculate & Extract Data**

#### **Input:**
```python
{
    'name': 'John Doe',
    'date': '1990-05-15',
    'time': '14:30:00',
    'latitude': 26.9124,
    'longitude': 75.7873,
    'timezone': 5.5
}
```

#### **Step 1: VedicAstro Calculation**
Uses Swiss Ephemeris to compute:
- Exact planetary longitudes (0-360°)
- Sign placements (which of 12 rashis)
- House cusps (Whole Sign system)
- Nakshatra positions (which of 27 + pada)
- Retrograde status
- KP sublords (bonus data)

#### **Step 2: Normalization**
Maps VedicAstro output to your ontology:
```
VedicAstro: "Mars"     → Your Ontology: "MARS"
VedicAstro: "Mesha"    → Your Ontology: "ARIES"
VedicAstro: "Lagna"    → Your Ontology: "HOUSE_1"
VedicAstro: "Ashwini"  → Your Ontology: "ASHWINI"
```

**Why Critical:** Without this, "Mars", "Kuja", "Mangala" become 3 separate entities in graph.

#### **Step 3: Dignity Analysis**
For each planet, determine:
```python
dignity = {
    'exalted': True/False,           # In exaltation sign?
    'debilitated': True/False,        # In debilitation sign?
    'own_sign': True/False,           # In sign it rules?
    'moolatrikona': True/False,       # In moolatrikona range?
    'friend_sign': True/False,        # Sign ruled by friend?
    'enemy_sign': True/False,         # Sign ruled by enemy?
    'status': 'exalted',              # Overall status
    'strength_modifier': 5            # Numeric bonus/penalty
}
```

**Example:**
- Mars in Capricorn at 15° → **Exalted** → +5 strength
- Venus in Virgo at 10° → **Debilitated** → -5 strength
- Jupiter in Sagittarius → **Own Sign** → +4 strength

#### **Step 4: Aspect Calculation**
Implement Vedic drishti (aspect) rules:

**Universal Rule:** All planets aspect 7th house from their position (opposition)

**Special Aspects:**
- **Mars:** Also aspects 4th and 8th houses
- **Jupiter:** Also aspects 5th and 9th houses
- **Saturn:** Also aspects 3rd and 10th houses

**Example:**
```
Mars in House 3 aspects:
- House 9 (7th from 3rd) — full aspect
- House 6 (4th from 3rd) — special Mars aspect
- House 10 (8th from 3rd) — special Mars aspect
```

**Output:**
```python
aspects = [
    {
        'from_planet': 'MARS',
        'to_planet': 'JUPITER',
        'type': 'OPPOSITION',
        'strength': 1.0
    },
    {
        'from_planet': 'SATURN',
        'to_house': 10,
        'type': 'SATURN_SPECIAL',
        'strength': 1.0
    }
]
```

#### **Step 5: House Lord Determination**
For each house, find which planet rules it:

**Logic:**
1. Identify sign on house cusp
2. Look up ruling planet of that sign (from Phase 1 ontology)
3. Find where that planet sits in THIS chart

**Example:**
```
House 10 cusp: Aquarius
Aquarius ruler: Saturn (from ontology)
Saturn placement: House 3, Gemini
→ Therefore: 10th lord is Saturn, placed in 3rd house
```

**Why This Matters:**
- Career (10th house) = Saturn themes
- Saturn in 3rd = communication/skills/effort
- Career through communication confirmed

---

### **Week 18: Build Neo4j Graph Structure**

#### **The Graph Schema**

```
                    [Chart]
                       |
            ┌──────────┴──────────┐
            ↓                     ↓
      [ChartPlanet]          [ChartHouse]
            |                     |
    ┌───────┼───────┐            |
    ↓       ↓       ↓            ↓
 [Planet] [Sign] [Nakshatra]  [Sign]
    ↑
    |
 [Rule] ← Links to 50,000+ extracted rules from Phase 3
```

#### **Node Types Created:**

**1. Chart (Master Node)**
```cypher
CREATE (c:Chart {
    chart_id: 'uuid-123',
    name: 'John Doe',
    date: '1990-05-15',
    time: '14:30:00',
    latitude: 26.9124,
    longitude: 75.7873,
    timezone: 5.5,
    ayanamsa: 'Lahiri',
    created_at: timestamp()
})
```

**2. ChartPlanet (9 nodes per chart)**
```cypher
CREATE (cp:ChartPlanet {
    id: 'chart_123_MARS',
    planet_name: 'MARS',
    sign: 'CAPRICORN',
    degree: 15.23,
    longitude: 285.23,
    house: 10,
    nakshatra: 'SHRAVANA',
    nakshatra_pada: 2,
    sublord: 'JUPITER',
    retrograde: false,
    combustion: false,
    dignity_status: 'exalted',
    strength_modifier: 5
})
```

**3. ChartHouse (12 nodes per chart)**
```cypher
CREATE (ch:ChartHouse {
    id: 'chart_123_HOUSE_10',
    house_number: 10,
    sign: 'AQUARIUS',
    degree: 0.0,
    lord: 'SATURN'
})
```

#### **Relationship Types Created:**

**Planet Relationships:**
```cypher
// Link to base ontology
(ChartPlanet)-[:INSTANCE_OF]->(Planet)

// Placement relationships
(ChartPlanet)-[:PLACED_IN_SIGN]->(Sign)
(ChartPlanet)-[:PLACED_IN_HOUSE]->(ChartHouse)
(ChartPlanet)-[:IN_NAKSHATRA {pada: 2}]->(Nakshatra)

// Aspect relationships
(ChartPlanet)-[:ASPECTS {type: 'OPPOSITION', strength: 1.0}]->(ChartPlanet)
(ChartPlanet)-[:ASPECTS {type: 'MARS_SPECIAL', strength: 1.0}]->(ChartHouse)

// Conjunction (same house)
(ChartPlanet)-[:CONJOINS {orb: 5.2}]->(ChartPlanet)

// Dispositor (sign ruler)
(ChartPlanet)-[:DISPOSED_BY]->(ChartPlanet)
```

**House Relationships:**
```cypher
// Chart ownership
(Chart)-[:CONTAINS_PLANET]->(ChartPlanet)
(Chart)-[:CONTAINS_HOUSE]->(ChartHouse)

// House lordship
(ChartHouse)-[:RULED_BY]->(ChartPlanet)
(ChartHouse)-[:SIGN_ON_CUSP]->(Sign)

// Link to base meanings
(ChartHouse)-[:REPRESENTS]->(House)  // Links to base House_10 ontology
```

---

### **Week 19: House Lord Chains & Dispositor Trees**

#### **The House Lord Chain Concept**

**What It Answers:** "How does this house manifest in this person's life?"

**Example: 10th House Analysis**

```
Step 1: What is 10th house?
→ Career, status, public life (from base House ontology)

Step 2: What sign is on 10th cusp?
→ Aquarius (in this chart)

Step 3: Who rules Aquarius?
→ Saturn (from Sign ontology)

Step 4: Where is Saturn placed?
→ House 3, Gemini (in this chart)

Step 5: What does House 3 represent?
→ Communication, skills, effort, siblings (from base House ontology)

Step 6: What is Saturn's nature?
→ Discipline, structure, delays, persistence (from Planet ontology)

Step 7: What aspects Saturn?
→ Jupiter aspects Saturn (wisdom, expansion added)

Synthesis:
Career (10th) → Saturn (structure) → 3rd house (communication) + Jupiter aspect (wisdom)
= Career through disciplined communication, writing, teaching, analysis
```

**Graph Query to Get This:**
```cypher
MATCH path = (c:Chart {chart_id: $id})-[:CONTAINS_HOUSE]->
             (h:ChartHouse {house_number: 10})-[:RULED_BY]->
             (lord:ChartPlanet)-[:PLACED_IN_HOUSE]->(lord_house:ChartHouse)
MATCH (lord)-[:INSTANCE_OF]->(base_planet:Planet)
MATCH (lord_house)-[:REPRESENTS]->(base_lord_house:House)
OPTIONAL MATCH (lord)<-[:ASPECTS]-(aspector:ChartPlanet)
RETURN 
    h.sign AS house_sign,
    lord.planet_name AS lord_name,
    lord.dignity_status AS lord_dignity,
    lord_house.house_number AS lord_placement,
    base_planet.karakatvam AS planet_meanings,
    base_lord_house.primary_meanings AS house_meanings,
    collect(aspector.planet_name) AS aspects
```

#### **The Dispositor Chain Concept**

**What It Answers:** "What empowers/weakens this planet?"

**Example: Mars Dispositor Chain**

```
Mars in Gemini → Mercury is dispositor (Mercury rules Gemini)
Mercury in Virgo → Mercury disposes itself (Mercury rules Virgo)
= Chain ends (Mercury in own sign = strong)

Result: Mars supported by strong Mercury
= Action (Mars) guided by intellect (Mercury)
```

**Another Example:**

```
Venus in Aries → Mars is dispositor
Mars in Cancer → Moon is dispositor  
Moon in Scorpio → Mars is dispositor
= Cycle! Venus → Mars → Moon → Mars

Result: Mutual reception cycle = complex interplay
= Relationships (Venus) driven by action (Mars) driven by emotions (Moon)
```

**Graph Structure:**
```cypher
(ChartPlanet {name: 'MARS'})-[:DISPOSED_BY]->(ChartPlanet {name: 'MERCURY'})
(ChartPlanet {name: 'MERCURY'})-[:DISPOSED_BY]->(ChartPlanet {name: 'MERCURY'})
```

---

### **Week 20: Query Interface & Integration**

#### **Build Reusable Query Functions**

These functions become the API for Phase 5 reasoning engine:

```python
class ChartQueries:
    """
    High-level query interface
    Hides Neo4j complexity from reasoning engine
    """
    
    def get_house_lord(chart_id, house_number):
        """
        Returns: {
            'lord': 'SATURN',
            'lord_house': 3,
            'lord_sign': 'GEMINI',
            'lord_dignity': 'neutral',
            'lord_strength': 2.0
        }
        """
    
    def get_planet_placement(chart_id, planet):
        """
        Returns: {
            'house': 10,
            'sign': 'CAPRICORN',
            'degree': 15.23,
            'nakshatra': 'SHRAVANA',
            'pada': 2,
            'dignity': 'exalted'
        }
        """
    
    def get_aspects_to_planet(chart_id, planet):
        """
        Returns: [
            {
                'from_planet': 'JUPITER',
                'type': 'OPPOSITION',
                'strength': 1.0
            },
            ...
        ]
        """
    
    def get_planets_in_house(chart_id, house):
        """
        Returns: ['MARS', 'MERCURY']
        """
    
    def get_conjunctions(chart_id, planet):
        """
        Returns: [
            {
                'planet': 'MERCURY',
                'orb': 3.5,
                'same_nakshatra': True
            }
        ]
        """
    
    def traverse_house_chain(chart_id, house):
        """
        Complete house analysis chain
        Returns entire reasoning path as structured data
        """
```

#### **Integration with Phase 1-3 Knowledge**

**Connect Chart Data to Extracted Rules:**

```cypher
// Find rules that apply to Mars placement in this chart
MATCH (c:Chart {chart_id: $id})-[:CONTAINS_PLANET]->
      (cp:ChartPlanet {planet_name: 'MARS'})
MATCH (cp)-[:PLACED_IN_HOUSE]->(ch:ChartHouse)
MATCH (r:Rule)
WHERE r.condition CONTAINS 'MARS'
  AND r.condition CONTAINS ('HOUSE_' + ch.house_number)
  AND r.confidence >= 0.7
RETURN r.rule_id, r.condition, r.result, r.source_book
ORDER BY r.confidence DESC
LIMIT 10
```

**This returns:**
```json
[
    {
        "rule_id": "saravali_ch12_r045",
        "condition": "MARS in HOUSE_10 and EXALTED",
        "result": "Great success in career through courage and action. Leadership in competitive fields.",
        "source_book": "Saravali"
    },
    ...
]
```

**The Magic:** Chart-specific data queries classical knowledge automatically.

---

## 🔄 Complete Data Flow (End-to-End)

### **Phase 4 Complete Pipeline:**

```
1. User Input:
   └─> name, date, time, lat, lon, timezone

2. VedicAstro Calculator:
   └─> Calls Swiss Ephemeris
   └─> Returns raw planet/house positions

3. Normalizer:
   └─> Maps "Surya" → "SUN"
   └─> Maps "Mesha" → "ARIES"
   └─> Maps all entity names to canonical forms

4. Dignity Analyzer:
   └─> Checks exaltation/debilitation
   └─> Checks own sign/moolatrikona
   └─> Checks friend/enemy sign
   └─> Assigns strength modifiers

5. Aspect Calculator:
   └─> Applies Vedic drishti rules
   └─> Identifies all aspects between planets
   └─> Calculates aspect strengths

6. House Lord Calculator:
   └─> For each house, finds ruling planet
   └─> Tracks where lord is placed

7. Graph Builder:
   └─> Creates Chart node
   └─> Creates 9 ChartPlanet nodes
   └─> Creates 12 ChartHouse nodes
   └─> Creates all relationships
   └─> Links to Phase 1 ontology

8. Output:
   └─> chart_id (UUID)
   └─> Complete queryable graph in Neo4j
   └─> Ready for reasoning engine (Phase 5)
```

---

## 📊 What Makes This Architecture Powerful

### **1. Separation of Concerns**

**Static Knowledge (Phase 1):**
- Universal astrological truth
- Never changes
- Shared across all charts

**Dynamic Data (Phase 4):**
- Person-specific chart
- Changes per individual
- Linked to static knowledge

**Reasoning Logic (Phase 5+):**
- Query patterns
- Traversal algorithms
- No hard-coded interpretations

### **2. Novel Combination Handling**

**Traditional System:**
```
IF Mars in 10th AND exalted THEN "successful career"
```
- Only works for exactly this combination
- Fails if Mars is in 9th, or 10th but not exalted

**Your System:**
```
Query: What is career? → 10th house
Query: Who rules 10th? → Saturn
Query: Where is Saturn? → 3rd house
Query: What is Saturn's nature? → Discipline, structure
Query: What is 3rd house? → Communication, skills
Synthesis: Career through disciplined communication
```
- Works for ANY 10th lord in ANY house
- Never explicitly programmed
- Emerges from graph traversal

### **3. Multi-Factor Integration**

**Single query can integrate:**
- Base planet nature (Mars = action)
- Dignity status (exalted = strong)
- House placement (10th = career)
- Aspects received (Jupiter = wisdom added)
- Sign qualities (Capricorn = structure)
- Nakshatra influence (Shravana = listening)
- Classical rules (from Phase 3 extraction)
- Strength scores (from Phase 6)

All connected in one graph, one query.

---

## 🎯 Phase 4 Success Criteria

**Before Phase 5 begins, you must be able to:**

### **Test 1: Basic Chart Loading**
```python
chart_id = builder.build_chart_graph(
    name="Test Chart",
    date="1990-05-15",
    time="14:30:00",
    lat=26.9124,
    lon=75.7873,
    tz=5.5
)

# Verify: chart_id returns successfully
# Verify: Neo4j contains 1 Chart + 9 Planets + 12 Houses
```

### **Test 2: Data Accuracy**
```python
mars_data = queries.get_planet_placement(chart_id, 'MARS')

# Verify: Position matches Jagannatha Hora (< 1' deviation)
# Verify: Dignity correctly detected
# Verify: Nakshatra correct
```

### **Test 3: Relationship Queries**
```python
lord_data = queries.get_house_lord(chart_id, 10)

# Verify: Returns correct ruling planet
# Verify: Returns where lord is placed
# Verify: Returns lord's dignity
```

### **Test 4: Aspect Detection**
```python
aspects = queries.get_aspects_to_planet(chart_id, 'MARS')

# Verify: All Vedic aspects correctly identified
# Verify: Special aspects (Mars/Jupiter/Saturn) included
# Verify: Aspect strengths calculated
```

### **Test 5: Integration with Knowledge Base**
```cypher
// Find rules that apply to this chart
MATCH (c:Chart {chart_id: $id})-[:CONTAINS_PLANET]->(cp:ChartPlanet)
MATCH (cp)-[:PLACED_IN_HOUSE]->(ch:ChartHouse)
MATCH (r:Rule)
WHERE r.condition CONTAINS cp.planet_name
  AND r.condition CONTAINS ('HOUSE_' + ch.house_number)
RETURN count(r) AS matching_rules

// Verify: Returns > 0 (rules from Phase 3 connect to chart)
```

### **Test 6: Performance**
```python
import time

start = time.time()
chart_id = builder.build_chart_graph(...)
elapsed = time.time() - start

# Verify: Complete chart ingestion < 5 seconds
```

### **Test 7: Batch Processing**
```python
chart_ids = processor.process_csv('test_charts.csv')

# Verify: Can process 10 charts without errors
# Verify: All charts queryable
# Verify: No data corruption
```

---

## 📋 Phase 4 Deliverables Summary

### **Code Modules:**
✅ `vedicastro_calculator.py` - Chart calculation wrapper  
✅ `dignity_analyzer.py` - Dignity/strength determination  
✅ `aspect_calculator.py` - Vedic drishti computation  
✅ `house_lord_calculator.py` - Lordship chains  
✅ `graph_builder.py` - Neo4j population pipeline  
✅ `queries.py` - High-level query interface  
✅ `batch_processor.py` - Multi-chart processing  

### **Neo4j Schema:**
✅ Chart, ChartPlanet, ChartHouse node types  
✅ All placement relationships  
✅ All aspect relationships  
✅ House lord relationships  
✅ Dispositor chains  
✅ Links to Phase 1 ontology  

### **Documentation:**
✅ CHART_CALCULATION.md - How calculations work  
✅ NEO4J_SCHEMA.md - Complete graph structure  
✅ API_REFERENCE.md - Query function docs  
✅ Example notebooks  

### **Tests:**
✅ Calculation accuracy tests  
✅ Dignity detection tests  
✅ Aspect calculation tests  
✅ House lord tests  
✅ End-to-end pipeline tests  
✅ Integration tests with Phase 1-3  

---

## 🚀 What Comes Next (Phase 5 Preview)

With Phase 4 complete, you have:
- ✅ Any chart → queryable graph structure
- ✅ Connected to 50,000+ rules from books
- ✅ All relationships explicit and traversable

**Phase 5 builds the reasoning engine:**
```python
# Phase 5 will enable this:
interpretation = reasoner.analyze_house(chart_id, house=10)

# Returns:
{
    'house': 10,
    'theme': 'Career and Public Life',
    'lord': 'SATURN',
    'lord_placement': 'House 3 (Communication)',
    'lord_dignity': 'neutral',
    'synthesis': 'Career through structured communication...',
    'supporting_rules': [...],  # From Phase 3
    'strength_score': 6.8,      # From Phase 6 (future)
    'yogas_active': [...],      # From Phase 7 (future)
    'reasoning_chain': [...]    # Full traceable path
}
```

**The graph you build in Phase 4 makes this possible.**

--- 