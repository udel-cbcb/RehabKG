#!/usr/bin/env python3
"""Report vocabulary vs dataset vs schema composition of the RehabKG graph.

The headline node count is dominated by large biomedical vocabularies
(ICD-10, HPO, Uberon, Mondo). This report separates those from the much
smaller clinical/dataset layer and the schema bookkeeping nodes so the
snapshot is not mistaken for a dataset size.

Usage:
    python scripts/graph_composition.py
    python scripts/graph_composition.py --json eval/graph_composition.json
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))  # allow `python scripts/graph_composition.py` from anywhere

VOCABULARY_LABELS = frozenset({
    "ICD10Code",
    "HPOConcept",
    "MondoDisease",
    "UberonConcept",
    "ICFConcept",
    "EXMOConcept",
    "PAINConcept",
    "REHABOConcept",
    "OntologyClass",
    "OntologyProperty",
    "OntologyIndividual",
    # ICF domain labels are extra labels on ICFConcept nodes.
    "BodyFunction",
    "BodyStructure",
    "Activity",
    "EnvironmentalFactor",
})

DATASET_LABELS = frozenset({
    "Condition",
    "ClinicalTrial",
    "Patient",
    "Session",
    "Outcome",
    "Exercise",
    "Muscle",
    "BodyPart",
    "Equipment",
    "AdverseEvent",
    "AssessmentScale",
    "Observation",
})

SCHEMA_LABELS = frozenset({"NodeType", "RelType"})

CATEGORIES = ("vocabulary", "dataset", "schema", "other")


def classify_labels(labels):
    """Classify one node by its label set, checking vocabulary first.

    ICF nodes carry both ``ICFConcept`` and a domain label such as
    ``BodyFunction``; REHABO nodes carry both ``REHABOConcept`` and
    ``OntologyClass``. Either label is enough to count the node once.
    """
    labels = set(labels or ())
    if labels & VOCABULARY_LABELS:
        return "vocabulary"
    if labels & DATASET_LABELS:
        return "dataset"
    if labels & SCHEMA_LABELS:
        return "schema"
    return "other"


def node_composition(session):
    """Stream node labels and return counts per composition category."""
    counts = {category: 0 for category in CATEGORIES}
    for record in session.run("MATCH (n) RETURN labels(n) AS labels"):
        counts[classify_labels(record["labels"])] += 1
    total = sum(counts.values())
    return {
        "total_nodes": total,
        "categories": {
            category: {
                "count": count,
                "percent": (100.0 * count / total) if total else 0.0,
            }
            for category, count in counts.items()
        },
    }


def relationship_count(session):
    record = session.run(
        "MATCH ()-[r]->() RETURN count(r) AS total").single()
    return record["total"] if record else 0


def build_report(driver_factory=None):
    if driver_factory is None:
        from dotenv import load_dotenv
        load_dotenv(REPO / ".env")
        from db import get_driver, get_session_config
        driver_factory = get_driver
    else:
        from db import get_session_config

    driver = driver_factory()
    try:
        with driver.session(**get_session_config()) as session:
            report = node_composition(session)
            report["total_relationships"] = relationship_count(session)
    finally:
        driver.close()
    return report


def print_report(report):
    print("## Graph composition")
    print(f"  Nodes: {report['total_nodes']:,}")
    for category in CATEGORIES:
        row = report["categories"][category]
        print(f"  {category:<10} {row['count']:>8,}"
              f"  ({row['percent']:.1f}%)")
    print(f"  Relationships: {report['total_relationships']:,}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", help="write the report as JSON to this path")
    args = parser.parse_args(argv)

    report = build_report()
    print_report(report)
    if args.json:
        Path(args.json).write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
