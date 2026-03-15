import pdfplumber
import tiktoken
import json
import os
import re
from .config import (
    BOOK_NAME, CHUNK_TOKENS, OVERLAP_TOKENS, 
    MAX_PAGES, INPUT_DIR, CHUNKS_FILE
)

def chunk_pdf(*args, **kwargs):
    """Dummy for pipeline compatibility."""
    return []

def extract_pages(pdf_path, max_pages=None):
    """Extracts raw text and page numbers from PDF."""
    pages = []
    print(f"Opening PDF: {pdf_path}")
    with pdfplumber.open(pdf_path) as pdf:
        pages_to_extract = pdf.pages
        if max_pages:
            pages_to_extract = pages_to_extract[:max_pages]
            print(f"Limiting to first {max_pages} pages.")
            
        for i, page in enumerate(pages_to_extract):
            text = page.extract_text()
            if text:
                pages.append({
                    "page_num": i + 1,
                    "text": text
                })
    return pages

def chunk_text(pages, chunk_tokens=CHUNK_TOKENS, overlap_tokens=OVERLAP_TOKENS, book_name=BOOK_NAME):
    """Chunks text into token-sized pieces with overlap and metadata."""
    encoding = tiktoken.get_encoding("cl100k_base")
    chunks = []
    
    # Combine all text with page delimiters to track source
    full_text_with_meta = []
    for p in pages:
        full_text_with_meta.append((p["page_num"], p["text"]))
    
    all_tokens = []
    token_to_page = []
    
    print("Tokenizing text and mapping to pages...")
    current_chapter = "General"
    
    for page_num, text in full_text_with_meta:
        chapter_match = re.search(r'(?i)(Chapter\s+\d+|CHAPTER\s+[IVXLCDM]+|CHAPTER\s+\d+)', text)
        if chapter_match:
            current_chapter = chapter_match.group(0)
            
        page_tokens = encoding.encode(text + "\n")
        all_tokens.extend(page_tokens)
        token_to_page.extend([(page_num, current_chapter)] * len(page_tokens))

    print(f"Total tokens: {len(all_tokens)}")
    
    # Create chunks
    step = chunk_tokens - overlap_tokens
    for i in range(0, len(all_tokens), step):
        chunk_token_slice = all_tokens[i : i + chunk_tokens]
        if not chunk_token_slice:
            break
            
        chunk_text = encoding.decode(chunk_token_slice)
        
        # Get metadata from the mapped tokens
        slice_meta = token_to_page[i : i + chunk_tokens]
        page_start = slice_meta[0][0]
        page_end = slice_meta[-1][0]
        chapter = slice_meta[0][1] 
        
        chunk_id = f"{book_name}_{len(chunks) + 1:03d}"
        
        chunks.append({
            "chunk_id": chunk_id,
            "page_start": page_start,
            "page_end": page_end,
            "chapter": chapter,
            "token_count": len(chunk_token_slice),
            "text": chunk_text
        })
        
        if len(chunk_token_slice) < chunk_tokens and i > 0:
            break
            
    return chunks

def run_chunking():
    pdf_path = INPUT_DIR / f"{BOOK_NAME}.pdf"
    
    if not pdf_path.exists():
        pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]
        if pdf_files:
            pdf_path = INPUT_DIR / pdf_files[0]
            print(f"Auto-detected PDF: {pdf_path}")
        else:
            print(f"Error: No PDF found in {INPUT_DIR}")
            return False

    pages = extract_pages(pdf_path, MAX_PAGES)
    if not pages:
        print("Error: No text extracted from PDF.")
        return False
        
    chunks = chunk_text(pages)
    
    with open(CHUNKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=2)
        
    print(f"\nSummary:")
    print(f"Total Pages:   {len(pages)}")
    print(f"Total Chunks:  {len(chunks)}")
    if chunks:
        avg_tokens = sum(c['token_count'] for c in chunks) / len(chunks)
        print(f"Avg Tokens:    {avg_tokens:.1f}")
    print(f"Output saved to: {CHUNKS_FILE}")
    return True
