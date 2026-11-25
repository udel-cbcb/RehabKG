#!/usr/bin/env python3
"""
Load processed exercise data into Neo4j for the Rehabilitation KG.

Reads:
  data/processed/exercises_nodes.csv          (Neo4j admin-import format)
  data/processed/exercises_relationships.csv

Uses batched UNWIND + MERGE over bolt, so no APOC or import-directory
copying is required. Idempotent: re-running updates existing nodes/rels.

Run: python load_data.py
"""

import csv
from pathlib import Path

from dotenv import load_dotenv

from db import get_driver, get_uri

load_dotenv()

DATA_DIR = Path(__file__).parent / "data" / "processed"
NODES_FILE = DATA_DIR / "free-exercise-db" / "exercises_nodes.csv"
RELS_FILE = DATA_DIR / "free-exercise-db" / "exercises_relationships.csv"
BATCH_SIZE = 500

META_PROPS = {"id:ID", "labels:LABEL", ":START_ID", ":END_ID", ":TYPE"}
LIST_PROPS = {"instructions", "images"}  # stored as lists split on '|'


def clean_props(row: dict) -> dict:
    """Keep non-empty data properties; split list-typed fields on '|'."""
    props = {}
    for key, value in row.items():
        if key in META_PROPS or value is None or value == "":
            continue
        if key in LIST_PROPS:
            props[key] = [p.strip() for p in value.split("|") if p.strip()]
        else:
            props[key] = value
    return props


def read_nodes():
    """Yield (primary_label, extra_labels, id, props) per CSV row."""
    with open(NODES_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            labels = [l for l in row["labels:LABEL"].split(";") if l]
            yield labels[0], labels[1:], row["id:ID"], clean_props(row)


def load_nodes(session) -> int:
    print("\n=== Loading Nodes ===")
    queries = {
        "Exercise": """
            UNWIND $rows AS row
            MERGE (n:Exercise {exercise_id: row.id})
            SET n += row.props
            RETURN count(n) AS c
        """,
        "Equipment": """
            UNWIND $rows AS row
            MERGE (n:Equipment {equipment_id: row.id})
            SET n += row.props
            RETURN count(n) AS c
        """,
        # 'Muscle;BodyPart' rows carry both labels
        "Muscle": """
            UNWIND $rows AS row
            MERGE (n:Muscle:BodyPart {muscle_id: row.id})
            SET n.part_id = row.id, n += row.props
            RETURN count(n) AS c
        """,
    }

    buckets: dict[str, list] = {k: [] for k in queries}
    for primary, _extra, node_id, props in read_nodes():
        buckets[primary].append({"id": node_id, "props": props})

    total = 0
    for label, rows in buckets.items():
        if not rows:
            continue
        loaded = 0
        for i in range(0, len(rows), BATCH_SIZE):
            result = session.run(queries[label], rows=rows[i : i + BATCH_SIZE])
            loaded += result.single()["c"]
        total += loaded
        print(f"  {label}: {loaded} nodes")
    return total


def load_relationships(session) -> int:
    print("\n=== Loading Relationships ===")
    with open(RELS_FILE, newline="", encoding="utf-8") as f:
        rows = [
            {"start": r[":START_ID"], "end": r[":END_ID"], "type": r[":TYPE"]}
            for r in csv.DictReader(f)
        ]

    from collections import Counter

    # Node ids are unique across the file and each id lives on exactly one of
    # the four merge-key properties, so coalesce resolves both endpoints.
    match_clause = """
        UNWIND $rows AS row
        MATCH (a), (b)
        WHERE coalesce(a.exercise_id, a.muscle_id, a.part_id, a.equipment_id) = row.start
          AND coalesce(b.exercise_id, b.muscle_id, b.part_id, b.equipment_id) = row.end
        MERGE (a)-[:%s]->(b)
    """

    counts: Counter = Counter()
    allowed = {"TARGETS_PRIMARY", "TARGETS_SECONDARY", "REQUIRES"}
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        for rel_type in sorted({r["type"] for r in batch}):
            if rel_type not in allowed:
                raise ValueError(f"Unexpected relationship type: {rel_type!r}")
            typed = [r for r in batch if r["type"] == rel_type]
            result = session.run(match_clause % rel_type, rows=typed)
            result.consume()
            counts[rel_type] += len(typed)

    for rel_type, n in sorted(counts.items()):
        print(f"  {rel_type}: {n}")
    return sum(counts.values())


def verify(session):
    print("\n=== Verification ===")
    for label in ("Exercise", "Muscle", "BodyPart", "Equipment"):
        cnt = session.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()["c"]
        print(f"  :{label} nodes: {cnt}")
    for rel in ("TARGETS_PRIMARY", "TARGETS_SECONDARY", "REQUIRES"):
        cnt = session.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS c").single()["c"]
        print(f"  :{rel} rels: {cnt}")

    sample = session.run(
        """
        MATCH (e:Exercise)-[:TARGETS_PRIMARY]->(m)
        RETURN e.name AS exercise, m.name AS muscle LIMIT 3
        """
    )
    print("\n  Sample TARGETS_PRIMARY edges:")
    for rec in sample:
        print(f"    ({rec['exercise']})-[:TARGETS_PRIMARY]->({rec['muscle']})")


def main():
    driver = get_driver()
    try:
        with driver.session() as session:
            session.run("RETURN 1").consume()
            print(f"Connected to {get_uri()}")

            existing = session.run(
                "MATCH (n:Exercise) RETURN count(n) AS c"
            ).single()["c"]
            if existing:
                print(f"Note: {existing} Exercise nodes already exist "
                      "(MERGE keeps this idempotent)")

            n_nodes = load_nodes(session)
            n_rels = load_relationships(session)
            verify(session)

            print(f"\n✓ Done: {n_nodes} nodes, {n_rels} relationships processed")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
