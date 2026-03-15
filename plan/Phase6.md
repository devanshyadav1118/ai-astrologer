# Phase 6: Strength Engine - Roadmap

**Goal:** Implement a sophisticated planetary strength calculation engine (Shadbala-lite or Vimsopaka) to provide the **Phase 5 Reasoning Engine** with accurate `strength_weight` values for each planet. This will replace the current hardcoded dignity-based modifiers.

## 🎯 Phase 6 Deliverables

1. **`chart/strength_engine.py`**: A new component that calculates multiple strength factors.
2. **Updated `ChartGraphIngestor`**: To store the granular strength scores in Neo4j.
3. **Updated `HouseReasoner`**: To use the new scores for fact-weighting.
4. **Validation Test Case**: Verifying that a strong planet results in a more confident interpretation.

## 📅 Task Breakdown

### **1. Core Strength Factors (Implementation)**
We will implement the following strength components:

- **Sthana Bala (Positional Strength)**:
  - Exaltation/Debilitation (already partially there, but need degrees)
  - Saptavargiya (Dignity in divisional charts - *Optional for now, but good to plan*)
  - House placement (Kendra/Trikona/Dusthana)
- **Dig Bala (Directional Strength)**:
  - Jupiter/Mercury strong in 1st house
  - Sun/Mars strong in 10th house
  - Saturn strong in 7th house
  - Moon/Venus strong in 4th house
- **Drig Bala (Aspectual Strength)**:
  - Benefic vs Malefic aspects influencing the planet's power.
- **Chesta Bala (Motional Strength)**:
  - Retrograde status modifiers.
- **Naisargika Bala (Natural Strength)**:
  - Standard hierarchy: Sun > Moon > Venus > Jupiter > Mercury > Mars > Saturn.

### **2. Integration**

- **`ChartGraphIngestor` Updates**:
  - Add `sthana_bala`, `dig_bala`, `drig_bala`, etc., as properties on `ChartPlanet` nodes.
  - Compute a unified `total_strength` (0.0 to 1.0 or 0.0 to 10.0).
- **`HouseReasoner` Updates**:
  - Instead of just `lord_strength`, use the weighted `total_strength` for all planets involved in the house analysis.

---

## 🚀 Why This Matters
A "weak" planet in a "good" house produces a different result than a "strong" planet. Currently, the system treat all "Sun in Aries" cases the same. Phase 6 will allow the system to say: *"Even though Sun is exalted, its low Dig Bala and malefic aspects make it struggle to deliver its full potential."*
