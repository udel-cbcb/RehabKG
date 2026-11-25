"""Tests for Neo4j graph connectivity, schema, and data integrity.

Note on bulk vs Cypher path: some node/relationship minimums below assume a
full Cypher-path graph (rehabkg.py), including the network-expanded clinical
trials (~1,300+), the 37-scale RMD set, TARGETS_ANATOMY/PROGRESSES_TO from
add_additional_data, and HPO's full 30k load. The offline bulk-import path
(import_bulk.py) ships a deterministic subset (856 trials, 22 curated
scales) and will fail those volume assertions — that is a known content
gap, not a wiring bug. The structural bridges (STUDIES_CONDITION,
MAPS_TO_MONDO, RECOMMENDS_EXERCISE, bridge_all) run on both paths.
"""
import pytest
from dotenv import load_dotenv

from db import get_driver

load_dotenv()


@pytest.fixture(scope="session")
def driver():
    """Shared Neo4j driver for all graph tests."""
    d = get_driver()
    yield d
    d.close()


@pytest.fixture(scope="session")
def session(driver):
    """Shared session for read-only graph queries."""
    s = driver.session()
    yield s
    s.close()


def run_count(session, query):
    return session.run(query).single()["cnt"]


# ── Connectivity ──────────────────────────────────────────────────────────


class TestConnectivity:
    def test_connection(self, session):
        result = session.run("RETURN 1 AS test").single()
        assert result["test"] == 1

    def test_node_count(self, session):
        count = run_count(session, "MATCH (n) RETURN count(n) AS cnt")
        assert count >= 100_000, f"Expected >= 100K nodes, got {count}"

    def test_relationship_count(self, session):
        count = run_count(session, "MATCH ()-[r]->() RETURN count(r) AS cnt")
        assert count >= 25_000, f"Expected >= 25K relationships, got {count}"


# ── Schema: Constraints ───────────────────────────────────────────────────


class TestSchema:
    EXPECTED_CONSTRAINTS = {
        "patient_patient_id_unique",
        "condition_code_unique",
        "exercise_exercise_id_unique",
        "bodypart_part_id_unique",
        "muscle_muscle_id_unique",
        "equipment_equipment_id_unique",
        "session_session_id_unique",
        "outcome_outcome_id_unique",
        "icfconcept_code_unique",
        "observation_observation_id_unique",
    }

    def test_constraints_exist(self, session):
        result = session.run("SHOW CONSTRAINTS").data()
        names = {r.get("name", "") for r in result}
        for c in self.EXPECTED_CONSTRAINTS:
            assert c in names, f"Missing constraint: {c}"


# ── Node integrity ────────────────────────────────────────────────────────


