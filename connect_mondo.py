#!/usr/bin/env python3
"""
Connect Mondo Disease Ontology to Condition nodes via ICD-10 codes.

Strategy:
1. Assign ICD-10 codes to Mondo diseases by keyword matching
2. Connect Conditions → Mondo via ICD-10 prefix matching
3. Connect Conditions → Mondo via name similarity
"""

from dotenv import load_dotenv
from db import get_driver

load_dotenv()

# Keyword → ICD-10 code mapping for rehab-relevant diseases
KEYWORD_ICD10 = [
    ("back pain", "M54"),
    ("low back", "M54.5"),
    ("knee osteoarthritis", "M17"),
    ("osteoarthritis", "M15"),
    ("shoulder", "M75"),
    ("rotator cuff", "M75"),
    ("stroke", "I69"),
    ("hip replacement", "Z96"),
    ("plantar fasciitis", "M72"),
    ("gait", "R26"),
    ("fracture", "T14"),
    ("arthritis", "M13"),
    ("tendinitis", "M77"),
    ("bursitis", "M70"),
    ("pain", "M79"),
    ("muscle", "M62"),
    ("nerve", "G58"),
    ("neuropathy", "G62"),
    ("fibromyalgia", "M79"),
    ("spinal cord", "S24"),
    ("brain injury", "S06"),
    ("cerebral palsy", "G80"),
    ("multiple sclerosis", "G35"),
    ("parkinson", "G20"),
    ("scoliosis", "M41"),
    ("disc", "M51"),
    ("hernia", "M51"),
    ("stenosis", "M48"),
    ("ligament", "S83"),
    ("meniscus", "S83"),
    ("cartilage", "M24"),
    ("cartilag", "M24"),
    ("synovial", "M12"),
    ("rheumatoid", "M06"),
    ("ankylosing", "M45"),
    ("spondylosis", "M47"),
    ("radiculopathy", "M54"),
    ("sciatica", "M54"),
    ("cervical", "M54"),
    ("lumbar", "M54"),
    ("thoracic", "M54"),
]


def assign_icd10_to_mondo(session):
    """Assign ICD-10 codes to Mondo diseases by keyword matching."""
    total = 0
    for keyword, icd10 in KEYWORD_ICD10:
        result = session.run(
            "MATCH (m:MondoDisease) "
            "WHERE toLower(m.name) CONTAINS $keyword AND m.icd10_code IS NULL "
            "SET m.icd10_code = $icd10 "
            "RETURN count(m) AS c",
            keyword=keyword, icd10=icd10,
        ).single()
        total += result["c"]
    print(f"  Assigned ICD-10 codes to {total} Mondo diseases")


def connect_conditions_to_mondo(session):
    """Connect Conditions → Mondo via ICD-10 prefix matching."""
    # Get all Conditions with ICD-10 codes
    conditions = list(session.run(
        "MATCH (c:Condition) WHERE c.icd10_code IS NOT NULL "
        "RETURN c.name AS name, c.icd10_code AS icd10"
    ))

    total = 0
    for cond in conditions:
        icd10 = cond["icd10"]
        prefix = icd10.split(".")[0] if "." in icd10 else icd10

        # Exact match or prefix match
        result = session.run(
            "MATCH (c:Condition {name: $name}) "
            "MATCH (m:MondoDisease) "
            "WHERE m.icd10_code IS NOT NULL "
            "AND (m.icd10_code = $icd10 OR m.icd10_code = $prefix "
            "     OR m.icd10_code STARTS WITH $prefix) "
            "MERGE (c)-[:MAPS_TO_MONDO]->(m) "
            "RETURN count(m) AS c",
            name=cond["name"], icd10=icd10, prefix=prefix,
        ).single()
        total += result["c"]
        if result["c"] > 0:
            print(f"  {cond['name']} ({icd10}): {result['c']} Mondo diseases")

    print(f"  Total ICD-10 bridges: {total}")


def connect_conditions_by_name(session):
    """Connect Conditions → Mondo via name similarity."""
    result = session.run(
        "MATCH (c:Condition), (m:MondoDisease) "
        "WHERE NOT (c)-[:MAPS_TO_MONDO]->(m) "
        "AND (toLower(m.name) CONTAINS toLower(c.name) "
        "     OR toLower(c.name) CONTAINS toLower(m.name)) "
        "MERGE (c)-[:MAPS_TO_MONDO]->(m) "
        "RETURN c.name AS condition, collect(m.name) AS diseases"
    )

    total_edges = 0
    for r in result:
        n = len(r["diseases"])
        total_edges += n
        print(f"  {r['condition']}: +{n} via name match")

    print(f"  Total name bridges: {total_edges}")


def main():
    driver = get_driver()

    try:
        with driver.session() as session:
            session.run("RETURN 1").consume()
            print("Connected to Neo4j")

            print("\n=== Step 1: Assign ICD-10 codes to Mondo diseases ===")
            assign_icd10_to_mondo(session)

            print("\n=== Step 2: Connect Conditions → Mondo via ICD-10 ===")
            connect_conditions_to_mondo(session)

            print("\n=== Step 3: Connect Conditions → Mondo via name ===")
            connect_conditions_by_name(session)

            print("\n=== Verification ===")
            result = session.run(
                "MATCH (c:Condition)-[:MAPS_TO_MONDO]->(m:MondoDisease) "
                "RETURN c.name AS condition, count(m) AS mondo_count "
                "ORDER BY mondo_count DESC"
            )
            for r in result:
                print(f"  {r['condition']}: {r['mondo_count']} Mondo diseases")

            total = session.run(
                "MATCH ()-[r:MAPS_TO_MONDO]->() RETURN count(r) AS c"
            ).single()["c"]
            print(f"\nTotal MAPS_TO_MONDO edges: {total}")

    finally:
        driver.close()


if __name__ == "__main__":
    main()
