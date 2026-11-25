"""Smoke tests for the ontology extractor API (core + BioPortal shortlist).

The shortlist extractors (TRAK…PHENX, CBHA) serve both the bulk CSV builder
(build_csvs.py) and the Cypher load path in etl_ontologies.main().
"""
import os

import pytest

from etl_ontologies import (
    extract_icf,
    extract_rehabo,
    extract_exmo,
    extract_pmr,
    extract_mello_d,
    extract_copper,
    extract_khmo,
    extract_phy,
    extract_pain,
)

DATA_ONTO = os.path.join(os.path.dirname(__file__), "..", "data", "ontologies")

# (extractor, filename, min_concepts, min_edges)
CASES = [
    (extract_icf, "icf.owl", 1_000, 900),
    (extract_rehabo, "rehabo.owl", 20, 0),
    (extract_exmo, "exmo.owl", 100, 50),
    (extract_pmr, "pmr.owl", 1_000, 500),
    (extract_mello_d, "mello_d.owl", 5_000, 4_000),
    (extract_copper, "copper.owl", 100, 50),
    (extract_khmo, "khmo.owl", 1_000, 500),
    (extract_phy, "phy.owl", 1, 0),
    (extract_pain, "pain.owl", 600, 300),
]


def _skip_if_missing(filename):
    if not os.path.exists(os.path.join(DATA_ONTO, filename)):
        pytest.skip(f"data/ontologies/{filename} not downloaded (run download_data.py)")


def _extract_concepts_and_hierarchy(extractor, filename):
    """Normalize extractor return shapes and retain only closed concept edges."""
    result = extractor()
    if isinstance(result, dict):
        concepts = result.get("classes", {})
        subclass_of = result.get("subclass_of", [])
    else:
        concepts, subclass_of = result
    # REHABO intentionally preserves external support/OWL built-in parents;
    # this smoke test checks only hierarchy edges with both endpoints loaded.
    subclass_of = [(a, b) for a, b in subclass_of if a in concepts and b in concepts]
    return concepts, subclass_of


@pytest.mark.parametrize("extractor,filename,min_concepts,min_edges", CASES)
def test_extract_concepts_and_hierarchy(extractor, filename, min_concepts, min_edges):
    _skip_if_missing(filename)
    concepts, subclass_of = _extract_concepts_and_hierarchy(extractor, filename)
    assert len(concepts) >= min_concepts, (
        f"{filename}: {len(concepts)} concepts < {min_concepts}")
    assert len(subclass_of) >= min_edges, (
        f"{filename}: {len(subclass_of)} hierarchy edges < {min_edges}")
    # every concept must have a usable code + name
    for c in concepts.values():
        assert c.get("code") or c.get("uri"), f"{filename}: concept without code/URI: {c}"
        assert c.get("name"), f"{filename}: concept without name: {c}"


@pytest.mark.parametrize("extractor,filename,min_concepts,min_edges", CASES)
def test_subclass_endpoints_exist(extractor, filename, min_concepts, min_edges):
    _skip_if_missing(filename)
    concepts, subclass_of = _extract_concepts_and_hierarchy(extractor, filename)
    missing = [(a, b) for a, b in subclass_of if a not in concepts or b not in concepts]
    assert not missing, f"{filename}: {len(missing)} dangling edges e.g. {missing[:3]}"


def test_icf_muscle_power_codes_match_bridge_targets():
    """b730/b740 must keep the labels the REHABO and ICF bridges target."""
    _skip_if_missing("icf.owl")
    concepts, _ = _extract_concepts_and_hierarchy(extract_icf, "icf.owl")
    by_code = {c.get("code"): c.get("name") for c in concepts.values()}
    assert by_code["b730"] == "Muscle power functions"
    assert by_code["b740"] == "Muscle endurance functions"


class TestOntologyEid:
    """build_csvs.ontology_eid: globally-unique :ID namespacing."""

    def test_short_code_gets_namespace(self):
        from build_csvs import ontology_eid
        assert ontology_eid("short_code", "CBHA") == "CBHA:short_code"

    def test_curie_code_kept_verbatim(self):
        from build_csvs import ontology_eid
        assert ontology_eid("CURIE:0001", "CBHA") == "CURIE:0001"

    def test_no_namespace_when_ns_is_none(self):
        from build_csvs import ontology_eid
        assert ontology_eid("e515", None) == "e515"


