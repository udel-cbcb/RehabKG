"""Opt-in end-to-end test for the focused ontology refresh graph path.

This test is intentionally excluded from the default offline suite. It requires
a disposable Neo4j database and local source data. Set REHABKG_E2E=1, NEO4J_DATABASE to a database name
containing "test", and REHABKG_E2E_ALLOW_RESET=1 to run it. The test refuses to
target the default/production database name.
"""
import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]


def _enabled():
    return os.getenv("REHABKG_E2E") == "1"


@pytest.mark.e2e
@pytest.mark.skipif(not _enabled(), reason="set REHABKG_E2E=1 to run disposable-db integration")
def test_focused_refresh_end_to_end(tmp_path):
    database = os.getenv("NEO4J_DATABASE", "")
    if "test" not in database.lower():
        pytest.fail("Refusing destructive E2E refresh: NEO4J_DATABASE must include 'test'")
    if os.getenv("REHABKG_E2E_ALLOW_RESET") != "1":
        pytest.fail("Set REHABKG_E2E_ALLOW_RESET=1 to authorize replacing the disposable test DB")

    export_dir = tmp_path / "export"
    env = os.environ.copy()
    env["REHABKG_EXPORT_DIR"] = str(export_dir)
    env["REHABKG_DATA_DIR"] = str(ROOT / "data")
    env["REHABKG_REFRESH_MANIFEST"] = str(tmp_path / "refresh-manifest.json")
    env["NEO4J_DATABASE"] = database

    build = subprocess.run(
        [sys.executable, "build_csvs.py", "--validate", "--clean"],
        cwd=ROOT, env=env, text=True, capture_output=True, timeout=900,
    )
    assert build.returncode == 0, build.stdout + "\n" + build.stderr
    assert "all IDs valid" in build.stdout

    _assert_default_source_csvs(export_dir / "nodes")
    _assert_closed_relationship_ids(export_dir / "nodes", export_dir / "relationships")

    refresh = subprocess.run(
        [sys.executable, "scripts/refresh_public_ontologies.py"],
        cwd=ROOT, env=env, text=True, capture_output=True, timeout=1800,
    )
    assert refresh.returncode == 0, refresh.stdout + "\n" + refresh.stderr

    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD")),
    )
    try:
        with driver.session(database=database) as session:
            _assert_graph_contract(session)
    finally:
        driver.close()


def _assert_default_source_csvs(nodes_dir):
    expected = {
        "nodes_icfconcept.csv", "nodes_exmoconcept.csv", "nodes_painconcept.csv",
        "nodes_mondodisease.csv", "nodes_uberonconcept.csv", "nodes_hpoconcept.csv",
        "nodes_ontologyclass.csv", "nodes_ontologyproperty.csv",
        "nodes_ontologyindividual.csv",
    }
    actual = {p.name for p in nodes_dir.glob("nodes_*.csv")}
    assert expected <= actual
    excluded = {
        "nodes_copperconcept.csv", "nodes_khmoconcept.csv",
        "nodes_cbhaconcept.csv", "nodes_cbhaactivity.csv",
        "nodes_pmrconcept.csv", "nodes_mellodconcept.csv",
        "nodes_opeconcept.csv", "nodes_phyconcept.csv",
        "nodes_ontolococoncept.csv",
    }
    assert not (excluded & actual), f"excluded ontology CSV(s) emitted: {excluded & actual}"


def _assert_closed_relationship_ids(nodes_dir, rels_dir):
    ids = set()
    for path in nodes_dir.glob("nodes_*.csv"):
        with path.open(encoding="utf-8", newline="") as fh:
            ids.update(row[":ID"] for row in csv.DictReader(fh) if row.get(":ID"))
    missing = []
    for path in rels_dir.glob("*.csv"):
        with path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                for key in (":START_ID", ":END_ID"):
                    if row.get(key) and row[key] not in ids:
                        missing.append((path.name, key, row[key]))
    assert not missing, f"relationship endpoint(s) missing from staged nodes: {missing[:10]}"


def _assert_graph_contract(session):
    assert session.run("MATCH (n) RETURN count(n) AS c").single()["c"] > 100_000
    assert session.run("MATCH (n:ICFConcept) RETURN count(n) AS c").single()["c"] == 1509
    assert session.run("MATCH (n:HPOConcept) RETURN count(n) AS c").single()["c"] >= 30_000
    assert session.run("MATCH (n:MondoDisease) RETURN count(n) AS c").single()["c"] == 5000
    assert session.run("MATCH (n:UberonConcept) RETURN count(n) AS c").single()["c"] == 10000
    assert session.run("MATCH (n:EXMOConcept) RETURN count(n) AS c").single()["c"] == 220
    assert session.run("MATCH (n:PAINConcept) RETURN count(n) AS c").single()["c"] >= 600

    excluded = session.run("""
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label IN [
            'COPPERConcept','KHMOConcept','CBHAConcept','CBHAActivity',
            'PMRConcept','MELLODConcept','OPEConcept','PHYConcept','ONTOLOCOConcept'
        ])
        RETURN count(n) AS c
    """).single()["c"]
    assert excluded == 0

    hpo = session.run("""
        MATCH (:HPOConcept)-[r:RELATED_TO_ICF]->(:ICFConcept)
        RETURN count(r) AS total,
               sum(CASE WHEN r.method='curated'
                             AND r.match_type='explicit_code_pair'
                             AND r.review_status='unreviewed'
                             AND r.confidence=1.0 THEN 1 ELSE 0 END) AS valid
    """).single()
    assert hpo["total"] == 9
    assert hpo["valid"] == 9
    assert session.run("MATCH (:Patient)-[r:HAS_STAY]->(:Session) RETURN count(r) AS c").single()["c"] >= 1000
