"""Offline tests for curated/apply_decisions.py (no Neo4j required).

The review loop contract:
  - approved requires a citation; rejected does not
  - unknown keys are refused with errors (exit path), never silently skipped
  - dry_run leaves the CSV untouched
  - blank decision rows are not in the workload (load_decisions filters)
"""

import csv
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "curated"))

import apply_decisions as ad  # noqa: E402


@pytest.fixture
def curated_copy(tmp_path):
    """Copy the real curated CSVs into tmp; return (condition_path, safety_path)."""
    src_cond = REPO / "curated" / "condition_exercise.csv"
    src_safety = REPO / "curated" / "safety_contraindications.csv"
    cond = tmp_path / "condition_exercise.csv"
    safety = tmp_path / "safety_contraindications.csv"
    shutil.copy(src_cond, cond)
    shutil.copy(src_safety, safety)
    return cond, safety


def _read_row(path, exercise_name):
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["exercise_name"] == exercise_name:
                return row
    raise AssertionError(f"no row with exercise_name={exercise_name!r}")


def _decision(file, match_type, condition_key, exercise_name, decision,
              reviewed_by="Dr Test", reviewed_on="2026-10-22",
              citation="", rel_type=""):
    return {
        "file": file,
        "match_type": match_type,
        "rel_type": rel_type,
        "condition_key": condition_key,
        "exercise_name": exercise_name,
        "decision": decision,
        "reviewed_by": reviewed_by,
        "reviewed_on": reviewed_on,
        "citation": citation,
        "comment": "",
    }


def test_approve_with_citation_applies(curated_copy):
    cond, _ = curated_copy
    decisions = [_decision(
        "condition_exercise.csv", "keyword_group",
        "low back pain;back pain;lumbar", "Physioball Hip Bridge",
        "approved", citation="10.1000/lbp-study")]
    applied, errors = ad.apply_to_csv(cond, decisions)
    assert not errors, errors
    assert len(applied) == 1
    row = _read_row(cond, "Physioball Hip Bridge")
    assert row["status"] == "approved"
    assert row["reviewed_by"] == "Dr Test"
    assert row["reviewed_on"] == "2026-10-22"
    assert row["citation"] == "10.1000/lbp-study"


def test_reject_without_citation_applies(curated_copy):
    cond, _ = curated_copy
    decisions = [_decision(
        "condition_exercise.csv", "keyword_group",
        "low back pain;back pain;lumbar", "Physioball Hip Bridge",
        "rejected")]
    applied, errors = ad.apply_to_csv(cond, decisions)
    assert not errors, errors
    row = _read_row(cond, "Physioball Hip Bridge")
    assert row["status"] == "rejected"


def test_approve_without_citation_refused(curated_copy):
    cond, _ = curated_copy
    decisions = [_decision(
        "condition_exercise.csv", "keyword_group",
        "low back pain;back pain;lumbar", "Physioball Hip Bridge",
        "approved")]  # no citation
    applied, errors = ad.apply_to_csv(cond, decisions)
    assert not applied
    assert len(errors) == 1
    assert "requires a citation" in errors[0]
    row = _read_row(cond, "Physioball Hip Bridge")
    assert row["status"] == "unreviewed"  # untouched


def test_unknown_key_refused(curated_copy):
    cond, _ = curated_copy
    decisions = [_decision(
        "condition_exercise.csv", "keyword_group",
        "no such key", "No Such Exercise", "rejected")]
    applied, errors = ad.apply_to_csv(cond, decisions)
    assert not applied
    assert len(errors) == 1
    assert "unknown row refused" in errors[0]


def test_dry_run_writes_nothing(curated_copy):
    cond, _ = curated_copy
    before = cond.read_text(encoding="utf-8")
    decisions = [_decision(
        "condition_exercise.csv", "keyword_group",
        "low back pain;back pain;lumbar", "Physioball Hip Bridge",
        "approved", citation="10.1000/lbp-study")]
    applied, errors = ad.apply_to_csv(cond, decisions, dry_run=True)
    assert not errors
    assert len(applied) == 1
    assert cond.read_text(encoding="utf-8") == before  # untouched


def test_safety_row_with_rel_type_key(curated_copy):
    _, safety = curated_copy
    # Find one real safety row to approve
    with open(safety, newline="", encoding="utf-8") as f:
        row = next(csv.DictReader(f))
    decisions = [_decision(
        "safety_contraindications.csv", row["match_type"],
        row["condition_key"], row["exercise_name"],
        "approved", citation="10.1000/safety-study", rel_type=row["rel_type"])]
    applied, errors = ad.apply_to_csv(safety, decisions)
    assert not errors, errors
    updated = _read_row(safety, row["exercise_name"])
    assert updated["status"] == "approved"
    assert updated["citation"] == "10.1000/safety-study"


def test_load_decisions_filters_blank(tmp_path):
    path = tmp_path / "d.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "file", "match_type", "condition_key", "exercise_name",
            "decision", "reviewed_by", "reviewed_on"])
        w.writeheader()
        w.writerow({"file": "condition_exercise.csv", "match_type": "keyword_group",
                    "condition_key": "x", "exercise_name": "y",
                    "decision": "", "reviewed_by": "", "reviewed_on": ""})
        w.writerow({"file": "condition_exercise.csv", "match_type": "keyword_group",
                    "condition_key": "x2", "exercise_name": "y2",
                    "decision": "rejected", "reviewed_by": "Dr", "reviewed_on": "2026-10-22"})
    rows = ad.load_decisions(path)
    assert len(rows) == 1
    assert rows[0]["decision"] == "rejected"


def test_load_decisions_missing_columns(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("file,decision\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        ad.load_decisions(path)


def test_invalid_decision_refused(curated_copy):
    cond, _ = curated_copy
    decisions = [_decision(
        "condition_exercise.csv", "keyword_group",
        "low back pain;back pain;lumbar", "Physioball Hip Bridge",
        "maybe")]
    applied, errors = ad.apply_to_csv(cond, decisions)
    assert not applied
    assert len(errors) == 1
    assert "invalid decision" in errors[0]
