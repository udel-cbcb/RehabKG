"""Unit tests for bridges.py keyword matching and the curated CSV.

These are pure-Python tests (no Neo4j): they pin the whole-word matcher
semantics and validate curated/condition_exercise.csv so a bad row
cannot silently change clinical-adjacent edges.
"""
import csv
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bridges import (
    ASSESSMENT_ICF_BRIDGES,
    CONDITION_EXERCISE_CSV,
    CONDITION_ICD10_OVERRIDES_CSV,
    COPPER_KEYWORDS,
    EVIDENCE_COLUMNS,
    OBSERVATION_SEED_CSV,
    ICF_CORE_SETS_CSV,
    PMROWL_KEYWORDS,
    SAFETY_CSV,
    SAFETY_REL_TYPES,
    SCALE_IDENTIFIERS_CSV,
    SYNTHETIC_PATIENT_ID,
    _word_pattern,
    KEYWORD_GROUP_CONFIDENCE,
    apply_scale_identifiers,
    condition_matches_keywords,
    apply_icf_core_set_rows,
    evidence_props,
    load_condition_exercise_rows,
    load_icd10_override_rows,
    load_observation_seed_rows,
    load_scale_identifier_rows,
    load_icf_core_set_rows,
    link_conditions_to_exercises,
    link_safety_edges,
    load_safety_rows,
    name_matches_keyword,
)
from provenance import (
    ICD10_BIND_CONFIDENCE,
    REVIEW_STATUSES,
    icd10_edge_props,
)
from scripts.eval_hpo_icf_vs_core_sets import load_register, render_report


class TestIcfCoreSets:
    def test_header_only_register_is_valid_noop(self):
        assert ICF_CORE_SETS_CSV.is_file()
        assert load_icf_core_set_rows() == []

        class Session:
            def run(self, *args, **kwargs):
                raise AssertionError("empty Core Set register must not write")

        assert apply_icf_core_set_rows(Session()) == (0, [])

    def test_core_set_loader_wires_both_paths(self):
        root = os.path.dirname(os.path.dirname(__file__))
        for filename, marker in (("rehabkg.py", "apply_icf_core_set_rows(session)"),
                                 ("import_bulk.py", "apply_icf_core_set_rows(s)")):
            with open(os.path.join(root, filename), encoding="utf-8") as f:
                assert marker in f.read()

    def test_report_handles_empty_human_input_register(self):
        assert load_register() == []
        text = render_report([], {
            "core_codes": [], "reachable_codes": set(),
            "hpo_icf_target_codes": {"d450"}, "uncovered_target_codes": 1,
            "per_code": {},
        })
        assert "register `curated/icf_core_sets.csv` is empty" in text
        assert "Distinct target codes not present" in text


