# HAIC Integration Plan

**Created**: 2026-10-22 · **Status tracker for the trust/API/evaluation workstream**

> Context: an external review proposed repositioning RehabKG from "a graph that
> catalogs rehabilitation knowledge" to "a graph other AI components can query,
> trust, and give feedback to" (HAIC alignment). This plan is the agreed
> implementation order, verified against the actual codebase on 2026-10-22.
> Priorities assume the trustworthy/queryable positioning; confirm with HAIC
> before investing in the later measurement-layer items.

## Priority order and status

| # | Item | Effort | Status |
|---|------|--------|--------|
| 1 | Provenance sweep: every relationship creator stamps `method`, `match_type`, `confidence`, `source`, `review_status`; flag the loose HPO→ICF matcher | S | done |
| 2 | Evidence columns on curated CSVs (`citation_doi`, `citation_pmid`, `evidence_level`, `population`, `reviewed_on`) + loader passthrough | S | done |
| 3 | Safety edges (`PRECAUTION` / `CONTRAINDICATION`) from a curated CSV, returned together with recommendations | M | done |
| 4 | Numeric outcomes + `Observation` seed layer (also fixes the dashboard `AVG` bug) | M | done |
| 5 | Read-only FastAPI service with provenance-carrying `/explain` payloads | M | done |
| 6 | Clinician review loop: dashboard "Evidence & review" page + decision-CSV round trip (`curated/apply_decisions.py`) | M | done |
| 7 | Evaluation: gold question set + runner, coverage audit, edge-audit sampler | M | done |
| 8 | Governance: datasheet, CITATION.cff, curated-data README/license note, clinician contribution guide | S | done |
| 9 | Stroke-gait pilot assembly: seed safety rows, 20 gold questions, pilot doc, audit run | M | done |
| 10 | Deferred: GraphRAG demo via API, MCID rows, dose props, teaching subgraph, link prediction, full FHIR/OMOP export | — | deferred |

## Design decisions (locked for this workstream)

- **Edge provenance contract** (every typed clinical edge):
  `method` ∈ {`curated`, `rule_based`}; `match_type` (string, rule name);
  `confidence` (float 0–1); `source` (file or `pipeline:rule`); `review_status`
  ∈ {`unreviewed`, `approved`, `rejected`}. Implemented once in
  `provenance.py`, applied via Cypher `SET r += $props`.
- **Curated CSVs stay in Git** as the system of record (versioned, PR-reviewable).
  Clinicians interact through the dashboard review page and decision CSVs —
  never through Git. `curated/status` column maps to edge `review_status`.
- **Model-generated edges do not exist yet**; when they do they must use
  `method='model_generated'` and be excluded from any consumer that filters
  `review_status=approved`. Consumers see provenance on every edge; filters
  are opt-in, not hidden defaults.
- **No clinical-readiness claims** until the review loop and gold-set
  evaluation have run. `review_status=unreviewed` is load-bearing.
- **Observation seed data is synthetic and labeled** (`source=synthetic_demo`)
  and attaches to a synthetic demo patient — never to MOTU patients.

## Per-item acceptance criteria

### 1. Provenance sweep
- [x] `provenance.py` module with named preset prop-maps for each pipeline rule
- [x] All postload Cypher in `import_bulk.py` and `rehabkg.py` stamps provenance
      (HAS_ICD10, MAPS_TO_MONDO, STUDIES_CONDITION, HPO→ICF, MAPS_TO_UBERON,
      trial-keyword ICF, TARGETS_ANATOMY, muscle→ICF)
- [x] HPO→ICF bidirectional-CONTAINS matcher flagged `confidence=0.4`,
      `match_type=name_contains_bidirectional`, `review_status=unreviewed`
- [x] `bridges.py` uses the same contract (`method`, `review_status` added;
      RECOMMENDS `status` prop renamed to `review_status`)
- [x] Offline tests pass; ruff clean
- [x] CSV-import backfill (`backfill_csv_import_edges`) stamps property-less
      bulk-imported clinical edges as `rule_based`/`csv_import`; live-graph
      `TestProvenance` in `test_graph.py` gates full contract coverage

### 2. Evidence columns
- [x] `curated/condition_exercise.csv` gains the five evidence columns
- [x] Loader writes non-empty values onto edges; missing values stay NULL
      (`evidence_props()` shared helper, reused by the safety loader)
- [x] `tests/test_bridges.py` updated

### 3. Safety edges
- [x] `curated/safety_contraindications.csv` (rel_type allowlist, same match
      semantics as condition CSV, evidence columns, all rows `unreviewed`)
- [x] `bridges.link_safety_edges()` wired into bulk postload and
      `rehabkg.py` post-additional linking
- [x] Seed rows: 6 stroke-gait pilot rows (4 precautions + 2 contraindications),
      clearly marked as seeds requiring clinician review
- [x] `test_graph.py` asserts safety edges exist on a live graph
      (MIN_RELS + provenance coverage)

### 4. Observation layer
- [x] MOTU outcomes get `value_numeric` (float) alongside string `value`
      (build_csvs typed column + etl_motu Cypher + postload backfill)
- [x] Dashboard outcomes query uses
      `avg(coalesce(o.value_numeric, toFloat(o.value)))` — works on old
      and new graphs (verified live, no reimport needed)
