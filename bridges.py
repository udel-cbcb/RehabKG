#!/usr/bin/env python3
"""
Cross-ontology bridge relationships for RehabKG.

Creates MAPS_TO_ICF relationships between non-ICF ontologies and ICF,
plus AssessmentScale -> ICF bridges and hierarchy propagation.

Idempotent: all writes use MERGE.
"""

import csv
import re
from pathlib import Path

from provenance import (
    ASSESSMENT_MEASURES,
    EXACT_NAME_ICF as EXACT_NAME_ICF_PROPS,
    HIERARCHY_PROPAGATION,
    KEYWORD_ICF_COPPER,
    KEYWORD_ICF_PMR,
    edge_props,
    icd10_edge_props,
)

CURATED_DIR = Path(__file__).resolve().parent / "curated"
CONDITION_EXERCISE_CSV = CURATED_DIR / "condition_exercise.csv"
CONDITION_EXERCISE_SOURCE = "curated/condition_exercise.csv"
SAFETY_CSV = CURATED_DIR / "safety_contraindications.csv"
SAFETY_SOURCE = "curated/safety_contraindications.csv"
OBSERVATION_SEED_CSV = CURATED_DIR / "observation_seed.csv"
OBSERVATION_SEED_SOURCE = "curated/observation_seed.csv"
CONDITION_ICD10_OVERRIDES_CSV = CURATED_DIR / "condition_icd10_overrides.csv"
CONDITION_ICD10_OVERRIDES_SOURCE = "curated/condition_icd10_overrides.csv"
SCALE_IDENTIFIERS_CSV = CURATED_DIR / "scale_identifiers.csv"
SCALE_IDENTIFIERS_SOURCE = "curated/scale_identifiers.csv"
ICF_CORE_SETS_CSV = CURATED_DIR / "icf_core_sets.csv"
ICF_CORE_SETS_SOURCE = "curated/icf_core_sets.csv"
SYNTHETIC_PATIENT_ID = "SYNTHETIC-GAIT-001"

# Clinical safety relationship types. Only these may be created from the
# curated safety CSV — the loader validates rel_type against this allowlist
# so a bad CSV row can never inject an arbitrary relationship type into
# interpolated Cypher.
SAFETY_REL_TYPES = ("PRECAUTION", "CONTRAINDICATION")


def name_matches_keyword(name, keyword):
    """Whole-word, case-insensitive match; mirrors the Cypher regex below.

    Keyword bridges use word boundaries so short keywords like 'rom' or
    'fall' cannot match inside unrelated words ('chromosome', 'false').
    """
    return re.search(r"\b" + re.escape(keyword) + r"\b", name or "",
                     re.IGNORECASE) is not None


def _word_pattern(keyword):
    """Neo4j `=~` full-string regex for a whole-word keyword match."""
    return r"(?i).*\b" + re.escape(keyword) + r"\b.*"


def _split_keywords(value):
    """Split a semicolon-separated CSV keyword cell, dropping blanks."""
    return [keyword.strip() for keyword in (value or "").split(";")
            if keyword.strip()]


def condition_matches_keywords(name, keywords, exclude_keywords=()):
    """Whole-word include/exclude matcher mirroring the Cypher filters."""
    return (any(name_matches_keyword(name, keyword) for keyword in keywords)
            and not any(name_matches_keyword(name, keyword)
                        for keyword in exclude_keywords))


KEYWORD_GROUP_CONFIDENCE = 0.6


