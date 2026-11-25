"""Offline tests for the vocabulary/dataset/schema composition classifier."""

import json
from pathlib import Path

from scripts.graph_composition import (
    CATEGORIES,
    DATASET_LABELS,
    SCHEMA_LABELS,
    VOCABULARY_LABELS,
    classify_labels,
)

MANIFEST = Path(__file__).resolve().parent.parent / "eval" / "public_ontology_refresh_manifest.json"


def test_vocabulary_labels_win_over_domain_labels():
    assert classify_labels(["ICFConcept", "BodyFunction"]) == "vocabulary"
    assert classify_labels(["REHABOConcept", "OntologyClass"]) == "vocabulary"
    assert classify_labels(["ICD10Code"]) == "vocabulary"


def test_dataset_labels_are_classified_once():
    assert classify_labels(["Exercise"]) == "dataset"
    assert classify_labels(["Muscle", "BodyPart"]) == "dataset"
    assert classify_labels(["Patient"]) == "dataset"


def test_schema_and_unknown_labels():
    assert classify_labels(["NodeType"]) == "schema"
    assert classify_labels(["RelType"]) == "schema"
    assert classify_labels(["SomethingNew"]) == "other"
    assert classify_labels([]) == "other"


def test_label_sets_are_disjoint():
    assert not (VOCABULARY_LABELS & DATASET_LABELS)
    assert not (VOCABULARY_LABELS & SCHEMA_LABELS)
    assert not (DATASET_LABELS & SCHEMA_LABELS)
    assert set(CATEGORIES) == {"vocabulary", "dataset", "schema", "other"}


def test_manifest_labels_are_all_classified():
    if not MANIFEST.exists():
        return
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    labels = {
        row["label"]
        for row in manifest.get("validation", {}).get(
            "after_source_label_counts", [])
    }
    known = VOCABULARY_LABELS | DATASET_LABELS | SCHEMA_LABELS
    assert labels <= known, f"unclassified labels: {labels - known}"
