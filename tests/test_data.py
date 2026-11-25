"""Tests for data file existence and basic validity.

Data files under data/ are gitignored and only present in the dev
environment (downloaded via download_data.py). In CI, where the
BIOPORTAL_API_KEY secret may be unset, these tests self-skip rather
than fail — mirroring tests/test_ontology_extract.py.
"""
import os
import csv
import json
import pytest

DATA_ROOT = os.path.join(os.path.dirname(__file__), "..", "data")


def _skip_if_missing(rel):
    """Skip (not fail) when a gitignored data file is absent (CI)."""
    if not os.path.exists(os.path.join(DATA_ROOT, rel)):
        pytest.skip(f"data/{rel} not downloaded (run download_data.py)")


def exists(rel):
    _skip_if_missing(rel)
    p = os.path.join(DATA_ROOT, rel)
    assert os.path.exists(p), f"Missing: {rel}"
    return p


def file_size(rel):
    p = exists(rel)
    return os.path.getsize(p)


# ── Raw data ──────────────────────────────────────────────────────────────


class TestRawData:
    def test_free_exercise_db_json(self):
        p = exists("raw/free-exercise-db/free_exercise_db.json")
        with open(p) as f:
            data = json.load(f)
        assert len(data) >= 870, f"Expected >= 870 exercises, got {len(data)}"

    def test_motu_patient_csv(self):
        p = exists("raw/motu/Patient.csv")
        with open(p) as f:
            rows = list(csv.DictReader(f))
        assert len(rows) >= 1000

    def test_motu_hospital_stay_csv(self):
        p = exists("raw/motu/HospitalStay.csv")
        with open(p) as f:
            rows = list(csv.DictReader(f))
        assert len(rows) >= 1900

    def test_motu_fall_csv(self):
        p = exists("raw/motu/Fall.csv")
        with open(p) as f:
            rows = list(csv.DictReader(f))
        assert len(rows) >= 100

    def test_motu_knee_csv(self):
        p = exists("raw/motu/Knee.csv")
        with open(p) as f:
            rows = list(csv.DictReader(f))
        assert len(rows) >= 10

    def test_icd10_csv(self):
        p = exists("raw/icd10/icd10cm_data.csv")
        with open(p) as f:
            rows = list(csv.DictReader(f))
        assert len(rows) >= 74000, f"Expected >= 74K codes, got {len(rows)}"

    def test_clinicaltrials_extracted(self):
        p = exists("raw/clinicaltrials/clinicaltrials_extracted.json")
        with open(p) as f:
            data = json.load(f)
        assert len(data) >= 850

    def test_rehab_exercises(self):
        p = os.path.join(DATA_ROOT, "raw/rehab-exercises/open-rehab-exercises-main/exercises")
        if not os.path.isdir(p):
            pytest.skip("data/raw/rehab-exercises not downloaded (run download_data.py)")
        jsons = [f for f in os.listdir(p) if f.endswith(".json")]
        assert len(jsons) >= 70, f"Expected >= 70 exercise JSONs, got {len(jsons)}"


# ── Processed data ────────────────────────────────────────────────────────


class TestProcessedData:
    def test_exercises_nodes_csv(self):
        p = exists("processed/free-exercise-db/exercises_nodes.csv")
        with open(p) as f:
            rows = list(csv.DictReader(f))
        assert len(rows) >= 870

    def test_exercises_relationships_csv(self):
        p = exists("processed/free-exercise-db/exercises_relationships.csv")
        with open(p) as f:
            rows = list(csv.DictReader(f))
        assert len(rows) >= 3000


# ── Ontology files ────────────────────────────────────────────────────────


class TestOntologies:
    ONTOLOGIES = [
        ("icf.owl", 1_000_000),
        ("pmr.owl", 500_000),
        ("copper.owl", 100_000),
        ("exmo.owl", 500_000),
        ("rehabo.owl", 50_000),
        ("mondo.owl", 100_000_000),
        ("uberon.owl", 50_000_000),
        ("phy.owl", 5_000),
        ("mello_d.owl", 1_000_000),
        ("khmo.owl", 1_000_000),
        ("hp.owl", 50_000_000),
        ("ope.owl", 500_000),
        ("ontoloco.owl", 100_000),
        # BioPortal shortlist (2026-10)
        ("trak.owl", 300_000),
        ("frmo.owl", 500_000),
        ("pain.owl", 1_000_000),
        ("bcio.owl", 1_000_000),
        ("bctt.owl", 20_000),
        ("sto.owl", 1_000_000),
        ("paco.owl", 100_000),
    ]

    @pytest.mark.parametrize("filename,min_size", ONTOLOGIES)
    def test_ontology_exists_and_has_size(self, filename, min_size):
        p = exists(f"ontologies/{filename}")
        size = os.path.getsize(p)
        assert size >= min_size, f"{filename}: {size} < {min_size} bytes"
