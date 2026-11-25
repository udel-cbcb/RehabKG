"""MOTU outcome / MEASURED_BY parity between the two load paths (F3/F9).

Phase 0 found the bulk path silently dropped every 10m Walk Test outcome
the Cypher path creates (Barthel-only inline loop), and Phase 2 task 1
resolved F3 as an audit-query bug (`o.measure_name` does not exist).
Since then both paths consume etl_motu.build_motu_outcomes over
MOTU_OUTCOME_SPECS, so outcome content and MEASURED_BY links are
identical by construction. These tests pin that construction:

1. both load-path files consume the shared builder (no reimplementation);
2. the builder emits the expected outcome set from representative rows;
3. the spec's (scale_id, assessment) pairs exist in RMD_SCALES;
4. the audit joins MEASURED_BY instead of the phantom measure_name key.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from etl_motu import MOTU_OUTCOME_SPECS, build_motu_outcomes

REPO = os.path.join(os.path.dirname(__file__), "..")


def _read(path):
    with open(os.path.join(REPO, path), encoding="utf-8") as f:
        return f.read()


def _full_stay(anon, barthel_adm="85", barthel_dc="90",
               twt_adm="12.5", twt_dc="10.1"):
    return {
        "AnonymousID": anon,
        "BarthelAdmissionTotalScore": barthel_adm,
        "BarthelDischargeTotalScore": barthel_dc,
        "TWTInitialTime_m": twt_adm,
        "TWTDischargeTime_m": twt_dc,
    }


class TestSharedBuilderConsumedByBothPaths:
    """Source-level guard: one implementation, two import sites."""

    def test_build_csvs_imports_shared_builder(self):
        src = _read("build_csvs.py")
        assert "from etl_motu import build_motu_outcomes" in src, (
            "build_csvs.py must consume the shared MOTU outcome builder"
        )

    def test_bulk_path_has_no_inline_outcome_columns(self):
        # The Barthel/TWT column literals and outcome-id suffixes may live
        # only in MOTU_OUTCOME_SPECS (etl_motu.py) — an inline copy in the
        # bulk path is exactly how TWT outcomes got lost once already.
        src = _read("build_csvs.py")
        for literal in ("BarthelAdmissionTotalScore", "TWTInitialTime_m",
                        "BARTEL-ADM", "TWT-ADM", "barthel_scale_id"):
            assert literal not in src, (
                f"build_csvs.py hardcodes {literal!r} — use "
                "build_motu_outcomes/MOTU_OUTCOME_SPECS instead"
            )

    def test_cypher_path_builds_from_shared_builder(self):
        src = _read("etl_motu.py")
        assert "build_motu_outcomes" in src
        # load_outcomes must not rebuild rows inline anymore.
        assert "outcomes.append" not in src, (
            "etl_motu.load_outcomes rebuilds outcome rows inline instead "
            "of consuming build_motu_outcomes"
        )

    def test_both_paths_cover_barthel_and_twt(self):
        # MEASURED_BY parity needs both assessments in the single spec.
        assessments = {s[3] for s in MOTU_OUTCOME_SPECS}
        assert assessments == {"Barthel Index", "10 Meter Walk Test"}
        assert len(MOTU_OUTCOME_SPECS) == 4  # 2 scales x admission/discharge


class TestBuildMotuOutcomes:
    def test_full_row_yields_four_outcomes(self):
        outcomes = build_motu_outcomes([_full_stay("123")])
        assert len(outcomes) == 4
        by_id = {o["outcome_id"]: o for o in outcomes}
        assert set(by_id) == {
            "MOTU-STAY-123-BARTEL-ADM", "MOTU-STAY-123-BARTEL-DC",
            "MOTU-STAY-123-TWT-ADM", "MOTU-STAY-123-TWT-DC",
        }
        twt = by_id["MOTU-STAY-123-TWT-ADM"]
        assert twt == {
            "outcome_id": "MOTU-STAY-123-TWT-ADM",
            "stay_id": "MOTU-STAY-123",
            "assessment": "10 Meter Walk Test",
            "scale_id": "ASM-023",
            "value": "12.5",
            "unit": "seconds",
            "phase": "admission",
        }
        barthel = by_id["MOTU-STAY-123-BARTEL-ADM"]
        assert barthel["scale_id"] == "ASM-030"
        assert barthel["unit"] == ""

    def test_empty_columns_are_skipped(self):
        # NA strings are kept (they are real "recorded but unparseable"
        # values); only empty cells drop the outcome.
        outcomes = build_motu_outcomes([
            _full_stay("9", twt_adm="", twt_dc=""),
        ])
        ids = {o["outcome_id"] for o in outcomes}
        assert ids == {
            "MOTU-STAY-9-BARTEL-ADM", "MOTU-STAY-9-BARTEL-DC",
        }
        na_row = _full_stay("10", barthel_dc="NA")
        outcomes = build_motu_outcomes([na_row])
        assert len(outcomes) == 4  # 'NA' is truthy — outcome still exists

    def test_duplicate_ids_collapse_keep_last(self):
        # The raw file reuses AnonymousID across stays: Cypher MERGE and
        # the bulk :ID dict both keep the last row's properties.
        rows = [
            _full_stay("77", barthel_adm="10"),
            _full_stay("77", barthel_adm="55"),
        ]
        outcomes = build_motu_outcomes(rows)
        adm = [o for o in outcomes
               if o["outcome_id"] == "MOTU-STAY-77-BARTEL-ADM"]
        assert len(adm) == 1
        assert adm[0]["value"] == "55"

    def test_measured_by_pairs_match_scale_ids(self):
        # Every outcome must map to exactly one (scale_id) that exists in
        # the RMD set — this is the pair the two paths both write.
        outcomes = build_motu_outcomes([_full_stay("5")])
        pairs = {(o["outcome_id"], o["scale_id"]) for o in outcomes}
        assert pairs == {
            ("MOTU-STAY-5-BARTEL-ADM", "ASM-030"),
            ("MOTU-STAY-5-BARTEL-DC", "ASM-030"),
            ("MOTU-STAY-5-TWT-ADM", "ASM-023"),
            ("MOTU-STAY-5-TWT-DC", "ASM-023"),
        }

    def test_spec_pairs_exist_in_rmd_scales(self):
        from etl_datasets import RMD_SCALES
        by_id = {s["scale_id"]: s["name"] for s in RMD_SCALES}
        for _phase, col, _suffix, assessment, scale_id, _unit in MOTU_OUTCOME_SPECS:
            assert by_id.get(scale_id) == assessment, (
                f"MOTU_OUTCOME_SPECS ({col}) points at {scale_id}="
                f"{by_id.get(scale_id)!r}, expected {assessment!r}"
            )


class TestAuditJoinsMeasuredBy:
    """F3: the audit must group by the scale node, not a phantom key."""

    def test_no_phantom_measure_name(self):
        src = _read("scripts/audit_coverage.py")
        assert "measure_name" not in src, (
            "audit still queries Outcome.measure_name (does not exist — "
            "returns NULL for every row; join MEASURED_BY instead)"
        )

    def test_top_scales_joins_measured_by(self):
        src = _read("scripts/audit_coverage.py")
        assert "[:MEASURED_BY]" in src, (
            "audit top_scales must join (Outcome)-[:MEASURED_BY]->"
            "(AssessmentScale) and group by a.name"
        )
