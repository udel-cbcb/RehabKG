# Stroke-gait pilot

Scope document for the HAIC pilot: stroke-related functioning and gait,
the first vertical slice through RehabKG's provenance, review, safety
and evaluation stack.

## Scope

**In scope**

- Stroke conditions in the graph (post-stroke, stroke sequelae,
  hemiplegia/hemiparesis, ischemic/hemorrhagic stroke — ~25 condition
  nodes match stroke keywords).
- Gait and walking concepts: ICF `d450` (Walking), `d4500`–`d4509`
  (walking sub-codes), `d469` (walking and moving), `b770` (gait
  pattern functions); HPO gait terms (Gait disturbance, Gait
  imbalance, Gait ataxia, …).
- Exercises relevant to stroke gait rehabilitation from Free Exercise
  DB (e.g. `Walking Program (Progressive)`), plus balance exercises
  that carry fall-risk precautions (e.g. `Single-Leg Balance`).
- Outcome instrumentation: Barthel index admission/discharge outcomes
  from MOTU (synthetic cohort) and the synthetic observation seed
  (gait speed, 6-minute walk distance, daily step count, Berg balance).

**Out of scope (for now)**

- Non-stroke pilots (MS via MSO, knee via TRAK/FRMO) — ontologies are
  loaded but not yet piloted.
- DVT contraindications (removed as dead rows; see
  `curated/README.md`) — re-add when a DVT condition lands.
- Link prediction, dosing, MCID computation (plan item 10).

## What is real vs synthetic

| Layer | Status |
|-------|--------|
| Ontology concepts (ICF/HPO/STO/…) | Real, released versions |
| Clinical trial titles/conditions | Real ClinicalTrials.gov records |
| MOTU patients/outcomes | Synthetic/de-identified single-center demo cohort (`source=MOTU`) |
| Observation seed (`SYNTHETIC-GAIT-001`) | Fully synthetic, labeled `source=synthetic_demo` |
| Curated recommendations/precautions | Seed rows, **all unreviewed** until clinician sign-off |
| HPO→ICF and trial→ICF links | Rule-based loose matches, confidence ≤ 0.4 |
| ICF Core Set reference categories | Not supplied yet; see `curated/icf_core_sets.csv` (header-only pending human source/licence review) |

Nothing in this graph is clinical advice. Unreviewed edges are
research candidates.

## How to query the pilot

Cypher examples (via Neo4j browser, `rehabkg.py`, or the FastAPI
`/paths` endpoint):

```cypher
// Stroke conditions and their curated recommendations (with provenance)
MATCH (c:Condition)-[r:RECOMMENDS_EXERCISE]->(e:Exercise)
WHERE c.name CONTAINS 'Stroke'
RETURN c.name, e.name, r.rationale, r.review_status, r.source
LIMIT 50;

// Safety layer on the pilot set
MATCH (c:Condition)-[r:PRECAUTION|CONTRAINDICATION]->(e:Exercise)
WHERE c.name CONTAINS 'Stroke' OR c.name CONTAINS 'Hemiplegia'
RETURN type(r), c.name, e.name, r.rationale, r.review_status;

// HPO terms → ICF concepts (the nine curated explicit code pairs only)
MATCH (h:HPOConcept)-[r:RELATED_TO_ICF]->(i:ICFConcept)
RETURN h.name, i.code, i.name, r.confidence, r.match_type, r.review_status;

// Synthetic observation seed (post item-4 import)
MATCH (p:Patient {patient_id: 'SYNTHETIC-GAIT-001'})-[:HAS_OBSERVATION]->(o:Observation)
RETURN o.feature, o.value, o.unit;
```

HTTP equivalents (read-only API, `requirements-api.txt`):

```bash
uvicorn api.app:app --host 127.0.0.1 --port 8000
curl 'localhost:8000/conditions?q=stroke'
curl 'localhost:8000/conditions/Stroke/recommendations'
curl 'localhost:8000/paths?start_name=Stroke&end_name=Walking%20Program%20(Progressive)'
```

Dashboard: `streamlit run dashboard/app.py` → **✅ Evidence & Review**
for the review loop.

Further runnable examples (safety-aware lookup, explain-this-path, gait
concept resolver, coverage audit) are in [USE_CASES.md](USE_CASES.md).

## Pilot evaluation

Core Set reachability is report-only and does not modify HPO→ICF matching:

```bash
python scripts/eval_hpo_icf_vs_core_sets.py
```

Until source-backed category rows and redistribution permission are supplied,
the report explicitly states that per-Core-Set recall cannot be evaluated.

The gold set (`eval/gold_questions.jsonl`) is stroke-gait themed:
recommendation/safety coverage, ICF gait codes, HPO gait links,
trial keyword links, observation seed, provenance completeness. Run:

```bash
python eval/run_gold.py                 # full report, exit = #failures
python eval/run_gold.py --category core # core slice only
python scripts/audit_coverage.py        # coverage + cohort limits
python scripts/graph_composition.py     # vocabulary vs dataset vs schema
python scripts/sample_edges_for_audit.py --out audit_sample.csv  # review sample
```

## Pilot workflow (maintainers)

1. Clinician reviews unreviewed edges on the dashboard; decisions
   applied via `curated/apply_decisions.py --update-graph`.
2. New curated rows follow `curated/README.md`; dead rows are blocked by
   the live-graph liveness test.
3. Gold questions updated when the pilot scope changes; the offline
   `test_gold_file_shape` keeps the file honest, the live
   `tests/test_gold.py` keeps the graph honest.
4. Full graph verification after pipeline changes:
   `python import_bulk.py` (full, with CSV export) →
   `pytest tests/test_graph.py tests/test_gold.py` → API smoke →
   dashboard e2e (`tests/test_e2e.py`, needs Streamlit on :8501).

*Last updated: 2026-10-22*
