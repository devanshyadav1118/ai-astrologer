# Phase 5 Deliverables

## Reasoning Chain Model

The implemented house reasoning flow is:

1. Read the base meaning of the house from ontology.
2. Find the house lord from the chart graph.
3. Find where that lord is placed.
4. Read the lord's natural qualities from ontology.
5. Read aspects to the lord.
6. Read conjunctions with the lord.
7. Read occupants in the house itself.
8. Read the dispositor chain.
9. Pull matching classical rules and analogous rules.
10. Convert all of the above into structured facts.
11. Score those facts.
12. Build a reasoning tree and a natural-language synthesis.

This is implemented across:

- [reasoning/house_reasoner.py](/Users/devanshydv/Desktop/Astrology%20final%20boss/reasoning/house_reasoner.py)
- [reasoning/models.py](/Users/devanshydv/Desktop/Astrology%20final%20boss/reasoning/models.py)
- [reasoning/novel_synthesizer.py](/Users/devanshydv/Desktop/Astrology%20final%20boss/reasoning/novel_synthesizer.py)

## Core Traversal Function Specs

### `get_house_lord(chart_id, house)`

- Input: chart id, house number
- Output: lord name, lord house, lord sign, dignity, strength
- Current source: [storage/chart_queries.py](/Users/devanshydv/Desktop/Astrology%20final%20boss/storage/chart_queries.py)

### `get_placement_of(chart_id, planet)`

- Input: chart id, planet name
- Output: house, sign, degree, nakshatra, pada, dignity

### `get_aspects_to(chart_id, planet)`

- Input: chart id, target planet
- Output: aspecting planet, aspect type, strength

### `get_conjunctions(chart_id, planet)`

- Input: chart id, planet
- Output: conjunct planets with orb and same-nakshatra flag

### `get_dispositor_chain(chart_id, planet)`

- Input: chart id, planet
- Output: dispositor chain with depth markers

## Fact Accumulation System

The fact object is implemented in [reasoning/models.py](/Users/devanshydv/Desktop/Astrology%20final%20boss/reasoning/models.py) as `ReasoningFact`.

Fields:

- `id`
- `type`
- `source_step`
- `entities_involved`
- `content`
- `strength_weight`
- `confidence`
- `supporting_rules`
- `contradictions`

Fact combination rules used now:

- additive weighting through `rank_score`
- confidence blending through `_compute_confidence`
- contradiction capture through `contradictions`
- traceability through `reasoning_tree`

## `interpret_house()` Algorithm

Implemented entry point: `HouseReasoner.analyze_house(chart_id, house)`

It returns:

- house metadata
- lord and lord placement
- classical supporting rules
- analogous rules
- structured facts
- contradictions
- confidence
- rank score
- reasoning chain
- reasoning tree
- novel synthesis output

## Cross-House Dependency Handler

Implemented in [reasoning/chart_reasoner.py](/Users/devanshydv/Desktop/Astrology%20final%20boss/reasoning/chart_reasoner.py).

Current behavior:

- builds a dependency map from each house to the house containing its lord
- computes traversal order
- detects cycles
- exposes cycle data in `dependency_resolution`

Current limitation:

- it detects cycles but does not yet run a special two-pass enrichment for mutual reception

## Novel Combination Synthesis

Implemented in [reasoning/novel_synthesizer.py](/Users/devanshydv/Desktop/Astrology%20final%20boss/reasoning/novel_synthesizer.py).

Current logic:

- combine planet nature and karakatvas
- combine house meaning and purushartha
- add aspect/conjunction/occupant modifiers
- search analogous rules from Neo4j
- assign `high`, `medium`, or `low` confidence band

### Ten Worked Example Patterns

1. Mercury in 8th, Jupiter aspect, Ketu conjunction
   Result: research, occult study, analytical depth, spiritualized intellect
2. Saturn ruling 10th in 3rd
   Result: career through effort, skill-building, writing, repetition, discipline
3. Venus ruling 7th in 11th with Jupiter aspect
   Result: gains through partnership, socially supported marriage
4. Mars in 4th aspecting 7th
   Result: intense domestic energy affecting relationship dynamics
5. Moon ruling 4th in 12th with Ketu
   Result: inward emotional life, private home karma, retreat themes
6. Sun ruling 5th in 10th with Mercury
   Result: visible intelligence, leadership through expression or teaching
7. Jupiter ruling 9th in 6th
   Result: dharma expressed through service, teaching in practical settings
8. Rahu in 11th with Saturn aspect
   Result: unconventional gains, delayed but scalable networks
9. Ketu in 5th with Mercury aspect
   Result: abstract intelligence, detached creativity, mantra or symbolic thinking
10. Venus in 2nd with Mars conjunction
   Result: wealth mixed with appetite, aesthetics plus forceful speech

## Full Chart Orchestration

Implemented entry point:

- [pipeline/analyze_chart.py](/Users/devanshydv/Desktop/Astrology%20final%20boss/pipeline/analyze_chart.py)

Core outputs:

- 12 house analyses
- dependency map
- dependency order and cycle list
- ranked interpretations
- dominant patterns
- life theme reports
- chart fingerprint

## Reasoning Tree Structure

Implemented as `ReasoningNode` and `SupportingFact` in [reasoning/models.py](/Users/devanshydv/Desktop/Astrology%20final%20boss/reasoning/models.py).

Structure:

- root statement
- supporting facts
- applied classical rules
- novel-synthesis flag
- child nodes for sub-facts

## Ranking System

Implemented in `ChartReasoner._rank_interpretations`.

Weights:

- strength/rank score: 40%
- confidence: 30%
- focus relevance: 20%
- cross verification: 10%

Output tiers:

- `tier_1`
- `tier_2`
- `tier_3`

## Test Library

Implemented in [reasoning/test_chart_library.json](/Users/devanshydv/Desktop/Astrology%20final%20boss/reasoning/test_chart_library.json).

Current coverage:

- 20 documented chart cases
- expected rule ids
- expected contradiction houses
- novel-review placeholders

## Quality Metrics

Implemented in [reasoning/validation.py](/Users/devanshydv/Desktop/Astrology%20final%20boss/reasoning/validation.py).

Metrics:

- reasoning chain completeness
- classical rule coverage
- contradiction handling
- novel synthesis quality
- response time
- ranked output count

## Validation Runner

Implemented in [pipeline/validate_phase5.py](/Users/devanshydv/Desktop/Astrology%20final%20boss/pipeline/validate_phase5.py).

This runs the test library through the full-chart analyzer and returns aggregate metrics.
