#!/usr/bin/env python3
"""Shared edge-provenance contract for RehabKG.

Every typed clinical edge created by pipeline Cypher stamps five properties:

  method        'curated' (hand-maintained table/CSV) | 'rule_based'
  match_type    rule name (e.g. 'keyword_whole_word', 'exact_name')
  confidence    float 0-1 (rule quality, not probability)
  source        originating file or 'pipeline:<rule-name>' (stable rule
                identity shared by both load paths, not the entry point)
  review_status 'unreviewed' | 'approved' | 'rejected'

Usage in Cypher (props passed as a query parameter):

    MERGE (a)-[r:REL_TYPE]->(b)
    SET r += $props

with ``props`` taken from a preset below or built with :func:`edge_props`.

The contract exists so consumers (dashboard, API, GraphRAG) can filter and
cite edges mechanically. Structural edges (SUBCLASS_OF, INSTANCE_OF,
FROM/TO_NODE_TYPE, HAS_STAY, HAS_OUTCOME, MEASURED_BY, ...) keep their
load-time properties and are documented in docs/DATASHEET.md instead.

Model-generated edges (none exist yet) must use method='model_generated'
and stay review_status='unreviewed' until a human approves them.
"""

METHODS = ("curated", "rule_based", "model_generated")
REVIEW_STATUSES = ("unreviewed", "approved", "rejected")


def edge_props(method, match_type, confidence, source,
               review_status="unreviewed", **extra):
    """Build a validated provenance property map for ``SET r += $props``.

    Extra keyword args with non-None values are merged in (e.g. ``keyword``,
    ``category``, ``rationale``); None values are dropped so empty CSV cells
    become absent properties instead of empty strings.
    """
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}, got {method!r}")
    if review_status not in REVIEW_STATUSES:
        raise ValueError(
            f"review_status must be one of {REVIEW_STATUSES}, got {review_status!r}"
        )
    conf = float(confidence)
    if not 0.0 <= conf <= 1.0:
        raise ValueError(f"confidence must be within [0, 1], got {confidence!r}")
    if not source or not isinstance(source, str):
        raise ValueError(f"source must be a non-empty string, got {source!r}")
    props = {
        "method": method,
        "match_type": match_type,
        "confidence": conf,
        "source": source,
        "review_status": review_status,
    }
    for key, value in extra.items():
        if value is not None:
            props[key] = value
    return props


# ── Postload rule presets (shared by import_bulk.py and rehabkg.py) ───────
# Source strings name the *rule*, not the entry point, so both load paths
# produce identical provenance.

HAS_ICD10 = edge_props(
    "rule_based", "icd10_normalized_prefix", 0.9, "pipeline:postload#has_icd10")
MAPS_TO_MONDO = edge_props(
    "rule_based", "name_contains", 0.6, "pipeline:postload#maps_to_mondo")
STUDIES_CONDITION = edge_props(
    "rule_based", "condition_name_match", 0.7,
    "pipeline:postload#studies_condition")
# Flagged: loose bidirectional CONTAINS over ~30k HPO x ~150 ICF names.
# Low confidence is deliberate — consumers must filter review_status or
# confidence before treating these as trustworthy.
HPO_TO_ICF = edge_props(
    "rule_based", "name_contains_bidirectional", 0.4,
    "pipeline:postload#hpo_to_icf")
MAPS_TO_UBERON = edge_props(
    "rule_based", "name_contains_bidirectional", 0.6,
    "pipeline:postload#maps_to_uberon")
TRIAL_KEYWORD_TO_ICF = edge_props(
    "rule_based", "trial_keyword", 0.7, "pipeline:postload#trial_keywords_icf")
TARGETS_ANATOMY = edge_props(
    "rule_based", "via_muscle_uberon", 0.8,
    "pipeline:postload#targets_anatomy")

# ── Cypher-path extras ────────────────────────────────────────────────────

MUSCLE_TO_ICF = edge_props(
    "curated", "muscle_region_map", 1.0,
    "pipeline:etl_ontologies:bridge_muscles_to_icf")
RMD_MEASURES = edge_props(
    "curated", "rmd_scale_icf", 1.0, "pipeline:etl_datasets:create_rmd_scales")
