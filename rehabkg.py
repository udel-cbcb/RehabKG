#!/usr/bin/env python3
"""
RehabKG Unified Pipeline

Streamlined, repeatable pipeline for loading the Rehabilitation Knowledge Graph.

Usage:
    python rehabkg.py                    # Full load (idempotent, skips existing)
    python rehabkg.py --fresh            # Delete everything and reload from scratch
    python rehabkg.py --only ontologies  # Run only ontologies step
    python rehabkg.py --skip datasets    # Skip datasets step
    python rehabkg.py --add hpo          # Add only HPO data
    python rehabkg.py --add trials       # Add only expanded clinical trials
    python rehabkg.py --status           # Show current graph status
    python rehabkg.py --reset-label HPOConcept  # Delete specific label and reload

Steps:
    1. schema      - Constraints, indexes, schema docs
    2. ontologies  - ICF, REHABO, EXMO, COPPER, KHMO, PAIN, CBHA
    3. datasets    - Exercises, MOTU, trials, ICD-10, scales
    4. anatomy     - Uberon, Mondo, Muscle mappings
    5. additional  - HPO, expanded trials
    6. provenance  - Source/SAB tracking

Post-load linking (runs automatically after all steps complete):
    - Muscle→ICF (after datasets — needs Muscle nodes)
    - HAS_ICD10 (after anatomy — needs MondoDisease.icd10_code)
    - MAPS_TO_MONDO (after additional — needs Condition nodes)
    - STUDIES_CONDITION (after additional — needs Condition nodes)
    - RECOMMENDS_EXERCISE (after additional — needs Condition + Exercise)
    - bridges.py bridge_all (after additional — includes bridges for all loaded concept families)

WARNING: the general `ontologies` step still loads staged COPPER, KHMO, and
CBHA files. The 2026-11-05 focused public-source refresh excludes those files;
do not use a general full/incremental ontology load to reproduce that graph
until the loader allowlist and bulk path are reconciled.
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from db import get_driver, get_session_config

load_dotenv()

# Pipeline steps (bridges removed — bridge_all runs as post-load linking)
ALL_STEPS = ["schema", "ontologies", "datasets", "anatomy", "additional", "provenance"]

# Labels that can be reset individually
RESETTABLE_LABELS = {
    "HPOConcept": "HPO ontology",
    "ClinicalTrial": "Clinical trials",
    "Condition": "Trial conditions",
    "UberonConcept": "Uberon anatomy",
    "MondoDisease": "Mondo diseases",
    "ICD10Code": "ICD-10 codes",
    "Exercise": "Exercises",
    "Patient": "MOTU patients",
    "AssessmentScale": "Assessment scales",
}


def show_status(driver):
    """Display current graph status."""
    with driver.session(**get_session_config()) as s:
        print("=== Graph Status ===\n")

        # Node counts by label
        r = s.run("MATCH (n) RETURN count(n) AS c").single()
        print(f"Total nodes: {r['c']:,}\n")

        print("By label:")
        labels = s.run(
            "MATCH (n) UNWIND labels(n) AS l "
            "RETURN l, count(n) AS c ORDER BY c DESC"
        ).data()
        for row in labels:
            print(f"  {row['l']:25s} {row['c']:>8,}")

        # Relationship counts
        print("\nRelationships:")
        rels = s.run(
            "MATCH ()-[r]->() RETURN type(r) AS t, count(r) AS c ORDER BY c DESC"
        ).data()
        total_rels = sum(row['c'] for row in rels)
        print(f"  Total: {total_rels:,}\n")
        for row in rels:
            print(f"  {row['t']:25s} {row['c']:>8,}")

        # Disconnected components
        print("\nDisconnected nodes (no relationships):")
        disc = s.run(
            "MATCH (n) WHERE NOT (n)--() "
            "UNWIND labels(n) AS l "
            "RETURN l, count(n) AS c ORDER BY c DESC"
        ).data()
        total_disc = sum(row['c'] for row in disc)
        print(f"  Total: {total_disc:,}\n")
        for row in disc:
            print(f"  {row['l']:25s} {row['c']:>8,}")


def reset_graph(driver):
    """Delete all nodes and relationships."""
    with driver.session(**get_session_config()) as s:
        s.run("MATCH (n) DETACH DELETE n").consume()
        print("Deleted all nodes and relationships")


def reset_label(driver, label):
    """Delete all nodes of a specific label and their relationships.

    The label is interpolated into Cypher, so it must come from the
    hardcoded RESETTABLE_LABELS allowlist (also enforced by argparse).
    """
    if label not in RESETTABLE_LABELS:
        raise ValueError(
            f"Refusing to reset non-allowlisted label {label!r}; "
            f"allowed: {sorted(RESETTABLE_LABELS)}"
        )
    with driver.session(**get_session_config()) as s:
        s.run(f"MATCH (n:{label}) DETACH DELETE n").consume()
        print(f"Deleted all :{label} nodes ({RESETTABLE_LABELS[label]})")


def run_schema():
    """Create constraints, indexes, schema docs."""
    print("=== 1. Schema ===")
    from setup_neo4j_schema import main
    main()


def run_ontologies():
    """Load all ontologies."""
    print("=== 2. Ontologies ===")
    from etl_ontologies import main
    main()


def run_datasets():
    """Load clinical datasets."""
    print("=== 3. Datasets ===")
    from etl_datasets import main
    main()


def run_anatomy():
    """Load Uberon, Mondo, Muscle mappings."""
    print("=== 4. Anatomy ===")
    from import_ontologies import main
    main()


def run_additional():
    """Load HPO, expanded trials."""
    print("=== 5. Additional ===")
    from add_additional_data import main
    main()


def run_provenance():
    """Add source/SAB tracking to all nodes and relationships."""
    print("=== 6. Provenance ===")
    from add_provenance import main
    main()


STEP_FUNCTIONS = {
    "schema": run_schema,
    "ontologies": run_ontologies,
    "datasets": run_datasets,
    "anatomy": run_anatomy,
    "additional": run_additional,
    "provenance": run_provenance,
}


# ── Post-load linking ──────────────────────────────────────────────────────
# All cross-step relationship creation happens here, AFTER all nodes exist.

def link_post_datasets(session):
    """Linking that requires nodes from datasets step (Exercise, Muscle, ICD10Code, etc.)."""
    print("\n=== Post-datasets linking ===")

    # 1. Muscle→ICF bridge (Muscle loaded in datasets, ICFConcept in ontologies)
    from etl_ontologies import bridge_muscles_to_icf
    bridge_muscles_to_icf(session)


def link_post_anatomy(session):
    """Linking that requires nodes from anatomy step (MondoDisease, UberonConcept)."""
    print("\n=== Post-anatomy linking ===")

    # 1. Set icd10_code on MondoDisease (needed for HAS_ICD10)
    from import_ontologies import DISEASE_TO_ICD10
    set_count = 0
    for disease, icd10 in DISEASE_TO_ICD10.items():
        result = session.run("""
            MATCH (m:MondoDisease)
            WHERE toLower(m.name) CONTAINS $disease
            SET m.icd10_code = $icd10
            RETURN count(m) AS c
        """, disease=disease, icd10=icd10).single()
        set_count += result["c"]
    print(f"  Set icd10_code on {set_count} MondoDisease nodes")

    # 2. HAS_ICD10: MondoDisease→ICD10Code
    from provenance import HAS_ICD10
    r = session.run("""
        MATCH (m:MondoDisease)
        WHERE m.icd10_code IS NOT NULL
        MATCH (i:ICD10Code)
        WHERE i.code STARTS WITH m.icd10_code
        MERGE (m)-[r:HAS_ICD10]->(i)
        SET r += $props
        RETURN count(*) AS connected
    """, props=HAS_ICD10).single()
    print(f"  HAS_ICD10: {r['connected']} MondoDisease→ICD10Code edges")


def link_post_additional(session):
    """Linking that requires nodes from additional step (Condition, HPOConcept)."""
    print("\n=== Post-additional linking ===")

    # 1. MAPS_TO_MONDO: Condition→MondoDisease (name matching)
    from provenance import MAPS_TO_MONDO, STUDIES_CONDITION
    r = session.run("""
        MATCH (m:MondoDisease)
        WHERE m.name IS NOT NULL
        MATCH (c:Condition)
        WHERE c.name IS NOT NULL
          AND (toLower(trim(m.name)) = toLower(trim(c.name))
               OR (size(c.name) >= 5 AND toLower(m.name) CONTAINS toLower(c.name)))
        MERGE (c)-[r:MAPS_TO_MONDO]->(m)
        SET r += $props
        RETURN count(*) AS c
    """, props=MAPS_TO_MONDO).single()
    print(f"  MAPS_TO_MONDO: {r['c']} Condition→MondoDisease edges")

    # 2. Condition.icd10_code (Gate 0 policy: exact-name Mondo propagation
    # + curated/condition_icd10_overrides.csv). Shared with the bulk path;
    # must run after MAPS_TO_MONDO and before the curated match_type=icd10
    # rows in link_conditions_to_exercises below bind on it.
    from bridges import set_condition_icd10_codes
    set_condition_icd10_codes(session)

    # 3. STUDIES_CONDITION: ClinicalTrial→Condition (read from JSON data)
    import json
    trials_file = Path("data/raw/clinicaltrials/clinicaltrials_extracted.json")
    if trials_file.exists():
        with open(trials_file) as f:
            trials = json.load(f)
        total_cond = 0
        for trial in trials:
            for cond in trial.get("conditions", []):
                result = session.run("""
                    MATCH (t:ClinicalTrial {nct_id: $nct_id})
                    MATCH (c:Condition)
                    WHERE toLower(trim(c.name)) = toLower(trim($cond))
                       OR (size(c.name) >= 5 AND toLower($cond) CONTAINS toLower(c.name))
                    MERGE (t)-[r:STUDIES_CONDITION]->(c)
                    SET r += $props
                    RETURN count(c) AS c
                """, nct_id=trial["nct_id"], cond=cond,
                    props=STUDIES_CONDITION).single()
                total_cond += result["c"]
        print(f"  STUDIES_CONDITION: {total_cond} ClinicalTrial→Condition edges")
    else:
        print("  STUDIES_CONDITION: skipped (file not found)")

    # 4. RECOMMENDS_EXERCISE: Condition→Exercise via the shared curated
    # CSV (curated/condition_exercise.csv, loaded by bridges.py — same
    # source the bulk import postload applies). Safety edges come from
    # curated/safety_contraindications.csv via the same loader family;
    # scale identifiers from curated/scale_identifiers.csv (empty cells
    # are a no-op until HUMAN INPUT fills LOINC/ICF columns).
    from bridges import (
        apply_scale_identifiers,
        apply_icf_core_set_rows,
        link_conditions_to_exercises,
        link_safety_edges,
        load_observation_seed,
    )
    link_conditions_to_exercises(session)
    link_safety_edges(session)
    load_observation_seed(session)
    apply_scale_identifiers(session)
    apply_icf_core_set_rows(session)

    # 5. Bridge only the selected default source set; do not call legacy
    # bridge_all, which includes strategies for excluded ontology families.
    from bridges import bridge_default_sources
    bridge_default_sources(session)

    # 6. Backfill provenance on edges the Cypher path creates without the
    # contract (load_data MERGEs etc.). Must run last.
    from provenance import backfill_csv_import_edges
    backfill_csv_import_edges(session)


# ── Main pipeline ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="RehabKG Unified Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rehabkg.py                          # Full load (idempotent)
  python rehabkg.py --fresh                  # Delete everything and reload
  python rehabkg.py --only ontologies        # Run only ontologies
  python rehabkg.py --skip datasets anatomy  # Skip datasets and anatomy
  python rehabkg.py --add hpo                # Add only HPO
  python rehabkg.py --add trials             # Add only expanded trials
  python rehabkg.py --status                 # Show graph status
  python rehabkg.py --reset-label HPOConcept # Delete HPO and reload
        """,
    )
    parser.add_argument("--fresh", action="store_true",
                        help="Delete everything and reload from scratch")
    parser.add_argument("--yes", action="store_true",
                        help="Skip the --fresh/--reset-label confirmation prompt")
    parser.add_argument("--only", nargs="+", choices=ALL_STEPS,
                        help="Run only these steps")
    parser.add_argument("--skip", nargs="+", choices=ALL_STEPS,
                        help="Skip these steps")
    parser.add_argument("--add", nargs="+", choices=["hpo", "trials"],
                        help="Add specific data (HPO, trials)")
    parser.add_argument("--status", action="store_true",
                        help="Show current graph status")
    parser.add_argument("--reset-label", choices=list(RESETTABLE_LABELS.keys()),
                        help="Delete specific label before running")

    args = parser.parse_args()

    def confirm(destruction):
        if args.yes:
            return
        answer = input(f"{destruction} Continue? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            sys.exit(1)

    # Status check
    if args.status:
        driver = get_driver()
        try:
            show_status(driver)
        finally:
            driver.close()
        return

    # Fresh start
    if args.fresh:
        confirm("This deletes ALL nodes and relationships in the graph.")
        driver = get_driver()
        try:
            reset_graph(driver)
        finally:
            driver.close()

    # Reset specific label
    if args.reset_label:
        confirm(f"This deletes all :{args.reset_label} nodes and their relationships.")
        driver = get_driver()
        try:
            reset_label(driver, args.reset_label)
        finally:
            driver.close()

    # Incremental add
    if args.add:
        driver = get_driver()
        try:
            for item in args.add:
                if item == "hpo":
                    print("=== Adding HPO ===")
                    from add_additional_data import load_hpo
                    with driver.session(**get_session_config()) as s:
                        load_hpo(s)
                elif item == "trials":
                    print("=== Adding expanded trials ===")
                    from add_additional_data import load_expanded_clinicaltrials
                    with driver.session(**get_session_config()) as s:
                        load_expanded_clinicaltrials(s)
            # Post-load linking must run here too, otherwise --add leaves
            # the new Condition/HPO nodes unlinked (STUDIES_CONDITION,
            # RECOMMENDS_EXERCISE, bridges).
            with driver.session(**get_session_config()) as session:
                link_post_additional(session)
        finally:
            driver.close()
        return

    # Determine which steps to run
    if args.only:
        steps = args.only
    elif args.skip:
        steps = [s for s in ALL_STEPS if s not in args.skip]
    else:
        steps = ALL_STEPS

    # Run data loading steps
    # For --fresh runs, tee output to a log file so nothing is lost
    log_file = None
    log_path = None
    old_stdout, old_stderr = sys.stdout, sys.stderr
    if args.fresh:
        log_path = Path("logs") / "pipeline_latest.log"
        log_path.parent.mkdir(exist_ok=True)
        log_file = open(log_path, "w")
        print(f"Full log: {log_path}")

        class Tee:
            """Write to both stdout and a file."""
            def __init__(self, original, log):
                self.original = original
                self.log = log
            def write(self, s):
                self.original.write(s)
                self.log.write(s)
                self.log.flush()
            def flush(self):
                self.original.flush()
                self.log.flush()

        sys.stdout = Tee(sys.stdout, log_file)
        sys.stderr = Tee(sys.stderr, log_file)

    try:
        for step in steps:
            print(f"\n{'='*60}")
            STEP_FUNCTIONS[step]()
            print()

        # Run post-load linking (order matters!)
        driver = get_driver()
        try:
            with driver.session(**get_session_config()) as session:
                # After datasets: Muscle→ICF bridge
                if "datasets" in steps:
                    link_post_datasets(session)

                # After anatomy: HAS_ICD10, DISEASE_TO_ICD10 mapping
                if "anatomy" in steps:
                    link_post_anatomy(session)

                # After additional: MAPS_TO_MONDO, STUDIES_CONDITION, bridges
                if "additional" in steps:
                    link_post_additional(session)
        finally:
            driver.close()
    finally:
        # Restore stdout/stderr and close log even on failure
        if log_file:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            log_file.close()
            print(f"Full log saved to: {log_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