# 1. Exact class-name -> ICF mappings.
# Curated by hand; codes below were spot-checked against the WHO ICF
# browser on 2026-10-22 for the KHMO movement rows (reach/throw -> d445
# Hand and arm use (reaching/catching/throwing); grasp/grip -> d440
# Hand and arm use (manipulating objects); running/jumping/climbing ->
# d455 Moving around; squatting -> d410 Changing basic body position;
# crawling stays d450, which is literally "Crawling").
EXACT_NAME_ICF = [
    ('PMRConcept', 'Joint_movement', 'b710'),
    ('PMRConcept', 'Muscle_strength', 'b730'),
    ('PMRConcept', 'Gait', 'd450'),
    ('PMRConcept', 'Balance', 'b235'),
    ('PMRConcept', 'Range_of_motion', 'b710'),
    ('PMRConcept', 'Endurance', 'b455'),
    ('PMRConcept', 'Coordination', 'b760'),
    ('PMRConcept', 'Proprioception', 'b260'),
    ('PMRConcept', 'Postural_control', 'b235'),
    ('PMRConcept', 'Functional_movement', 'b730'),
    ('PMRConcept', 'Motor_control', 'b140'),
    ('PMRConcept', 'Sensory_integration', 'b140'),
    ('COPPERConcept', 'aerobic', 'b455'),
    ('COPPERConcept', 'resistance', 'b730'),
    ('COPPERConcept', 'flexibility', 'b710'),
    ('COPPERConcept', 'balance', 'd455'),
    ('COPPERConcept', 'coordination', 'b760'),
    ('COPPERConcept', 'endurance', 'b455'),
    ('COPPERConcept', 'stretching', 'b710'),
    ('COPPERConcept', 'range_of_motion', 'b710'),
    ('COPPERConcept', 'strength', 'b730'),
    ('COPPERConcept', 'gait', 'd450'),
    ('KHMOConcept', 'walking', 'd450'),
    ('KHMOConcept', 'running', 'd455'),
    ('KHMOConcept', 'jumping', 'd455'),
    ('KHMOConcept', 'squatting', 'd410'),
    ('KHMOConcept', 'lifting', 'd430'),
    ('KHMOConcept', 'reaching', 'd445'),
    ('KHMOConcept', 'bending', 'b710'),
    ('KHMOConcept', 'turning', 'd455'),
    ('KHMOConcept', 'balancing', 'd455'),
    ('KHMOConcept', 'climbing', 'd455'),
    ('KHMOConcept', 'crawling', 'd450'),
    ('KHMOConcept', 'kneeling', 'd410'),
    ('KHMOConcept', 'sitting', 'd410'),
    ('KHMOConcept', 'standing', 'd415'),
    ('KHMOConcept', 'carrying', 'd430'),
    ('KHMOConcept', 'throwing', 'd445'),
    ('KHMOConcept', 'catching', 'd445'),
    ('EXMOConcept', 'exercise', 'd450'),
    ('EXMOConcept', 'physical_activity', 'd450'),
    ('EXMOConcept', 'strength_training', 'b730'),
    ('EXMOConcept', 'aerobic_exercise', 'b455'),
    ('EXMOConcept', 'flexibility_exercise', 'b710'),
    ('EXMOConcept', 'balance_exercise', 'd455'),
    ('PHYConcept', 'ankle_pump', 'b710'),
    ('PHYConcept', 'quad_set', 'b730'),
    ('PHYConcept', 'heel_slide', 'b710'),
    ('PHYConcept', 'straight_leg_raise', 'b730'),
    ('PHYConcept', 'glute_bridge', 'b730'),
    ('MELLODConcept', 'walking', 'd450'),
    ('MELLODConcept', 'standing', 'd415'),
    ('MELLODConcept', 'sitting', 'd410'),
    ('MELLODConcept', 'dressing', 'd520'),
    ('MELLODConcept', 'eating', 'd550'),
    ('MELLODConcept', 'bathing', 'd510'),
    ('MELLODConcept', 'toileting', 'd530'),
    ('MELLODConcept', 'transferring', 'd420'),
    ('MELLODConcept', 'grooming', 'd510'),
]


# 2. PMR.Owl# class name keyword matching -> ICF
PMROWL_KEYWORDS = [
    ('marcha', 'd450'),
    ('gait', 'd450'),
    ('walking', 'd450'),
    ('standing', 'd415'),
    ('sitting', 'd410'),
    ('transferencia', 'd420'),
    ('transfer', 'd420'),
    ('wheelchair', 'd450'),
    ('escaleras', 'd450'),
    ('stairs', 'd450'),
    ('reach', 'd445'),
    ('throw', 'd445'),
    ('grasp', 'd440'),
    ('grip', 'd440'),
    ('balance', 'd455'),
    ('coordination', 'b760'),
    ('mobility', 'd450'),
    ('locomotion', 'd450'),
    ('exercise', 'd450'),
    ('ejercicio', 'd450'),
    ('physical_activity', 'd450'),
    ('actividad_fisica', 'd450'),
    ('training', 'd450'),
    ('entrenamiento', 'd450'),
    ('aerobic', 'b455'),
    ('resistance', 'b730'),
    ('strengthening', 'b730'),
    ('fortalecimiento', 'b730'),
    ('flexibility', 'b710'),
    ('stretching', 'b710'),
    ('range_of_motion', 'b710'),
    ('rom', 'b710'),
    ('cardiovascular', 'b455'),
    ('fitness', 'b455'),
    ('cycling', 'd450'),
    ('swimming', 'd450'),
    ('aquatic', 'd450'),
    ('yoga', 'b710'),
    ('pilates', 'b730'),
    ('tai_chi', 'd455'),
    ('pain', 'b280'),
    ('dolor', 'b280'),
    ('fatigue', 'b455'),
    ('breathing', 'b440'),
    ('respiracion', 'b440'),
    ('heart_rate', 'b410'),
    ('blood_pressure', 'b420'),
    ('posture', 'b710'),
    ('muscle', 'b730'),
    ('nerve', 'b140'),
    ('sensation', 'b260'),
    ('proprioception', 'b260'),
    ('cognitive', 'b1'),
    ('executive', 'b164'),
    ('attention', 'b140'),
    ('memory', 'b144'),
    ('speech', 'b167'),
    ('language', 'b167'),
    ('swallowing', 'b330'),
    ('deglutition', 'b330'),
    ('respiratory', 'b440'),
    ('cardiac', 'b410'),
    ('circulatory', 'b420'),
    ('neurological', 'b140'),
    ('orthopedic', 'b730'),
    ('amputation', 'b720'),
    ('prosthesis', 'b720'),
    ('protesis', 'b720'),
    ('orthosis', 'b720'),
    ('ortesis', 'b720'),
    ('assistive', 'd450'),
    ('adaptive', 'd450'),
    ('disability', 'b7'),
    ('impairment', 'b7'),
    ('functional', 'b7'),
    ('independence', 'd5'),
    ('dependence', 'd5'),
    ('rehabilitation', 'b7'),
    ('terapia', 'b7'),
    ('fisioterapia', 'b7'),
    ('kinesiologia', 'b7'),
    ('neurology', 'b140'),
    ('stroke', 'b110'),
    ('fall', 'd455'),
    ('caida', 'd455'),
    ('fear', 'b152'),
    ('anxiety', 'b152'),
    ('depression', 'b152'),
    ('cognition', 'b1'),
    ('perception', 'b110'),
    ('sensory', 'b260'),
    ('motor', 'b730'),
    ('tremor', 'b765'),
    ('spasticity', 'b735'),
    ('rigidity', 'b735'),
    ('weakness', 'b730'),
    ('dizziness', 'b235'),
    ('vertigo', 'b235'),
]


