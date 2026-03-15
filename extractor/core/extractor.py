import os
import json
import asyncio
import time
import sys
import re
from pathlib import Path
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# Add project root to path for normaliser
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import (
    GEMINI_API_KEY, MODELS, BOOK_NAME, CHUNK_TOKENS, 
    CONCURRENCY, RETRY_DELAY, CHUNKS_FILE, RAW_DIR
)
from normaliser.normaliser import AstrologyNormaliser

# Initialize Normaliser
NORMALISER = AstrologyNormaliser()

# Prompt Templates for Astrology Rules
SYSTEM_PROMPT = """You are a structured knowledge extraction engine specializing in classical Vedic astrology (Jyotish). Your job is to extract every piece of astrological knowledge from the provided text chunk and return it as a JSON array of structured objects. You are NOT a chatbot. You do NOT summarize or explain. You extract.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Return ONLY a valid JSON array. No preamble. No explanation. No markdown. No code fences.
If the chunk contains no extractable astrological knowledge, return an empty array: []

Each element in the array must be a JSON object with a "type" field that determines its schema (see formats below).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENTITY NAMING RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Do NOT normalize entity names yourself. Preserve the exact name as it appears in the text (e.g. "Surya", "Kuja", "Lagna", "Mesha", "Guru"). A separate normalizer will map these to canonical forms. Your job is accurate extraction, not normalization.

If you encounter an entity name you cannot confidently identify as a planet, sign, house, nakshatra, or yoga — add it to the entity_flags array in that object with the note "unknown — needs review". Do not invent a mapping.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SOURCE TEXT REQUIREMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Every extracted object MUST include a "source_text" field containing the verbatim sentence(s) from the input that the extraction is based on. This is mandatory for validation and traceability. Do not paraphrase. Do not truncate if the statement is a continuous claim.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THE 8 EXTRACTION FORMATS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

--- FORMAT A: CONDITIONAL RULE ---
Use when the text states a cause-effect or if-then prediction.
Example: "Mars in the 10th house gives a person military fame."

{
  "type": "rule",
  "condition": {
    "planets": ["Mars"],
    "houses": ["10th"],
    "signs": [],
    "nakshatras": [],
    "aspects": [],
    "dignity": null,
    "additional": ""
  },
  "result": "military fame",
  "result_domain": "career",
  "intensity": "high",
  "probability": "likely",
  "timing": null,
  "modifiers": {
    "enhancers": [],
    "reducers": []
  },
  "confidence": 0.85,
  "source_text": "Mars in the 10th house gives a person military fame.",
  "entity_flags": []
}

Allowed values:
- result_domain: career, wealth, marriage, health, children, education, spirituality, longevity, personality, family, travel, enemies, losses, general
- intensity: low, moderate, high, very_high
- probability: possible, likely, very_likely, certain
- confidence: 0.0–1.0 (use lower values when the text is ambiguous or conditional on unstated factors)

--- FORMAT B: ENTITY DESCRIPTION ---
Use when the text defines or describes the inherent nature of a planet, sign, house, or nakshatra (not a predictive rule).
Example: "Saturn is the planet of discipline, karma, and delay."

{
  "type": "description",
  "entity_type": "planet",
  "entity_name": "Saturn",
  "aspect": "nature",
  "description": "discipline, karma, delay, longevity, service, restriction",
  "confidence": 0.9,
  "source_text": "Saturn is the planet of discipline, karma, and delay.",
  "entity_flags": []
}

Allowed entity_type values: planet, sign, house, nakshatra, yoga, aspect_type, dignity_type
Allowed aspect values: nature, significations, physical_appearance, health, relationships, element, modality, direction, deity, symbol

--- FORMAT C: CALCULATION OR PROCEDURE ---
Use when the text describes a step-by-step method, formula, or computational procedure.
Example: "To compute Shadbala, first determine the positional strength..."

{
  "type": "calculation",
  "name": "Shadbala",
  "purpose": "Numerical planetary strength scoring",
  "steps": [
    "Determine positional strength from sign placement",
    "Determine temporal strength from day/night and planetary age",
    "Determine directional strength based on kendra placement",
    "Sum all components for total Shadbala score"
  ],
  "output_type": "numerical_score",
  "input_required": ["birth_chart", "planet"],
  "confidence": 0.9,
  "source_text": "To compute Shadbala, first determine the positional strength...",
  "entity_flags": []
}

--- FORMAT D: CULTURAL OR MYTHOLOGICAL CONTEXT ---
Use when the text provides mythological, symbolic, or philosophical background that informs astrological meaning (not a direct rule).

{
  "type": "context",
  "subject": "Mars",
  "context_type": "mythology",
  "content": "Mars (Mangala) is born from the Earth and associated with Skanda, the god of war, explaining his martial and fiery nature.",
  "relevance": "Explains Mars's role as significator of courage and conflict.",
  "confidence": 0.75,
  "source_text": "...",
  "entity_flags": []
}

Allowed context_type: mythology, symbolism, philosophy, historical, etymology

--- FORMAT E: CASE STUDY OR EXAMPLE CHART ---
Use when the text presents a real or illustrative birth chart example with interpretations.

{
  "type": "case_study",
  "chart_description": "A person with Jupiter in the 1st house aspected by Venus",
  "placements": [
    {"planet": "Jupiter", "house": "1st", "sign": null},
    {"planet": "Venus", "aspect_to_house": "1st"}
  ],
  "stated_outcomes": ["fame", "wealth", "good character"],
  "confidence": 0.7,
  "source_text": "...",
  "entity_flags": []
}

--- FORMAT F: SOURCE REFERENCE OR CITATION ---
Use when the text explicitly credits another classical text or scholar.

{
  "type": "reference",
  "citing_text": "Saravali",
  "cited_source": "Brihat Parashara Hora Shastra",
  "cited_chapter": "Chapter 24",
  "context": "Saravali cites BPHS on the topic of planetary dignities.",
  "source_text": "...",
  "entity_flags": []
}

--- FORMAT G: CONTRADICTION OR DISSENT ---
Use when the text explicitly states that different authorities disagree on a rule, or that a rule has exceptions.

{
  "type": "contradiction",
  "topic": "Saturn in 7th house",
  "view_a": {
    "claim": "delays marriage",
    "source": "Brihat Jataka"
  },
  "view_b": {
    "claim": "gives a disciplined and dutiful spouse",
    "source": "Phaladeepika"
  },
  "resolution": null,
  "confidence": 0.65,
  "source_text": "...",
  "entity_flags": []
}

--- FORMAT H: YOGA (NAMED COMBINATION) ---
Use when the text defines or describes a named planetary combination (yoga) with its formation conditions and effects.
Example: "Gaja Kesari Yoga is formed when Jupiter is in a kendra from the Moon..."

{
  "type": "yoga",
  "name": "Gaja Kesari",
  "alternate_names": ["Gajakesari"],
  "yoga_type": "benefic",
  "formation_conditions": {
    "logic": "AND",
    "rules": [
      {"type": "placement", "planet": "Jupiter", "relative_to": "Moon", "positions": ["kendra", "1st", "4th", "7th", "10th"]},
      {"type": "exclusion", "planet": "Jupiter", "houses": ["6th", "8th", "12th"]}
    ]
  },
  "cancellation_conditions": [
    "Saturn or Rahu strongly aspecting Jupiter"
  ],
  "effects": {
    "primary": "wisdom, fame, benevolence, leadership",
    "secondary": "wealth, good reputation"
  },
  "strength_modifiers": {
    "enhancers": ["Jupiter strong in dignity", "Moon in good sign"],
    "reducers": ["Jupiter combust", "Jupiter debilitated"]
  },
  "classical_sources_mentioned": ["Brihat Parashara Hora Shastra", "Phaladeepika"],
  "confidence": 0.9,
  "source_text": "Gaja Kesari Yoga is formed when Jupiter is in a kendra from the Moon...",
  "entity_flags": []
}

Allowed yoga_type: benefic, raja_yoga, dhana_yoga, duryoga, neecha_bhanga, parivartana, other

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXTRACTION BEHAVIOR RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Extract EVERYTHING. Do not filter out rules that seem minor or obvious. Every extractable claim goes into the output.

2. One object per claim. If a single paragraph contains three distinct rules, output three Format A objects.

3. Never invent or infer beyond the text. If the text says "Mars in the 10th gives courage", do not add "therefore military success" unless the text also says that.

4. Preserve specificity. If the text says "Mars in the 10th in Aries", the condition must include sign: ["Aries"]. Do not generalize.

5. Partial extraction is better than skipping. If you can extract a condition but the result is vague, extract what you have and set confidence low.

6. Multi-condition rules: If a rule has multiple required conditions (e.g. planet + dignity + aspect), place ALL conditions in the condition block of a single Format A object, not as multiple separate rules.

7. Implicit negation: If the text says "if Jupiter is NOT in the 6th, 8th, or 12th house", capture this as a negative condition in additional: "Jupiter not in 6th, 8th, 12th house".

8. Degree-level precision: If the text specifies exact degrees (e.g. "Sun exalted at 10° Aries"), include this in the condition's additional field.

9. Relative placements: If the text says "Jupiter in kendra from Moon" (not from the ascendant), capture this as a relative placement, not an absolute house number.

10. Confidence calibration:
    - 0.9–1.0: Text is direct, specific, unambiguous
    - 0.7–0.89: Text is reasonably clear but uses hedging language ("may", "often", "generally")
    - 0.5–0.69: Text is ambiguous, metaphorical, or the context is unclear
    - Below 0.5: Highly uncertain — flag for human review

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT NOT TO EXTRACT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Table of contents, chapter headings, index entries, page numbers
- Dedications, prefaces, publisher information
- Pure transliteration tables with no astrological meaning
- Repeated content already stated verbatim in the same chunk
- Modern psychological reinterpretations clearly framed as the author's opinion rather than classical teaching (use Format D context type if borderline)
"""

