import asyncio
import argparse
import sys
import os
from pathlib import Path

async def main():
    parser = argparse.ArgumentParser(description="AI Astrologer: Knowledge Extraction Pipeline")
    parser.add_argument("action", choices=["all", "chunk", "extract", "stitch", "inspect"], 
                        help="Action to perform")
    parser.add_argument("--book", help="Name of the book (without .pdf extension)")
    parser.add_argument("--limit", type=int, help="Limit number of chunks to extract")
    
    args = parser.parse_args()

    if args.book:
        os.environ["BOOK_NAME"] = args.book

    # Add project root to path
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    # Import core modules AFTER setting environment variables
    from core.chunker import run_chunking
    from core.extractor import run_extraction
    from core.stitcher import run_stitching
    from core.inspector import run_inspection

    if args.action == "chunk":
        run_chunking()
    elif args.action == "extract":
        await run_extraction(limit=args.limit)
    elif args.action == "stitch":
        run_stitching()
    elif args.action == "inspect":
        run_inspection()
    elif args.action == "all":
        book_name = os.environ.get('BOOK_NAME', 'default')
        print(f"--- STARTING FULL PIPELINE FOR: {book_name} ---")
        print("\n--- PHASE 1: CHUNKING ---")
        if run_chunking():
            print("\n--- PHASE 2: EXTRACTION ---")
            if await run_extraction(limit=args.limit):
                print("\n--- PHASE 3: STITCHING ---")
                if run_stitching():
                    print("\n--- PHASE 4: INSPECTION ---")
                    run_inspection()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nPipeline error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