# 3. COPPER behavioral change technique keywords -> ICF
COPPER_KEYWORDS = [
    ('goal_setting', 'b164'),
    ('self_monitoring', 'd5'),
    ('action_planning', 'd175'),
    ('coping_planning', 'b130'),
    ('social_support', 'd920'),
    ('self_efficacy', 'b130'),
    ('motivation', 'b130'),
    ('barrier_identification', 'b164'),
    ('stimulus_control', 'd160'),
    ('reinforcement', 'b140'),
    ('self_reward', 'b130'),
    ('commitment', 'b130'),
    ('feedback', 'b140'),
    ('monitoring', 'd5'),
    ('relaxation', 'b152'),
    ('stress_management', 'b152'),
    ('time_management', 'd175'),
    ('problem_solving', 'b164'),
    ('decision_making', 'b164'),
    ('behavioral_rehearsal', 'b730'),
    ('graded_task', 'd450'),
    ('exposure', 'b152'),
    ('systematic_desensitization', 'b152'),
    ('modeling', 'b140'),
    ('persuasion', 'b130'),
    ('health_belief', 'b130'),
    ('outcome_expectations', 'b130'),
    ('intention', 'b130'),
    ('self_directed', 'd175'),
    ('monitoring_outcomes', 'd5'),
    ('feedback_on_outcomes', 'd5'),
]


# 4. AssessmentScale -> ICF keyword bridges
ASSESSMENT_ICF_BRIDGES = [
    ('balance', 'd455'),
    ('gait', 'd450'),
    ('walk', 'd450'),
    ('strength', 'b730'),
    ('endurance', 'b455'),
    ('flexibility', 'b710'),
    ('mobility', 'd450'),
    ('adl', 'd5'),
    ('self_care', 'd5'),
    ('daily', 'd5'),
    ('pain', 'b280'),
    ('cognitive', 'b1'),
    ('function', 'b7'),
    ('barthel', 'd5'),
    ('fim', 'd5'),
    ('berg', 'd455'),
    ('timed', 'd450'),
    ('turn', 'd455'),
    ('transfer', 'd420'),
    ('stairs', 'd450'),
    ('reach', 'd440'),
    ('grip', 'd445'),
    ('stroke', 'b110'),
    ('fall', 'd455'),
    ('falls', 'd455'),
    ('turning', 'd455'),
    ('wheelchair', 'd450'),
]


def bridge_exact_names(session):
    """Bridge non-ICF concepts to ICF via exact name matching."""
    total = 0
    for label, name, code in EXACT_NAME_ICF:
        r = session.run(
            f"MATCH (n:{label} {{name: $name}}) "
            "MATCH (i:ICFConcept {code: $code}) "
            "MERGE (n)-[r:MAPS_TO_ICF]->(i) "
            "SET r += $props "
            "RETURN count(n) AS c",
            name=name, code=code, props=EXACT_NAME_ICF_PROPS,
        ).single()
        total += r["c"]
    print(f"  Exact name -> ICF: {total} edges")


def bridge_pmr_owl(session):
    """Bridge PMR concepts to ICF via keyword matching on Owl# class names.

    Names are matched whole-word (so 'rom' cannot match 'chromosome');
    longer keywords are applied first so specific phrases win over short
    generic ones when a concept matches several.
    """
    total = 0
    for keyword, code in sorted(PMROWL_KEYWORDS, key=lambda kc: len(kc[0]), reverse=True):
        r = session.run(
            "MATCH (n:PMRConcept) WHERE NOT (n)-[:MAPS_TO_ICF]->() "
            "AND (n.name =~ $pat OR toLower(n.code) CONTAINS $kw) "
            "MATCH (i:ICFConcept {code: $code}) "
            "MERGE (n)-[r:MAPS_TO_ICF]->(i) "
            "SET r += $props "
            "RETURN count(n) AS c",
            kw=keyword, pat=_word_pattern(keyword), code=code,
            props=dict(KEYWORD_ICF_PMR, keyword=keyword),
        ).single()
        total += r["c"]
    print(f"  PMR keyword -> ICF: {total} edges")


def bridge_copper_keywords(session):
    """Bridge COPPER concepts to ICF via behavioral change technique keywords.

    Whole-word matching; longer keywords first (see bridge_pmr_owl).
    """
    total = 0
    for keyword, code in sorted(COPPER_KEYWORDS, key=lambda kc: len(kc[0]), reverse=True):
        r = session.run(
            "MATCH (n:COPPERConcept) WHERE NOT (n)-[:MAPS_TO_ICF]->() "
            "AND n.name =~ $pat "
            "MATCH (i:ICFConcept {code: $code}) "
            "MERGE (n)-[r:MAPS_TO_ICF]->(i) "
            "SET r += $props "
            "RETURN count(n) AS c",
            kw=keyword, pat=_word_pattern(keyword), code=code,
            props=dict(KEYWORD_ICF_COPPER, keyword=keyword),
        ).single()
        total += r["c"]
    print(f"  COPPER keyword -> ICF: {total} edges")


