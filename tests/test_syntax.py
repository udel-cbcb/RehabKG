"""Tests for Python script syntax and imports."""
import importlib
import os
import py_compile
import re

import pytest

SCRIPTS = [
    "add_provenance.py",
    "bridges.py",
    "connect_mondo.py",
    "download_data.py",
    "etl_datasets.py",
    "etl_ontologies.py",
    "import_bulk.py",
    "import_ontologies.py",
    "provenance.py",
    "rehabkg.py",
    "setup_neo4j_schema.py",
    "use_cases.py",
]

SUBDIR_SCRIPTS = [
    "curated/apply_decisions.py",
    "eval/run_gold.py",
    "scripts/audit_coverage.py",
    "scripts/sample_edges_for_audit.py",
]


@pytest.mark.parametrize("script", SCRIPTS + SUBDIR_SCRIPTS)
def test_script_compiles(script):
    """Every Python script should compile without syntax errors."""
    path = os.path.join(os.path.dirname(__file__), "..", script)
    assert os.path.exists(path), f"{script} not found"
    py_compile.compile(path, doraise=True)


@pytest.mark.parametrize(
    "module",
    ["neo4j", "dotenv", "csv", "json", "pathlib", "rdflib"],
)
def test_required_imports(module):
    """Required third-party modules should be importable."""
    importlib.import_module(module)


# Names the pipeline imports lazily inside functions. A py_compile pass
# cannot catch a missing name here — the failure would only surface
# mid-pipeline after the long loads (this actually happened once with
# bridges.link_conditions_to_exercises).
LAZY_IMPORTS = [
    ("bridges", "link_conditions_to_exercises"),
    ("bridges", "link_safety_edges"),
    ("bridges", "load_observation_seed"),
    ("bridges", "bridge_all"),
    ("bridges", "bridge_default_sources"),
    ("scripts.refresh_public_ontologies", "_rebuild_hpo_icf"),
    ("etl_ontologies", "bridge_muscles_to_icf"),
    ("add_additional_data", "load_hpo"),
    ("add_additional_data", "load_expanded_clinicaltrials"),
    ("import_ontologies", "main"),
    ("import_ontologies", "DISEASE_TO_ICD10"),
    ("setup_neo4j_schema", "main"),
    ("provenance", "edge_props"),
    ("provenance", "HPO_TO_ICF"),
    ("import_bulk", "post_load"),
    ("curated.apply_decisions", "update_graph"),
    ("eval.run_gold", "check_expected"),
    ("scripts.audit_coverage", "audit"),
    ("scripts.sample_edges_for_audit", "sample"),
    ("scripts.eval_hpo_icf_vs_core_sets", "render_report"),
    # BioPortal shortlist extractors used lazily by build_csvs.build_ontologies
    ("etl_ontologies", "extract_pain"),
    ("etl_ontologies", "extract_cbha"),
    ("etl_ontologies", "CBHA_TO_ICF"),
    ("etl_ontologies", "bridge_activity_ontologies_to_icf"),
    ("etl_datasets", "RMD_SCALES"),
    ("etl_datasets", "SCALE_ICF_LINKS"),
    ("etl_datasets", "EXERCISE_PROGRESSIONS"),
]


@pytest.mark.parametrize("module_name,attr", LAZY_IMPORTS)
def test_lazy_pipeline_imports_resolve(module_name, attr):
    """Every lazily-imported pipeline name must exist at import time."""
    module = importlib.import_module(module_name)
    assert hasattr(module, attr), (
        f"{module_name}.{attr} is imported lazily by the pipeline but missing"
    )


# Matches the node pattern in CREATE CONSTRAINT / CREATE INDEX statements:
# FOR (var:Label) or FOR (var:Label1:Label2). Captures everything between
# the first ':' and the closing ')' so a label with a space inside
# (e.g. the historical "KneE PADPatient" typo) is caught.
_FOR_LABEL_RE = re.compile(r"FOR\s*\(\s*\w+\s*:([^)]+)\)")


def test_cypher_labels_have_no_spaces():
    """Labels in schema.cypher constraint/index statements must not contain spaces.

    A space inside a label (e.g. ``FOR (p:KneE PADPatient)``) is a Cypher
    syntax error that only surfaces when the file is fed to cypher-shell;
    this guard caught it at test time instead (see schema.cypher git
    history, constraint knee_patient_id_unique).
    """
    path = os.path.join(os.path.dirname(__file__), "..", "schema.cypher")
    assert os.path.exists(path), "schema.cypher not found"
    with open(path, encoding="utf-8") as f:
        content = f.read()
    statements = [
        line for line in content.splitlines()
        if "CREATE CONSTRAINT" in line or "CREATE INDEX" in line
    ]
    assert statements, "no CREATE CONSTRAINT/INDEX statements found"
    checked = 0
    for line in statements:
        for match in _FOR_LABEL_RE.finditer(line):
            labels = match.group(1).split(":")
            for label in labels:
                checked += 1
                assert label.strip(), f"empty label in: {line.strip()}"
                assert " " not in label, (
                    f"label {label!r} contains a space (Cypher syntax error): "
                    f"{line.strip()}"
                )
    assert checked > 0, f"no labels parsed from: {statements[:3]}"
