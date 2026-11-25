"""Unit tests for the shared edge-provenance contract (provenance.py).

Pure-Python (no Neo4j): pins the validation rules, the preset vocabulary,
and the curated CSV status column against the contract's review_status
enum so a bad status string cannot silently create unparsable edges.
"""
import csv
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from provenance import (
    ASSESSMENT_MEASURES,
    EXACT_NAME_ICF,
    HIERARCHY_PROPAGATION,
    HPO_TO_ICF,
    KEYWORD_ICF_COPPER,
    KEYWORD_ICF_PMR,
    MAPS_TO_MONDO,
    METHODS,
    REVIEW_STATUSES,
    RMD_MEASURES,
    EXERCISE_PROGRESSES_TO,
    edge_props,
    backfill_csv_import_edges,
)

ROOT = Path(__file__).resolve().parent.parent
CONDITION_EXERCISE_CSV = ROOT / "curated" / "condition_exercise.csv"

CONTRACT_KEYS = {"method", "match_type", "confidence", "source", "review_status"}

ALL_PRESETS = [
    EXACT_NAME_ICF,
    KEYWORD_ICF_PMR,
    KEYWORD_ICF_COPPER,
    ASSESSMENT_MEASURES,
    HIERARCHY_PROPAGATION,
    HPO_TO_ICF,
    MAPS_TO_MONDO,
    RMD_MEASURES,
    EXERCISE_PROGRESSES_TO,
]


class TestEdgeProps:
    def test_returns_contract_keys(self):
        props = edge_props("curated", "exact_name", 0.9, "file.csv")
        assert set(props) == CONTRACT_KEYS
        assert props["review_status"] == "unreviewed"  # default

    def test_extra_none_values_dropped(self):
        props = edge_props("curated", "x", 0.5, "s", citation=None)
        assert "citation" not in props

    def test_extra_non_none_values_kept(self):
        props = edge_props("curated", "x", 0.5, "s", keyword="gait")
        assert props["keyword"] == "gait"

    @pytest.mark.parametrize("method", METHODS)
    def test_all_methods_accepted(self, method):
        edge_props(method, "x", 0.5, "s")

    @pytest.mark.parametrize("status", REVIEW_STATUSES)
    def test_all_review_statuses_accepted(self, status):
        edge_props("curated", "x", 0.5, "s", review_status=status)

    def test_rejects_bad_method(self):
        with pytest.raises(ValueError, match="method"):
            edge_props("llm", "x", 0.5, "s")

    def test_rejects_bad_review_status(self):
        with pytest.raises(ValueError, match="review_status"):
            edge_props("curated", "x", 0.5, "s", review_status="maybe")

    @pytest.mark.parametrize("conf", [-0.1, 1.1])
    def test_rejects_confidence_out_of_range(self, conf):
        with pytest.raises(ValueError, match="confidence"):
            edge_props("curated", "x", conf, "s")

    def test_rejects_empty_source(self):
        with pytest.raises(ValueError, match="source"):
            edge_props("curated", "x", 0.5, "")

    def test_confidence_coerced_to_float(self):
        props = edge_props("curated", "x", 1, "s")
        assert props["confidence"] == 1.0


class TestPresets:
    @pytest.mark.parametrize("props", ALL_PRESETS, ids=lambda p: p["source"])
    def test_preset_is_valid_contract(self, props):
        assert set(props) == CONTRACT_KEYS
        assert props["method"] in METHODS
        assert props["review_status"] in REVIEW_STATUSES
        assert 0.0 <= props["confidence"] <= 1.0
        assert props["source"]

    def test_hpo_to_icf_is_flagged_low_confidence(self):
        # The loose bidirectional CONTAINS matcher must stay <= 0.4 so
        # consumers filtering by confidence exclude it by default.
        assert HPO_TO_ICF["confidence"] == 0.4
        assert HPO_TO_ICF["match_type"] == "name_contains_bidirectional"
        assert HPO_TO_ICF["review_status"] == "unreviewed"

    def test_keyword_presets_share_match_type(self):
        for preset in (KEYWORD_ICF_PMR, KEYWORD_ICF_COPPER, ASSESSMENT_MEASURES):
            assert preset["match_type"] == "keyword_whole_word"

    def test_rule_sources_name_the_rule_not_the_entry_point(self):
        # Both load paths (import_bulk.py and rehabkg.py) share presets;
        # source strings must not mention a single entry-point module.
        for preset in (HPO_TO_ICF, MAPS_TO_MONDO):
            assert preset["source"].startswith("pipeline:")

    def test_explicit_hpo_icf_mapping_contract(self):
        props = edge_props(
            "curated", "explicit_code_pair", 1.0,
            "add_additional_data.py:HPO_TO_ICF_MAPPINGS",
            review_status="unreviewed",
        )
        assert props["method"] == "curated"
        assert props["match_type"] == "explicit_code_pair"
        assert props["confidence"] == 1.0
        assert props["review_status"] == "unreviewed"


class TestCuratedStatusVocabulary:
    def test_csv_statuses_are_valid_review_statuses(self):
        """Every curated CSV status value must be a contract review_status."""
        with open(CONDITION_EXERCISE_CSV, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert rows
        for row in rows:
            assert row["status"] in REVIEW_STATUSES, (
                f"CSV status {row['status']!r} not in {REVIEW_STATUSES}"
            )


class TestCsvImportBackfillExclusions:
    class _Result:
        def single(self):
            return {"c": 0}

    class _Session:
        def __init__(self):
            self.queries = []

        def run(self, query, **params):
            self.queries.append((query, params))
            return TestCsvImportBackfillExclusions._Result()

    def test_phase3_reviewed_mapping_keeps_its_curated_provenance(self):
        session = self._Session()
        backfill_csv_import_edges(session, rel_types=["MAPS_TO_ICF"])
        query, params = session.queries[0]
        assert params["source"] == "export:rel_maps_to_icf.csv"

    def test_other_relationships_use_normal_csv_import_backfill(self):
        session = self._Session()
        backfill_csv_import_edges(session, rel_types=["RECOMMENDS_EXERCISE"])
        query, _ = session.queries[0]
