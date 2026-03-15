# Phase 7: Yoga Detection Engine - Roadmap

**Goal:** Implement a pattern-matching engine that detects classical astrological combinations (Yogas) defined in `yogas.json` and integrates them into the Phase 5 reasoning chain.

## 🎯 Phase 7 Deliverables

1. **`reasoning/yoga_detector.py`**: The core engine that evaluates yoga conditions against chart data.
2. **Yoga Fact Generation**: Converting detected yogas into `ReasoningFact` objects for the `HouseReasoner`.
3. **Yoga Strength Analysis**: Applying Phase 6 strength scores to the participating planets to calculate the "Impact Score" of the yoga.
4. **Validation Test Suite**: Verifying detection of complex yogas like *Gaja Kesari*, *Pancha Mahapurusha*, and *Neecha Bhanga*.

## 📅 Task Breakdown

### **1. Pattern Matching Engine (Implementation)**
We need to handle the following condition types found in `yogas.json`:

- **Position-based**: `in_kendra_from`, `in_house_type`, `placed_in`, `adjacent_houses`.
- **Relationship-based**: `aspect_between`, `conjunction_between`, `mutual_reception_between`.
- **Lordship-based**: `trikona_lord`, `kendra_lord`, `HOUSE_X_lord`.
- **State-based**: `is_combust`, `retrograde`, `strong`, `debilitated`.
- **Nodal-based**: `all_planets_between_nodes` (Kala Sarpa).

### **2. Strength & Cancellation Logic**
- **Impact Score**: A yoga's final weight = `(Average Strength of Planets) * (Yoga Confidence)`.
- **Cancellation**: Automatically checking `cancellation_conditions` (e.g., Gaja Kesari cancelled by Saturn aspecting Jupiter).

### **3. Integration**
- **House Reasoning**: When analyzing the 10th house, the engine should automatically pull in any detected *Raja Yogas* or *Amala Yogas* affecting the 10th lord or 10th house.

---

## 🚀 Why This Matters
Yogas are the "high-level features" of Vedic astrology. While Phase 5 looks at individual placements, Phase 7 looks at the **Gestalt**. 

*Example:* Mars in 10th is good, but Mars in 10th in Capricorn (exalted) forming a **Ruchaka Yoga** is a completely different tier of power. Phase 7 allows the AI to recognize these "Royal Combinations" and prioritize them in the final interpretation.