def bridge_assessment_scales(session):
    """Bridge AssessmentScale nodes to ICF using whole-word keyword matching."""
    total = 0
    for keyword, code in sorted(ASSESSMENT_ICF_BRIDGES,
                                key=lambda kc: len(kc[0]), reverse=True):
        r = session.run(
            "MATCH (a:AssessmentScale) WHERE NOT (a)-[:MEASURES]->() "
            "AND a.name =~ $pat "
            "MATCH (i:ICFConcept {code: $code}) "
            "MERGE (a)-[r:MEASURES]->(i) "
            "SET r += $props "
            "RETURN count(a) AS c",
            kw=keyword, pat=_word_pattern(keyword), code=code,
            props=dict(ASSESSMENT_MEASURES, keyword=keyword),
        ).single()
        total += r["c"]
    print(f"  AssessmentScale -> ICF: {total} edges")


def propagate_hierarchy(session):
    """Propagate ICF mappings up the hierarchy for PMR/COPPER/EXMO."""
    total = 0
    for label in ["PMRConcept", "COPPERConcept", "EXMOConcept"]:
        r = session.run(
            "MATCH (root:" + label + ")-[:SUBCLASS_OF*1..6]->"
            "(child:" + label + ")-[:MAPS_TO_ICF]->(i:ICFConcept) "
            "WHERE NOT (root)-[:MAPS_TO_ICF]->() "
            "WITH DISTINCT root, i "
            "MERGE (root)-[r:MAPS_TO_ICF]->(i) "
            "SET r += $props "
            "RETURN count(DISTINCT root) AS c",
            props=HIERARCHY_PROPAGATION,
        ).single()
        total += r["c"]
        print(f"  {label}: +{r['c']} via hierarchy")
    print(f"  Total hierarchy propagation: {total} edges")


# ── Condition.icd10_code (prerequisite for curated match_type=icd10 rows) ──
#
# Gate 0 policy (docs/notes/phase0_findings.md): a Condition receives an
# ICD-10 code only from (a) an EXACT case-insensitive name match against a
# MondoDisease that carries one — never from the fuzzy name_contains
# MAPS_TO_MONDO edges — or (b) curated/condition_icd10_overrides.csv. The
# origin is stamped in icd10_source so downstream edge match_types stay
# honest (icd10_via_mondo vs icd10_override, see provenance.icd10_edge_props).


