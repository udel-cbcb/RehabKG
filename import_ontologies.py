#!/usr/bin/env python3
"""
Import publicly available ontologies into RehabKG and connect them to existing nodes.

Ontologies imported:
- Mondo Disease Ontology (diseases with ICD-10 xrefs)
- Uberon (cross-species anatomy for muscles/joints)
- PMR (Physical Medicine & Rehabilitation - already loaded, verify connections)

Connections created:
- Muscle/BodyPart → Uberon anatomy (quadriceps → UBERON:0001508)
- Condition → Mondo disease → ICD-10 codes
- Assessment → LOINC (if available)
- REHABO/TRAK → ICF (if available)
"""

from pathlib import Path
import os
import rdflib
from rdflib import RDF, RDFS, OWL, URIRef
from dotenv import load_dotenv
from db import get_driver, get_session_config

load_dotenv()

HERE = Path(__file__).parent
ONTO_DIR = Path(os.getenv("REHABKG_DATA_DIR", str(HERE / "data"))) / "ontologies"

# Muscle name → Uberon ID mapping (verified from Uberon)
MUSCLE_TO_UBERON = {
    "abdominals": "UBERON_0004511",  # skeletal muscle tissue of rectus abdominis
    "abductors": "UBERON_0001376",   # tensor fasciae latae muscle
    "adductors": "UBERON_0000370",   # adductor magnus
    "biceps": "UBERON_0004502",      # skeletal muscle tissue of biceps brachii
    "calves": "UBERON_0011910",      # gastrocnemius externus
    "chest": "UBERON_0001495",       # pectoral muscle
    "forearms": "UBERON_3010734",    # M. flexor carpi ulnaris
    "glutes": "UBERON_0001371",      # gluteus medius
    "hamstrings": "UBERON_0001374",  # biceps femoris
    "lats": "UBERON_3010701",        # m. latissimus dorsi
    "lower back": "UBERON_0002462",  # erector spinae muscle group
    "neck": "UBERON_0001128",        # sternocleidomastoid
    "quadriceps": "UBERON_0001377",  # quadriceps femoris
    "shoulders": "UBERON_0001476",   # deltoid
    "traps": "UBERON_0010955",       # trapezius pre-muscle mass
    "triceps": "UBERON_0001509",     # triceps brachii
}

# Disease name → ICD-10 mapping (common rehab conditions)
DISEASE_TO_ICD10 = {
    "stroke": "I69",
    "spinal cord injury": "S24",
    "traumatic brain injury": "S06",
    "osteoarthritis": "M15",
    "rheumatoid arthritis": "M06",
    "low back pain": "M54.5",
    "fracture": "T14",
    "amputation": "T89",
    "cerebral palsy": "G80",
    "multiple sclerosis": "G35",
    "parkinson disease": "G20",
    "muscular dystrophy": "G71",
    "peripheral neuropathy": "G62",
    "fibromyalgia": "M79.7",
    "tendinitis": "M77",
    "bursitis": "M70",
    "sprain": "S93",
    "strain": "S36",
}


def parse_ontology(filepath):
    """Parse an OWL file and return an rdflib Graph."""
    g = rdflib.Graph()
    try:
        g.parse(filepath, format="xml")
        return g
    except Exception as e:
        print(f"  Warning: parsing {filepath.name} failed: {e}")
        return None


def import_mondo(session):
    """Import Mondo Disease Ontology and connect to conditions."""
    print("\n=== Importing Mondo Disease Ontology ===")
    filepath = ONTO_DIR / "mondo.owl"
    if not filepath.exists():
        print("  Mondo not found, skipping")
        return

    g = parse_ontology(filepath)
    if g is None:
        return

    # Extract disease classes with labels
    diseases = []
    for s in set(g.subjects(RDF.type, OWL.Class)):
        if not isinstance(s, URIRef):
            continue
        label = None
        for o in g.objects(s, RDFS.label):
            label = str(o)
            break
        if label:
            diseases.append({"uri": str(s), "name": label})

    print(f"  Extracted {len(diseases)} disease classes")

    # Load into Neo4j
    rows = diseases[:5000]  # Limit for performance
    for i in range(0, len(rows), 500):
        session.run("""
            UNWIND $rows AS row
            MERGE (n:MondoDisease {uri: row.uri})
            SET n.name = row.name, n.source = 'mondo.owl'
        """, rows=rows[i:i+500]).consume()

    # NOTE: MAPS_TO_MONDO linking moved to rehabkg.py (needs Condition nodes from step 6)
    print(f"  Loaded {len(rows)} diseases")