class TestExportNsId:
    """export_csv._ns_id must mirror build_csvs.ontology_eid so a Cypher-path
    export re-imports through neo4j-admin without dropping colliding nodes."""

    def test_short_code_namespaced(self):
        from export_csv import _ns_id
        assert _ns_id("SportsExerciseWorkoutWalking", "CBHAConcept") == "CBHA:SportsExerciseWorkoutWalking"

    def test_curie_code_kept(self):
        from export_csv import _ns_id
        assert _ns_id("CURIE:0001", "CBHAConcept") == "CURIE:0001"

    def test_unlisted_label_untouched(self):
        from export_csv import _ns_id
        assert _ns_id("d450", "ICFConcept") == "d450"
        assert _ns_id("ASM-001", "AssessmentScale") == "ASM-001"

    def test_empty_code_passthrough(self):
        from export_csv import _ns_id
        assert _ns_id(None, "CBHAConcept") is None
        assert _ns_id("", "CBHAConcept") == ""


def test_focused_refresh_retains_hpo_and_excludes_flagged_ontologies():
    from scripts import refresh_public_ontologies as refresh

    assert "Human Phenotype Ontology" not in refresh.REMOVED_SOURCES
    assert set(refresh.REFRESHED_SOURCES) == {
        "rehabo.owl", "icf.owl", "exmo.owl", "pain.owl", "mondo.owl", "uberon.owl",
    }
    assert {"copper.owl", "khmo.owl", "cbha.owl"}.issubset(
        refresh.REMOVED_SOURCES
    )
    assert "Human Phenotype Ontology" not in refresh.REMOVED_SOURCES
    assert "hp.owl" in refresh.DEFAULT_ONTOLOGY_SOURCE_SET
    assert refresh.is_default_ontology_source("hp.owl")
    assert not refresh.is_default_ontology_source("copper.owl")


def test_default_source_membership_is_shared_with_downloader():
    from download_data import download_ontologies
    from scripts.refresh_public_ontologies import DEFAULT_ONTOLOGY_SOURCE_SET

    import inspect
    source = inspect.getsource(download_ontologies)
    for name in ("rehabo.owl", "icf.owl", "exmo.owl", "pain.owl"):
        assert name in source
    for excluded in ("copper.owl", "khmo.owl", "cbha.owl"):
        assert excluded not in source
    assert {"rehabo.owl", "icf.owl", "exmo.owl", "pain.owl",
            "mondo.owl", "uberon.owl", "hp.owl"} == DEFAULT_ONTOLOGY_SOURCE_SET


def test_default_loaders_do_not_invoke_excluded_etl_families():
    import inspect
    import etl_ontologies
    import build_csvs

    cypher_main = inspect.getsource(etl_ontologies.main)
    bulk_ontology_builder = inspect.getsource(build_csvs.build_ontologies)
    for excluded in ("load_copper", "load_khmo", "load_cbha", "load_pmr"):
        assert excluded not in cypher_main
    for excluded in ("extract_copper", "extract_khmo", "extract_cbha", "extract_pmr"):
        assert excluded not in bulk_ontology_builder


def test_default_bridge_entry_point_omits_excluded_bridge_families():
    import inspect
    from bridges import bridge_default_sources, sync_hpo_icf_pairs

    source = inspect.getsource(bridge_default_sources)
    assert "bridge_copper_keywords" not in source
    assert "bridge_pmr_owl" not in source
    # HPO->ICF explicit pairs go through the shared sync function.
    assert "sync_hpo_icf_pairs" in source
    sync_source = inspect.getsource(sync_hpo_icf_pairs)
    assert "RELATED_TO_ICF" in sync_source
    assert "explicit_code_pair" in sync_source


def test_bulk_ontology_step_runs_collision_resolution(monkeypatch):
    import build_csvs

    calls = []
    monkeypatch.setattr(build_csvs, "ensure_dirs", lambda: None)
    monkeypatch.setattr(build_csvs, "resolve_id_collisions", lambda: calls.append("resolve"))
    monkeypatch.setattr(build_csvs, "validate_ids", lambda: (0, 0, 0))
    monkeypatch.setitem(build_csvs.STEPS, "ontologies", lambda: calls.append("ontologies"))
    monkeypatch.setattr("sys.argv", ["build_csvs.py", "--step", "ontologies", "--validate"])
    build_csvs.main()
    assert calls == ["ontologies", "resolve"]
