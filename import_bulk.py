"""
Bulk import orchestrator for neo4j-admin import.

Stops Neo4j, runs bulk import, restarts, then runs post-load Cypher
(constraints, indexes, multi-label assignment, bridges).

Usage:
    python import_bulk.py              # Full import
    python import_bulk.py --skip-export  # Skip CSV export (use existing CSVs)
    python import_bulk.py --dry-run      # Show what would be imported
"""

import subprocess
import time
import glob
import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

from db import get_driver, get_password, get_session_config
from provenance import (
    HAS_ICD10,
    MAPS_TO_MONDO,
    STUDIES_CONDITION,
)

load_dotenv()

EXPORT_DIR = Path(os.getenv("REHABKG_EXPORT_DIR", "export"))
NODES_DIR = EXPORT_DIR / "nodes"
RELS_DIR = EXPORT_DIR / "relationships"


def run_neo4j_cmd(cmd):
    """Run a neo4j CLI command (argv list, no shell)."""
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr}")
    return result


def _container_names(all_containers=False):
    """List Docker container names (no shell/grep)."""
    cmd = ["docker", "ps", "--format", "{{.Names}}"]
    if all_containers:
        cmd.insert(2, "-a")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.split()


def stop_neo4j():
    """Stop the Neo4j Docker container (or local neo4j) before admin import.

    neo4j-admin refuses to import while the database is locked by a running
    server, so the import container and the serving container cannot share
    the data dir at the same time.
    """
    if os.getenv("NEO4J_BULK_TEST_MODE") == "1":
        # The isolated E2E harness uses neo4j-admin against a separate
        # temporary data directory, never the developer's running database.
        print("\n[1/4] Skipping service stop for isolated bulk test mode.")
        return
    print("\n[1/4] Stopping Neo4j...")
    running = [n for n in _container_names() if "neo4j" in n]
    if running:
        for name in running:
            print(f"  Stopping Docker container {name}...")
            subprocess.run(["docker", "stop", name], check=True,
                           capture_output=True, text=True)
        time.sleep(5)
    else:
        run_neo4j_cmd(["neo4j", "stop"])
        time.sleep(5)


def start_neo4j():
    print("\n[4/4] Starting Neo4j...")
    if os.getenv("NEO4J_BULK_TEST_MODE") == "1":
        print("  Skipping service start for isolated bulk test mode.")
        return
    password = get_password()
    # Check if we should start Docker container
    if "neo4j-test-serve" in _container_names(all_containers=True):
        # Container exists, check if running
        if "neo4j-test-serve" not in _container_names():
            print("  Starting Docker container...")
            subprocess.run(["docker", "start", "neo4j-test-serve"], check=True)
            time.sleep(15)

            # Change password. The new password is passed on stdin (not
            # argv, which would be visible in `ps` output).
            print("  Setting password...")
            escaped = password.replace("'", "''")
            subprocess.run(
                ["docker", "exec", "-i", "neo4j-test-serve", "cypher-shell",
                 "-u", "neo4j", "-p", "neo4j", "-d", "system"],
                input=f"ALTER CURRENT USER SET PASSWORD FROM 'neo4j' TO '{escaped}';",
                capture_output=True, text=True,
            )
            time.sleep(5)
        print("  ✅ Neo4j is running on port 7688")
    else:
        # Create and start new container
        print("  Creating Docker container...")
        data_dir = Path("neo4j_test_data").absolute()
        plugins_dir = Path("docker/plugins").absolute()
        run_args = [
            "docker", "run", "-d",
            "--name", "neo4j-test-serve",
            "-p", "7475:7474",
            "-p", "7688:7687",
            f"--volume={data_dir}:/data",
            "-e", f"NEO4J_AUTH=neo4j/{password}",
        ]
        if plugins_dir.is_dir():
            # APOC is required by dedup_check (apoc.refactor.mergeNodes)
            run_args += [
                f"--volume={plugins_dir}:/plugins",
                "-e", "NEO4J_dbms_security_procedures_unrestricted=apoc.*",
            ]
        run_args += ["neo4j:5.26.29-community"]
        subprocess.run(run_args, check=True)
        time.sleep(15)
        print("  ✅ Neo4j is running on port 7688")