class TestWholeWordMatching:
    """name_matches_keyword must reject substring false positives."""

    @pytest.mark.parametrize("name", ["Chromosome", "chromatin", "Rhythm"])
    def test_rom_does_not_match_substrings(self, name):
        assert not name_matches_keyword(name, "rom")

    @pytest.mark.parametrize("name", ["ROM", "active rom", "rom exercises"])
    def test_rom_matches_whole_words(self, name):
        assert name_matches_keyword(name, "rom")

    @pytest.mark.parametrize("name", ["False", "Falling rocks", "waterfall"])
    def test_fall_does_not_match_substrings(self, name):
        assert not name_matches_keyword(name, "fall")

    @pytest.mark.parametrize("name", ["Fall risk", "falls", "Falls"])
    def test_fall_and_falls_match_whole_words(self, name):
        assert name_matches_keyword(name, "fall") or name_matches_keyword(name, "falls")

    @pytest.mark.parametrize("name", ["Administrative scale", "handling"])
    def test_adl_does_not_match_substrings(self, name):
        assert not name_matches_keyword(name, "adl")

    @pytest.mark.parametrize("name", ["ADL independence", "Basic ADL"])
    def test_adl_matches_whole_words(self, name):
        assert name_matches_keyword(name, "adl")

    def test_fatigue_matches_but_not_fatigued_substring_after_word(self):
        # 'fatigued' contains 'fatigue' + 'd'; word boundary rejects it.
        assert name_matches_keyword("Fatigue", "fatigue")
        assert not name_matches_keyword("Fatigued ness", "fatigue")

    def test_multiword_underscored_class_names(self):
        assert name_matches_keyword("Range_of_motion", "range_of_motion")
        assert not name_matches_keyword("Range of motion", "range_of_motion")

    def test_word_pattern_is_neo4j_full_match_shape(self):
        pat = _word_pattern("rom")
        assert pat.startswith("(?i).*")
        assert pat.endswith(".*")
        assert r"\brom\b" in pat

    def test_exclude_keyword_prevents_heat_stroke_match(self):
        assert condition_matches_keywords("Stroke", ["stroke"], ["heat stroke"])
        assert not condition_matches_keywords(
            "Heat stroke", ["stroke"], ["heat stroke"])
        assert not condition_matches_keywords(
            "Heatstroke", ["stroke"], ["heat stroke"])

    def test_keyword_confidence_is_below_exact_id_bindings(self):
        assert KEYWORD_GROUP_CONFIDENCE == 0.6
        assert KEYWORD_GROUP_CONFIDENCE < ICD10_BIND_CONFIDENCE


class TestKeywordTables:
    """The in-code keyword tables must not regress to the old bugs."""

    def test_no_duplicate_keywords_per_table(self):
        for table in (PMROWL_KEYWORDS, COPPER_KEYWORDS, ASSESSMENT_ICF_BRIDGES):
            kws = [kw for kw, _ in table]
            dupes = {k for k in kws if kws.count(k) > 1}
            assert not dupes, f"duplicate keywords: {dupes}"

    def test_reviewed_icf_code_fixes(self):
        # Reviewer-verified ICF browser corrections (2026-10-22).
        pmr = dict(PMROWL_KEYWORDS)
        assert pmr["reach"] == "d445"      # reaching/throwing
        assert pmr["throw"] == "d445"
        assert pmr["grasp"] == "d440"      # manipulating objects
        assert pmr["grip"] == "d440"

    def test_assessment_has_falls_and_turning_variants(self):
        assess = dict(ASSESSMENT_ICF_BRIDGES)
        assert assess["fall"] == "d455"
        assert assess["falls"] == "d455"
        assert assess["turning"] == "d455"


class TestConditionExerciseCSV:
    """curated/condition_exercise.csv schema and content checks."""

    REQUIRED_COLUMNS = {
        "match_type", "condition_key", "exclude_keywords", "exercise_name",
        "category", "rationale", "citation", "reviewed_by", "status",
    }

    def test_csv_exists(self):
        assert CONDITION_EXERCISE_CSV.exists(), (
            f"{CONDITION_EXERCISE_CSV} missing — both load paths read it"
        )

    def test_schema_and_match_types(self):
        rows = load_condition_exercise_rows()
        assert rows, "CSV must not be empty"
        with open(CONDITION_EXERCISE_CSV, newline="", encoding="utf-8") as f:
            header = set(csv.DictReader(f).fieldnames or [])
        expected = self.REQUIRED_COLUMNS | set(EVIDENCE_COLUMNS)
        assert expected <= header, (
            f"missing columns: {expected - header}"
        )
        for row in rows:
            assert row["match_type"] in ("keyword_group", "icd10")
            assert row["exercise_name"].strip()
            assert row["status"].strip()

    def test_stroke_rows_exclude_heat_stroke(self):
        for row in load_condition_exercise_rows():
            if row["match_type"] != "keyword_group":
                continue
            if "stroke" in row["condition_key"].lower():
                assert "heat stroke" in row["exclude_keywords"].lower(), row



    def test_rows_start_unreviewed(self):
        # Until a clinician fills citation/reviewed_by, everything is
        # explicitly unreviewed; flip rows only together with a citation.
        for row in load_condition_exercise_rows():
            if not row["citation"].strip():
                assert row["status"] == "unreviewed", row

    def test_evidence_props_drop_empty_cells(self):
        # Empty CSV evidence cells must become absent props, not ''.
        row = {col: "" for col in EVIDENCE_COLUMNS}
        assert evidence_props(row) == {col: None for col in EVIDENCE_COLUMNS}
        row["citation_doi"] = "10.1000/test"
        props = evidence_props(row)
        assert props["citation_doi"] == "10.1000/test"
        assert props["citation_pmid"] is None


