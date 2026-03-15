
import json
import logging
from pathlib import Path
import sys
from typing import Any

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from normaliser.normaliser import AstrologyNormaliser
from storage.neo4j_client import Neo4jClient

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

class RuleBridge:
    def __init__(self):
        self.normaliser = AstrologyNormaliser()
        self.neo4j = Neo4jClient()
        self.stats = {"rules": 0, "yogas": 0, "errors": 0}

    def normalize_value(self, value: Any) -> Any:
        if not isinstance(value, str):
            return value
        
        # Try normalising
        norm = self.normaliser.normalise(value)
        if norm:
            return norm
        
        # Special case for numeric house strings "1" -> "HOUSE_1"
        if value.isdigit() and 1 <= int(value) <= 12:
            return f"HOUSE_{value}"
            
        return value

    def process_clauses(self, clauses: list[dict]) -> list[dict]:
        processed = []
        for clause in clauses:
            new_clause = clause.copy()
            
            # Recurse if nested logic block
            if "clauses" in new_clause:
                new_clause["clauses"] = self.process_clauses(new_clause["clauses"])
            
            # Normalize fields
            for key in ["planet", "sign", "house", "nakshatra", "planet_a", "planet_b", "house_b"]:
                if key in new_clause:
                    new_clause[key] = self.normalize_value(new_clause[key])
            
            # Handle complex state objects (like lord_state)
            if "state" in new_clause and isinstance(new_clause["state"], dict):
                if "value" in new_clause["state"]:
                    new_clause["state"]["value"] = self.normalize_value(new_clause["state"]["value"])
            
            # Handle aspect objects
            if "is_aspecting" in new_clause and isinstance(new_clause["is_aspecting"], dict):
                if "value" in new_clause["is_aspecting"]:
                    new_clause["is_aspecting"]["value"] = self.normalize_value(new_clause["is_aspecting"]["value"])

            processed.append(new_clause)
        return processed

    def normalize_rule(self, rule: dict) -> dict:
        # Map JS schema to Python Neo4j schema
        rule["source_text"] = rule.pop("original_text", rule.get("source_text"))
        
        if "conditions" in rule:
            if "logic_block" in rule["conditions"]:
                rule["conditions"]["logic_block"]["clauses"] = self.process_clauses(
                    rule["conditions"]["logic_block"]["clauses"]
                )
            # Normalize top-level conditions like ascendant_sign
            if "ascendant_sign" in rule["conditions"]:
                rule["conditions"]["ascendant_sign"] = self.normalize_value(rule["conditions"]["ascendant_sign"])
        
        return rule

    def run(self, input_path: str, limit: int = None):
        path = Path(input_path)
        if not path.exists():
            logger.error(f"Input file not found: {input_path}")
            return

        with open(path, "r") as f:
            data = json.load(f)

        if limit:
            data = data[:limit]
            logger.info(f"Loaded {len(data)} items (limited from total) from {input_path}")
        else:
            logger.info(f"Loaded {len(data)} items from {input_path}")

        for i, item in enumerate(data):
            if not isinstance(item, dict):
                logger.warning(f"Skipping item {i} because it is not a dictionary: {type(item)}")
                continue
            
            # Flatten: item could be {"rules": [...]} or {"yogas": [...]}
            rules = item.get("rules", [])
            yogas = item.get("yogas", [])

            for rule in rules:
                try:
                    norm_rule = self.normalize_rule(rule)
                    book_id = norm_rule.get("metadata", {}).get("source", "UNKNOWN_BOOK")
                    # Sanitize book_id for Neo4j
                    book_id = book_id.replace(" ", "_").upper()
                    
                    self.neo4j.load_rule(norm_rule, book_id)
                    self.stats["rules"] += 1
                except Exception as e:
                    logger.error(f"Error processing rule {rule.get('id', 'unknown')}: {e}")
                    self.stats["errors"] += 1

            for yoga in yogas:
                try:
                    # Normalize yoga formation logic
                    if "formation_logic" in yoga:
                        yoga["formation_logic"]["clauses"] = self.process_clauses(yoga["formation_logic"]["clauses"])
                    
                    # Yoga schema in Neo4jClient is simpler, map description
                    yoga["description"] = yoga.get("original_text", yoga.get("description"))
                    book_id = yoga.get("metadata", {}).get("source", "UNKNOWN_BOOK")
                    book_id = book_id.replace(" ", "_").upper()
                    
                    self.neo4j.load_yoga(yoga, book_id)
                    self.stats["yogas"] += 1
                except Exception as e:
                    logger.error(f"Error processing yoga {yoga.get('id', 'unknown')}: {e}")
                    self.stats["errors"] += 1

            if (i + 1) % 100 == 0:
                logger.info(f"Progress: Processed {i+1} containers...")

        logger.info(f"Finished! Stats: {self.stats}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Bridge JS rules to Neo4j")
    parser.add_argument("--input", default="data/extracted/all_rules_merged.json", help="Path to the source JSON")
    parser.add_argument("--limit", type=int, help="Limit number of containers to process")
    args = parser.parse_args()

    bridge = RuleBridge()
    bridge.run(args.input, limit=args.limit)
