# Phase 2 findings — outcome-to-scale linkage and scale identifiers

**Date:** 2026-10-26 · **Graph:** live `bolt://localhost:7688` · **Scope:**
read-only verification of Phase 2 implementation and current graph state.

## Implemented work verified

- `scripts/audit_coverage.py` groups outcomes through
  `(Outcome)-[:MEASURED_BY]->(AssessmentScale)` and reports scale names; it no
  longer queries the nonexistent `Outcome.measure_name`.
- `etl_motu.py` exposes the shared `build_motu_outcomes` builder consumed by
  both the Cypher loader and `build_csvs.py`. `tests/test_motu_parity.py` pins
  the shared outcome and scale mapping contract.
- The bulk CSV includes `AssessmentScale.scale_id`; `import_bulk.py` includes
  an idempotent backfill for older imported graphs.
- `curated/scale_identifiers.csv` has all 40 `RMD_SCALES` identifiers and is
  loaded through the shared `bridges.apply_scale_identifiers` function on
  both paths. The register currently has 18 non-empty LOINC identifiers,
  each retained as `review_status=unreviewed`; `icf_codes` are empty. No ICF
  edges were created from this register.
- NIHSS is wired into both loading paths and the staged graph has its
  `AssessmentScale` instance link.

## Live graph verification

| Check | Result |
|---|---:|
| `AssessmentScale` nodes | 40 |
| Nodes with `scale_id` | 40 |
| `Outcome` nodes | 4,024 |
| Outcomes linked by `MEASURED_BY` | 4,024 |
| 10 Meter Walk Test outcomes | 2,012 |
| Barthel Index outcomes | 2,012 |
| NIHSS concepts | 18 |
| NIHSS `SUBCLASS_OF` edges | 15 |
| ASM-110 → NIHStrokeScale `INSTANCE_OF` | 1 |
| Register-derived scale → ICF edges | 0 |

`python3 scripts/audit_coverage.py` reports the two real scale names and
counts above. No live graph write or reimport was performed during this
verification.

## Validation

- `python3 -m pytest tests/test_motu_parity.py tests/test_bridges.py
  tests/test_ontology_extract.py tests/test_graph.py tests/test_syntax.py -q`:
  **279 passed**.
- Live `python3 -m pytest tests/test_graph.py -q`: **90 passed**.
- `python3 -m ruff check --select E9,F .`: clean.
- `git diff --check`: clean.
- `python3 eval/run_gold.py`: **35/35 passed**.

LOINC mappings remain unreviewed curated suggestions, not clinical approvals.
The Phase 2 human-input rule against inferring LOINC codes was followed; this
note records current state rather than certifying the mappings.

## Gate 2

Phase 2 acceptance checks are satisfied on the current graph. No Phase 3
bridge implementation was started here. Existing unrelated uncommitted
ACVD work was left untouched.
