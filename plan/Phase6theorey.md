Here's a super detailed theoretical roadmap for Phase 6 — Planetary Strength Scoring. This is one of the most mathematically precise phases in the entire project, and getting it right underpins every interpretation the system will ever produce.

---

## Phase 6: Planetary Strength Scoring
### Weeks 25–26 | Core Deliverable: `strength_scorer.py`

---

### Why This Phase Exists

Before Phase 6, the reasoning engine can identify *what* a planet represents (Mars = action, courage) and *where* it sits (10th house = career). But it has no answer to *how strongly* that combination manifests. A debilitated Mars in the 10th house and an exalted Mars in the 10th house both "mean" career through action — but they produce radically different life outcomes. Strength scoring is the numerical layer that makes this distinction computable.

Without it, every interpretation has the same weight. With it, the system can say "this promise is strong, this one is compromised, this one is cancelled entirely."

------

### The Five Scoring Components

The strength score for any planet is the weighted sum of five independent components, each computed separately and then aggregated. Here's how each one works theoretically.

---

#### Component 1 — Dignity Score (Weight: 40%)

This is the single highest-weighted component because a planet's dignity determines whether it can *express its nature freely or is constrained*. The modifier table is adapted from classical Shadbala and your project documents:**Key design decision for Phase 6:** The system must distinguish between whole-sign exaltation (+5) and the *exact peak degree* (+5 with an additional 0.5 bonus). Sun's peak degree is 10° Aries, Moon's is 3° Taurus, etc. This is a subtle but classical distinction — a planet at its peak degree gets the highest possible dignity score.

**Neecha Bhanga (Debilitation Cancellation):** The system must implement this classical rule — debilitation can be cancelled when specific conditions are met (the dispositor of the debilitated planet is in kendra from the Lagna or Moon, or the exaltation sign lord is in kendra). When cancellation fires, the score penalty is *reversed* to a moderate positive, representing the classical teaching that cancelled debilitation often produces outstanding results through initial struggle.

---

#### Component 2 — House Position Score (Weight: 25%)

Where a planet sits determines how easily it can *act* in the world. Kendras and trikonas amplify; dusthanas suppress.**Critical nuance — planet-specific house dignity (Dig Bala):** Certain planets have directional strength in specific houses regardless of the above: Jupiter and Mercury gain Dig Bala in the 1st house, the Sun and Mars in the 10th, Saturn in the 7th, Venus and Moon in the 4th. This adds an additional +1 modifier and must be computed as a sub-step within the house position component.

---

#### Component 3 — Aspect Score (Weight: 20%)

Every planet modifying another planet through aspect either *adds to* or *subtracts from* the target's effective strength. The system must implement Jyotish-specific aspect rules, which differ significantly from Western astrology.

The theoretical model here is a *running aspect tally* computed per planet:

1. Identify all planets aspecting the target planet (both sign-based aspects and the special Mars/Jupiter/Saturn aspects)
2. Classify each aspecting planet as benefic, malefic, or functional (depends on lagna)
3. Apply modifier: natural benefics (Jupiter, Venus, waxing Moon, unafflicted Mercury) = +1 per aspect; natural malefics (Saturn, Mars, Rahu, Ketu, Sun) = −1 per aspect; mutual aspects between same-nature planets get halved
4. Apply aspect strength: full aspect = 100%, partial = 75%, weak = 50%
5. Cap total aspect contribution at ±3 so no single planet can fully dominate the score

**Functional vs natural benefics/malefics:** This is where Phase 6 gains real depth. Whether a planet is beneficial *for a specific chart* depends on which houses it rules for that lagna. Saturn ruling the 1st and 2nd for Capricorn lagna is a functional benefic. Saturn ruling the 8th for Gemini lagna is a functional malefic. The system must use the lagna to dynamically assign functional roles, then apply those to the aspect scoring.

---

#### Component 4 — Special States (Weight: 10%)

These are binary or near-binary conditions that apply strong overrides:

**Combustion:** A planet within 6° of the Sun loses independence — its significations are "burnt" by solar heat. Score modifier: −3 (severe). Exception: the Moon is exempt, and a combust planet in own sign or exaltation has the penalty reduced to −1.5.

**Retrograde:** The theoretical model here is nuanced. Classical astrology holds that retrograde planets are in some ways *stronger* (they appear brighter and closer to Earth), but their significations manifest with delay, reversal, or internalization. The score modifier should therefore be +0.5 to the raw score but with a flag `is_retrograde: true` passed to the interpretation layer. The interpretation layer uses this flag to add qualifying language ("results come with delay" or "through revisiting").

**Planetary war (Graha Yuddha):** When two planets are within 1° of each other, the one with lower ecliptic latitude "loses." The loser gets −2 and the winner gets +0.5. This is a rare event but must be computed.

**Gandanta degrees:** Planets at the junction degrees between water and fire signs (Pisces/Aries, Cancer/Leo, Scorpio/Sagittarius) are at a conceptual "knot" — −1 modifier.

---

#### Component 5 — Dispositor Strength (Weight: 5%)

Every planet sits in a sign that is *ruled by* another planet (its dispositor). If that dispositor is strong, the tenant planet benefits. If the dispositor is debilitated or combust, the tenant is weakened regardless of its own dignity. The theoretical model:

