"""Tests for build_csvs.resolve_id_collisions.

neo4j-admin import treats :ID as one keyspace across all node files and
silently drops later-file duplicates; the resolver renames later copies
("<PREFIX>:<id>") and rewrites the renamed file's relationship CSVs.
"""
import csv
from pathlib import Path

import pytest

from build_csvs import resolve_id_collisions


def _write_csv(path: Path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def _read_csv(path: Path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture
def graph_dirs(tmp_path):
    nodes = tmp_path / "nodes"
    rels = tmp_path / "relationships"
    nodes.mkdir()
    rels.mkdir()
    return nodes, rels


def test_first_file_wins_later_renamed(graph_dirs):
    nodes, rels = graph_dirs
    # alphabetically: copper before khmo
    _write_csv(nodes / "nodes_copperconcept.csv",
               [":ID", "code"], [{":ID": "BFO_0000002", "code": "BFO_0000002"}])
    _write_csv(nodes / "nodes_khmoconcept.csv",
               [":ID", "code"], [{":ID": "BFO_0000002", "code": "BFO_0000002"}])
    n = resolve_id_collisions(nodes, rels)
    assert n == 1
    assert _read_csv(nodes / "nodes_copperconcept.csv")[0][":ID"] == "BFO_0000002"
    assert _read_csv(nodes / "nodes_khmoconcept.csv")[0][":ID"] == "KHMO:BFO_0000002"


def test_renamed_file_rels_rewritten(graph_dirs):
    nodes, rels = graph_dirs
    _write_csv(nodes / "nodes_ontologyclass.csv",
               [":ID"], [{":ID": "http://x/UBERON_1"}])
    _write_csv(nodes / "nodes_uberonconcept.csv",
               [":ID"], [{":ID": "http://x/UBERON_1"}, {":ID": "http://x/UBERON_2"}])
    _write_csv(rels / "rel_subclass_of_uberon.csv",
               [":START_ID", ":END_ID", ":TYPE"],
               [{":START_ID": "http://x/UBERON_1", ":END_ID": "http://x/UBERON_2",
                 ":TYPE": "SUBCLASS_OF"}])
    resolve_id_collisions(nodes, rels)
    rel = _read_csv(rels / "rel_subclass_of_uberon.csv")[0]
    # uberon lost the shared id, so its rel endpoints follow the rename
    assert rel[":START_ID"] == "UBERON:http://x/UBERON_1"
    assert rel[":END_ID"] == "http://x/UBERON_2"  # uncontested id untouched


def test_unmapped_file_left_as_is(graph_dirs):
    nodes, rels = graph_dirs
    _write_csv(nodes / "nodes_exercise.csv",
               [":ID"], [{":ID": "shared"}, {":ID": "shared"}])
    _write_csv(nodes / "nodes_patient.csv",
               [":ID"], [{":ID": "shared"}])
    # nodes_exercise has no COLLISION_PREFIX entry: duplicates stay (import
    # drops them, same as before the resolver existed)
    n = resolve_id_collisions(nodes, rels)
    assert n == 0
    ids = [r[":ID"] for r in _read_csv(nodes / "nodes_exercise.csv")]
    assert ids == ["shared", "shared"]


def test_idempotent(graph_dirs):
    nodes, rels = graph_dirs
    _write_csv(nodes / "nodes_mellodconcept.csv", [":ID"], [{":ID": "Neoplasm"}])
    _write_csv(nodes / "nodes_ontolococoncept.csv", [":ID"], [{":ID": "Neoplasm"}])
    assert resolve_id_collisions(nodes, rels) == 1
    assert resolve_id_collisions(nodes, rels) == 0
    assert _read_csv(nodes / "nodes_ontolococoncept.csv")[0][":ID"] == "ONTOLOCO:Neoplasm"


def test_real_build_has_no_collisions():
    """After a full build the resolver must have left zero duplicate :IDs."""
    nodes_dir = Path("export/nodes")
    if not nodes_dir.exists() or not list(nodes_dir.glob("nodes_*.csv")):
        pytest.skip("export/nodes CSVs not built (run python build_csvs.py)")
    seen = set()
    dups = []
    for f in sorted(nodes_dir.glob("nodes_*.csv")):
        for row in csv.DictReader(open(f, encoding="utf-8")):
            nid = row.get(":ID")
            if not nid:
                continue
            if nid in seen:
                dups.append((f.name, nid))
            else:
                seen.add(nid)
    assert not dups, f"{len(dups)} duplicate :IDs remain, e.g. {dups[:5]}"
