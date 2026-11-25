# Phase 0 findings — baseline and diagnosis

**Date:** 2026-10-22 · **Graph:** live bulk-import snapshot (`neo4j-test-serve`,
bolt://localhost:7688) · **Python:** 3.9.0

## Baseline numbers (commit `eval/baseline_audit.json`)

| Metric | Value |
|---|---|
| Offline suite (`pytest`, e2e/graph ignored) | **243 passed** (244 after the F7 guard test added here) |
| `ruff check --select E9,F .` (HAIC gate) | clean |
| `ruff check .` (full) | **103 pre-existing errors** (I001×24, EXE001×20, BLE001×17, …) — none introduced by this phase; see Decisions |
| Gold questions (`eval/run_gold.py`) | **30/30 passed** |
| Conditions | 1,320 · with ICD-10 code: **0** · with recs: 209 · precautions: 42 · contraindications: 18 |
| Outcomes | 2,012 (value_numeric backfilled: 1,451; ADM 1,006 / DC 1,006) |
| Exercises | 949 · recommended ≥1 time: **8** |
| Provenance coverage | RECOMMENDS 217/217 · Safety 228/228 |

These match the committed `eval/audit_report.txt` and `eval/gold_report.json`
exactly — the committed reports were not stale.

## F3 resolved — audit-query bug (plan case **a**)

The `None: 2,012` scale rows were **not** missing links. Against the live graph:

- `MATCH (o:Outcome)-[:MEASURED_BY]->(a) RETURN labels(a), count(*)`
  → `[AssessmentScale]: 2,012` — every Outcome is linked.
- All 2,012 link to the Barthel Index scale (bulk path stamps
  `MEASURED_BY` to `ASM-030`; `etl_motu.py` MERGEs by `{name}` on the
  Cypher path — both land on the same logical scale).
- `Outcome` node keys are `outcome_id, phase, source, value,
  value_numeric` — there is **no `measure_name` property**.

`scripts/audit_coverage.py` L66 queries `o.measure_name`, which Neo4j
returns as `NULL` for every row (it also emits an
`UnknownPropertyKeyWarning`). **Fix belongs to Phase 2 task 1**: change
`top_scales` to join `()-[:MEASURED_BY]->(a:AssessmentScale)` and group by
`a.name`. No graph change needed for F3 itself.

## F1 preconditions recorded (for the Phase 1 policy decision)

| Check | Result |
|---|---|
| Conditions with `MAPS_TO_MONDO` | 523 — **all** `match_type=name_contains`, `confidence=0.6` (fuzzy) |
| …whose Mondo target has `icd10_code` | 118 |
| MondoDisease nodes with `icd10_code` (total) | 2,117 |
| `Mondo-[:HAS_ICD10]->ICD10Code` edges | 12,294 (92,694 ICD10Code nodes) |
| Curated codes present on `Mondo.icd10_code` | **M75.1 ✓, M75.4 ✓**; I69.3, M17.9, M54.5, M72.2, R26.81, Z96.641 **✗** |
| …same 6 absent codes, Mondo coverage at *prefix* level | I69/M17/R26/Z96: **0 nodes**; M54: 2 (radiculopathy, sciatica); M72: 3 (knuckle pads, necrotizing/nodular fasciitis — none is plantar fasciitis) |
| `DISEASE_TO_ICD10` (`import_ontologies.py`) | 18 keyword→category-code entries; only `M54.5` among the 8 curated codes appears as a value; **no live Mondo node currently carries `icd10_code='M54.5'`** |
| Conditions already mapped to the two covered codes | 5 links, mixed quality via fuzzy matcher: `Rotator Cuff Syndrome→rotator cuff syndrome` (exact-looking), `Impingement Syndrome→shoulder impingement syndrome` and `Shoulder→shoulder impingement syndrome` (substring over-matches) |

**Consequence for Phase 1:** an exact-name-only policy will activate at most
the rotator-cuff pair; the other 6 curated codes need
`curated/condition_icd10_overrides.csv` entries (unreviewed). The fuzzy
`MAPS_TO_MONDO` edges confirm the plan's design risk — copying ICD codes
through them wholesale would launder `confidence=0.6` name-contains matches
into apparently exact curated bindings.

## F9 (new) — `scale_id` property missing on the bulk path (parity gap)

- Live graph: 40 `AssessmentScale` nodes, **0 have `scale_id`** as a
  property (the value exists only as the neo4j-admin `:ID`).
- Cypher path sets the property: `etl_datasets.py` `MERGE (a:AssessmentScale
  {scale_id: row.scale_id})`.
- Bulk path does not: `build_csvs.py` L689 writes `:ID = s["scale_id"]` but
  no `scale_id` property column — so `nodes_assessmentscale.csv` lacks it.
- Impact: Phase 2's `curated/scale_identifiers.csv` loader (keyed by
  `scale_id`) and any `scale_id`-keyed query silently see NULL on bulk
  graphs; the `scale_id IS UNIQUE` constraint created by `import_bulk.py`
  is vacuous. `MEASURED_BY` linking is unaffected (matches by name/ID).