class TestSafetyCSV:
    """curated/safety_contraindications.csv schema and content checks."""

    REQUIRED_COLUMNS = {
        "rel_type", "match_type", "condition_key", "exclude_keywords",
        "exercise_name", "rationale", "citation", "reviewed_by", "status",
    } | set(EVIDENCE_COLUMNS)

    def test_csv_exists(self):
        assert SAFETY_CSV.exists(), (
            f"{SAFETY_CSV} missing — link_safety_edges reads it"
        )

    def test_schema_and_allowlists(self):
        rows = load_safety_rows()
        assert len(rows) >= 5, "need at least 5 seed safety rows"
        with open(SAFETY_CSV, newline="", encoding="utf-8") as f:
            header = set(csv.DictReader(f).fieldnames or [])
        assert self.REQUIRED_COLUMNS <= header, (
            f"missing columns: {self.REQUIRED_COLUMNS - header}"
        )
        for row in rows:
            assert row["rel_type"] in SAFETY_REL_TYPES, row
            assert row["match_type"] in ("keyword_group", "icd10")
            assert row["exercise_name"].strip()
            assert row["rationale"].strip(), "safety rows need a rationale"
            assert row["status"].strip()

    def test_stroke_rows_exclude_heat_stroke(self):
        for row in load_safety_rows():
            if row["match_type"] != "keyword_group":
                continue
            if "stroke" in row["condition_key"].lower():
                assert "heat stroke" in row["exclude_keywords"].lower(), row

    def test_fracture_rows_keep_plural_variant(self):
        for row in load_safety_rows():
            if row["match_type"] != "keyword_group":
                continue
            if "fracture" in row["condition_key"].lower():
                assert "fractures" in row["condition_key"].lower(), row

    def test_all_seed_rows_unreviewed(self):
        # Safety seeds must never ship as approved — they are candidates
        # for clinician review, not clinical advice.
        for row in load_safety_rows():
            assert row["status"] == "unreviewed", row

    def test_pilot_stroke_gait_seeds_present(self):
        rows = load_safety_rows()
        precautions = [r for r in rows if r["rel_type"] == "PRECAUTION"]
        contraindications = [r for r in rows if r["rel_type"] == "CONTRAINDICATION"]
        stroke_rows = [r for r in precautions if "stroke" in r["condition_key"]]
        assert len(stroke_rows) >= 3, "stroke-gait pilot needs >=3 stroke precautions"
        assert len(contraindications) >= 1, "need at least one contraindication seed"

    def test_seed_rationales_flag_review_needed(self):
        # Every seed rationale must say it needs review so nobody mistakes
        # an unreviewed seed for clinical guidance.
        for row in load_safety_rows():
            assert "review" in row["rationale"].lower(), row