def import_uberon(session):
    """Import Uberon anatomy and connect to muscles/joints."""
    print("\n=== Importing Uberon Anatomy ===")
    filepath = ONTO_DIR / "uberon.owl"
    if not filepath.exists():
        print("  Uberon not found, skipping")
        return

    g = parse_ontology(filepath)
    if g is None:
        return

    # Extract anatomy classes (muscles, joints, bones)
    anatomy_classes = []
    for s in set(g.subjects(RDF.type, OWL.Class)):
        if not isinstance(s, URIRef):
            continue
        uri = str(s)
        if "UBERON:" not in uri and "obo/UBERON_" not in uri:
            continue

        label = None
        for o in g.objects(s, RDFS.label):
            label = str(o)
            break
        if label:
            anatomy_classes.append({"uri": uri, "name": label})

    print(f"  Extracted {len(anatomy_classes)} anatomy classes")

    # Load into Neo4j
    rows = anatomy_classes[:10000]  # Limit for performance
    for i in range(0, len(rows), 500):
        session.run("""
            UNWIND $rows AS row
            MERGE (n:UberonConcept {uri: row.uri})
            SET n.name = row.name, n.source = 'uberon.owl'
        """, rows=rows[i:i+500]).consume()

    print(f"  Loaded {len(rows)} anatomy concepts")


def connect_muscles_to_uberon(session):
    """Connect Muscle/BodyPart nodes to Uberon anatomy."""
    print("\n=== Connecting Muscles → Uberon ===")
    connected = 0
    for muscle, uberon_id in MUSCLE_TO_UBERON.items():
        result = session.run("""
            MATCH (m:Muscle)
            WHERE toLower(m.name) = $muscle
            MATCH (u:UberonConcept)
            WHERE u.uri CONTAINS $uberon_id
            MERGE (m)-[:MAPS_TO_UBERON]->(u)
            RETURN count(*) AS c
        """, muscle=muscle, uberon_id=uberon_id).single()
        connected += result["c"]

    print(f"  Connected {connected} muscles to Uberon")


def connect_exercises_to_uberon(session):
    """Connect exercises to Uberon via their target muscles."""
    print("\n=== Connecting Exercises → Uberon (via muscles) ===")
    result = session.run("""
        MATCH (e:Exercise)-[:TARGETS_PRIMARY]->(m:Muscle)-[:MAPS_TO_UBERON]->(u:UberonConcept)
        MERGE (e)-[:TARGETS_ANATOMY]->(u)
        RETURN count(*) AS c
    """).single()
    print(f"  Connected {result['c']} exercises to Uberon anatomy")


def verify_connections(session):
    """Verify all new connections."""
    print("\n=== Verification ===")

    # Count new node types
    for label in ["MondoDisease", "UberonConcept"]:
        c = session.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()["c"]
        print(f"  {label}: {c} nodes")

    # Count new relationships
    for rel in ["MAPS_TO_MONDO", "MAPS_TO_UBERON", "TARGETS_ANATOMY"]:
        c = session.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS c").single()["c"]
        print(f"  {rel}: {c} edges")

    # Sample path: Exercise → Muscle → Uberon
    print("\n  Sample path (Exercise → Uberon):")
    for r in session.run("""
        MATCH (e:Exercise)-[:TARGETS_PRIMARY]->(m:Muscle)-[:MAPS_TO_UBERON]->(u:UberonConcept)
        WHERE e.name = 'Barbell Squat'
        RETURN e.name AS exercise, m.name AS muscle, u.name AS anatomy
    """):
        print(f"    {r['exercise']} → {r['muscle']} → {r['anatomy']}")

    # Component analysis
    print("\n  Component analysis:")
    nodes = {r["id"]: r["labels"] for r in
             session.run("MATCH (n) RETURN elementId(n) AS id, labels(n) AS labels")}
    edges = [(r["a"], r["b"]) for r in
             session.run("MATCH (a)--(b) RETURN elementId(a) AS a, elementId(b) AS b")]

    parent = {n: n for n in nodes}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    comps = {}
    for n in nodes:
        comps.setdefault(find(n), []).append(n)
    ordered = sorted(comps.values(), key=len, reverse=True)
    print(f"    Total components: {len(ordered)}")
    print(f"    Largest component: {len(ordered[0])} nodes")


def main():
    driver = get_driver()

    try:
        with driver.session(**get_session_config()) as session:
            session.run("RETURN 1").consume()
            print("Connected to Neo4j")

            import_mondo(session)
            import_uberon(session)
            connect_muscles_to_uberon(session)
            connect_exercises_to_uberon(session)
            verify_connections(session)

    finally:
        driver.close()


if __name__ == "__main__":
    main()