USER_PROMPT_TEMPLATE = """Extract all astrological rules from this text:

book_id: {book_id}
chunk_id: {chunk_id}
chapter_hint: {chapter_hint}
overlap_note: {overlap_note}

{chunk_text}"""

class GeminiRotator:
    def __init__(self):
        self.models = MODELS
        self.current_idx = 0
        self.model = self._setup_current_model()

    def _setup_current_model(self):
        model_name = self.models[self.current_idx]
        print(f"Switching to model: {model_name}")
        genai.configure(api_key=GEMINI_API_KEY)
        return genai.GenerativeModel(model_name, system_instruction=SYSTEM_PROMPT)

    def rotate(self):
        self.current_idx = (self.current_idx + 1) % len(self.models)
        self.model = self._setup_current_model()
        return self.model

ROTATOR = None

def setup_gemini():
    global ROTATOR
    if GEMINI_API_KEY == "your-key-here" or not GEMINI_API_KEY:
        print("Error: Please set GEMINI_API_KEY in .env or config.py")
        return None
    ROTATOR = GeminiRotator()
    return ROTATOR.model

def normalize_extracted_item(item):
    """Normalize entities in an extracted item using AstrologyNormaliser."""
    if item.get("type") == "rule" and "condition" in item:
        cond = item["condition"]
        for field in ["planets", "houses", "signs", "nakshatras"]:
            if field in cond and isinstance(cond[field], list):
                cond[field] = [NORMALISER.normalise(v) or v for v in cond[field]]
    
    elif item.get("type") == "description":
        if "entity_name" in item:
            item["entity_name"] = NORMALISER.normalise(item["entity_name"]) or item["entity_name"]
            
    # Add normalization metadata
    item["normalized"] = True
    return item

