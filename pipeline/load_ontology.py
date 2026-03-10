"""Run-once Neo4j ontology seeder for Phase 1."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from storage.neo4j_client import Neo4jClient


def ontology_directory(project_root: Path) -> Path:
    """Return the ontology directory location."""
    return project_root / "normaliser" / "ontology"


def main() -> None:
    ontology_dir = ontology_directory(PROJECT_ROOT)
    db = Neo4jClient()
    print("Connection:", db.verify_connection())
    print("\nCreating constraints...")
    db.create_constraints()

    steps = [
        ("Planets", lambda: db.load_planets(ontology_dir / "planets.json")),
        ("Signs", lambda: db.load_signs(ontology_dir / "signs.json")),
        ("Houses", lambda: db.load_houses(ontology_dir / "houses.json")),
        ("Nakshatras", lambda: db.load_nakshatras(ontology_dir / "nakshatras.json")),
        ("Yogas", lambda: db.load_yogas(ontology_dir / "yogas.json")),
    ]
    for label, loader in steps:
        loaded = loader()
        print(f"  {label}: {loaded} loaded")

    print("\nLoading planet relationships...")
    db.load_planet_relationships(ontology_dir / "planets.json")

    print("\nEntity counts in Neo4j:")
    counts = db.verify_entity_counts()
    expected = {"Planet": 9, "Sign": 12, "House": 12, "Nakshatra": 27, "Yoga": 50}
    all_ok = True
    for entity_type, count in counts.items():
        ok = count >= expected[entity_type] if entity_type == "Yoga" else count == expected[entity_type]
        if not ok:
            all_ok = False
        status = "OK" if ok else "FAIL"
        print(f"  {status} {entity_type}: {count} (expected {expected[entity_type]})")

    print("\nOntology loaded successfully!" if all_ok else "\nCheck counts above.")
    db.close()


if __name__ == "__main__":
    main()
