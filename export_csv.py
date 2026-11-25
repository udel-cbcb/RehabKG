"""
CSV Export for neo4j-admin bulk import.

Writes node and relationship CSV files that can be loaded with:
    neo4j-admin database import full \
        --nodes=export/nodes/*.csv \
        --relationships=export/relationships/*.csv

Usage:
    python export_csv.py                  # Export all
    python export_csv.py --step ontologies  # Export one step only
"""

import csv
import os
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password_here")

EXPORT_DIR = Path("export")
NODES_DIR = EXPORT_DIR / "nodes"
RELS_DIR = EXPORT_DIR / "relationships"

# These are the only candidate sources that the project-level hosting audit
# currently proposes for unconditional inclusion. This is not legal clearance;
# callers must opt in explicitly, and every exported relationship must still
# have both endpoints in the exported node set.
PROPOSED_PUBLIC_SOURCES = frozenset({
    "REHABO", "EXMO", "COPPER", "Mondo", "Uberon", "PAIN", "KHMO",
    "Free Exercise DB", "synthetic_demo",
})


def filter_public_export(nodes_dir, rels_dir, allowed_sources):
    """Filter exported CSVs by source and drop relationships with absent ends.

    Only node rows whose ``source`` value is explicitly allowed are retained.
    Nodes without a source column/value are excluded rather than implicitly
    treated as shareable. Relationship rows are retained only when both IDs
    exist in the filtered node export, preventing dangling endpoints.

    Returns counts useful for a reviewable export manifest.
    """
    nodes_dir, rels_dir = Path(nodes_dir), Path(rels_dir)
    allowed_sources = set(allowed_sources)
    retained_ids = set()
    counts = {"nodes_before": 0, "nodes_retained": 0,
              "relationships_before": 0, "relationships_retained": 0}

    for path in sorted(nodes_dir.glob("nodes_*.csv")):
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            fields = reader.fieldnames or []
            rows = list(reader)
        counts["nodes_before"] += len(rows)
        kept = [row for row in rows if row.get("source") in allowed_sources
                and row.get(":ID")]
        counts["nodes_retained"] += len(kept)
        retained_ids.update(row[":ID"] for row in kept)
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(kept)

    for path in sorted(rels_dir.glob("*.csv")):
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            fields = reader.fieldnames or []
            rows = list(reader)
        counts["relationships_before"] += len(rows)
        kept = [row for row in rows
                if row.get(":START_ID") in retained_ids
                and row.get(":END_ID") in retained_ids]
        counts["relationships_retained"] += len(kept)
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(kept)

    return counts


def ensure_dirs():
    NODES_DIR.mkdir(parents=True, exist_ok=True)
    RELS_DIR.mkdir(parents=True, exist_ok=True)


def run_query(driver, query, **params):
    with driver.session() as s:
        result = s.run(query, **params)
        return [dict(r) for r in result]


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {path}: {len(rows)} rows")


# ─── Node Exports ────────────────────────────────────────────