async def extract_from_chunk(chunk, retry_count=0):
    global ROTATOR
    chunk_id = chunk['chunk_id']
    text = chunk['text']
    
    try:
        response = await ROTATOR.model.generate_content_async(
            USER_PROMPT_TEMPLATE.format(
                book_id=BOOK_NAME,
                chunk_id=chunk_id,
                chapter_hint=chunk.get('chapter', 'General'),
                overlap_note="mid_chunk",
                chunk_text=text
            )
        )
        
        resp_text = response.text.strip()
        # Clean response text (remove markdown if model ignores instruction)
        if resp_text.startswith("```json"):
            resp_text = resp_text.split("```json")[1].split("```")[0].strip()
        elif resp_text.startswith("```"):
            resp_text = resp_text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(resp_text)
        
        # Apply Normalization
        normalized_data = []
        if isinstance(data, list):
            for item in data:
                normalized_item = normalize_extracted_item(item)
                normalized_data.append(normalized_item)
        else:
            # Fallback for single object instead of list
            normalized_data = [normalize_extracted_item(data)]
        
        return {"chunk_id": chunk_id, "data": normalized_data, "success": True}

    except google_exceptions.ResourceExhausted:
        if retry_count < len(MODELS):
            print(f"Quota exhausted for {ROTATOR.models[ROTATOR.current_idx]}. Rotating...")
            ROTATOR.rotate()
            return await extract_from_chunk(chunk, retry_count + 1)
        else:
            print(f"All models exhausted for {chunk_id}")
            return {"chunk_id": chunk_id, "error": "All models exhausted", "success": False}
            
    except Exception as e:
        if retry_count < 2:
            print(f"Error on {chunk_id}, retrying in {RETRY_DELAY}s... ({e})")
            await asyncio.sleep(RETRY_DELAY)
            return await extract_from_chunk(chunk, retry_count + 1)
        else:
            print(f"Failed {chunk_id} after retries: {e}")
            return {"chunk_id": chunk_id, "error": str(e), "success": False}