**Recommended fix (needs your go-ahead — code change + reimport):** add a
`scale_id` column to the bulk CSV (mirroring `:ID`), plus a one-off postload
backfill `SET a.scale_id = <ID>` for the current graph. Candidate home:
Phase 2 task 1 (same area as the audit fix), or fold into Phase 0 as a
follow-up commit.

## F7 fixed

- `schema.cypher` L32: `(p:KneE PADPatient)` → `(p:KneEPADPatient)`.
- Loader check (`grep` across `*.py`): **no loader creates any KneE patient
  label at all** — `etl_datasets.py`'s KneE-PAD block only creates
  `Dataset`, `RehabMovement`, `MovementError` metadata. The constraint was
  aspirational, matching the plan's fallback instruction.
- New guard: `tests/test_syntax.py::test_cypher_labels_have_no_spaces`
  parses every `CREATE CONSTRAINT`/`CREATE INDEX` line in `schema.cypher`
  and fails on labels containing spaces. Suite: 244 passed.

## Decisions needed (Gate 0)

1. **F1 / Phase 1 ICD-10 policy** — recommended default from the plan:
   copy `icd10_code` onto `Condition` only on exact (case-insensitive) name
   matches to a Mondo node that has the code, stamp
   `icd10_source='mondo_exact_name'`, emit `match_type='icd10_via_mondo'` at
   `confidence=0.7`; add unreviewed overrides CSV for the 6 codes Mondo
   does not cover. Confirm or amend.
2. **F9 scope** — fix the bulk `scale_id` column now (Phase 0 follow-up) or
   in Phase 2? A live-graph backfill requires a small Cypher write against
   the current database (no reimport needed if done as postload).
3. **Ruff baseline** — full `ruff check .` has 103 pre-existing style
   errors, so the plan's per-phase "ruff clean" DoD cannot hold as written.
   Options: (a) keep the HAIC gate `ruff check --select E9,F` and forbid
   *new* full-ruff errors per phase, bulk-fixing in Phase 9; (b) fix all
   103 now before Phase 1. Recommendation: (a).

### Gate 0 outcome (2026-10-22): all three recommendations accepted

1. Exact-match-only ICD-10 propagation (`icd10_source='mondo_exact_name'`),
   `match_type='icd10_via_mondo'`, `confidence=0.7`, plus an unreviewed
   `curated/condition_icd10_overrides.csv` for codes Mondo does not cover.
2. The F9 bulk `scale_id` fix is deferred to **Phase 2 task 1** (same area
   as the audit `top_scales` fix; one validation cycle instead of two).
3. Per-phase ruff gate is `ruff check --select E9,F` (HAIC protocol) plus
   a no-new-full-ruff-errors ratchet; the 103 pre-existing errors are
   bulk-fixed in **Phase 9**.