class TestObservationSeedCSV:
    """curated/observation_seed.csv schema and safety checks."""

    REQUIRED_COLUMNS = {
        "observation_id", "patient_id", "feature", "value", "unit",
        "observed_at", "device", "icf_code",
    }

    def test_csv_exists(self):
        assert OBSERVATION_SEED_CSV.exists(), (
            f"{OBSERVATION_SEED_CSV} missing — load_observation_seed reads it"
        )

    def test_schema_and_numeric_values(self):
        rows = load_observation_seed_rows()
        assert len(rows) >= 5, "need at least 5 seed observations"
        with open(OBSERVATION_SEED_CSV, newline="", encoding="utf-8") as f:
            header = set(csv.DictReader(f).fieldnames or [])
        assert self.REQUIRED_COLUMNS <= header, (
            f"missing columns: {self.REQUIRED_COLUMNS - header}"
        )
        for row in rows:
            assert row["observation_id"].startswith("SYNTHETIC-"), row
            float(row["value"])  # must parse as float
            assert row["feature"].strip()
            assert row["unit"].strip()
            assert row["observed_at"].strip()
            assert row["icf_code"].strip()

    def test_patients_are_synthetic_only(self):
        # Never attach synthetic observations to real (MOTU) patients.
        rows = load_observation_seed_rows()
        pids = {r["patient_id"] for r in rows}
        assert pids == {SYNTHETIC_PATIENT_ID}
        for pid in pids:
            assert pid.startswith("SYNTHETIC-")

    def test_gait_features_cover_pilot(self):
        features = {r["feature"] for r in load_observation_seed_rows()}
        assert "gait_speed_m_s" in features
        assert "six_minute_walk_distance_m" in features


class TestConditionIcd10Overrides:
    """curated/condition_icd10_overrides.csv — Gate 0 policy register.

    These rows are the ONLY sanctioned source of Condition.icd10_code
    besides exact-name Mondo propagation, so the schema is enforced here:
    bad codes or premature approvals must fail offline, before any load.
    """

    REQUIRED_COLUMNS = {
        "condition_name", "icd10_code", "source", "rationale",
        "review_status", "reviewed_by", "reviewed_on",
    }
    # ICD-10-CM: letter + 2 digits + optional 4th char + optional .extension.
    ICD10_RE = re.compile(r"^[A-Z][0-9]{2}[0-9A-Z]?(\.[0-9A-Z]{1,4})?$")

    def test_csv_exists(self):
        assert CONDITION_ICD10_OVERRIDES_CSV.exists(), (
            f"{CONDITION_ICD10_OVERRIDES_CSV} missing — "
            "set_condition_icd10_codes reads it"
        )

    def test_schema_and_content(self):
        rows = load_icd10_override_rows()
        assert rows, "overrides CSV must not be empty"
        with open(CONDITION_ICD10_OVERRIDES_CSV, newline="", encoding="utf-8") as f:
            header = set(csv.DictReader(f).fieldnames or [])
        assert self.REQUIRED_COLUMNS <= header, (
            f"missing columns: {self.REQUIRED_COLUMNS - header}"
        )
        seen = set()
        for row in rows:
            name = row["condition_name"].strip()
            code = row["icd10_code"].strip()
            assert name and code, f"blank fields: {row}"
            assert self.ICD10_RE.match(code), f"bad ICD-10 code {code!r}"
            assert row["source"].strip(), f"source required: {row}"
            assert row["rationale"].strip(), f"rationale required: {row}"
            assert row["review_status"] in REVIEW_STATUSES, row
            key = (name.lower(), code)
            assert key not in seen, f"duplicate override row: {key}"
            seen.add(key)

    def test_unreviewed_rows_without_reviewer(self):
        # Approvals must arrive with a reviewer recorded; a bare status flip
        # cannot smuggle an agent-authored code binding past review.
        for row in load_icd10_override_rows():
            if not row["reviewed_by"].strip():
                assert row["review_status"] == "unreviewed", row

    def test_all_codes_are_the_curated_rows_need(self):
        # The overrides exist to light up curated match_type=icd10 rows;
        # every code in the register must appear in condition_key of at
        # least one curated row (and vice versa is checked live).
        needed = {
            r["condition_key"].strip()
            for r in load_condition_exercise_rows()
            if r["match_type"] == "icd10"
        }
        supplied = {r["icd10_code"].strip() for r in load_icd10_override_rows()}
        assert supplied <= needed, (
            f"override codes not requested by any curated row: "
            f"{supplied - needed}"
        )
        # Codes neither Mondo nor the register can supply simply cannot
        # fire; warn via the curated README instead of failing here — the
        # live liveness test enforces presence on the canonical graph.