async def process_batch(chunks):
    tasks = [extract_from_chunk(chunk) for chunk in chunks]
    return await asyncio.gather(*tasks)

async def run_extraction(limit=None):
    if not CHUNKS_FILE.exists():
        print(f"Error: {CHUNKS_FILE} not found. Run chunking first.")
        return False

    with open(CHUNKS_FILE, 'r') as f:
        chunks = json.load(f)

    if limit:
        chunks = chunks[:limit]
        print(f"Limiting extraction to first {limit} chunks for testing.")

    if not setup_gemini(): return False

    total = len(chunks)
    success_count = 0
    fail_count = 0
    start_time = time.time()

    print(f"Starting extraction for {total} chunks with concurrency {CONCURRENCY}...")

    for i in range(0, total, CONCURRENCY):
        batch = chunks[i : i + CONCURRENCY]
        print(f"Processing batch {i//CONCURRENCY + 1}/{(total + CONCURRENCY - 1)//CONCURRENCY}...")
        
        results = await process_batch(batch)
        
        for res in results:
            chunk_id = res['chunk_id']
            output_file = RAW_DIR / f"{BOOK_NAME}_{chunk_id}.json"
            
            # Skip if already exists and was successful
            if output_file.exists():
                try:
                    with open(output_file, 'r') as f:
                        existing_data = json.load(f)
                        if "error" not in existing_data:
                            print(f"Skipping already processed chunk: {chunk_id}")
                            success_count += 1
                            continue
                except:
                    pass

            with open(output_file, 'w') as f:
                if res['success']:
                    json.dump(res['data'], f, indent=2)
                    success_count += 1
                else:
                    json.dump({"error": res['error']}, f, indent=2)
                    fail_count += 1
        
        # Rate limit delay between batches
        if i + CONCURRENCY < total:
            await asyncio.sleep(5)

    elapsed = time.time() - start_time
    print(f"\nExtraction Complete!")
    print(f"Total Chunks: {total}")
    print(f"Successful:   {success_count}")
    print(f"Failed:       {fail_count}")
    print(f"Time Taken:   {elapsed:.1f}s")
    
    avg_input_tokens = CHUNK_TOKENS
    avg_output_tokens = 300 # Estimated avg output per chunk
    
    est_cost = (total * avg_input_tokens / 1_000_000 * 0.075) + (total * avg_output_tokens / 1_000_000 * 0.30)
    print(f"Estimated Gemini Cost: ${est_cost:.6f}")
    return True