def bulk_import(dry_run=False):
    print("\n[2/4] Running neo4j-admin import via Docker...")

    # Collect all CSV files
    node_files = sorted(glob.glob(str(NODES_DIR / "*.csv")))
    rel_files = sorted(glob.glob(str(RELS_DIR / "*.csv")))

    if not node_files:
        print("  ❌ No node CSV files found. Run build_csvs.py first.")
        sys.exit(1)

    print(f"  Node files: {len(node_files)}")
    print(f"  Relationship files: {len(rel_files)}")

    # Label mapping: filename -> label (preserving original casing from filename)
    LABEL_MAP = {
        "nodes_adverseevent": "AdverseEvent",
        "nodes_assessmentscale": "AssessmentScale",
        "nodes_clinicaltrial": "ClinicalTrial",
        "nodes_equipment": "Equipment",
        "nodes_equipment_motu": "Equipment",
        "nodes_exercise": "Exercise",
        "nodes_exmoconcept": "EXMOConcept",
        "nodes_hpoconcept": "HPOConcept",
        "nodes_icd10code": "ICD10Code",
        "nodes_icfconcept": "ICFConcept",
        "nodes_mondodisease": "MondoDisease",
        "nodes_muscle": "Muscle",
        "nodes_nodetype": "NodeType",
        "nodes_ontologyclass": "OntologyClass",
        "nodes_ontology_prop": "OntologyProperty",
        "nodes_ontologyindividual": "OntologyIndividual",
        "nodes_ontologyproperty": "OntologyProperty",
        "nodes_openrehabexercise": "Exercise",
        "nodes_outcome": "Outcome",
        "nodes_painconcept": "PAINConcept",
        "nodes_patient": "Patient",
        "nodes_reltype": "RelType",
        "nodes_session": "Session",
        "nodes_uberonconcept": "UberonConcept",
        "nodes_condition": "Condition",
    }

    def filename_to_label(path):
        """Extract label from filename using LABEL_MAP."""
        stem = Path(path).stem  # nodes_icfconcept
        return LABEL_MAP.get(stem, stem)

    def rel_filename_to_type(path):
        """Extract type from filename like 'rel_targets_primary.csv' -> 'TARGETS_PRIMARY'."""
        name = Path(path).stem  # rel_targets_primary
        parts = name.split("_", 1)  # [rel, targets_primary]
        if len(parts) > 1:
            return parts[1].upper()
        return name.upper()

    # Build node args with labels
    node_args = []
    for f in node_files:
        label = filename_to_label(f)
        node_args.append(f"--nodes={label}=/import/{Path(f).name}")

    # Build relationship args with types
    rel_args = []
    for f in rel_files:
        rel_type = rel_filename_to_type(f)
        rel_args.append(f"--relationships={rel_type}=/import/{Path(f).name}")

    # Build the full command
    cmd_parts = [
        "neo4j-admin database import full",
        "--overwrite-destination",
        "--verbose",
        "--id-type=string",
        "--skip-bad-relationships",
        "--skip-duplicate-nodes",
        "--multiline-fields=true",
    ]
    cmd_parts.extend(node_args)
    cmd_parts.extend(rel_args)
    target_database = os.getenv("NEO4J_DATABASE", "neo4j")
    cmd_parts.append(f"-- {target_database}")  # Database name must be last, after --

    if dry_run:
        print("\n  Dry run — command would be:")
        print("  " + " \\\n    ".join(cmd_parts))
        return

    # For Docker, we need to copy CSVs to a mount point and run import
    import_dir = Path(os.getenv("NEO4J_BULK_IMPORT_DIR", "neo4j_test_import"))
    data_dir = Path(os.getenv("NEO4J_BULK_DATA_DIR", "neo4j_test_data"))

    # Prepare directories
    import_dir.mkdir(exist_ok=True)
    data_dir.mkdir(exist_ok=True)

    # Copy CSVs to import dir
    import shutil
    for f in node_files + rel_files:
        shutil.copy2(f, import_dir / Path(f).name)

    print(f"\n  Import dir: {import_dir}")
    print(f"  Data dir: {data_dir}")

    # Build the shell script for the container
    script = " ".join(cmd_parts)

    # Run import via Docker
    docker_cmd = [
        "docker", "run", "--rm", "--tty",
        f"--volume={import_dir.absolute()}:/import",
        f"--volume={data_dir.absolute()}:/data",
        "neo4j:5.26.29-community",
        "sh", "-c", script
    ]

    print("\n  Running Docker import...")
    result = subprocess.run(docker_cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"\n  ❌ Import failed (exit code {result.returncode})")
        print(f"  STDERR: {result.stderr[-1000:]}")
        sys.exit(1)

    print("  ✅ Import complete")