- Compute dispositor's score *first* (without this component, to avoid circularity)
- Map dispositor score to a multiplier: 0–3 → −0.5, 3–5 → 0, 5–7 → +0.3, 7–10 → +0.5
- Apply as the final additive term

This creates a natural dependency chain: a strong Jupiter in Sagittarius improves every planet in Sagittarius. A debilitated Saturn in Aries reduces every planet in Aries. The knowledge graph already stores these relationships, making this a straightforward traversal.

---

### The Aggregation Formula

With all five components computed, the final score is:

```python
raw_score = (
    5.0                             # base neutral
    + dignity_score     * 0.40     # ±5 → weighted contribution up to ±2.0
    + house_score       * 0.25     # ±2.5 → up to ±0.625
    + aspect_score      * 0.20     # ±3 → up to ±0.6
    + special_state_mod * 0.10     # ±3 → up to ±0.3
    + dispositor_mod    * 0.05     # ±0.5 → up to ±0.025
)
final_score = max(0.0, min(10.0, raw_score))
```

The base of 5.0 places a planet in "neutral territory" before any modifiers apply. The weights ensure dignity dominates while aspects and position add meaningful but secondary colour.

---

### The `strength_scorer.py` File Structure

The implementation is a single, well-contained module. Here is the complete theoretical structure you'll hand to the Reasoning Agent:The public interface is `score_planet()`, which returns a `PlanetStrength` dataclass containing: the raw score (float), the final clamped score (float), the band classification (string), each component's individual contribution (for explainability), any special flags (`is_combust`, `is_retrograde`, `neecha_bhanga_active`), and the complete breakdown formatted for the reasoning tree.

---

### Week 25 Tasks (Build & Unit Test)

**Day 1–2:** Build the data structures. Define the `PlanetStrength` dataclass and the static lookup tables — dignity tables per planet (exaltation sign + degree, debilitation sign + degree, own signs, moolatrikona ranges), friendship tables (permanent, temporary, combined), and house classification tables. These all come from the ontology JSON files already created in Phase 1, so this is wiring existing data, not inventing new data.

**Day 3:** Implement `compute_dignity_score()`. Test against a minimum of 27 known combinations (9 planets × 3 dignity states each as a minimum). This function must handle the moolatrikona range check — a simple degree range comparison — and the peak degree bonus.

**Day 4:** Implement `compute_house_score()` including Dig Bala logic. Test with all 9 planets placed in all 12 houses (108 test cases). This is purely table-driven so it should be fast to build.

**Day 5:** Implement `check_neecha_bhanga()`. This is the most logically complex helper — it requires checking multiple cancellation conditions against the full chart structure. Build and test with at least 10 known neecha bhanga cases from classical literature (e.g. Vargottama debilitated planet, exaltation lord in kendra).

### Week 26 Tasks (Aspects, Integration & Validation)

**Day 1–2:** Implement `compute_aspect_score()` and `get_functional_nature()`. The functional nature lookup requires building a lagna-specific benefic/malefic table — all 12 lagnas × 9 planets = 108 assignments. Source these from BPHS rules already extracted in Phase 2–3. Test aspect scoring on 20 charts with manually verified expected outcomes.

**Day 3:** Implement `compute_special_states()` — combustion check (degree distance from Sun), retrograde flag, planetary war check, and Gandanta detection. Test each condition independently.

**Day 4:** Integrate everything into `score_planet()`. Run the full scoring on 100 test charts. Compare score bands against expected assessments from classical texts and consult any professional software output you can access for verification.

**Day 5:** Integration test — pass scored charts to a mock reasoning engine stub and confirm the scores modulate interpretation language correctly. Document edge cases (e.g. a planet that is simultaneously exalted, combust, and in a trik house — the system should resolve these in priority order without crashing). Write the handoff documentation for the Reasoning Agent.

---

### Success Criteria for Phase 6

Every criterion maps to a specific test:

1. All 9 planets scored for 100 test charts without errors or exceptions
2. Score bands align with expert assessment in 90%+ of test cases — a planet any practitioner would call "strong" must score above 7, one they'd call "weak" must score below 4
3. Neecha Bhanga correctly identified in all 10 classical test cases
4. Combust planets always score lower than their non-combust counterparts in identical charts
5. The `PlanetStrength` dataclass always contains a complete breakdown (no None fields in the component scores)
6. Scoring runtime under 10ms per planet on local hardware
7. Orchestrator reviews 10 sample score outputs and approves the breakdown as architecturally compliant and interpretively sensible

---

### What Phase 6 Unlocks

Once the strength scorer is complete and tested, every downstream phase becomes quantitatively grounded. Phase 7's yoga detection gains the ability to compute *yoga strength* as the combined score of the planets forming it. Phase 8's propagation algorithm uses strength scores as the edge weights in the network graph. Phase 9's temporal engine uses strength to determine how powerfully a dasha period activates its natal promise. And the interpretation layer gains the language modulation it needs — "strongly placed" vs "compromised placement" vs "severely weakened" — backed by actual numbers rather than qualitative guesses.

This is the phase that transforms the system from a *pattern matcher* into a *quantitative reasoner*.