- [x] `curated/observation_seed.csv` + `bridges.load_observation_seed()`
      creates synthetic demo patient SYNTHETIC-GAIT-001, 6 `Observation`
      nodes (gait speed, 6MWT, steps, Berg), `HAS_OBSERVATION` +
      `MAPS_TO_ICF` (d450/d455) links with provenance
- [x] `observation_observation_id_unique` constraint on both load paths

### 5. Read-only API
- [x] `api/app.py` (FastAPI): `/health`, `/stats`, `/conditions?q=`,
      `/conditions/{ref}/recommendations` (safety edges always attached),
      `/paths` (bounded depth/limit, per-edge provenance in payload)
- [x] `requirements-api.txt` (pinned to a Python-3.9-verified combo);
      localhost binding documented in module docstring
- [x] `tests/test_api.py`: factory/route/read-only/validation smoke tests
      without Neo4j (importorskip fastapi); live smoke verified against
      the running graph (paths, 404, 422)
- [x] Bonus: curated CSV dead-row audit found 18 condition rows + 3 safety
      rows referencing exercises absent from the Free Exercise DB — all
      remapped to real exercise names; DVT contraindication row dropped
      (no DVT Condition in graph yet); new live-graph
      `TestCuratedCsvLiveness` gate prevents dead rows returning

### 6. Review loop
- [x] Dashboard "✅ Evidence & Review" nav page: unreviewed-edge summary by
      type, per-type unreviewed tables (cap 200), decisions-template download,
      workflow instructions (`--update-graph` skips full reimport)
- [x] `curated/apply_decisions.py`: applies decision CSVs back to curated CSVs
      (status, reviewed_by, reviewed_on, optional citation); approvals require
      a citation; unknown keys refused per-row with non-zero exit; `--dry-run`;
      `--update-graph` re-runs idempotent curated loaders on the live graph
- [x] `tests/test_apply_decisions.py` (9 offline tests: approve/reject,
      citation-required, unknown-key, dry-run, safety rel_type key, blank
      filter, column validation, invalid decision)
- [x] Live smoke: one LBP decision flipped 41 graph edges to approved with
      citation; state restored after verification

### 7. Evaluation
- [x] `eval/gold_questions.jsonl` (30 stroke-gait questions across
      core/ontology/provenance/observation, expected bounds, reviewer
      field) + `eval/run_gold.py` report runner (--category, --json,
      exit code = failures)
- [x] `tests/test_gold.py` auto-skips without Neo4j (CI-safe); parametrized
      per-question with precise failure reporting; offline
      `test_gold_file_shape` guards the JSONL itself (≥20 questions, unique
      ids, valid categories). 6 observation/provenance questions require
      the item-9 clean reimport (currently 24/30 live)
- [x] `scripts/audit_coverage.py`: condition ICD/rec/safety coverage,
      outcome scale + value backfill, exercise fan-in, MOTU cohort limits,
      provenance coverage, known-gaps section
- [x] `scripts/sample_edges_for_audit.py`: stratified edge sample
      (7 rel types, seeded) → review CSV

### 8. Governance
- [x] `docs/DATASHEET.md`: motivation, composition (sources + license
      pointers), collection/preprocessing, biases (MOTU single-center
      amputation cohort, fitness-oriented exercise catalog, loose-match
      bridges, ICD-10 binding policy), intended uses, explicit non-intended uses
      (no CDS/care), maintenance
- [x] `CITATION.cff` (MIT, CBHB lab, abstract + keywords)
- [x] `curated/README.md`: column contract, match_type semantics
      (keyword_group whole-word matching vs icd10 bindings), provenance mapping table, review
      workflow, DVT-row removal note, fracture-rationale note, dead-row
      audit note
- [x] `docs/CONTRIBUTING_CLINICIANS.md`: 10-minute no-Git review loop,
      per-edge-type guidance, citation-required rule, safety/scope
      disclaimers (root LICENSE already MIT)

### 9. Stroke-gait pilot
- [x] `docs/PILOT_STROKE_GAIT.md` (scope, real-vs-synthetic table, Cypher +
      HTTP query examples, pilot evaluation commands, maintainer workflow)
- [x] Safety seeds + gold questions are the pilot set (30 gold questions;
      stroke recs + 5 precautions + 18 contraindications live)
- [x] Reports checked in: `eval/gold_report.json` (30/30), 
      `eval/audit_report.{json,txt}` (coverage + cohort limits)
- [x] Final verification on a clean full reimport (`python3 import_bulk.py`):
      graph tests 77/77 (incl. curated CSV liveness), gold 30/30, offline
      suite 243 passed, API live smoke (Stroke → Walking Program path with
      full provenance; precautions attached), dashboard e2e 44/44
      (Streamlit on :8501)
- [x] Blockers fixed en route: pipeline refactor had dropped the BioPortal
      shortlist extractors + RMD shared constants + the stop_neo4j container
      stop (see commit `37088f8`)

## Deferred (item 10) — explicitly not now

GraphRAG demo (after API is stable), MCID table beyond pilot scales, dose
props, teaching subgraph, link prediction (no feedback data yet), full
FHIR/OMOP export (document the MOTU↔FHIR mapping instead), GraphQL, auth.

## Verification protocol (after each item, and once at the end)

1. `python -m pytest tests/ -q --ignore=tests/test_e2e.py --ignore=tests/test_graph.py`
2. `ruff check --select E9,F .`
3. Final: re-run `python import_bulk.py --skip-export`, then
   `pytest tests/test_graph.py`, API smoke, and dashboard e2e.
