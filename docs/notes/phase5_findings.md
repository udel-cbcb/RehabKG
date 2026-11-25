# Phase 5 findings — ICF Core Sets reference layer

**Date:** 2026-10-27

## Human input status

No ICF Research Branch category lists or redistribution confirmation were
present in the repository. No category codes or source claims were invented.
`curated/icf_core_sets.csv` is a header-only template pending those inputs.

## Implemented

- Shared loader on Cypher and bulk post-load paths; the empty template is a
  no-op. Populated rows require exact condition-name matching and create
  `HAS_CORE_SET_CATEGORY` edges with full curated provenance and
  `review_status=unreviewed`.
- Read-only evaluator at `scripts/eval_hpo_icf_vs_core_sets.py`. It reports
  per-Core-Set reachability when human-supplied categories exist and identifies
  HPO→ICF target codes outside the supplied sets. It never changes matcher
  behavior or graph edges.
- Initial report at `eval/hpo_icf_core_sets_report.md` states that recall is
  not evaluable until source data and redistribution terms are provided.
- Curated register use is documented in `curated/README.md` and
  `docs/PILOT_STROKE_GAIT.md`.

## Gate 5

Implementation is ready, but clinical coverage evaluation is blocked on human
input: provide the licensed/reusable Core Set category lists (stroke, low back
pain, osteoarthritis) and confirm redistribution terms. Until then, the
register remains empty and no Core Set category edges are created.
