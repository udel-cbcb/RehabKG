"""Tests for the opt-in public-candidate CSV export screen."""

import csv

from export_csv import filter_public_export


def _write(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _read(path):
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_filter_retains_allowed_nodes_and_only_closed_relationships(tmp_path):
    nodes = tmp_path / "nodes"
    rels = tmp_path / "relationships"
    nodes.mkdir()
    rels.mkdir()
    _write(nodes / "nodes_concept.csv", [":ID", "name", "source"], [
        {":ID": "ok:1", "name": "Allowed", "source": "Allowed"},
        {":ID": "no:1", "name": "Conditional", "source": "Conditional"},
        {":ID": "none:1", "name": "No source", "source": ""},
    ])
    _write(rels / "rel_links.csv", [":START_ID", ":END_ID", ":TYPE"], [
        {":START_ID": "ok:1", ":END_ID": "ok:1", ":TYPE": "SELF"},
        {":START_ID": "ok:1", ":END_ID": "no:1", ":TYPE": "LEAK"},
        {":START_ID": "missing", ":END_ID": "ok:1", ":TYPE": "DANGLING"},
    ])

    counts = filter_public_export(nodes, rels, {"Allowed"})

    assert counts == {
        "nodes_before": 3,
        "nodes_retained": 1,
        "relationships_before": 3,
        "relationships_retained": 1,
    }
    assert [row[":ID"] for row in _read(nodes / "nodes_concept.csv")] == ["ok:1"]
    assert [row[":TYPE"] for row in _read(rels / "rel_links.csv")] == ["SELF"]


def test_filter_drops_all_relationships_when_endpoint_node_file_is_missing(tmp_path):
    nodes = tmp_path / "nodes"
    rels = tmp_path / "relationships"
    nodes.mkdir()
    rels.mkdir()
    _write(rels / "rel_links.csv", [":START_ID", ":END_ID", ":TYPE"], [
        {":START_ID": "a", ":END_ID": "b", ":TYPE": "LINK"},
    ])

    counts = filter_public_export(nodes, rels, {"Allowed"})

    assert counts["relationships_retained"] == 0
    assert _read(rels / "rel_links.csv") == []


def test_default_loader_source_allowlist_excludes_removed_ontologies():
    from scripts.refresh_public_ontologies import DEFAULT_ONTOLOGY_SOURCE_SET

    assert DEFAULT_ONTOLOGY_SOURCE_SET == {
        "rehabo.owl", "icf.owl", "exmo.owl", "pain.owl", "mondo.owl",
        "uberon.owl", "hp.owl",
    }
    assert not ({"copper.owl", "khmo.owl", "cbha.owl", "nihss.owl"}
                & DEFAULT_ONTOLOGY_SOURCE_SET)


def test_exporter_default_ontology_families_are_allowlisted():
    import inspect
    import export_csv

    source = inspect.getsource(export_csv.export_ontologies)
    assert '"COPPERConcept"' not in source
    assert '"KHMOConcept"' not in source
    assert '"CBHAConcept"' not in source
    assert '"PAINConcept"' in source
    assert '"EXMOConcept"' in source
