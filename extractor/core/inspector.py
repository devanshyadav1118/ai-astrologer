import json
import os
import random
from collections import Counter
from difflib import SequenceMatcher
from .config import FINAL_FILE, BOOK_NAME, REPORT_FILE

# Seed list for canonical entities
CANONICAL_ENTITIES = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
    "1st house", "2nd house", "3rd house", "4th house", "5th house", "6th house",
    "7th house", "8th house", "9th house", "10th house", "11th house", "12th house",
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

def fuzzy_match(name, canonical_list, threshold=0.8):
    """Checks if a name fuzzy matches any item in the canonical list."""
    if not name: return False
    name_str = str(name).lower()
    for canon in canonical_list:
        if SequenceMatcher(None, name_str, canon.lower()).ratio() > threshold:
            return True
    return False

def run_inspection():
    if not FINAL_FILE.exists():
        print(f"Error: {FINAL_FILE} not found. Run stitching first.")
        return False

    try:
        with open(FINAL_FILE, 'r', encoding='utf-8') as f:
            rules = json.load(f)
    except Exception as e:
        print(f"Error loading {FINAL_FILE}: {e}")
        return False

    print(f"Analyzing {len(rules)} rules...")
    
    types = [r.get('type', 'unknown') for r in rules]
    type_counts = Counter(types)
    
    all_entities = []
    for r in rules:
        # UPDATED: Extract from current schema (condition block)
        if r.get('type') == 'rule' and 'condition' in r:
            cond = r['condition']
            for field in ['planets', 'houses', 'signs', 'nakshatras']:
                vals = cond.get(field, [])
                if isinstance(vals, list):
                    all_entities.extend([str(v) for v in vals])
        elif r.get('type') == 'description':
            name = r.get('entity_name')
            if name: all_entities.append(str(name))
            
    entity_counts = Counter(all_entities)
    
    unknown_count = 0
    unique_entities = list(entity_counts.keys())
    for ent in unique_entities:
        if not fuzzy_match(ent, CANONICAL_ENTITIES):
            unknown_count += entity_counts[ent] 
            
    total_entity_appearances = len(all_entities)
    unknown_rate = (unknown_count / total_entity_appearances * 100) if total_entity_appearances > 0 else 0
    
    report = []
    report.append("="*60)
    report.append(f"EXTRACTION QUALITY REPORT: {BOOK_NAME.upper()}")
    report.append("="*60)
    report.append(f"\nTotal Rules Extracted: {len(rules)}")
    report.append("\nBreakdown by Type:")
    for t, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        report.append(f"  - {t:15}: {count}")
        
    report.append(f"\nUnknown Entity Rate: {unknown_rate:.1f}%")
    report.append(f"  (Matched against {len(CANONICAL_ENTITIES)} canonical terms)")
    
    report.append("\nTop 50 Entities Found:")
    for ent, count in entity_counts.most_common(50):
        report.append(f"  - {ent:30}: {count}")
        
    report.append("\n" + "="*60)
    report.append("10 RANDOM SAMPLE RULES FOR REVIEW")
    report.append("="*60)
    
    if rules:
        samples = random.sample(rules, min(10, len(rules)))
        for i, s in enumerate(samples):
            report.append(f"\n[{i+1}] Rule ID: {s.get('rule_id', 'N/A')}")
            report.append(f"    Type: {s.get('type', 'N/A')}")
            
            # Simplified display
            if s.get('type') == 'rule':
                report.append(f"    Cond: {json.dumps(s.get('condition', {}))}")
            else:
                report.append(f"    Subject: {s.get('entity_name') or s.get('subject') or 'N/A'}")
                
            report.append(f"    Res:  {s.get('result') or s.get('description') or 'N/A'}")
            report.append(f"    Text: {s.get('source_text', 'N/A')[:200]}...")
    else:
        report.append("\nNo rules available to sample.")

    report_text = "\n".join(report)
    print(report_text)
    
    # Use config-defined path
    os.makedirs(REPORT_FILE.parent, exist_ok=True)
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report_text)
        
    print(f"\nReport saved to: {REPORT_FILE}")
    return True
