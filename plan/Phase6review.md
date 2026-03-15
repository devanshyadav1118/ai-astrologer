This is a solid, grounded plan — you've clearly been building from the actual codebase rather than theorizing. Here's an honest assessment of what's strong, what's missing, and what needs rethinking.

---

**What's genuinely good:**

The component selection is correct and the integration targets (`ChartGraphIngestor`, `HouseReasoner`) show you're thinking architecturally rather than just building a standalone calculator. The "Why This Matters" section is exactly the right framing — grounding it in a concrete example ("Sun in Aries, low Dig Bala") means you'll know when the system is actually working.

Sthana Bala + Dig Bala + Drig Bala + Chesta Bala + Naisargika Bala is the correct classical five-component structure.

---

**What's missing that will hurt you later:**

**1. No Neecha Bhanga logic.** This is the single most important omission. A debilitated planet with cancellation conditions is actually *stronger* than a neutral planet in classical teaching. If you skip this, you'll produce systematically wrong results for a significant percentage of charts — and the errors will be subtle and hard to catch because the score will look "reasonable" without the cancellation.

**2. No combustion handling.** A planet within 6° of the Sun loses independent function. This is separate from Drig Bala and needs its own check. It's computationally trivial but conceptually critical.

**3. Naisargika Bala is too simplified.** The standard hierarchy (Sun > Moon > Venus > Jupiter > Mercury > Mars > Saturn) is correct, but it should be a small additive modifier (+0.5 to +0 scaled across the 7 planets), not a dominant factor. Right now it's listed as a flat peer to Sthana Bala, which would overweight it. Natural strength matters less than positional strength in practice.

**4. No weight distribution between components.** Your plan lists five components but doesn't specify how they combine. This is the most important design decision in the entire phase. If Sthana Bala and Naisargika Bala have equal weight, a naturally strong Sun will score high even when debilitated — which is wrong. You need explicit weights before you write any aggregation code.

**5. Functional benefic/malefic is absent from Drig Bala.** "Benefic vs malefic aspects" needs to be lagna-relative, not just naturally benefic/malefic. Jupiter aspecting a planet is benefic for most lagnas but Jupiter is the 8th lord for Taurus lagna — its aspect on certain planets becomes functionally harmful. Without this, your aspect scoring will be systematically incorrect for roughly half the twelve lagnas.

---

**What needs rethinking:**

The `0.0 to 1.0 or 0.0 to 10.0` ambiguity in your integration section is a real problem — pick 0–10 now and commit. Every downstream system (Phase 7 yoga strength, Phase 8 propagation weights, Phase 9 dasha effectiveness) will consume this number. Changing the scale later means touching all of them.

"Saptavargiya — Optional for now" is fine as a deferral, but mark it explicitly as Phase 10 scope. If you leave it as "optional," it will never get built, and D9/D10 strength divergence from D1 is genuinely useful information.

---

**Suggested additions before you start coding:**

Add a sixth task to your breakdown: **Test Cases with Known Outcomes** — at minimum 20 charts where you already know what a practitioner would call "strong" or "weak" for specific planets. Without a validation dataset defined upfront, you'll build something that feels right but has no ground truth to test against.

Add explicit weight constants at the top of `strength_engine.py` as named variables, not magic numbers inside functions:

```python
WEIGHTS = {
    "sthana_bala":    0.40,
    "dig_bala":       0.15,
    "drig_bala":      0.20,
    "chesta_bala":    0.10,
    "naisargika_bala":0.05,
    "combustion":     0.10,   # override/penalty
}
```

This makes the scoring philosophy explicit and lets you tune it during validation without hunting through function internals.

---

**Overall verdict:** 75% of the way there. The structure is right, the integration targets are right, the component list is right. The gaps are Neecha Bhanga, combustion, explicit weighting, and lagna-relative aspect logic. Add those and this becomes a production-grade plan. Without them, the engine will produce plausible-looking but systematically incorrect scores for debilitated, combust, and functionally afflicted planets — exactly the edge cases where strength scoring matters most.