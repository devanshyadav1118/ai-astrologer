import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# List of models to rotate through if quota is hit
MODELS = ["gemini-flash-latest", "gemini-pro-latest", "gemini-2.0-flash"]
MODEL_NAME = MODELS[0]

# Book specific config - can be overridden via command line or env
BOOK_NAME = os.getenv("BOOK_NAME", "default_book")

# Chunking config
CHUNK_TOKENS = 800
OVERLAP_TOKENS = 100
MAX_PAGES = 10 # Process first 10 pages for test

# Concurrency config
CONCURRENCY = 5
RETRY_DELAY = 10

# Dynamic Paths
INPUT_DIR = DATA_DIR / "raw"
CHUNKS_DIR = DATA_DIR / "chunks"
CHUNKS_FILE = CHUNKS_DIR / f"{BOOK_NAME}_chunks.json"
RAW_DIR = DATA_DIR / "extracted" / BOOK_NAME / "raw"
FINAL_FILE = DATA_DIR / "extracted" / BOOK_NAME / f"{BOOK_NAME}_rules.json"
REPORT_FILE = DATA_DIR / "extracted" / BOOK_NAME / f"{BOOK_NAME}_report.txt"

# Ensure directories exist
for d in [INPUT_DIR, CHUNKS_DIR, RAW_DIR.parent, RAW_DIR]:
    d.mkdir(parents=True, exist_ok=True)
