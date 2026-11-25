"""Opt-in Cypher-vs-bulk parity test.

Builds the focused CSV export, imports it with ``neo4j-admin`` into a
disposable Neo4j container, runs the bulk post-load bridges, and compares the
result with the committed focused-refresh baseline in
``eval/bulk_parity_baseline.json``.

Set ``REHABKG_BULK_PARITY=1`` to run. Requires Docker and the local ``data/``
source files. Ontology hierarchy (SUBCLASS_OF) is intentionally excluded: the
focused refresh only rebuilds selected source-owned hierarchy, while the bulk
path also emits Mondo/Uberon/HPO/EXMO hierarchy.
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "eval" / "bulk_parity_baseline.json"
PASSWORD = "testpass"
NEO4J_IMAGE = "neo4j:5.26.29-community"


def _enabled():
    return os.getenv("REHABKG_BULK_PARITY") == "1"


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _run(cmd, env, timeout, label):
    result = subprocess.run(
        cmd, cwd=ROOT, env=env, text=True, capture_output=True,
        timeout=timeout,
    )
    assert result.returncode == 0, (
        f"{label} failed (exit {result.returncode})\n"
        f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    return result


def _wait_for_bolt(uri, timeout=120):
    driver = GraphDatabase.driver(uri, auth=("neo4j", PASSWORD))
    deadline = time.time() + timeout
    try:
        while True:
            try:
                driver.verify_connectivity()
                return driver
            except Exception:
                if time.time() >= deadline:
                    raise
                time.sleep(2)
    except Exception:
        driver.close()
        raise


@pytest.mark.parity
@pytest.mark.slow
@pytest.mark.skipif(not _enabled(), reason="set REHABKG_BULK_PARITY=1 to run bulk parity")
def test_bulk_import_matches_focused_snapshot(tmp_path):
    if shutil.which("docker") is None:
        pytest.skip("docker is not available")
    if not (ROOT / "data" / "ontologies" / "rehabo.owl").is_file():
        pytest.skip("local data/ontologies source files are not staged")

    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    export_dir = tmp_path / "export"
    import_dir = tmp_path / "import"
    data_dir = tmp_path / "data"
    container = f"rehabkg-parity-{uuid.uuid4().hex[:8]}"
    port = _free_port()
    bulk_uri = f"bolt://127.0.0.1:{port}"
    driver = None

    env = os.environ.copy()
    env.update({
        "REHABKG_EXPORT_DIR": str(export_dir),
        "REHABKG_DATA_DIR": str(ROOT / "data"),
        "NEO4J_BULK_TEST_MODE": "1",
        "NEO4J_BULK_IMPORT_DIR": str(import_dir),
        "NEO4J_BULK_DATA_DIR": str(data_dir),
        "NEO4J_DATABASE": "neo4j",
    })

    try:
        _run([sys.executable, "build_csvs.py", "--validate", "--clean"],
             env, timeout=900, label="build_csvs")
        _run([sys.executable, "import_bulk.py", "--skip-export", "--skip-postload"],
             env, timeout=900, label="bulk import")

        run_cmd = [
            "docker", "run", "-d", "--name", container,
            "-p", f"127.0.0.1:{port}:7687",
            f"--volume={data_dir}:/data",
            "-e", f"NEO4J_AUTH=neo4j/{PASSWORD}",
        ]
        plugins = ROOT / "docker" / "plugins"
        if (plugins / "apoc-5.26.29-core.jar").is_file():
            run_cmd += [
                f"--volume={plugins}:/plugins",
                "-e", "NEO4J_dbms_security_procedures_unrestricted=apoc.*",
            ]
        run_cmd.append(NEO4J_IMAGE)
        _run(run_cmd, env, timeout=120, label="start Neo4j")

        driver = _wait_for_bolt(bulk_uri)

        post_env = env.copy()
        post_env.pop("NEO4J_BULK_TEST_MODE", None)
        post_env.update({
            "NEO4J_URI": bulk_uri,
            "NEO4J_PASSWORD": PASSWORD,
            "NEO4J_DATABASE": "neo4j",
        })
        _run([sys.executable, "-c", "import import_bulk; import_bulk.post_load()"],
             post_env, timeout=900, label="bulk post_load")

        with driver.session(database="neo4j") as session:
            total = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            assert total == baseline["total_nodes"]

            actual_nodes = {
                (row["label"], row["source"]): row["count"]
                for row in session.run("""
                    MATCH (n)
                    WITH labels(n) AS labels, n.source AS source
                    UNWIND labels AS label
                    RETURN label, source, count(*) AS count
                """)
            }
            expected_nodes = {
                (row["label"], row["source"]): row["count"]
                for row in baseline["node_label_sources"]
            }
            assert actual_nodes == expected_nodes

            for rel_type, expected in baseline["relationship_counts"].items():
                actual = session.run(
                    f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS c"
                ).single()["c"]
                assert actual == expected, f"{rel_type}: {actual} != {expected}"

        gold_path = tmp_path / "gold.json"
        _run([sys.executable, "eval/run_gold.py", "--json", str(gold_path)],
             post_env, timeout=300, label="gold questions")
        gold = json.loads(gold_path.read_text(encoding="utf-8"))
        assert gold["total"] == baseline["gold"]["total"]
        assert gold["failed"] == baseline["gold"]["failed"]
    finally:
        subprocess.run(["docker", "rm", "-f", container],
                       capture_output=True, text=True)
        if driver is not None:
            driver.close()