class TestNodeIntegrity:
    MIN_COUNTS = {
        "Exercise": 900,
        "Patient": 1000,
        "Session": 1000,
        "Outcome": 1500,
        "Observation": 5,
        "ClinicalTrial": 1300,
        "Condition": 1200,
        "ICD10Code": 70_000,
        "ICFConcept": 100,
        "EXMOConcept": 100,
        "PAINConcept": 500,
        "MondoDisease": 1000,
        "UberonConcept": 1000,
        "HPOConcept": 30_000,
        "OntologyClass": 200,
        "OntologyProperty": 30,
        "OntologyIndividual": 20,
        "REHABOConcept": 50,
        "AssessmentScale": 30,
        "AdverseEvent": 100,
        "BodyPart": 10,
        "Muscle": 10,
        "Equipment": 5,
    }

    @pytest.mark.parametrize("label,min_count", list(MIN_COUNTS.items()))
    def test_node_minimum(self, session, label, min_count):
        count = run_count(session, f"MATCH (n:{label}) RETURN count(n) AS cnt")
        assert count >= min_count, f"{label}: {count} < {min_count}"

    REMOVED_ONTOLOGY_LABELS = (
        "MELLODConcept", "TRAKConcept", "FRMOConcept", "BCIOConcept",
        "BCTTConcept", "STOConcept", "PACOConcept", "MSOConcept",
        "POEMConcept", "PHENXConcept", "NIHSSConcept", "ACVDConcept",
    )

    @pytest.mark.parametrize("label", REMOVED_ONTOLOGY_LABELS)
    def test_removed_ontology_labels_are_absent(self, session, label):
        count = run_count(session, f"MATCH (n:{label}) RETURN count(n) AS cnt")
        assert count == 0, f"removed source was reloaded: {label} has {count} nodes"

    FOCUSED_REFRESH_EXCLUDED_LABELS = (
        "COPPERConcept", "KHMOConcept", "CBHAConcept", "CBHAActivity",
    )

    @pytest.mark.parametrize("label", FOCUSED_REFRESH_EXCLUDED_LABELS)
    def test_focused_refresh_excluded_unreviewed_ontology_labels(self, session, label):
        count = run_count(session, f"MATCH (n:{label}) RETURN count(n) AS cnt")
        assert count == 0, f"excluded from focused refresh but found {count} :{label} nodes"

    def test_exercises_have_muscles(self, session):
        count = run_count(session, """
            MATCH (e:Exercise)-[:TARGETS_PRIMARY]->(m:Muscle)
            RETURN count(DISTINCT e) AS cnt
        """)
        assert count >= 800, f"Only {count} exercises linked to muscles"

    def test_exercises_have_equipment(self, session):
        count = run_count(session, """
            MATCH (e:Exercise)-[:REQUIRES]->(eq:Equipment)
            RETURN count(DISTINCT e) AS cnt
        """)
        assert count >= 700, f"Only {count} exercises linked to equipment"

    def test_patients_have_stays(self, session):
        count = run_count(session, """
            MATCH (p:Patient)-[:HAS_STAY]->(s:Session)
            RETURN count(DISTINCT p) AS cnt
        """)
        assert count >= 1000, f"Only {count} patients with stays"

    def test_sessions_have_outcomes(self, session):
        count = run_count(session, """
            MATCH (s:Session)-[:HAS_OUTCOME]->(o:Outcome)
            RETURN count(DISTINCT s) AS cnt
        """)
        assert count >= 1000, f"Only {count} sessions with outcomes"


# ── Relationship integrity ────────────────────────────────────────────────