class TestIcd10EdgeProps:
    """provenance.icd10_edge_props — match_type derives from icd10_source."""

    def test_mondo_source_maps_to_icd10_via_mondo(self):
        p = icd10_edge_props("curated/condition_exercise.csv", "unreviewed",
                             "mondo_exact_name")
        assert p["match_type"] == "icd10_via_mondo"
        assert p["confidence"] == ICD10_BIND_CONFIDENCE == 0.7
        assert p["method"] == "curated"
        assert p["review_status"] == "unreviewed"

    def test_override_source_maps_to_icd10_override(self):
        p = icd10_edge_props("curated/condition_exercise.csv", "unreviewed",
                             "curated_override")
        assert p["match_type"] == "icd10_override"
        assert p["confidence"] == 0.7

    def test_unknown_icd10_source_raises(self):
        # A graph mutated outside the Gate 0 policy must not mint edges
        # under a made-up match_type.
        with pytest.raises(ValueError, match="icd10_source"):
            icd10_edge_props("curated/condition_exercise.csv", "unreviewed",
                             "mystery_origin")

    def test_invalid_review_status_still_raises(self):
        with pytest.raises(ValueError, match="review_status"):
            icd10_edge_props("curated/condition_exercise.csv", "approved?",
                             "mondo_exact_name")


class TestLoadPathParity:
    """Both load paths must call the shared ICD-10 step, before the loader.

    The two paths (rehabkg.py link_post_additional, import_bulk.py
    post_load) share bridges.set_condition_icd10_codes; if either call site
    drifts or runs after link_conditions_to_exercises, curated icd10 rows
    silently stop binding on that path. Source-level guard: cheap, offline,
    and runs on every commit. (The fixture-based Cypher parity test lands
    with Phase 3.)
    """

    CALL = "set_condition_icd10_codes("
    BEFORE = "link_conditions_to_exercises("

    @pytest.mark.parametrize("path", ["rehabkg.py", "import_bulk.py"])
    def test_shared_step_called_before_loader(self, path):
        full = os.path.join(os.path.dirname(__file__), "..", path)
        with open(full, encoding="utf-8") as f:
            src = f.read()
        # Match the call sites (name + paren), not comment/docstring mentions.
        assert self.CALL in src, f"{path} never calls {self.CALL[:-1]}"
        assert self.BEFORE in src, f"{path} never calls {self.BEFORE[:-1]}"
        assert src.index(self.CALL) < src.index(self.BEFORE), (
            f"{path}: {self.CALL[:-1]} must run BEFORE {self.BEFORE[:-1]} — "
            "the curated icd10 rows bind on Condition.icd10_code set by "
            "that step"
        )

    def test_step_shared_not_reimplemented(self):
        # The Cypher must live in bridges.py exactly once, not be copy-pasted
        # into either path (both paths only import-and-call).
        for path in ("rehabkg.py", "import_bulk.py"):
            full = os.path.join(os.path.dirname(__file__), "..", path)
            with open(full, encoding="utf-8") as f:
                src = f.read()
            assert "icd10_source = 'mondo_exact_name'" not in src, (
                f"{path} reimplements the policy Cypher inline"
            )
        import bridges
        assert hasattr(bridges, self.CALL[:-1])

    @pytest.mark.parametrize("path", ["rehabkg.py", "import_bulk.py"])
    def test_scale_identifier_loader_called_by_both_paths(self, path):
        # Phase 2: curated/scale_identifiers.csv must load on both graphs.
        full = os.path.join(os.path.dirname(__file__), "..", path)
        with open(full, encoding="utf-8") as f:
            src = f.read()
        assert "apply_scale_identifiers(" in src, (
            f"{path} never calls apply_scale_identifiers"
        )