def post_load():
    print("\n[3/4] Running post-load Cypher...")

    driver = get_driver()
    try:
        with driver.session(**get_session_config()) as s:
            if os.getenv("NEO4J_BULK_TEST_MODE") == "1":
                s.run("MATCH (n) DETACH DELETE n").consume()
            # Multi-label assignment for ICF. Domain comes from the extractor
            # (same property the focused refresh uses) rather than URI
            # substring matching, which mislabels codes in other chapters.
            print("  Adding ICF domain labels...")
            for label in ("BodyFunction", "BodyStructure", "Activity",
                          "EnvironmentalFactor"):
                s.run(
                    f"MATCH (n:ICFConcept {{domain: $label}}) SET n:`{label}`",
                    label=label,
                ).consume()

            # Muscle dual-label
            print("  Adding Muscle/BodyPart labels...")
            s.run("MATCH (n:Muscle) SET n:BodyPart")

            # Constraints (names match setup_neo4j_schema.py's
            # {label}_{prop}_unique pattern — tests/test_graph.py asserts
            # these exact names exist)
            print("  Creating constraints...")
            constraints = [
                "CREATE CONSTRAINT patient_patient_id_unique IF NOT EXISTS FOR (p:Patient) REQUIRE p.patient_id IS UNIQUE",
                "CREATE CONSTRAINT condition_code_unique IF NOT EXISTS FOR (c:Condition) REQUIRE c.code IS UNIQUE",
                "CREATE CONSTRAINT exercise_exercise_id_unique IF NOT EXISTS FOR (e:Exercise) REQUIRE e.exercise_id IS UNIQUE",
                "CREATE CONSTRAINT bodypart_part_id_unique IF NOT EXISTS FOR (b:BodyPart) REQUIRE b.part_id IS UNIQUE",
                "CREATE CONSTRAINT muscle_muscle_id_unique IF NOT EXISTS FOR (m:Muscle) REQUIRE m.muscle_id IS UNIQUE",
                "CREATE CONSTRAINT equipment_equipment_id_unique IF NOT EXISTS FOR (e:Equipment) REQUIRE e.equipment_id IS UNIQUE",
                "CREATE CONSTRAINT session_session_id_unique IF NOT EXISTS FOR (s:Session) REQUIRE s.session_id IS UNIQUE",
                "CREATE CONSTRAINT outcome_outcome_id_unique IF NOT EXISTS FOR (o:Outcome) REQUIRE o.outcome_id IS UNIQUE",
                "CREATE CONSTRAINT icfconcept_code_unique IF NOT EXISTS FOR (n:ICFConcept) REQUIRE n.code IS UNIQUE",
                "CREATE CONSTRAINT assessmentscale_scale_id_unique IF NOT EXISTS FOR (a:AssessmentScale) REQUIRE a.scale_id IS UNIQUE",
                "CREATE CONSTRAINT adverseevent_event_id_unique IF NOT EXISTS FOR (a:AdverseEvent) REQUIRE a.event_id IS UNIQUE",
                "CREATE CONSTRAINT observation_observation_id_unique IF NOT EXISTS FOR (o:Observation) REQUIRE o.observation_id IS UNIQUE",
            ]
            for c in constraints:
                s.run(c)

            # Indexes
            print("  Creating indexes...")
            indexes = [
                "CREATE INDEX icf_code IF NOT EXISTS FOR (n:ICFConcept) ON (n.code)",
                "CREATE INDEX icf_name IF NOT EXISTS FOR (n:ICFConcept) ON (n.name)",
                "CREATE INDEX mondo_name IF NOT EXISTS FOR (n:MondoDisease) ON (n.name)",
                "CREATE INDEX icd10_code IF NOT EXISTS FOR (n:ICD10Code) ON (n.code)",
                "CREATE INDEX exercise_name IF NOT EXISTS FOR (n:Exercise) ON (n.name)",
                "CREATE INDEX exercise_category IF NOT EXISTS FOR (n:Exercise) ON (n.category)",
                "CREATE INDEX muscle_name IF NOT EXISTS FOR (n:Muscle) ON (n.name)",
                "CREATE INDEX condition_name IF NOT EXISTS FOR (n:Condition) ON (n.name)",
                "CREATE INDEX patient_sex IF NOT EXISTS FOR (n:Patient) ON (n.sex)",
                "CREATE INDEX trial_status IF NOT EXISTS FOR (n:ClinicalTrial) ON (n.status)",
                "CREATE INDEX trial_nct IF NOT EXISTS FOR (n:ClinicalTrial) ON (n.nct_id)",
                "CREATE INDEX hpo_code IF NOT EXISTS FOR (n:HPOConcept) ON (n.code)",
                "CREATE INDEX uberon_name IF NOT EXISTS FOR (n:UberonConcept) ON (n.name)",
            ]
            for idx in indexes:
                s.run(idx)

            # Fulltext indexes
            print("  Creating fulltext indexes...")
            fulltext = [
                "CREATE FULLTEXT INDEX exercise_fulltext IF NOT EXISTS FOR (n:Exercise) ON EACH [n.name, n.description]",
                "CREATE FULLTEXT INDEX condition_fulltext IF NOT EXISTS FOR (n:Condition) ON EACH [n.name, n.description]",
            ]
            for ft in fulltext:
                s.run(ft)

            # 1b. AssessmentScale.scale_id backfill (F9, Gate 0 deferral):
            # old bulk CSVs wrote the value only as the neo4j-admin :ID, so
            # the property (and the scale_id IS UNIQUE constraint above)
            # stayed vacuous. build_csvs.py now emits a scale_id column for
            # fresh imports; this repairs graphs imported from older CSVs.
            # Idempotent — only fills NULLs, keyed by unique RMD names.
            from etl_datasets import RMD_SCALES
            backfilled = 0
            for sc in RMD_SCALES:
                backfilled += s.run(
                    "MATCH (a:AssessmentScale {name: $name}) "
                    "WHERE a.scale_id IS NULL "
                    "SET a.scale_id = $sid RETURN count(a) AS c",
                    name=sc["name"], sid=sc["scale_id"],
                ).single()["c"]
            print(f"    AssessmentScale.scale_id backfill: {backfilled}")
            unmatched = s.run(
                "MATCH (a:AssessmentScale) WHERE a.scale_id IS NULL "
                "RETURN count(a) AS c"
            ).single()["c"]
            if unmatched:
                print(f"    WARNING: {unmatched} AssessmentScale nodes lack "
                      "scale_id (not found in RMD_SCALES by name)")

            # Bridge relationships
            print("  Creating bridge relationships...")
            
            # 1. HAS_ICD10: MondoDisease → ICD10Code. Apply the same curated
            # disease/code overrides as the focused refresh before matching.
            from import_ontologies import DISEASE_TO_ICD10
            for disease, code in DISEASE_TO_ICD10.items():
                s.run(
                    "MATCH (m:MondoDisease) "
                    "WHERE toLower(m.name) CONTAINS $disease "
                    "SET m.icd10_code = $code",
                    disease=disease, code=code,
                ).consume()
            r = s.run("""
                MATCH (m:MondoDisease)
                WHERE m.icd10_code IS NOT NULL AND m.icd10_code <> ''
                WITH m, replace(m.icd10_code, '.', '') AS code
                MATCH (i:ICD10Code)
                WHERE i.code = code OR i.code STARTS WITH code
                MERGE (m)-[r:HAS_ICD10]->(i)
                SET r += $props
                RETURN count(*) AS connected
            """, props=HAS_ICD10).single()
            print(f"    HAS_ICD10: {r['connected']} MondoDisease→ICD10Code")

            # 2. MAPS_TO_MONDO: Condition → MondoDisease (name matching)
            r = s.run("""
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
            print(f"    MAPS_TO_MONDO: {r['c']} Condition→MondoDisease")

            # 2b. Condition.icd10_code (Gate 0 policy: exact-name Mondo
            # propagation + curated/condition_icd10_overrides.csv). Same
            # shared function the Cypher path runs — must precede
            # link_conditions_to_exercises (step 9), whose curated
            # match_type=icd10 rows bind on this property.
            from bridges import set_condition_icd10_codes
            set_condition_icd10_codes(s)

            # 3. STUDIES_CONDITION: ClinicalTrial → Condition (from JSON)
            import json
            from pathlib import Path
            trials_file = Path("data/raw/clinicaltrials/clinicaltrials_extracted.json")
            if trials_file.exists():
                with open(trials_file) as f:
                    trials = json.load(f)
                total_cond = 0
                for trial in trials:
                    for cond in trial.get("conditions", []):
                        r = s.run("""
                            MATCH (t:ClinicalTrial {nct_id: $nct_id})
                            MATCH (c:Condition)
                            WHERE toLower(trim(c.name)) = toLower(trim($cond))
                               OR (size(c.name) >= 5 AND toLower($cond) CONTAINS toLower(c.name))
                            MERGE (t)-[r:STUDIES_CONDITION]->(c)
                            SET r += $props
                            RETURN count(*) AS c
                        """, nct_id=trial.get("nct_id", ""), cond=cond,
                            props=STUDIES_CONDITION).single()
                        total_cond += r['c']
                print(f"    STUDIES_CONDITION: {total_cond} ClinicalTrial→Condition")

            # 4. RECOMMENDS_EXERCISE: handled by the shared curated CSV via
            # link_conditions_to_exercises below (same source the Cypher
            # path uses); the old inline name-containment matcher was
            # removed because its score filter admitted every pair.

            # HPO links are only the explicit, provenance-stamped code pairs
            # created by bridge_default_sources; no broad lexical matcher.

            # 6. MAPS_TO_UBERON: use the same curated muscle→UBERON pairs as
            # the focused refresh (broad lexical matching over-mapped).
            from import_ontologies import connect_muscles_to_uberon
            connect_muscles_to_uberon(s)

            # 7. MAPS_TO_ICF: Muscle→ICF curated bridge. The focused refresh
            # does not regenerate trial-keyword ICF edges.
            from etl_ontologies import bridge_muscles_to_icf
            bridge_muscles_to_icf(s)

            # 7b. CLOSE_MATCH: REHABO→ICF curated bridge.
            from etl_ontologies import bridge_rehabo_to_icf
            bridge_rehabo_to_icf(s)

            # 9. Condition→Exercise keyword maps (shared with rehabkg)
            from bridges import (
                link_conditions_to_exercises,
                link_safety_edges,
                load_observation_seed,
            )
            link_conditions_to_exercises(s)
            link_safety_edges(s)

            # 9b. Outcome.value_numeric backfill: old CSVs imported
            # Outcome.value as a string; typed numeric column enables
            # AVG/MIN/MAX. Idempotent: fills missing values and converts
            # string-typed ones from earlier imports.
            r = s.run("""
                MATCH (o:Outcome)
                WHERE o.value IS NOT NULL
                  AND (o.value_numeric IS NULL
                       OR valueType(o.value_numeric) STARTS WITH 'STRING')
                SET o.value_numeric = toFloat(coalesce(o.value_numeric, o.value))
                RETURN count(o) AS c
            """).single()
            print(f"    Outcome.value_numeric backfill: {r['c']} outcomes")

            # 9c. Synthetic Observation seed (stroke-gait pilot demo layer;
            # patient_id SYNTHETIC-* never collides with MOTU patients).
            # The focused refresh deletes ontology-source bridge edges after
            # seeding, leaving Observation nodes without MAPS_TO_ICF edges.
            load_observation_seed(s)
            s.run("MATCH (:Observation)-[r:MAPS_TO_ICF]->(:ICFConcept) "
                  "DELETE r").consume()

            # 9d. Scale external identifiers (curated register; shared with
            # rehabkg). All-empty identifier cells → validated no-op; F9's
            # scale_id backfill above keys this loader on scale_id.
            from bridges import apply_scale_identifiers
            apply_scale_identifiers(s)

            # Curated Core Set register is header-only until human-sourced
            # categories and redistribution terms are supplied.
            from bridges import apply_icf_core_set_rows
            apply_icf_core_set_rows(s)

            # 10. Default-source bridges only. Broad PMR/COPPER/KHMO mappings
            # belong to excluded source families and must not be regenerated.
            from bridges import bridge_default_sources
            print("  Running default-source ontology bridges...")
            bridge_default_sources(s)

            # 11. TARGETS_ANATOMY: Exercise→Uberon derived via Muscle
            # (shared helper used by the focused refresh).
            from import_ontologies import connect_exercises_to_uberon
            connect_exercises_to_uberon(s)

            # 12. Backfill provenance on CSV-imported clinical edges that
            # arrive property-less from neo4j-admin import (must run last,
            # after all rule-based stamping above).
            from provenance import backfill_csv_import_edges
            backfill_csv_import_edges(s)

            print("  ✅ Post-load schema and bridges complete")
    finally:
        driver.close()


def main():
    parser = argparse.ArgumentParser(description="Bulk import into Neo4j")
    parser.add_argument("--skip-export", action="store_true",
                        help="Skip CSV export, use existing files")
    parser.add_argument("--skip-postload", action="store_true",
                        help="Skip post-load Cypher (constraints, indexes, labels)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be imported without doing it")
    args = parser.parse_args()

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    if not args.skip_export and not args.dry_run:
        # Build CSVs from source files
        print("=" * 60)
        print("Phase 1: Build CSVs from source files")
        print("=" * 60)
        from build_csvs import main as build_main
        sys.argv = ["build_csvs.py", "--validate", "--clean"]
        build_main()

    print("=" * 60)
    print("Phase 2: Bulk Import")
    print("=" * 60)

    if not args.dry_run and os.getenv("NEO4J_BULK_TEST_MODE") != "1":
        stop_neo4j()
    bulk_import(dry_run=args.dry_run)

    if not args.dry_run and not args.skip_postload:
        # Start Neo4j container before post-load
        start_neo4j()
        post_load()

    print("\n" + "=" * 60)
    print("✅ Bulk import pipeline complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