class TestRelationshipIntegrity:
    MIN_RELS = {
        "RECOMMENDS_EXERCISE": 50,
        "PRECAUTION": 4,
        "CONTRAINDICATION": 2,
        "STUDIES_CONDITION": 1000,
        "TARGETS_PRIMARY": 800,
        "TARGETS_SECONDARY": 1000,
        "REQUIRES": 700,
        "HAS_ICD10": 1000,
        "RELATED_TO_ICF": 9,
        "TARGETS_ANATOMY": 400,
        "MAPS_TO_UBERON": 5,
        "PROGRESSES_TO": 5,
        "MEASURES": 15,
    }

    def test_hpo_icf_explicit_links_have_complete_provenance(self, session):
        rows = session.run("""
            MATCH (:HPOConcept)-[r:RELATED_TO_ICF]->(:ICFConcept)
            RETURN count(r) AS total,
                   sum(CASE WHEN r.method = 'curated'
                                  AND r.match_type = 'explicit_code_pair'
                                  AND r.confidence = 1.0
                                  AND r.review_status = 'unreviewed'
                                  AND r.source = 'add_additional_data.py:HPO_TO_ICF_MAPPINGS'
                            THEN 1 ELSE 0 END) AS valid
        """).single()
        assert rows["total"] == 9
        assert rows["valid"] == 9

    def test_excluded_ontology_bridge_types_absent(self, session):
        # There are no ontology nodes for these source families in the focused
        # graph; bridge strategies must not recreate their edges.
        count = run_count(session, """
            MATCH ()-[r:MAPS_TO_ICF]->(n)
            WHERE n:COPPERConcept OR n:KHMOConcept
            RETURN count(r) AS cnt
        """)
        assert count == 0

    @pytest.mark.parametrize("rel_type,min_count", list(MIN_RELS.items()))
    def test_relationship_minimum(self, session, rel_type, min_count):
        count = run_count(session, f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS cnt")
        assert count >= min_count, f"{rel_type}: {count} < {min_count}"


# ── Use case queries ──────────────────────────────────────────────────────


class TestUseCaseQueries:
    def test_uc1_exercise_recommendation(self, session):
        results = list(session.run("""
            MATCH (c:Condition)-[:RECOMMENDS_EXERCISE]->(e:Exercise)
            WHERE toLower(c.name) CONTAINS 'osteoarthritis'
            RETURN count(e) AS cnt
        """))
        assert results[0]["cnt"] > 0, "UC1: No exercises for osteoarthritis"

    def test_uc2_clinical_trial_matching(self, session):
        results = list(session.run("""
            MATCH (t:ClinicalTrial)-[:STUDIES_CONDITION]->(c:Condition)
            WHERE toLower(c.name) CONTAINS 'low back pain'
            AND t.status IN ['RECRUITING', 'NOT_YET_RECRUITING', 'ENROLLING_BY_INVITATION']
            RETURN count(t) AS cnt
        """))
        assert results[0]["cnt"] > 0, "UC2: No recruiting trials for low back pain"

    def test_uc3_outcome_prediction(self, session):
        results = list(session.run("""
            MATCH (p:Patient)-[:HAS_STAY]->(s:Session)-[:HAS_OUTCOME]->(o:Outcome)
            WHERE s.amputation_side = 'R'
            AND o.outcome_id CONTAINS 'BARTEL'
            RETURN count(p) AS cnt
        """))
        assert results[0]["cnt"] > 100, "UC3: Not enough outcome data"

    def test_uc4_icf_pathway(self, session):
        results = list(session.run("""
            MATCH (c:Condition)-[:RECOMMENDS_EXERCISE]->(e:Exercise)
                   -[:TARGETS_PRIMARY]->(m:Muscle)
            WHERE toLower(c.name) CONTAINS 'shoulder impingement'
            RETURN count(e) AS cnt
        """))
        assert results[0]["cnt"] > 0, "UC4: No shoulder impingement exercises"

    def test_uc5_assessment_scales(self, session):
        results = list(session.run("""
            MATCH (a:AssessmentScale)
            WHERE a.domain = 'balance'
            RETURN count(a) AS cnt
        """))
        assert results[0]["cnt"] >= 5, "UC5: Not enough balance scales"

    def test_uc6_equipment_usage(self, session):
        results = list(session.run("""
            MATCH (eq:Equipment)<-[:REQUIRES]-(e:Exercise)
            RETURN eq.name AS equipment, count(DISTINCT e) AS exercises
            ORDER BY exercises DESC
            LIMIT 1
        """))
        assert results[0]["exercises"] > 50, "UC6: Top equipment has < 50 exercises"

    def test_uc7_cohort_analysis(self, session):
        results = list(session.run("""
            MATCH (p:Patient)-[:HAS_STAY]->(s:Session)-[:HAS_OUTCOME]->(o:Outcome)
            WHERE o.outcome_id CONTAINS 'BARTEL' AND o.outcome_id CONTAINS 'DC'
            RETURN s.amputation_cause AS cause, count(DISTINCT p) AS patients
        """))
        causes = {r["cause"] for r in results}
        assert "vascular" in causes or "traumatic" in causes, "UC7: Missing cause data"

    def test_uc8_muscle_condition_map(self, session):
        results = list(session.run("""
            MATCH (c:Condition)-[:RECOMMENDS_EXERCISE]->(e:Exercise)
                   -[:TARGETS_PRIMARY]->(m:Muscle)
            RETURN c.name AS condition, count(DISTINCT m) AS muscles
            ORDER BY muscles DESC
            LIMIT 1
        """))
        assert results[0]["muscles"] >= 1, "UC8: No muscle-condition mappings"


# ── ICD-10 specific ──────────────────────────────────────────────────────


class TestICD10:
    def test_icd10_count(self, session):
        count = run_count(session, "MATCH (n:ICD10Code) RETURN count(n) AS cnt")
        assert count >= 74_000, f"ICD-10: {count} < 74000"

    def test_mondo_icd10_connections(self, session):
        count = run_count(session, """
            MATCH ()-[:HAS_ICD10]->(:ICD10Code) RETURN count(*) AS cnt
        """)
        assert count >= 1000, f"Mondo-ICD10: {count} < 1000"

    def test_icd10_codes_have_descriptions(self, session):
        count = run_count(session, """
            MATCH (i:ICD10Code)
            WHERE i.description IS NOT NULL AND i.description <> ''
            RETURN count(i) AS cnt
        """)
        assert count >= 70_000, f"ICD-10 descriptions: {count} < 70000"


# ── Observation layer (synthetic stroke-gait pilot seed) ──────────────────


class TestObservationLayer:
    def test_synthetic_patient_exists(self, session):
        r = session.run("""
            MATCH (p:Patient {patient_id: 'SYNTHETIC-GAIT-001'})
            RETURN p.source AS source
        """).single()
        assert r is not None, "synthetic demo patient missing"
        assert r["source"] == "synthetic_demo"

    def test_observations_linked_to_patient(self, session):
        count = run_count(session, """
            MATCH (:Patient {patient_id: 'SYNTHETIC-GAIT-001'})
                  -[:HAS_OBSERVATION]->(o:Observation)
            RETURN count(o) AS cnt
        """)
        assert count >= 5, f"only {count} observations on synthetic patient"

    def test_observations_map_to_icf(self, session):
        count = run_count(session, """
            MATCH (:Observation)-[:MAPS_TO_ICF]->(:ICFConcept)
            RETURN count(*) AS cnt
        """)
        assert count == 0, (
            "the verified 2026-11-05 snapshot has no Observation→ICF links; "
            "do not infer mappings during load")

    def test_observations_have_numeric_values(self, session):
        r = session.run("""
            MATCH (o:Observation)
            RETURN count(o) AS total,
                   sum(CASE WHEN o.value IS NOT NULL AND o.source = 'synthetic_demo'
                        THEN 1 ELSE 0 END) AS synthetic
        """).single()
        assert r["synthetic"] == r["total"], (
            "all Observation nodes must be synthetic_demo with numeric values")

    def test_outcomes_carry_value_numeric(self, session):
        # value_numeric enables AVG/MIN/MAX; string `value` stays for
        # display. Every castable value must be backfilled; MOTU's
        # legitimately missing entries (value='NA', 561 in the snapshot)
        # have nothing to cast and stay null.
        r = session.run(r"""
            MATCH (o:Outcome)
            RETURN count(o) AS total,
                   sum(CASE WHEN o.value =~ '[-+]?\d*\.?\d+' THEN 1 ELSE 0 END)
                       AS castable,
                   sum(CASE WHEN o.value =~ '[-+]?\d*\.?\d+'
                             AND o.value_numeric IS NULL THEN 1 ELSE 0 END)
                       AS missing
        """).single()
        assert r["castable"] > 0, "no castable outcome values found"
        assert r["missing"] == 0, (
            f"{r['missing']} castable outcomes missing value_numeric")


# ── Curated CSV liveness (rows must match real graph content) ────────────
# The Free Exercise DB is fitness-oriented, so rehab-style exercise names
# silently produce zero edges. This gate requires every curated CSV row to
# resolve against the loaded graph — including match_type=icd10 rows, which
# bind on Condition.icd10_code (Gate 0 policy: exact-name Mondo propagation
# + curated/condition_icd10_overrides.csv, both applied by
# bridges.set_condition_icd10_codes before the loaders).


class TestCuratedCsvLiveness:
    def _exercise_matches(self, session, name):
        return session.run(
            "MATCH (e:Exercise) WHERE toLower(e.name) STARTS WITH toLower($p) "
            "RETURN count(e) AS c", p=name).single()["c"]

    @pytest.mark.parametrize("csv_name", [
        "curated/condition_exercise.csv",
        "curated/safety_contraindications.csv",
    ])
    def test_every_exercise_name_matches(self, session, csv_name):
        import csv as _csv
        with open(csv_name, newline="", encoding="utf-8") as f:
            for row in _csv.DictReader(f):
                n = self._exercise_matches(session, row["exercise_name"])
                assert n >= 1, (
                    f"{csv_name}: exercise {row['exercise_name']!r} matches "
                    "no Exercise (STARTS WITH) — dead row")

    @pytest.mark.parametrize("csv_name", [
        "curated/condition_exercise.csv",
        "curated/safety_contraindications.csv",
    ])
    def test_keyword_rows_match_conditions(self, session, csv_name):
        import csv as _csv
        with open(csv_name, newline="", encoding="utf-8") as f:
            for row in _csv.DictReader(f):
                if row["match_type"] == "icd10":
                    n = session.run(
                        "MATCH (c:Condition) WHERE c.icd10_code = $code "
                        "RETURN count(c) AS c",
                        code=row["condition_key"].strip(),
                    ).single()["c"]
                    assert n >= 1, (
                        f"{csv_name}: icd10 row {row['condition_key']!r} "
                        "matches no Condition.icd10_code — dead row (was "
                        "set_condition_icd10_codes run?)"
                    )
                    continue
                kws = [k.strip().lower() for k in row["condition_key"].split(";") if k.strip()]
                flt = " OR ".join(f"toLower(c.name) CONTAINS '{k}'" for k in kws)
                n = session.run(
                    f"MATCH (c:Condition) WHERE {flt} RETURN count(c) AS c"
                ).single()["c"]
                assert n >= 1, (
                    f"{csv_name}: condition_key {row['condition_key']!r} "
                    "matches no Condition — dead row")

    def test_safety_rows_resolve(self, session):
        # Every safety seed must fire on the loaded graph: precaution and
        # contraindication edges must exist with provenance.
        for rel_type, minimum in (("PRECAUTION", 4), ("CONTRAINDICATION", 2)):
            count = run_count(session, f"""
                MATCH ()-[r:{rel_type}]->() RETURN count(r) AS cnt
            """)
            assert count >= minimum, (
                f"{rel_type}: {count} < {minimum} — safety seeds did not load")


# ── Condition.icd10_code policy (Gate 0) ─────────────────────────────────
# Condition.icd10_code may only be set by bridges.set_condition_icd10_codes:
# exact-name Mondo propagation (icd10_source='mondo_exact_name') or
# curated/condition_icd10_overrides.csv ('curated_override'). Curated
# match_type=icd10 rows bind on this property at ICD10_BIND_CONFIDENCE with
# match_type icd10_via_mondo / icd10_override — never the raw 'icd10' label.


class TestConditionIcd10:
    ALLOWED_SOURCES = {"mondo_exact_name", "curated_override"}
    BIND_MATCH_TYPES = {"icd10_via_mondo", "icd10_override"}

    def test_conditions_have_icd10_codes(self, session):
        # Exact-name propagation was measured at 55 conditions + up to 10
        # override names on the Phase 0 snapshot; a floor of 50 leaves room
        # for graph-content drift while still failing a broken policy step.
        r = session.run("""
            MATCH (c:Condition)
            WHERE c.icd10_code IS NOT NULL AND c.icd10_code <> ''
            RETURN count(c) AS n
        """).single()
        assert r["n"] >= 50, (
            f"only {r['n']} Conditions carry icd10_code — "
            "set_condition_icd10_codes not run or policy broken")

    def test_icd10_source_allowlist(self, session):
        # No Condition may carry an icd10_source outside the two sanctioned
        # values; codes with no source are also rejected (policy requires
        # the origin to be stamped alongside the code).
        r = session.run("""
            MATCH (c:Condition)
            WHERE c.icd10_code IS NOT NULL AND c.icd10_code <> ''
              AND NOT c.icd10_source IN ['mondo_exact_name', 'curated_override']
            RETURN count(c) AS bad,
                   collect(c.name)[..5] AS samples
        """).single()
        assert r["bad"] == 0, (
            f"{r['bad']} Conditions have icd10_code with a missing/unknown "
            f"icd10_source (samples: {r['samples']}) — outside Gate 0 policy")

    def test_icd10_bound_edges_exist_with_provenance(self, session):
        # The 29 curated match_type=icd10 rows (condition_exercise.csv) plus
        # any icd10 safety rows must have produced bound edges at 0.7 with
        # the shared provenance contract — the headline Phase 1 outcome.
        r = session.run("""
            MATCH (:Condition)-[r:RECOMMENDS_EXERCISE]->(:Exercise)
            WHERE r.match_type IN ['icd10_via_mondo', 'icd10_override']
            RETURN count(r) AS total,
                   sum(CASE WHEN r.method = 'curated' THEN 1 ELSE 0 END)
                       AS with_method,
                   sum(CASE WHEN r.source IS NOT NULL THEN 1 ELSE 0 END)
                       AS with_source,
                   sum(CASE WHEN r.review_status = 'unreviewed'
                            THEN 1 ELSE 0 END) AS unreviewed,
                   sum(CASE WHEN r.confidence = 0.7 THEN 1 ELSE 0 END)
                       AS at_bind_conf
        """).single()
        assert r["total"] >= 20, (
            f"only {r['total']} icd10-bound RECOMMENDS_EXERCISE edges — "
            "curated icd10 rows did not fire (was "
            "set_condition_icd10_codes run before the loaders?)")
        assert r["with_method"] == r["total"], "icd10 edges missing method"
        assert r["with_source"] == r["total"], "icd10 edges missing source"
        assert r["unreviewed"] == r["total"], (
            "icd10-bound edges must stay review_status=unreviewed")
        assert r["at_bind_conf"] == r["total"], (
            "icd10-bound edges must sit at ICD10_BIND_CONFIDENCE (0.7)")

    def test_no_raw_icd10_match_type_edges(self, session):
        # match_type='icd10' (the CSV vocabulary) must never leak onto
        # edges — the loader rewrites it to icd10_via_mondo/icd10_override
        # via provenance.icd10_edge_props.
        count = run_count(session, """
            MATCH ()-[r]->() WHERE r.match_type = 'icd10' RETURN count(r) AS cnt
        """)
        assert count == 0, (
            f"{count} edges carry raw match_type='icd10' — the loader must "
            "rewrite via icd10_edge_props, never SET the CSV vocabulary")


# ── Scale identifiers & Outcome→AssessmentScale linkage (Phase 2) ───────
# F9: bulk graphs must expose AssessmentScale.scale_id as a property, not
# only the neo4j-admin :ID (otherwise scale_id-keyed curated loaders see
# NULL and the UNIQUE constraint is vacuous). F3/parity: every Outcome is
# MEASURED_BY a scale, and the shared MOTU spec fires both scales — the
# old bulk path dropped all 10m Walk Test outcomes.


class TestScaleIdsAndMeasuredBy:
    def test_all_scales_have_scale_id(self, session):
        r = session.run("""
            MATCH (a:AssessmentScale)
            RETURN count(a) AS total,
                   sum(CASE WHEN a.scale_id IS NOT NULL
                             AND a.scale_id <> '' THEN 1 ELSE 0 END) AS with_id
        """).single()
        assert r["total"] >= 40, f"only {r['total']} AssessmentScale nodes"
        assert r["with_id"] == r["total"], (
            f"{r['total'] - r['with_id']} AssessmentScale nodes lack "
            "scale_id — F9 bulk fix/backfill not applied")

    def test_scale_id_unique_constraint_exists(self, session):
        # Name differs per path (schema.cypher: assessment_scale_id_unique,
        # import_bulk: assessmentscale_scale_id_unique) — assert by property.
        rows = session.run(
            "SHOW CONSTRAINTS YIELD properties, name "
            "RETURN name, properties"
        ).data()
        found = any(
            "scale_id" in (r.get("properties") or []) for r in rows
        )
        assert found, "no UNIQUE constraint on AssessmentScale.scale_id"

    def test_every_outcome_is_measured_by_a_scale(self, session):
        r = session.run("""
            MATCH (o:Outcome)
            OPTIONAL MATCH (o)-[:MEASURED_BY]->(a:AssessmentScale)
            RETURN count(o) AS total, count(a) AS linked
        """).single()
        assert r["total"] > 0, "no Outcomes in graph"
        assert r["linked"] == r["total"], (
            f"{r['total'] - r['linked']} Outcomes lack MEASURED_BY "
            "(was postload's value_numeric/bridge step run?)")

    def test_measured_by_covers_both_motu_scales(self, session):
        # Shared MOTU_OUTCOME_SPECS: Barthel (ASM-030) + 10m Walk Test
        # (ASM-023) both must fire; the pre-Phase-2 bulk path only wrote
        # Barthel (2,012 of a possible 4,024 MEASURED_BY links).
        rows = session.run("""
            MATCH (:Outcome)-[:MEASURED_BY]->(a:AssessmentScale)
            WHERE a.scale_id IN ['ASM-030', 'ASM-023']
            RETURN a.scale_id AS sid, count(*) AS n
        """).data()
        by = {r["sid"]: r["n"] for r in rows}
        for sid in ("ASM-030", "ASM-023"):
            assert by.get(sid, 0) >= 1000, (
                f"{sid} linked to only {by.get(sid, 0)} outcomes — "
                "MOTU outcome spec coverage gap on this path")

    def test_scale_register_ids_resolve(self, session):
        # Every scale_id in curated/scale_identifiers.csv must match a
        # graph node — the register is keyed on the F9 scale_id property.
        import csv as _csv
        with open("curated/scale_identifiers.csv", newline="",
                  encoding="utf-8") as f:
            ids = sorted({r["scale_id"].strip()
                          for r in _csv.DictReader(f)})
        r = session.run(
            "MATCH (a:AssessmentScale) WHERE a.scale_id IN $ids "
            "RETURN count(DISTINCT a) AS c",
            ids=ids,
        ).single()
        assert r["c"] == len(ids), (
            f"register has {len(ids)} scale_ids but only {r['c']} "
            "resolve in the graph"
        )


# ── Edge provenance contract ─────────────────────────────────────────────
# Requires a graph whose postload ran the provenance.py presets + backfill
# (python import_bulk.py). Older graphs fail these — that is intentional:
# provenance coverage is a release gate, not a soft check.


class TestProvenance:
    CLINICAL_RELS = [
        "RECOMMENDS_EXERCISE",
        "PRECAUTION",
        "CONTRAINDICATION",
        "MAPS_TO_ICF",
        "MAPS_TO_MONDO",
        "STUDIES_CONDITION",
        "HAS_ICD10",
        "TARGETS_ANATOMY",
        "TARGETS_PRIMARY",
        "TARGETS_SECONDARY",
        "REQUIRES",
        "MAPS_TO_UBERON",
        "MEASURES",
        "PROGRESSES_TO",
    ]

    @pytest.mark.parametrize("rel_type", CLINICAL_RELS)
    def test_clinical_edges_carry_full_contract(self, session, rel_type):
        r = session.run(f"""
            MATCH ()-[r:{rel_type}]->()
            RETURN count(r) AS total,
                   sum(CASE WHEN r.method IS NOT NULL THEN 1 ELSE 0 END)
                       AS with_method,
                   sum(CASE WHEN r.review_status IS NOT NULL THEN 1 ELSE 0 END)
                       AS with_status,
                   sum(CASE WHEN r.source IS NOT NULL THEN 1 ELSE 0 END)
                       AS with_source
        """).single()
        if r["total"] == 0:
            pytest.skip(f"{rel_type} absent from graph")
        assert r["with_method"] == r["total"], (
            f"{rel_type}: {r['total'] - r['with_method']} edges missing method")
        assert r["with_status"] == r["total"], (
            f"{rel_type}: {r['total'] - r['with_status']} edges missing review_status")
        assert r["with_source"] == r["total"], (
            f"{rel_type}: {r['total'] - r['with_source']} edges missing source")

    def test_recommends_are_all_curated(self, session):
        r = session.run("""
            MATCH ()-[r:RECOMMENDS_EXERCISE]->()
            RETURN count(r) AS total,
                   sum(CASE WHEN r.method = 'curated' THEN 1 ELSE 0 END) AS curated
        """).single()
        assert r["curated"] == r["total"], (
            "RECOMMENDS_EXERCISE must be exclusively curated-CSV derived")

    def test_hpo_icf_explicit_links_are_curated_and_unreviewed(self, session):
        # The focused refresh uses only explicit code pairs, not the broad
        # bidirectional-containment matcher.
        r = session.run("""
            MATCH (:HPOConcept)-[r:RELATED_TO_ICF]->(:ICFConcept)
            RETURN count(r) AS total,
                   sum(CASE WHEN r.method = 'curated'
                                  AND r.match_type = 'explicit_code_pair'
                                  AND r.confidence = 1.0
                                  AND r.review_status = 'unreviewed'
                            THEN 1 ELSE 0 END) AS valid
        """).single()
        assert r["total"] == 9
        assert r["valid"] == r["total"]

    def test_rehabo_icf_curated_matches_exist(self, session):
        count = run_count(session, """
            MATCH (:REHABOConcept)-[r:CLOSE_MATCH {source: 'curated'}]->(:ICFConcept)
            RETURN count(r) AS cnt
        """)
        assert count == 5

    def test_core_set_edges_remain_curated_and_unreviewed(self, session):
        r = session.run("""
            MATCH (c:Condition)-[r:HAS_CORE_SET_CATEGORY]->(i:ICFConcept)
            RETURN count(r) AS total,
                   sum(CASE WHEN r.method='curated'
                              AND r.match_type='icf_core_set_register'
                              AND r.source='curated/icf_core_sets.csv'
                              AND r.review_status='unreviewed'
                            THEN 1 ELSE 0 END) AS valid
        """).single()
        assert r["valid"] == r["total"]

    def test_no_model_generated_edges_yet(self, session):
        # Guardrail: if model_generated edges ever appear, they must stay
        # unreviewed. Today the count must be exactly zero.
        count = run_count(session, """
            MATCH ()-[r]->() WHERE r.method = 'model_generated' RETURN count(r) AS cnt
        """)
        assert count == 0, (
            f"{count} model_generated edges exist — they must be created "
            "only with an explicit review workflow")

    def test_hpo_icf_curated_links_have_provenance(self, session):
        rows = session.run("""
            MATCH (:HPOConcept)-[r:RELATED_TO_ICF]->(:ICFConcept)
            RETURN count(r) AS total,
                   sum(CASE WHEN r.method = 'curated'
                                  AND r.match_type = 'explicit_code_pair'
                                  AND r.review_status = 'unreviewed'
                                  AND r.source = 'add_additional_data.py:HPO_TO_ICF_MAPPINGS'
                                  AND r.confidence = 1.0
                            THEN 1 ELSE 0 END) AS valid
        """).single()
        assert rows["total"] >= 9
        assert rows["valid"] == rows["total"]