class TestScaleIdentifiersCSV:
    """curated/scale_identifiers.csv — external identifier register.

    LOINC cells are HUMAN INPUT from the official LOINC distribution,
    never inferred; the schema is enforced so any fill is safe. The
    shipped register carries 17 LOINC fills (2.83, all still
    `unreviewed`) and empty ICF cells; the all-empty no-op contract is
    exercised on cleared cells.
    """

    REQUIRED_COLUMNS = {
        "scale_id", "name", "loinc_code", "loinc_long_name", "icf_codes",
        "source_url", "review_status", "reviewed_by", "reviewed_on",
    }
    # LOINC concept numbers: 1–6 digits in LOINC 2.83 (14,290 ACTIVE
    # 6-digit codes, e.g. 104047-6), separator dash, 1+ digit instance.
    LOINC_RE = re.compile(r"^\d{1,6}-\d$")
    ICF_CODE_RE = re.compile(r"^[a-z][0-9]{2}[0-9a-z]*$")

    def test_csv_exists(self):
        assert SCALE_IDENTIFIERS_CSV.exists(), (
            f"{SCALE_IDENTIFIERS_CSV} missing — apply_scale_identifiers "
            "reads it"
        )

    def test_header_and_row_count(self):
        with open(SCALE_IDENTIFIERS_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            header = set(reader.fieldnames or [])
            rows = list(reader)
        assert self.REQUIRED_COLUMNS <= header, (
            f"missing columns: {self.REQUIRED_COLUMNS - header}"
        )
        assert len(rows) == 40, f"expected 40 RMD scales, got {len(rows)}"

    def test_rows_mirror_rmd_scales(self):
        from etl_datasets import RMD_SCALES
        register = {(r["scale_id"].strip(), r["name"].strip())
                    for r in load_scale_identifier_rows()}
        rmd = {(s["scale_id"], s["name"]) for s in RMD_SCALES}
        assert register == rmd, (
            f"register/RMD mismatch: missing={rmd - register}, "
            f"extra={register - rmd}"
        )

    def test_scale_ids_unique_and_named(self):
        rows = load_scale_identifier_rows()
        ids = [r["scale_id"].strip() for r in rows]
        assert len(ids) == len(set(ids)), "duplicate scale_id in register"
        for r in rows:
            assert r["name"].strip(), f"blank name: {r}"

    def test_identifier_cells_well_formed_when_filled(self):
        # Filled identifier cells must match the external vocabularies;
        # empty cells stay allowed (ICF fill is still HUMAN INPUT).
        for r in load_scale_identifier_rows():
            loinc = r["loinc_code"].strip()
            assert not loinc or self.LOINC_RE.match(loinc), (
                f"{r['scale_id']}: bad LOINC code {loinc!r}")
            codes = [c.strip() for c in
                     r["icf_codes"].split(";") if c.strip()]
            for code in codes:
                assert self.ICF_CODE_RE.match(code), (
                    f"{r['scale_id']}: bad ICF code {code!r}")
            url = r["source_url"].strip()
            assert not url or url.startswith(("http://", "https://")), (
                f"{r['scale_id']}: source_url must be a URL: {url!r}")

    def test_unreviewed_rows_without_reviewer(self):
        for r in load_scale_identifier_rows():
            assert r["review_status"] in REVIEW_STATUSES, r
            if not r["reviewed_by"].strip():
                assert r["review_status"] == "unreviewed", r

    def test_filled_loinc_rows_are_self_consistent(self):
        # A filled LOINC code must carry its long name and a source_url
        # that points at that exact code (LOINC fill landed from 2.83;
        # still unreviewed until a human records reviewed_by).
        for r in load_scale_identifier_rows():
            loinc = r["loinc_code"].strip()
            if not loinc:
                continue
            assert r["loinc_long_name"].strip(), (
                f"{r['scale_id']}: loinc_code {loinc} without long name")
            url = r["source_url"].strip()
            assert url and loinc in url, (
                f"{r['scale_id']}: source_url {url!r} must reference {loinc}")
            assert r["review_status"] == "unreviewed" or r["reviewed_by"].strip(), (
                f"{r['scale_id']}: reviewed status without reviewed_by")


class _StubResult:
    def __init__(self, count):
        self._count = count

    def single(self):
        return {"c": self._count}


class _StubSession:
    """Minimal session double: MATCH-count queries answered from flags,
    everything else recorded and treated as a zero-count write."""

    def __init__(self, scale_match=1, edge_match=1):
        self.scale_match = scale_match
        self.edge_match = edge_match
        self.calls = []

    def run(self, query, **params):
        self.calls.append((query, params))
        if "RETURN count(a) AS c" in query:
            return _StubResult(self.scale_match)
        if "MERGE (a)-[rel:MAPS_TO_ICF]" in query:
            return _StubResult(self.edge_match)
        return _StubResult(0)


class TestKeywordEdgeProvenance:
    """Keyword-group edges carry lower confidence and a curation basis."""

    @staticmethod
    def _row(**overrides):
        row = {
            "match_type": "keyword_group",
            "condition_key": "stroke",
            "exclude_keywords": "heat stroke",
            "exercise_name": "Balance",
            "category": "",
            "rationale": "",
            "citation": "",
            "reviewed_by": "",
            "status": "unreviewed",
        }
        row.update(overrides)
        return row

    def _edge_props(self, monkeypatch, loader, linker, **overrides):
        monkeypatch.setattr(f"bridges.{loader}", lambda: [self._row(**overrides)])
        session = _StubSession()
        linker(session)
        writes = [(q, p) for q, p in session.calls
                  if "MERGE (c)-[rel" in q and "SET rel += $props" in q]
        assert writes, "expected a keyword-group edge write"
        return writes[0][1]["props"], writes[0][0]

    def test_recommends_keyword_edges_use_keyword_confidence(self, monkeypatch):
        props, query = self._edge_props(
            monkeypatch, "load_condition_exercise_rows",
            link_conditions_to_exercises)
        assert props["confidence"] == KEYWORD_GROUP_CONFIDENCE == 0.6
        assert props["curation_basis"] == "keyword_group"
        assert "c.name =~ $kw0" in query
        assert "NOT (c.name =~ $ex0)" in query

    def test_safety_keyword_edges_use_keyword_confidence(self, monkeypatch):
        props, query = self._edge_props(
            monkeypatch, "load_safety_rows", link_safety_edges,
            rel_type="PRECAUTION", match_type="keyword_group")
        assert props["confidence"] == KEYWORD_GROUP_CONFIDENCE == 0.6
        assert props["curation_basis"] == "keyword_group"
        assert "c.name =~ $kw0" in query
        assert "NOT (c.name =~ $ex0)" in query


class TestApplyScaleIdentifiers:
    """Loader semantics — the Phase 2 acceptance in offline form."""

    def test_all_empty_register_is_a_noop_without_error(self, monkeypatch):
        # Acceptance: "scale_identifiers.csv loads idempotently with
        # all-empty identifiers without error" — zero writes, zero reads.
        # The shipped register now carries LOINC fills, so the contract
        # is exercised on a cleared copy of the real rows.
        rows = [dict(r, loinc_code="", loinc_long_name="", icf_codes="",
                     source_url="")
                for r in load_scale_identifier_rows()]
        monkeypatch.setattr("bridges.load_scale_identifier_rows",
                            lambda: rows)
        session = _StubSession()
        matched, edges = apply_scale_identifiers(session)
        assert (matched, edges) == (0, 0)
        assert session.calls == [], (
            "all-empty identifier cells must not hit the database"
        )
        # idempotent: a second run is equally silent
        session2 = _StubSession()
        assert apply_scale_identifiers(session2) == (0, 0)
        assert session2.calls == []

    def test_nonempty_cells_write_props_and_edges(self, monkeypatch):
        rows = [{
            "scale_id": "ASM-001", "name": "Berg Balance Scale",
            "loinc_code": "1234-5", "loinc_long_name": "Berg balance",
            "icf_codes": "b235", "source_url": "https://loinc.org/1234-5",
            "review_status": "unreviewed", "reviewed_by": "", "reviewed_on": "",
        }]
        monkeypatch.setattr("bridges.load_scale_identifier_rows",
                            lambda: rows)
        session = _StubSession(scale_match=1, edge_match=1)
        matched, edges = apply_scale_identifiers(session)
        assert (matched, edges) == (1, 1)
        queries = [q for q, _ in session.calls]
        # 1: existence check, 2: prop write, 3: ICF edge MERGE
        assert len(queries) == 3
        assert "SET a += $props" in queries[1]
        prop_write = session.calls[1][1]["props"]
        assert prop_write == {
            "loinc_code": "1234-5", "loinc_long_name": "Berg balance",
            "source_url": "https://loinc.org/1234-5",
        }
        edge_props_written = session.calls[2][1]["props"]
        assert edge_props_written["method"] == "curated"
        assert edge_props_written["match_type"] == "scale_icf_register"
        assert edge_props_written["confidence"] == 1.0
        assert edge_props_written["review_status"] == "unreviewed"

    def test_unknown_scale_id_writes_nothing(self, monkeypatch):
        rows = [{"scale_id": "ASM-999", "name": "Ghost Scale",
                 "loinc_code": "9999-9", "loinc_long_name": "",
                 "icf_codes": "", "source_url": "",
                 "review_status": "unreviewed",
                 "reviewed_by": "", "reviewed_on": ""}]
        monkeypatch.setattr("bridges.load_scale_identifier_rows",
                            lambda: rows)
        session = _StubSession(scale_match=0)
        matched, edges = apply_scale_identifiers(session)
        assert (matched, edges) == (0, 0)
        assert len(session.calls) == 1, (
            "unknown scale_id must not be written or edged"
        )

    def test_missing_icf_target_reports_zero_edges(self, monkeypatch):
        rows = [{"scale_id": "ASM-001", "name": "Berg Balance Scale",
                 "loinc_code": "", "loinc_long_name": "",
                 "icf_codes": "z999", "source_url": "",
                 "review_status": "unreviewed",
                 "reviewed_by": "", "reviewed_on": ""}]
        monkeypatch.setattr("bridges.load_scale_identifier_rows",
                            lambda: rows)
        session = _StubSession(scale_match=1, edge_match=0)
        matched, edges = apply_scale_identifiers(session)
        assert (matched, edges) == (1, 0)

    def test_blank_scale_id_raises(self, monkeypatch):
        rows = [{"scale_id": "  ", "name": "X", "loinc_code": "1-1",
                 "loinc_long_name": "", "icf_codes": "", "source_url": "",
                 "review_status": "unreviewed",
                 "reviewed_by": "", "reviewed_on": ""}]
        monkeypatch.setattr("bridges.load_scale_identifier_rows",
                            lambda: rows)
        with pytest.raises(ValueError, match="scale_id"):
            apply_scale_identifiers(_StubSession())

    def test_partial_fill_writes_only_nonempty_fields(self, monkeypatch):
        # Empty cells must never overwrite a previously filled value with
        # an empty string — they are skipped, so fills are additive.
        rows = [{"scale_id": "ASM-001", "name": "Berg Balance Scale",
                 "loinc_code": "4444-4", "loinc_long_name": "",
                 "icf_codes": "", "source_url": "",
                 "review_status": "approved", "reviewed_by": "dr x",
                 "reviewed_on": "2026-10-22"}]
        monkeypatch.setattr("bridges.load_scale_identifier_rows",
                            lambda: rows)
        session = _StubSession(scale_match=1)
        apply_scale_identifiers(session)
        prop_write = session.calls[1][1]["props"]
        assert prop_write == {"loinc_code": "4444-4"}, (
            "only non-empty cells may be written"
        )
