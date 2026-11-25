#!/usr/bin/env python3
"""
Add provenance (source/SAB) tracking to all nodes and relationships in RehabKG.

Run after initial load to ensure every node and relationship has a source property.

Usage:
    python add_provenance.py          # Add source to all missing nodes/relationships
    python add_provenance.py --dry-run # Show what would be updated
"""

import argparse
from dotenv import load_dotenv
from db import get_driver, get_session_config

load_dotenv()

# Node source mappings (label -> source)
NODE_SOURCES = {
    "Exercise": "Free Exercise DB",
    "BodyPart": "Free Exercise DB",
    "Muscle": "Free Exercise DB",
    "Equipment": "Free Exercise DB",
    "RelType": "RehabKG Schema",
    "NodeType": "RehabKG Schema",
}

# Relationship source mappings (relationship type -> source)
# These are applied to ALL relationships of that type if source is NULL
REL_SOURCES = {
    "SUBCLASS_OF": "Ontology hierarchy",
    "MAPS_TO_ICF": "RehabKG bridges",
    "STUDIES_CONDITION": "ClinicalTrials.gov",
    "HAS_OUTCOME": "MOTU dataset",
    "HAS_ICD10": "Mondo ontology",
    "TARGETS_SECONDARY": "Free Exercise DB",
    "HAS_STAY": "MOTU dataset",
    "TARGETS_PRIMARY": "Free Exercise DB",
    "REQUIRES": "Free Exercise DB",
    "TARGETS_ANATOMY": "Exercise→Uberon mapping",
    "EXPERIENCED": "MOTU dataset",
    "TARGETS_BODY_PART": "Open Rehab Exercises",
    "RECOMMENDS_EXERCISE": "RehabKG curated",
    "MEASURES": "Rehabilitation Measures Database",
    "FROM_NODE_TYPE": "RehabKG Schema",
    "INSTANCE_OF": "REHABO ontology",
    "RELATED_TO_ICF": "HPO→ICF bridge",
    "HAS_DOMAIN": "REHABO ontology",
    "HAS_RANGE": "REHABO ontology",
    "TO_NODE_TYPE": "RehabKG Schema",
    "MAPS_TO_UBERON": "Muscle→Uberon mapping",
    "PROGRESSES_TO": "RehabKG curated",
    "CLOSE_MATCH": "REHABO ontology",
}


def add_node_sources(session, dry_run=False):
    """Add source property to nodes that are missing it."""
    total = 0
    for label, source in NODE_SOURCES.items():
        if dry_run:
            r = session.run(
                f"MATCH (n:{label}) WHERE n.source IS NULL RETURN count(n) AS c"
            ).single()
        else:
            r = session.run(
                f"MATCH (n:{label}) WHERE n.source IS NULL "
                f"SET n.source = $source "
                f"RETURN count(n) AS c",
                source=source,
            ).single()
        total += r["c"]
        print(f"  {label:25s} +{r['c']:>5} nodes -> '{source}'")
    print(f"  Total nodes updated: {total}")
    return total


def add_relationship_sources(session, dry_run=False):
    """Add source property to relationships that are missing it."""
    total = 0
    for rel_type, source in REL_SOURCES.items():
        if dry_run:
            r = session.run(
                f"MATCH ()-[r:{rel_type}]->() WHERE r.source IS NULL RETURN count(r) AS c"
            ).single()
        else:
            r = session.run(
                f"MATCH ()-[r:{rel_type}]->() WHERE r.source IS NULL "
                f"SET r.source = $source "
                f"RETURN count(r) AS c",
                source=source,
            ).single()
        total += r["c"]
        print(f"  {rel_type:25s} +{r['c']:>5} edges -> '{source}'")
    print(f"  Total relationships updated: {total}")
    return total


def show_summary(session):
    """Show current source coverage."""
    print("\n=== Source Coverage ===\n")

    # Node coverage
    r = session.run("""
        MATCH (n)
        RETURN 
            count(n) AS total,
            count(n.source) AS with_source,
            count(n) - count(n.source) AS missing
    """).single()
    print(f"Nodes:     {r['total']:>8,} total, {r['with_source']:>8,} with source, {r['missing']:>6,} missing")

    # Relationship coverage
    r = session.run("""
        MATCH ()-[r]->()
        RETURN 
            count(r) AS total,
            count(r.source) AS with_source,
            count(r) - count(r.source) AS missing
    """).single()
    print(f"Relations: {r['total']:>8,} total, {r['with_source']:>8,} with source, {r['missing']:>6,} missing")


def main(dry_run=False):
    # dry_run can be passed programmatically or parsed from CLI
    if dry_run is None:
        parser = argparse.ArgumentParser(description="Add provenance tracking to RehabKG")
        parser.add_argument("--dry-run", action="store_true", help="Show what would be updated")
        args = parser.parse_args()
        dry_run = args.dry_run

    driver = get_driver()

    try:
        with driver.session(**get_session_config()) as session:
            session.run("RETURN 1").consume()
            print("Connected.\n")

            if dry_run:
                print("=== DRY RUN ===\n")

            print("=== Adding Node Sources ===")
            add_node_sources(session, dry_run=dry_run)

            print("\n=== Adding Relationship Sources ===")
            add_relationship_sources(session, dry_run=dry_run)

            show_summary(session)

    finally:
        driver.close()


if __name__ == "__main__":
    main(dry_run=None)