EXERCISE_PROGRESSES_TO = edge_props(
    "curated", "exercise_progression_table", 1.0,
    "pipeline:etl_datasets:create_exercise_progressions")

# ── bridges.py presets (keyword= added per row at call time) ──────────────

EXACT_NAME_ICF = edge_props(
    "curated", "exact_name", 0.9, "bridges.py:EXACT_NAME_ICF")
KEYWORD_ICF_PMR = edge_props(
    "rule_based", "keyword_whole_word", 0.6, "bridges.py:PMROWL_KEYWORDS")
KEYWORD_ICF_COPPER = edge_props(
    "rule_based", "keyword_whole_word", 0.6, "bridges.py:COPPER_KEYWORDS")
ASSESSMENT_MEASURES = edge_props(
    "rule_based", "keyword_whole_word", 0.6,
    "bridges.py:ASSESSMENT_ICF_BRIDGES")
HIERARCHY_PROPAGATION = edge_props(
    "rule_based", "hierarchy_propagation", 0.5,
    "bridges.py:propagate_hierarchy")


# ── Curated rows bound via Condition.icd10_code (Gate 0 policy) ───────────
# Postload sets Condition.icd10_code from either exact (case-insensitive)
# name matches against MondoDisease (icd10_source='mondo_exact_name') or
# curated/condition_icd10_overrides.csv (icd10_source='curated_override');
# see docs/notes/phase0_findings.md. Bound edges sit deliberately below
# keyword_group confidence: the Condition↔code binding is rule/agent
# derived and stays review_status=unreviewed until a clinician approves.

ICD10_BIND_CONFIDENCE = 0.7

# icd10_source value on Condition → match_type stamped on the bound edge.
# Unknown sources are rejected so a graph mutated outside the policy cannot
# silently mint edges under a made-up match_type.
ICD10_MATCH_TYPES = {
    "mondo_exact_name": "icd10_via_mondo",
    "curated_override": "icd10_override",
}


def icd10_edge_props(source, review_status, icd10_source, **extra):
    """Provenance props for a curated row that bound via Condition.icd10_code.

    ``icd10_source`` is the matched Condition's icd10_source property; it
    selects the match_type so consumers can separate exact-Mondo-propagated
    bindings from hand-written overrides. Extra kwargs follow :func:`edge_props`.
    """
    try:
        match_type = ICD10_MATCH_TYPES[icd10_source]
    except KeyError:
        raise ValueError(
            f"icd10_source must be one of {tuple(ICD10_MATCH_TYPES)}, "
            f"got {icd10_source!r}"
        ) from None
    return edge_props("curated", match_type, ICD10_BIND_CONFIDENCE, source,
                      review_status=review_status, **extra)


# ── CSV-import backfill ───────────────────────────────────────────────────
# neo4j-admin CSV import cannot stamp provenance props (the rel CSVs carry
# only :START_ID/:END_ID), so these types arrive property-less. The backfill
# stamps them as deterministic build_csvs transforms (rule_based/csv_import)
# — never hand-reviewed. Structural types (SUBCLASS_OF, HAS_STAY, ...) are
# intentionally excluded; see docs/DATASHEET.md.

CSV_IMPORT_RELS = (
    "RECOMMENDS_EXERCISE",
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
)


def backfill_csv_import_edges(session, rel_types=None):
    """Stamp clinical edges left unstamped by the CSV bulk import.

    Run AFTER all bridge/rule Cypher so only CSV-imported rows are
    touched (rule-created edges already carry method). Idempotent:
    only edges with r.method IS NULL are updated.
    """
    total = 0
    for rel_type in (rel_types or CSV_IMPORT_RELS):
        r = session.run(
            f"MATCH ()-[r:{rel_type}]->() WHERE r.method IS NULL"
            " "
            "SET r.method = 'rule_based', r.match_type = 'csv_import', "
            "    r.confidence = 1.0, r.source = $source, "
            "    r.review_status = 'unreviewed' "
            "RETURN count(r) AS c",
            source=f"export:rel_{rel_type.lower()}.csv",
        ).single()
        total += r["c"]
        if r["c"]:
            print(f"  Backfilled {r['c']} {rel_type} edges (csv_import)")
    return total