def export_ontologies(driver):
    """Export all ontology nodes."""
    print("\n[1/6] Exporting ontology nodes...")

    # ICF concepts (with domain labels assigned later)
    rows = run_query(driver, """
        MATCH (n:ICFConcept)
        RETURN n.code AS `:ID`, n.name AS name, n.description AS description,
               n.chapter AS chapter, n.uri AS uri, n.source AS source,
               'ICFConcept' AS `:LABEL`
    """)
    write_csv(NODES_DIR / "nodes_icf.csv", rows, [":ID", "name", "description", "chapter", "uri", "source", ":LABEL"])

    # Other ontologies
    for label, filename in [
        ("EXMOConcept", "nodes_exmo.csv"),
        ("PAINConcept", "nodes_pain.csv"),
    ]:
        rows = run_query(driver, f"""
            MATCH (n:{label})
            RETURN n.code AS `:ID`, n.name AS name, n.description AS description,
                   n.uri AS uri, n.source AS source
        """)
        for r in rows:
            r[":ID"] = _ns_id(r[":ID"], label)
        write_csv(NODES_DIR / filename, rows, [":ID", "name", "description", "uri", "source"])

    # REHABO (OntologyClass + REHABOConcept)
    rows = run_query(driver, """
        MATCH (n:OntologyClass)
        WHERE n.source = 'rehabo.owl'
        RETURN n.uri AS `:ID`, n.name AS name, n.description AS description,
               n.source AS source, n.uri AS uri
    """)
    write_csv(NODES_DIR / "nodes_rehabo.csv", rows, [":ID", "name", "description", "source", "uri"])

    rows = run_query(driver, """
        MATCH (n:OntologyProperty) WHERE n.source = 'rehabo.owl'
        RETURN n.uri AS `:ID`, n.name AS name, n.description AS description,
               n.source AS source, n.uri AS uri
    """)
    write_csv(NODES_DIR / "nodes_ontology_prop.csv", rows,
              [":ID", "name", "description", "source", "uri"])
    rows = run_query(driver, """
        MATCH (n:OntologyIndividual) WHERE n.source = 'rehabo.owl'
        RETURN n.uri AS `:ID`, n.name AS name, n.source AS source, n.uri AS uri
    """)
    write_csv(NODES_DIR / "nodes_ontology_individual.csv", rows,
              [":ID", "name", "source", "uri"])

    # OntologyProperty
    rows = run_query(driver, """
        MATCH (n:OntologyProperty)
        RETURN n.uri AS `:ID`, n.name AS name, n.description AS description,
               n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_ontology_prop.csv", rows, [":ID", "name", "description", "source"])

    # OntologyIndividual
    rows = run_query(driver, """
        MATCH (n:OntologyIndividual)
        RETURN n.uri AS `:ID`, n.name AS name, n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_ontology_individual.csv", rows, [":ID", "name", "source"])

    # Mondo
    rows = run_query(driver, """
        MATCH (n:MondoDisease)
        RETURN n.uri AS `:ID`, n.name AS name, n.source AS source,
               n.icd10_code AS icd10_code
    """)
    write_csv(NODES_DIR / "nodes_mondo.csv", rows, [":ID", "name", "source", "icd10_code"])

    # Uberon
    rows = run_query(driver, """
        MATCH (n:UberonConcept)
        RETURN n.uri AS `:ID`, n.name AS name, n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_uberon.csv", rows, [":ID", "name", "source"])

    # HPO
    rows = run_query(driver, """
        MATCH (n:HPOConcept)
        RETURN n.code AS `:ID`, n.name AS name, n.uri AS uri, n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_hpo.csv", rows, [":ID", "name", "uri", "source"])

    # Mondo and Uberon are selected default-source ontology layers.
    rows = run_query(driver, """
        MATCH (n:MondoDisease)
        RETURN n.uri AS `:ID`, n.name AS name, n.icd10_code AS icd10_code,
               n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_mondo.csv", rows,
              [":ID", "name", "icd10_code", "source"])
    rows = run_query(driver, """
        MATCH (n:UberonConcept)
        RETURN n.uri AS `:ID`, n.uri AS uri, n.name AS name, n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_uberon.csv", rows, [":ID", "uri", "name", "source"])

    # Assessment scales (used by MEASURES and Outcome-to-scale links)
    rows = run_query(driver, """
        MATCH (n:AssessmentScale)
        RETURN n.scale_id AS `:ID`, n.scale_id AS scale_id, n.name AS name,
               n.domain AS domain, n.scoring_range AS scoring_range,
               n.mcid AS mcid, n.population AS population, n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_assessmentscale.csv", rows,
              [":ID", "scale_id", "name", "domain", "scoring_range", "mcid", "population", "source"])

    # ICD10
    rows = run_query(driver, """
        MATCH (n:ICD10Code)
        RETURN n.code AS `:ID`, n.description AS description, n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_icd10.csv", rows, [":ID", "description", "source"])


def export_datasets(driver):
    """Export clinical dataset nodes."""
    print("\n[2/6] Exporting dataset nodes...")

    # Exercises
    rows = run_query(driver, """
        MATCH (n:Exercise)
        RETURN coalesce(n.exercise_id, n.rehab_id) AS `:ID`, n.name AS name,
               n.force AS force, n.level AS level, n.mechanic AS mechanic,
               n.equipment AS equipment, n.category AS category, n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_exercise.csv", rows,
              [":ID", "name", "force", "level", "mechanic", "equipment", "category", "source"])

    # Muscles
    rows = run_query(driver, """
        MATCH (n:Muscle)
        RETURN n.muscle_id AS `:ID`, n.name AS name, n.type AS type, n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_muscle.csv", rows, [":ID", "name", "type", "source"])

    # Equipment
    rows = run_query(driver, """
        MATCH (n:Equipment)
        RETURN n.equipment_id AS `:ID`, n.name AS name, n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_equipment.csv", rows, [":ID", "name", "source"])

    # Patients
    rows = run_query(driver, """
        MATCH (n:Patient)
        RETURN n.patient_id AS `:ID`, n.sex AS sex, n.birth_year AS birth_year,
               n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_patient.csv", rows, [":ID", "sex", "birth_year", "source"])

    # Sessions
    rows = run_query(driver, """
        MATCH (n:Session)
        RETURN n.session_id AS `:ID`, n.type AS type, n.admission_date AS admission_date,
               n.discharge_date AS discharge_date, n.length_of_stay AS length_of_stay,
               n.amputation_side AS amputation_side, n.amputation_cause AS amputation_cause,
               n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_session.csv", rows,
              [":ID", "type", "admission_date", "discharge_date", "length_of_stay",
               "amputation_side", "amputation_cause", "source"])

    # Outcomes
    rows = run_query(driver, """
        MATCH (n:Outcome)
        RETURN n.outcome_id AS `:ID`, n.value AS value, n.phase AS phase,
               n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_outcome.csv", rows, [":ID", "value", "phase", "source"])

    # Clinical Trials
    rows = run_query(driver, """
        MATCH (n:ClinicalTrial)
        RETURN n.nct_id AS `:ID`, n.title AS title, n.status AS status,
               n.start_date AS start_date, n.completion_date AS completion_date,
               n.study_type AS study_type, n.enrollment AS enrollment,
               n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_trial.csv", rows,
              [":ID", "title", "status", "start_date", "completion_date",
               "study_type", "enrollment", "source"])

    # Conditions
    rows = run_query(driver, """
        MATCH (n:Condition)
        RETURN n.name AS `:ID`, n.name AS name, n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_condition.csv", rows, [":ID", "name", "source"])

    # Assessment Scales
    rows = run_query(driver, """
        MATCH (n:AssessmentScale)
        RETURN n.scale_id AS `:ID`, n.name AS name, n.domain AS domain,
               n.scoring_range AS scoring_range, n.mcid AS mcid,
               n.population AS population, n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_assessment.csv", rows,
              [":ID", "name", "domain", "scoring_range", "mcid", "population", "source"])

    # Adverse Events
    rows = run_query(driver, """
        MATCH (n:AdverseEvent)
        RETURN n.event_id AS `:ID`, n.type AS type, n.date AS date,
               n.cause AS cause, n.consequence AS consequence, n.source AS source
    """)
    write_csv(NODES_DIR / "nodes_adverse.csv", rows,
              [":ID", "type", "date", "cause", "consequence", "source"])


def export_schema(driver):
    """Export schema nodes (NodeType, RelType)."""
    print("\n[3/6] Exporting schema nodes...")

    rows = run_query(driver, """
        MATCH (n:NodeType)
        RETURN n.name AS `:ID`, n.name AS name, n.description AS description,
               n.key_properties AS key_properties, n.example AS example
    """)
    write_csv(NODES_DIR / "nodes_nodetype.csv", rows,
              [":ID", "name", "description", "key_properties", "example"])

    rows = run_query(driver, """
        MATCH (n:RelType)
        RETURN n.name AS `:ID`, n.name AS name, n.description AS description,
               n.from_type AS from_type, n.to_type AS to_type
    """)
    write_csv(NODES_DIR / "nodes_reltype.csv", rows,
              [":ID", "name", "description", "from_type", "to_type"])


# ─── Relationship Exports ────────────────────────────────────


# Labels whose bulk-path :ID is namespaced by build_csvs.ontology_eid().
# Export must emit the same form or a round-trip re-import silently drops
# colliding nodes (short codes like "Per_week" exist in several ontologies).
# CURIE codes (e.g. TRAK:0000001) already carry a namespace and are kept.
NS_LABELS = {
    "CBHAConcept": "CBHA",
}


def _ns_id(code, label):
    """Match build_csvs.ontology_eid: prefix short codes with the acronym."""
    ns = NS_LABELS.get(label)
    if not code or ns is None or ":" in code:
        return code
    return f"{ns}:{code}"


def export_ontology_rels(driver):
    """Export ontology relationships."""
    print("\n[4/6] Exporting ontology relationships...")

    # SUBCLASS_OF (focused default ontology source set only)
    rows = run_query(driver, """
        MATCH (child)-[:SUBCLASS_OF]->(parent)
        WHERE child.source IN $sources AND parent.source IN $sources
        WITH child, parent,
             labels(child)[0] AS child_label, labels(parent)[0] AS parent_label
        RETURN child.code AS child_code, child.uri AS child_uri,
               parent.code AS parent_code, parent.uri AS parent_uri,
               child_label, parent_label
    """, sources=["rehabo.owl", "icf.owl", "exmo.owl", "pain.owl", "mondo.owl", "uberon.owl"])
    for r in rows:
        child_label = r.pop("child_label")
        parent_label = r.pop("parent_label")
        r[":START_ID"] = _ns_id(r.pop("child_code") or r.pop("child_uri"), child_label)
        r[":END_ID"] = _ns_id(r.pop("parent_code") or r.pop("parent_uri"), parent_label)
        r[":TYPE"] = "SUBCLASS_OF"
    write_csv(RELS_DIR / "rel_subclass_of.csv", rows, [":START_ID", ":END_ID", ":TYPE"])

    # Relationships that connect nodes from different label groups
    # We need to resolve IDs by joining through the actual node properties
    rel_queries = [
        ("MAPS_TO_MONDO", """
            MATCH (c:Condition)-[:MAPS_TO_MONDO]->(m:MondoDisease)
            RETURN c.name AS start_id, m.uri AS end_id
        """),
        ("HAS_ICD10", """
            MATCH (m:MondoDisease)-[:HAS_ICD10]->(i:ICD10Code)
            RETURN m.uri AS start_id, i.code AS end_id
        """),
        ("MAPS_TO_UBERON", """
            MATCH (m:Muscle)-[:MAPS_TO_UBERON]->(u:UberonConcept)
            RETURN m.muscle_id AS start_id, u.uri AS end_id
        """),
        ("TARGETS_ANATOMY", """
            MATCH (e:Exercise)-[:TARGETS_ANATOMY]->(u:UberonConcept)
            RETURN coalesce(e.exercise_id, e.rehab_id) AS start_id, u.uri AS end_id
        """),
        ("MEASURES", """
            MATCH (a:AssessmentScale)-[:MEASURES]->(i:ICFConcept)
            RETURN a.scale_id AS start_id, i.code AS end_id
        """),
        ("RELATED_TO_ICF", """
            MATCH (h:HPOConcept)-[:RELATED_TO_ICF]->(i:ICFConcept)
            RETURN h.code AS start_id, i.code AS end_id
        """),
        ("CLOSE_MATCH", """
            MATCH (a)-[r:CLOSE_MATCH]->(b)
            RETURN coalesce(a.code, a.uri) AS start_id,
                   coalesce(b.code, b.uri) AS end_id
        """),
        ("MAPS_TO_ICF", """
            MATCH (a)-[r:MAPS_TO_ICF]->(b)
            WHERE a.source IN ['rehabo.owl', 'exmo.owl', 'pain.owl']
               OR a:Muscle OR a:BodyPart OR a:AssessmentScale
            RETURN coalesce(a.code, a.uri, a.muscle_id, a.nct_id, a.name) AS start_id,
                   head(labels(a)) AS start_label,
                   b.code AS end_id
        """),
        ("MAPS_TO_UBERON", """
            MATCH (a)-[r:MAPS_TO_UBERON]->(b)
            RETURN a.muscle_id AS start_id, b.uri AS end_id
        """),
        ("HAS_DOMAIN", """
            MATCH (a:OntologyProperty)-[r:HAS_DOMAIN]->(b)
            RETURN a.uri AS start_id, b.uri AS end_id
        """),
        ("HAS_RANGE", """
            MATCH (a:OntologyProperty)-[r:HAS_RANGE]->(b)
            RETURN a.uri AS start_id, b.uri AS end_id
        """),
        ("INSTANCE_OF", """
            MATCH (a:OntologyIndividual)-[r:INSTANCE_OF]->(b)
            RETURN a.uri AS start_id, b.uri AS end_id
        """),
        ("FROM_NODE_TYPE", """
            MATCH (a:RelType)-[r:FROM_NODE_TYPE]->(b:NodeType)
            RETURN a.name AS start_id, b.name AS end_id
        """),
        ("TO_NODE_TYPE", """
            MATCH (a:RelType)-[r:TO_NODE_TYPE]->(b:NodeType)
            RETURN a.name AS start_id, b.name AS end_id
        """),
    ]

    for rel_type, query in rel_queries:
        rows = run_query(driver, query)
        for r in rows:
            # start_label is only present on MAPS_TO_ICF; others fall through
            r[":START_ID"] = _ns_id(r.pop("start_id"), r.pop("start_label", None))
            r[":END_ID"] = r.pop("end_id")
            r[":TYPE"] = rel_type
        write_csv(RELS_DIR / f"rel_{rel_type.lower()}.csv", rows, [":START_ID", ":END_ID", ":TYPE"])


def export_dataset_rels(driver):
    """Export clinical dataset relationships."""
    print("\n[5/6] Exporting dataset relationships...")

    rel_queries = [
        ("TARGETS_PRIMARY", """
            MATCH (e:Exercise)-[:TARGETS_PRIMARY]->(m:Muscle)
            RETURN coalesce(e.exercise_id, e.rehab_id) AS start_id, m.muscle_id AS end_id
        """),
        ("TARGETS_SECONDARY", """
            MATCH (e:Exercise)-[:TARGETS_SECONDARY]->(m:Muscle)
            RETURN coalesce(e.exercise_id, e.rehab_id) AS start_id, m.muscle_id AS end_id
        """),
        ("REQUIRES", """
            MATCH (e:Exercise)-[:REQUIRES]->(q:Equipment)
            RETURN coalesce(e.exercise_id, e.rehab_id) AS start_id, q.equipment_id AS end_id
        """),
        ("TARGETS_BODY_PART", """
            MATCH (e:Exercise)-[:TARGETS_BODY_PART]->(b:BodyPart)
            RETURN coalesce(e.exercise_id, e.rehab_id) AS start_id,
                   coalesce(b.part_id, b.muscle_id) AS end_id
        """),
        ("TARGETS_ANATOMY", """
            MATCH (e:Exercise)-[:TARGETS_ANATOMY]->(u:UberonConcept)
            RETURN coalesce(e.exercise_id, e.rehab_id) AS start_id, u.uri AS end_id
        """),
        ("HAS_STAY", """
            MATCH (p:Patient)-[:HAS_STAY]->(s:Session)
            RETURN p.patient_id AS start_id, s.session_id AS end_id
        """),
        ("HAS_OUTCOME", """
            MATCH (s:Session)-[:HAS_OUTCOME]->(o:Outcome)
            RETURN s.session_id AS start_id, o.outcome_id AS end_id
        """),
        ("MEASURED_BY", """
            MATCH (o:Outcome)-[:MEASURED_BY]->(a:AssessmentScale)
            RETURN o.outcome_id AS start_id, a.scale_id AS end_id
        """),
        ("EXPERIENCED", """
            MATCH (p:Patient)-[:EXPERIENCED]->(a:AdverseEvent)
            RETURN p.patient_id AS start_id, a.event_id AS end_id
        """),
        ("MEASURES", """
            MATCH (a:AssessmentScale)-[:MEASURES]->(i:ICFConcept)
            RETURN a.scale_id AS start_id, i.code AS end_id
        """),
        ("PROGRESSES_TO", """
            MATCH (a:Exercise)-[:PROGRESSES_TO]->(b:Exercise)
            RETURN coalesce(a.exercise_id, a.rehab_id) AS start_id,
                   coalesce(b.exercise_id, b.rehab_id) AS end_id
        """),
        ("RELATED_TO_ICF", """
            MATCH (h:HPOConcept)-[:RELATED_TO_ICF]->(i:ICFConcept)
            RETURN h.code AS start_id, i.code AS end_id
        """),
    ]

    for rel_type, query in rel_queries:
        rows = run_query(driver, query)
        for r in rows:
            r[":START_ID"] = r.pop("start_id")
            r[":END_ID"] = r.pop("end_id")
            r[":TYPE"] = rel_type
        write_csv(RELS_DIR / f"rel_{rel_type.lower()}.csv", rows, [":START_ID", ":END_ID", ":TYPE"])


def export_postload_rels(driver):
    """Export post-load linking relationships."""
    print("\n[6/6] Exporting post-load relationships...")

    rel_queries = [
        ("STUDIES_CONDITION", """
            MATCH (t:ClinicalTrial)-[:STUDIES_CONDITION]->(c:Condition)
            RETURN t.nct_id AS start_id, c.name AS end_id
        """),
        ("MAPS_TO_MONDO", """
            MATCH (c:Condition)-[:MAPS_TO_MONDO]->(m:MondoDisease)
            RETURN c.name AS start_id, m.uri AS end_id
        """),
        ("HAS_ICD10", """
            MATCH (m:MondoDisease)-[:HAS_ICD10]->(i:ICD10Code)
            RETURN m.uri AS start_id, i.code AS end_id
        """),
        ("RECOMMENDS_EXERCISE", """
            MATCH (c:Condition)-[:RECOMMENDS_EXERCISE]->(e:Exercise)
            RETURN c.name AS start_id, coalesce(e.exercise_id, e.rehab_id) AS end_id
        """),
    ]

    for rel_type, query in rel_queries:
        rows = run_query(driver, query)
        for r in rows:
            r[":START_ID"] = r.pop("start_id")
            r[":END_ID"] = r.pop("end_id")
            r[":TYPE"] = rel_type
        write_csv(RELS_DIR / f"rel_{rel_type.lower()}.csv", rows, [":START_ID", ":END_ID", ":TYPE"])


# ─── Main ────────────────────────────────────────────────────


STEPS = {
    "ontologies": [export_ontologies, export_ontology_rels],
    "datasets": [export_datasets, export_dataset_rels],
    "schema": [export_schema],
    "postload": [export_postload_rels],
}


def main():
    parser = argparse.ArgumentParser(description="Export graph to CSV for bulk import")
    parser.add_argument("--step", choices=list(STEPS.keys()) + ["all"],
                        default="all", help="Which step to export")
    parser.add_argument(
        "--public-candidate", action="store_true",
        help=("Filter the completed export to source rows in the proposed "
              "public-candidate set and drop relationships with excluded endpoints. "
              "This is a screening aid, not legal clearance."),
    )
    parser.add_argument(
        "--public-sources", nargs="+", metavar="SOURCE",
        help="Override candidate source set (only used with --public-candidate).",
    )
    args = parser.parse_args()

    ensure_dirs()
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    try:
        if args.step == "all":
            for step_name, funcs in STEPS.items():
                for func in funcs:
                    func(driver)
        else:
            for func in STEPS[args.step]:
                func(driver)

        if args.public_candidate:
            if args.step != "all":
                parser.error("--public-candidate requires --step all")
            counts = filter_public_export(
                NODES_DIR, RELS_DIR,
                args.public_sources or PROPOSED_PUBLIC_SOURCES,
            )
            manifest = {
                "purpose": "proposed public-hosting screening; not legal clearance",
                "allowed_sources": sorted(args.public_sources or PROPOSED_PUBLIC_SOURCES),
                **counts,
            }
            manifest_path = EXPORT_DIR / "public_candidate_manifest.json"
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            print(f"\nPublic-candidate screening manifest: {manifest_path}")
            print(f"  retained nodes: {counts['nodes_retained']}/{counts['nodes_before']}")
            print("  retained relationships: "
                  f"{counts['relationships_retained']}/{counts['relationships_before']}")

        print(f"\n✅ CSV export complete: {EXPORT_DIR}")
        print(f"   Nodes: {len(list(NODES_DIR.glob('*.csv')))} files")
        print(f"   Relationships: {len(list(RELS_DIR.glob('*.csv')))} files")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