def load_icd10_override_rows():
    """Read curated/condition_icd10_overrides.csv as a list of dict rows."""
    with open(CONDITION_ICD10_OVERRIDES_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def set_condition_icd10_codes(session):
    """Set Condition.icd10_code per the Gate 0 policy — shared by both paths.

    The Cypher path (rehabkg.py link_post_additional) and the bulk path
    (import_bulk.py post_load) must both call this AFTER MAPS_TO_MONDO and
    BEFORE link_conditions_to_exercises/link_safety_edges, whose curated
    match_type=icd10 rows bind on this property (guarded by
    tests/test_bridges.py::TestLoadPathParity).

    Idempotent: exact propagation only fills empty codes; override rows
    re-apply the same value (overrides are authoritative over propagated
    codes). Override rows naming a Condition absent from the graph are
    reported, not fatal — the live TestCuratedCsvLiveness gate catches them
    on the canonical graph.
    """
    # 1. Exact-name propagation from Mondo. head(collect(...)) after ORDER BY
    # keeps the result deterministic if a Condition ever exact-matches several
    # coded Mondo diseases (lexicographically smallest code wins).
    r = session.run("""
        MATCH (c:Condition)-[:MAPS_TO_MONDO]->(m:MondoDisease)
        WHERE m.icd10_code IS NOT NULL AND m.icd10_code <> ''
          AND toLower(trim(m.name)) = toLower(trim(c.name))
        WITH c, m ORDER BY m.icd10_code
        WITH c, head(collect(m)) AS m
        WHERE c.icd10_code IS NULL
        SET c.icd10_code = m.icd10_code, c.icd10_source = 'mondo_exact_name'
        RETURN count(c) AS c
    """).single()
    mondo_count = r["c"]

    # 2. Curated overrides (authoritative).
    applied = 0
    missing_names = []
    for row in load_icd10_override_rows():
        name = (row.get("condition_name") or "").strip()
        code = (row.get("icd10_code") or "").strip()
        if not name or not code:
            raise ValueError(
                f"blank condition_name/icd10_code in {CONDITION_ICD10_OVERRIDES_CSV}: {row}"
            )
        r = session.run(
            """
            MATCH (c:Condition)
            WHERE toLower(trim(c.name)) = toLower($name)
            SET c.icd10_code = $code, c.icd10_source = 'curated_override'
            RETURN count(c) AS c
            """,
            name=name, code=code,
        ).single()
        applied += r["c"]
        if r["c"] == 0:
            missing_names.append(f"{name} ({code})")

    print(f"  Condition.icd10_code: +{mondo_count} via exact-name Mondo, "
          f"+{applied} via curated overrides")
    if missing_names:
        print(f"    WARNING: override rows matched no Condition: "
              f"{', '.join(missing_names)}")
    return mondo_count, applied


def _link_icd10_row(session, row, rel_type, source):
    """Bind one curated match_type=icd10 row onto every Condition with its code.

    Two passes keep the property maps fully built in Python via
    provenance.icd10_edge_props (single source of truth): conditions whose
    code came from exact-name Mondo propagation vs curated overrides each
    get their own match_type at ICD10_BIND_CONFIDENCE. Conditions whose
    icd10_source is missing/unknown never match, so no edge can be minted
    outside the Gate 0 policy. ``rel_type`` must already have been validated
    against an allowlist by the caller before any interpolation.
    """
    extras = dict(
        category=(row.get("category") or None),
        rationale=(row.get("rationale") or None),
        citation=(row.get("citation") or None),
        reviewed_by=(row.get("reviewed_by") or None),
        icd10_code=row["condition_key"],
        **evidence_props(row),
    )
    total = 0
    for icd10_source in ("mondo_exact_name", "curated_override"):
        props = icd10_edge_props(source, row["status"], icd10_source, **extras)
        r = session.run(
            f"""
            MATCH (c:Condition)
            WHERE c.icd10_code = $icd_code AND c.icd10_source = $icd10_source
            MATCH (e:Exercise)
            WHERE toLower(e.name) STARTS WITH toLower($ex_name)
            MERGE (c)-[rel:{rel_type}]->(e)
            SET rel += $props
            RETURN count(rel) AS c
            """,
            icd_code=row["condition_key"], icd10_source=icd10_source,
            ex_name=row["exercise_name"], props=props,
        ).single()
        total += r["c"]
    return total


# ── Condition → Exercise (single curated source, both load paths) ──────────

def load_condition_exercise_rows():
    """Read curated/condition_exercise.csv as a list of dict rows."""
    with open(CONDITION_EXERCISE_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# Optional evidence columns shared by every curated-CSV loader (curated
# rows carry these onto edges; empty cells stay absent, not empty string).
EVIDENCE_COLUMNS = ("citation_doi", "citation_pmid", "evidence_level",
                    "population", "reviewed_on")


def evidence_props(row):
    """Map a curated CSV row's evidence columns to edge_props extras."""
    return {col: (row.get(col) or None) for col in EVIDENCE_COLUMNS}


def link_conditions_to_exercises(session):
    """Condition->Exercise links from curated/condition_exercise.csv.

    Single source of truth shared by the Cypher path (rehabkg.py
    link_post_additional) and the bulk-import postload (import_bulk.py),
    so both graphs produce the same edges. Every edge stores the shared
    provenance contract (method/match_type/confidence/source/
    review_status) plus category/rationale/citation/reviewed_by from the
    CSV; the CSV status column maps to the edge review_status property.
    Rows are review_status=unreviewed until a clinician reviews them;
    treat the edges as candidate recommendations, not clinical advice.

    match_type=keyword_group rows match Condition.name by whole-word
    keyword (semicolon-separated in condition_key) and may list
    semicolon-separated exclude_keywords. Keyword-group edges use
    confidence=KEYWORD_GROUP_CONFIDENCE (below exact-ID bindings) and
    curation_basis=keyword_group so consumers can separate the two.

    match_type=icd10 rows match Condition.icd10_code exactly. That
    property is set by set_condition_icd10_codes (exact-name Mondo
    propagation or curated overrides — the old documented no-op is
    gone), and the bound edges are stamped at ICD10_BIND_CONFIDENCE
    with match_type icd10_via_mondo / icd10_override reflecting the
    code's origin — see provenance.icd10_edge_props.
    """
    linked = 0
    for row in load_condition_exercise_rows():
        match_type = row["match_type"]
        if match_type == "icd10":
            linked += _link_icd10_row(
                session, row, "RECOMMENDS_EXERCISE", CONDITION_EXERCISE_SOURCE)
            continue
        props = edge_props(
            method="curated",
            match_type=match_type,
            confidence=KEYWORD_GROUP_CONFIDENCE,
            source=CONDITION_EXERCISE_SOURCE,
            review_status=row["status"],
            category=row["category"] or None,
            rationale=row["rationale"] or None,
            citation=row["citation"] or None,
            reviewed_by=row["reviewed_by"] or None,
            curation_basis="keyword_group",
            **evidence_props(row),
        )
        params = {"ex_name": row["exercise_name"], "props": props}
        if match_type == "keyword_group":
            kws = _split_keywords(row["condition_key"])
            if not kws:
                continue
            kw_filter = " OR ".join(
                f"c.name =~ $kw{i}" for i in range(len(kws))
            )
            params.update({f"kw{i}": _word_pattern(kw)
                           for i, kw in enumerate(kws)})
            excludes = _split_keywords(row.get("exclude_keywords"))
            exclude_filter = ""
            if excludes:
                exclude_filter = "AND NOT (" + " OR ".join(
                    f"c.name =~ $ex{i}" for i in range(len(excludes))
                ) + ")"
                params.update({f"ex{i}": _word_pattern(kw)
                               for i, kw in enumerate(excludes)})
            query = f"""
                MATCH (c:Condition)
                WHERE ({kw_filter}) {exclude_filter}
                MATCH (e:Exercise)
                WHERE toLower(e.name) STARTS WITH toLower($ex_name)
                MERGE (c)-[rel:RECOMMENDS_EXERCISE]->(e)
                SET rel += $props
                RETURN count(rel) AS c
            """
        else:
            raise ValueError(
                f"Unknown match_type {match_type!r} in {CONDITION_EXERCISE_CSV}"
            )
        r = session.run(query, **params).single()
        linked += r["c"]
    print(f"  RECOMMENDS_EXERCISE (curated CSV): {linked} edges")
    return linked


# ── Safety edges (PRECAUTION / CONTRAINDICATION) ──────────────────────────


def load_safety_rows():
    """Read curated/safety_contraindications.csv as a list of dict rows."""
    with open(SAFETY_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def link_safety_edges(session):
    """Condition->Exercise safety edges from curated/safety_contraindications.csv.

    Same matching semantics as link_conditions_to_exercises
    (keyword_group at KEYWORD_GROUP_CONFIDENCE, or icd10 via
    set_condition_icd10_codes at ICD10_BIND_CONFIDENCE with match_type
    icd10_via_mondo/icd10_override), but creates PRECAUTION or
    CONTRAINDICATION relationships with the shared provenance contract.
    rel_type is validated against SAFETY_REL_TYPES before any
    interpolation.

    Consumers that return recommendations MUST also return safety edges
    for the same (condition, exercise) pairs — a safety model that only
    surfaces when you think to ask is theater. All seed rows are
    review_status=unreviewed; they are candidate safety flags for pilot
    evaluation, not clinical advice.
    """
    linked = 0
    for row in load_safety_rows():
        rel_type = row["rel_type"].strip()
        if rel_type not in SAFETY_REL_TYPES:
            raise ValueError(
                f"rel_type {rel_type!r} not in {SAFETY_REL_TYPES} "
                f"({SAFETY_CSV})"
            )
        match_type = row["match_type"]
        if match_type == "icd10":
            linked += _link_icd10_row(session, row, rel_type, SAFETY_SOURCE)
            continue
        props = edge_props(
            method="curated",
            match_type=match_type,
            confidence=KEYWORD_GROUP_CONFIDENCE,
            source=SAFETY_SOURCE,
            review_status=row["status"],
            rationale=row["rationale"] or None,
            citation=row["citation"] or None,
            reviewed_by=row["reviewed_by"] or None,
            curation_basis="keyword_group",
            **evidence_props(row),
        )
        params = {"ex_name": row["exercise_name"], "props": props}
        if match_type == "keyword_group":
            kws = _split_keywords(row["condition_key"])
            if not kws:
                continue
            kw_filter = " OR ".join(
                f"c.name =~ $kw{i}" for i in range(len(kws))
            )
            params.update({f"kw{i}": _word_pattern(kw)
                           for i, kw in enumerate(kws)})
            excludes = _split_keywords(row.get("exclude_keywords"))
            exclude_filter = ""
            if excludes:
                exclude_filter = "AND NOT (" + " OR ".join(
                    f"c.name =~ $ex{i}" for i in range(len(excludes))
                ) + ")"
                params.update({f"ex{i}": _word_pattern(kw)
                               for i, kw in enumerate(excludes)})
            query = f"""
                MATCH (c:Condition)
                WHERE ({kw_filter}) {exclude_filter}
                MATCH (e:Exercise)
                WHERE toLower(e.name) STARTS WITH toLower($ex_name)
                MERGE (c)-[rel:{rel_type}]->(e)
                SET rel += $props
                RETURN count(rel) AS c
            """
        else:
            raise ValueError(
                f"Unknown match_type {match_type!r} in {SAFETY_CSV}"
            )
        r = session.run(query, **params).single()
        linked += r["c"]
    print(f"  Safety edges (curated CSV): {linked} edges")
    return linked


# ── Synthetic Observation seed (stroke-gait pilot demo layer) ─────────────


def load_observation_seed_rows():
    """Read curated/observation_seed.csv as a list of dict rows."""
    with open(OBSERVATION_SEED_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_observation_seed(session):
    """Create the synthetic demo patient + Observation nodes from CSV.

    This is the minimal Observation model for the stroke-gait pilot:
    (Patient)-[:HAS_OBSERVATION]->(Observation)-[:MAPS_TO_ICF]->(ICFConcept).
    Everything is source='synthetic_demo'; the patient id starts with
    SYNTHETIC- so it can never be mistaken for (or collide with) MOTU
    patients. Replace the seed CSV with real device data when available.
    """
    rows = load_observation_seed_rows()
    if not rows:
        return 0
    patient_ids = sorted({r["patient_id"] for r in rows})
    for pid in patient_ids:
        session.run(
            """
            MERGE (p:Patient {patient_id: $pid})
            SET p.source = 'synthetic_demo',
                p.note = 'Synthetic demo patient for the Observation-layer pilot; not real data'
            """,
            pid=pid,
        ).consume()
    props = edge_props(
        method="curated",
        match_type="observation_seed_icf",
        confidence=1.0,
        source=OBSERVATION_SEED_SOURCE,
        review_status="unreviewed",
    )
    linked = 0
    for row in rows:
        r = session.run(
            """
            MATCH (p:Patient {patient_id: $pid})
            MERGE (o:Observation {observation_id: $oid})
            SET o.feature = $feature, o.value = toFloat($value),
                o.unit = $unit, o.observed_at = $observed_at,
                o.device = $device, o.source = 'synthetic_demo'
            MERGE (p)-[:HAS_OBSERVATION]->(o)
            WITH o
            MATCH (i:ICFConcept {code: $icf_code})
            MERGE (o)-[r:MAPS_TO_ICF]->(i)
            SET r += $props
            RETURN count(o) AS c
            """,
            pid=row["patient_id"], oid=row["observation_id"],
            feature=row["feature"], value=row["value"], unit=row["unit"],
            observed_at=row["observed_at"], device=row["device"],
            icf_code=row["icf_code"], props=props,
        ).single()
        linked += r["c"]
    print(f"  Observation seed: {linked} observations "
          f"({len(patient_ids)} synthetic patient(s))")
    return linked


# ── Scale external identifiers (curated register → AssessmentScale) ───────
#
# curated/scale_identifiers.csv holds one row per RMD scale with LOINC /
# ICF identifiers to be filled by HUMAN INPUT (LOINC codes are looked up
# from the official LOINC distribution, never inferred). The shipped file
# has all identifier cells empty: loading it is a validated no-op, and the
# loader only ever writes non-empty cells (empty stays NULL), so filling a
# cell later is the complete review action. Keys on scale_id (F9: both
# load paths now expose the property).

_SCALE_IDENT_FIELDS = ("loinc_code", "loinc_long_name", "source_url")


def load_scale_identifier_rows():
    """Read curated/scale_identifiers.csv as a list of dict rows."""
    with open(SCALE_IDENTIFIERS_CSV, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def apply_scale_identifiers(session):
    """Write non-empty identifiers onto AssessmentScale nodes (both paths).

    Shared by rehabkg.py link_post_additional and import_bulk.py post_load
    (guarded by tests/test_bridges.py::TestLoadPathParity):

    - empty cells are skipped — the all-empty register loads without
      error and writes nothing (idempotent by construction);
    - non-empty ``icf_codes`` (``;``-separated) create MAPS_TO_ICF edges
      with the shared provenance contract (method='curated',
      match_type='scale_icf_register', confidence=1.0) — MERGE on the
      (scale, code) pair, so re-runs only stamp the same props;
    - unknown scale_ids / ICF codes are reported, not fatal (the live
      liveness gate enforces presence on the canonical graph).

    Returns (scales_matched, icf_edges).
    """
    matched_total = 0
    edges_total = 0
    missing_scales = []
    missing_codes = []
    for row in load_scale_identifier_rows():
        sid = (row.get("scale_id") or "").strip()
        if not sid:
            raise ValueError(
                f"blank scale_id in {SCALE_IDENTIFIERS_CSV}: {row}"
            )
        props = {f: (row.get(f) or "").strip() for f in _SCALE_IDENT_FIELDS}
        props = {k: v for k, v in props.items() if v}
        codes = [c.strip() for c in
                 (row.get("icf_codes") or "").split(";") if c.strip()]
        if not props and not codes:
            continue  # all-empty identifier cells: nothing to write
        r = session.run(
            "MATCH (a:AssessmentScale {scale_id: $sid}) "
            "RETURN count(a) AS c",
            sid=sid,
        ).single()
        if r["c"] == 0:
            missing_scales.append(sid)
            continue
        matched_total += r["c"]
        if props:
            session.run(
                "MATCH (a:AssessmentScale {scale_id: $sid}) "
                "SET a += $props",
                sid=sid, props=props,
            )
        for code in codes:
            props_e = edge_props(
                "curated", "scale_icf_register", 1.0,
                SCALE_IDENTIFIERS_SOURCE,
                review_status=(row.get("review_status") or "unreviewed"),
                reviewed_by=(row.get("reviewed_by") or None),
                reviewed_on=(row.get("reviewed_on") or None),
                source_url=(row.get("source_url") or None),
            )
            er = session.run(
                """
                MATCH (a:AssessmentScale {scale_id: $sid})
                MATCH (i:ICFConcept {code: $code})
                MERGE (a)-[rel:MAPS_TO_ICF]->(i)
                SET rel += $props
                RETURN count(rel) AS c
                """,
                sid=sid, code=code, props=props_e,
            ).single()
            if er["c"] == 0:
                missing_codes.append(f"{sid}:{code}")
            edges_total += er["c"]
    print(f"  Scale identifiers: {matched_total} scales matched, "
          f"{edges_total} MAPS_TO_ICF edges")
    if missing_scales:
        print(f"    WARNING: scale_ids absent from graph: "
              f"{', '.join(sorted(set(missing_scales)))}")
    if missing_codes:
        print(f"    WARNING: ICF codes absent from graph: "
              f"{', '.join(sorted(set(missing_codes)))}")
    return matched_total, edges_total


ICF_CORE_SET_COLUMNS = {
    "core_set", "condition_key", "icf_code", "component", "source_url",
    "review_status", "reviewed_by", "reviewed_on",
}


def load_icf_core_set_rows():
    """Load human-supplied Core Set rows; the shipped header-only template is a no-op."""
    with open(ICF_CORE_SETS_CSV, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = ICF_CORE_SET_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError("{} missing columns: {}".format(
                ICF_CORE_SETS_CSV, sorted(missing)))
        rows = []
        for row in reader:
            if not any((value or "").strip() for value in row.values()):
                continue
            required = ("core_set", "condition_key", "icf_code", "component",
                        "source_url", "review_status")
            empty = [name for name in required if not (row.get(name) or "").strip()]
            if empty:
                raise ValueError("ICF Core Set row missing {}: {}".format(empty, row))
            if row["review_status"].strip() != "unreviewed":
                raise ValueError("ICF Core Set rows must remain unreviewed on load")
            rows.append(row)
    return rows


def apply_icf_core_set_rows(session):
    """Create unreviewed Condition→ICF reference edges from supplied register rows."""
    rows = load_icf_core_set_rows()
    landed, missed = 0, []
    for row in rows:
        key = row["condition_key"].strip()
        code = row["icf_code"].strip()
        props = edge_props(
            "curated", "icf_core_set_register", 1.0, ICF_CORE_SETS_SOURCE,
            review_status="unreviewed", core_set=row["core_set"].strip(),
            component=row["component"].strip(), source_url=row["source_url"].strip(),
            reviewed_by=(row.get("reviewed_by") or "").strip() or None,
            reviewed_on=(row.get("reviewed_on") or "").strip() or None,
        )
        # Exact normalized condition-name match only; no fuzzy or keyword
        # expansion can add unintended clinical category edges.
        result = session.run("""
            MATCH (i:ICFConcept {code: $code})
            MATCH (c:Condition)
            WHERE toLower(trim(c.name)) = toLower(trim($key))
            MERGE (c)-[r:HAS_CORE_SET_CATEGORY {core_set: $core_set}]->(i)
            SET r += $props
            RETURN count(r) AS c
        """, code=code, key=key, core_set=row["core_set"].strip(),
            props=props).single()["c"]
        if result:
            landed += result
        else:
            missed.append("{}:{}->{}".format(key, row["core_set"], code))
    print("  ICF Core Set categories: {} landed, {} missing endpoints".format(
        landed, len(missed)))
    return landed, missed


def bridge_all(session):
    """Run all bridge strategies in order."""
    bridge_exact_names(session)
    bridge_pmr_owl(session)
    bridge_copper_keywords(session)
    bridge_assessment_scales(session)
    propagate_hierarchy(session)


# Single source of truth for HPO -> ICF explicit code pairs. Each pair maps an
# HPO term to the ICF concept describing the same impairment (corrected
# 2026-11-17; the earlier set was mismatched). All pairs are unreviewed
# candidates. Used by add_additional_data.load_hpo, bridge_default_sources and
# build_csvs.py. Comment = HPO label.
HPO_ICF_PAIRS = (
    ("HP:0001369", "b710"),  # Arthritis -> Mobility of joint functions
    ("HP:0001288", "b770"),  # Gait disturbance -> Gait pattern functions
    ("HP:0003011", "b730"),  # Abnormality of the musculature (broad) -> Muscle power
    ("HP:0002066", "b770"),  # Gait ataxia -> Gait pattern functions
    ("HP:0001252", "b735"),  # Hypotonia -> Muscle tone functions
    ("HP:0002067", "b760"),  # Bradykinesia -> Control of voluntary movement
    ("HP:0002093", "b440"),  # Respiratory insufficiency -> Respiration functions
    ("HP:0001250", "b765"),  # Seizure -> Involuntary movement functions
    ("HP:0003473", "b740"),  # Fatigable weakness -> Muscle endurance functions
)
HPO_ICF_SOURCE = "add_additional_data.py:HPO_TO_ICF_MAPPINGS"


def sync_hpo_icf_pairs(session):
    """Make HPO->ICF RELATED_TO_ICF edges match HPO_ICF_PAIRS exactly.

    Idempotent. Deletes stale edges written by this curated source (for
    example the pre-2026-11-17 mismatched pairs) before merging the current
    ones, so reloading an older graph cannot leave wrong links behind. Edges
    from any other source are left alone.
    """
    from provenance import edge_props
    props = edge_props(
        "curated", "explicit_code_pair", 1.0, HPO_ICF_SOURCE,
        review_status="unreviewed",
    )
    pairs = [{"h": h, "i": i} for h, i in HPO_ICF_PAIRS]
    removed = session.run("""
        MATCH (h:HPOConcept)-[r:RELATED_TO_ICF]->(i:ICFConcept)
        WHERE r.source = $source
          AND NOT any(p IN $pairs WHERE p.h = h.code AND p.i = i.code)
        DELETE r
        RETURN count(r) AS c
    """, source=HPO_ICF_SOURCE, pairs=pairs).single()["c"]
    created = session.run("""
        UNWIND $pairs AS p
        MATCH (h:HPOConcept {code: p.h})
        MATCH (i:ICFConcept {code: p.i})
        MERGE (h)-[r:RELATED_TO_ICF]->(i)
        SET r += $props
        RETURN count(r) AS c
    """, pairs=pairs, props=props).single()["c"]
    print(f"  HPO→ICF pairs: {created} synced, {removed} stale removed")
    return created


def bridge_default_sources(session):
    """Run only the bridge strategies supported by the focused default source set.

    Excludes PMR/COPPER/KHMO keyword strategies. HPO→ICF uses the nine explicit
    code pairs maintained by the additional-data loader, not broad name overlap.
    """
    bridge_exact_names(session)
    bridge_assessment_scales(session)
    propagate_hierarchy(session)
    # The observation seed loader itself creates its explicit code-pair edges
    # as part of node creation; no separate postload matcher is needed.
    sync_hpo_icf_pairs(session)
