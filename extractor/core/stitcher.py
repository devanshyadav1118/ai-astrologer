import os
import json
from difflib import SequenceMatcher
from .config import RAW_DIR, BOOK_NAME, FINAL_FILE

def stitch_book_chunks(*args, **kwargs):
    """Dummy for pipeline compatibility."""
    return {}

def are_similar(a, b, threshold=0.85):
    """Checks if two strings are more than threshold% similar."""
    if not a or not b: return False
    return SequenceMatcher(None, str(a), str(b)).ratio() > threshold

def run_stitching():
    if not RAW_DIR.exists():
        print(f"Error: {RAW_DIR} not found. Run extraction first.")
        return False

    all_rules = []
    files = [f for f in os.listdir(RAW_DIR) if f.endswith('.json')]
    
    print(f"Loading {len(files)} extraction files...")
    for filename in sorted(files):
        parts = filename.replace('.json', '').split('_')
        if len(parts) >= 2:
            chunk_id = "_".join(parts[1:])
        else:
            chunk_id = parts[0]
        
        file_path = RAW_DIR / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for rule in data:
                        rule['book'] = BOOK_NAME
                        rule['chunk_id'] = chunk_id
                        all_rules.append(rule)
                elif isinstance(data, dict) and "error" in data:
                    print(f"Skipping failed chunk: {filename}")
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    print(f"Total raw rules: {len(all_rules)}")
    
    print("Deduplicating rules (fuzzy match > 85%)...")
    unique_rules = []
    dedup_count = 0
    
    for rule in all_rules:
        is_dup = False
        cond = rule.get('condition', '')
        res = rule.get('result', '')
        
        for existing in unique_rules:
            ex_cond = existing.get('condition', '')
            ex_res = existing.get('result', '')
            
            if are_similar(cond, ex_cond) and are_similar(res, ex_res):
                if len(str(rule.get('source_text', ''))) > len(str(existing.get('source_text', ''))):
                    existing.update(rule)
                
                is_dup = True
                dedup_count += 1
                break
        
        if not is_dup:
            unique_rules.append(rule)

    for i, rule in enumerate(unique_rules):
        rule['rule_id'] = f"{BOOK_NAME}_r{i+1:04d}"

    os.makedirs(FINAL_FILE.parent, exist_ok=True)
    with open(FINAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_rules, f, indent=2)

    print(f"\nStitching Complete!")
    print(f"Merged Rules:     {len(all_rules)}")
    print(f"Deduplicated:     {dedup_count}")
    print(f"Final Rule Count: {len(unique_rules)}")
    print(f"Output saved to:  {FINAL_FILE}")
    return True
