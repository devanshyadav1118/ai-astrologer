#!/usr/bin/env python3
"""
Astrological PDF Chapter Processor
Extracts structured rules from astrology PDFs using Gemini Flash
"""

import fitz
import subprocess
import json
import os
from pathlib import Path
import logging
import argparse

from dotenv import load_dotenv

# === CONFIG ===
INPUT_PDF = Path("input/astrology_full_book.pdf")
OUTPUT_ROOT = Path("../output/")
CHAPTER_SIZE = 1  # pages per chunk (one page at a time)
MAX_CHAPTERS = 3  # safety limit
GEMINI_TIMEOUT = 180  # increased timeout for complex prompts
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-flash-lite-latest")
GEMINI_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", str(GEMINI_TIMEOUT)))
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PROMPT_TEMPLATE_PATH = Path("Prompt.txt")

def load_prompt_template():
    with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()

def format_prompt(pdf_text):
    template = load_prompt_template()
    # Replace the placeholder with the actual chunk text
    return template.replace("[Paste the full text from _Saravali_ or another source here.]", pdf_text)

def extract_chapter_text(doc, start_page, num_pages):
    text = ""
    for i in range(start_page, min(start_page + num_pages, len(doc))):
        text += doc.load_page(i).get_text()
    return text.strip()

def parse_json_from_text(text):
    """Extract JSON from text that may contain markdown or other formatting."""
    # Try to find JSON blocks
    import re
    json_patterns = [
        r'```json\s*\n(.*?)\n```',
        r'```\s*\n(.*?)\n```',
        r'\{.*\}',
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                data = json.loads(match)
                return data
            except json.JSONDecodeError:
                continue
    
    # If no JSON found, try to extract partial JSON
    try:
        # Look for the start of JSON
        start_idx = text.find('{')
        if start_idx != -1:
            # Try to find a balanced JSON object
            brace_count = 0
            end_idx = start_idx
            
            for i, char in enumerate(text[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                data = json.loads(json_str)
                return data
    except json.JSONDecodeError:
        pass
    
    return None

def run_gemini(prompt_text, output_path):
    try:
        logger.info(f"Processing {output_path.name}...")
        logger.info(f"Prompt length: {len(prompt_text)} characters")

        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if api_key:
            output = run_gemini_via_api(prompt_text, api_key)
            stderr_text = ""
        else:
            result = subprocess.run(
                ["gemini", "-m", GEMINI_MODEL, "-p", prompt_text],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=GEMINI_TIMEOUT,
                text=True
            )
            output = result.stdout.strip()
            stderr_text = result.stderr

        if not output:
            logger.error(f"Gemini returned no output for {output_path.name}. STDERR: {stderr_text}")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump({"error": "No output from Gemini", "stderr": stderr_text}, f, indent=2)
            return
        
        # Check if output looks like an error message or cached credentials
        if "Loaded cached credentials" in output or "cached" in output.lower():
            logger.error(f"Gemini returned cached credentials instead of processing. Output: {output[:200]}...")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump({
                    "error": "Gemini returned cached credentials instead of processing",
                    "raw_output": output,
                    "stderr": stderr_text
                }, f, indent=2)
            return
        
        logger.info(f"Gemini output length: {len(output)} characters")
        logger.info(f"First 200 chars of output: {output[:200]}...")
        
        # Try to parse JSON from the output
        parsed_data = parse_json_from_text(output)
        
        if parsed_data:
            # Save as JSON file
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Completed {output_path.name} (JSON saved)")
        else:
            # Save raw output as JSON with error info
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump({
                    "error": "Could not parse JSON from Gemini output",
                    "raw_output": output,
                    "stderr": stderr_text
                }, f, indent=2)
            logger.warning(f"⚠️ Could not parse JSON for {output_path.name}")
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ Timeout for {output_path.name} after {GEMINI_TIMEOUT}s")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"error": "Timeout", "timeout_seconds": GEMINI_TIMEOUT}, f, indent=2)
    except Exception as e:
        logger.error(f"❌ Error for {output_path.name}: {e}")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"error": str(e)}, f, indent=2)


def run_gemini_via_api(prompt_text, api_key):
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(prompt_text)
    return (getattr(response, "text", "") or "").strip()

def process_pdf(start_page=0, batch_size=1):
    doc = fitz.open(INPUT_PDF)
    total_pages = len(doc)
    logger.info(f"\U0001F4D8 Loaded PDF: {total_pages} pages")

    # Only process one batch starting from start_page
    if start_page >= total_pages:
        logger.warning(f"Start page {start_page} is beyond the end of the document.")
        return
    
    end_page = min(start_page + batch_size, total_pages)
    chapter_name = f"Pages_{start_page:02d}-{end_page-1:02d}"
    chapter_folder = OUTPUT_ROOT / chapter_name
    chapter_folder.mkdir(parents=True, exist_ok=True)

    logger.info(f"\u270D\ufe0f  Processing {chapter_name} (Pages {start_page}–{end_page-1})")
    chapter_text = extract_chapter_text(doc, start_page, batch_size)
    if not chapter_text.strip():
        logger.warning("\u26A0\ufe0f  Empty text, skipping...")
        return

    prompt = format_prompt(chapter_text)
    output_file = chapter_folder / "extracted_data.json"

    run_gemini(prompt, output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process PDF in batches.")
    parser.add_argument('--start-page', type=int, default=0, help='Page to start processing from (0-indexed)')
    parser.add_argument('--batch-size', type=int, default=1, help='Number of pages to process in this batch')
    args = parser.parse_args()
    process_pdf(start_page=args.start_page, batch_size=args.batch_size) 
