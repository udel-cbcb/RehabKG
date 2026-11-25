# RehabKG Snapshot-Linked Evaluation Report

**Snapshot date:** 2026-11-17 (local)
**Report generated:** 2026-11-17T16:07:53Z
**Evaluated git revision:** `de7c702` (`main`); working tree had no tracked changes
**Graph:** `bolt://localhost:7688`, database `neo4j`
**Neo4j:** Kernel 5.26.29, Community edition
**Graph origin:** rebuilt on 2026-11-17 from a fresh bulk export with `python import_bulk.py` (CSV build, `neo4j-admin import`, post-load bridges)
**Manifest:** `eval/public_ontology_refresh_manifest.json` (unchanged, see Notes)
**Manifest SHA-256:** `4fa423408c8b88d411f584fe08d023040f4fcae547f465be10d9a026e9e40d63`
**Manifest generated:** 2026-11-06T00:42:44.358493+00:00

Supersedes [snapshot_report_2026-11-05.md](snapshot_report_2026-11-05.md) for
current figures. The 2026-11-05 report remains the record of the earlier
Cypher-path focused refresh.

## What changed since 2026-11-05

- Graph rebuilt through the **bulk path**, so it now includes ontology
  hierarchy edges (`SUBCLASS_OF`) that the focused refresh did not load.
- Includes the 2026-11-06 keyword-matcher change: keyword-group edges carry
  confidence 0.6 (ICD-10-bound edges 0.7). The Nov 5 graph predated it.
- The 9 HPO→ICF explicit code pairs were corrected (single source of truth
  `bridges.HPO_ICF_PAIRS`, idempotent `sync_hpo_icf_pairs()`); all remain
  `unreviewed`.
- `Outcome.value_numeric` is now imported as a typed float column.
- Use cases reworked (`docs/USE_CASES.md`, `use_cases.py`); the gold set grew
  from 35 to 40 questions (5 `usecase` checks).

## Snapshot identity

| Metric | Value |
|--------|-------|
| Nodes | 153,069 |
| Relationships | 147,691 |
| `SUBCLASS_OF` (ontology hierarchy) | 117,005 |
| Relationships excluding `SUBCLASS_OF` | 30,686 |
| `MAPS_TO_UBERON` | 14 |
| `TARGETS_ANATOMY` | 776 |
| `RELATED_TO_ICF` (HPO→ICF) | 9 |
| `MEASURED_BY` | 4,024 |
| `HAS_ICD10` | 13,027 |
| `MAPS_TO_MONDO` | 673 |
| `RECOMMENDS_EXERCISE` | 267 |
| `PRECAUTION` | 210 |
| `CONTRAINDICATION` | 18 |
| Observation→ICF `MAPS_TO_ICF` edges | 0 (absent by design) |
| Edges with `review_status = approved` | **0** |

Edge counts for the three clinical relationship types are **edges, not curated
rows**: each curated row expands to every matching Condition node (for
example 40 stroke-related Condition nodes share the same Walking Program
recommendation). The curated CSVs hold 35 recommendation rows and 5 safety
rows.

Retained ontology sources are REHABO, ICF, EXMO, PAIN, Mondo, Uberon
(10,000 named-class subset), and HPO. COPPER, KHMO, CBHA, and other flagged
families are excluded; clinical/dataset nodes are retained. This is a local
research snapshot, not a public-hosting clearance.

## Graph composition

The headline node count is vocabulary-dominated. It is not a clinical cohort
size; the dataset/clinical layer is only ~6.5% of nodes.

| Layer | Nodes | Share |
|-------|-------|-------|
| Vocabulary/ontology (ICD-10, HPO, Uberon, Mondo, ICF, EXMO, PAIN, REHABO) | 143,128 | 93.5% |
| Dataset/clinical records and exercise metadata | 9,915 | 6.5% |
| Schema bookkeeping (`NodeType`, `RelType`) | 26 | <0.1% |
| **Total** | **153,069** | **100%** |

Generate this with `python scripts/graph_composition.py`. Node counts are
identical to the 2026-11-05 snapshot.

## Source hashes

Identical to the 2026-11-05 report (re-hashed from `data/ontologies/` on
2026-11-17):

| Source | SHA-256 |
|--------|---------|
| `rehabo.owl` | `b6e0627b60ea9a7f3607ea425baf872aef56db0d6d2bab7502978550eaa21117` |
| `icf.owl` | `ab3bca176884966c86114d9bf16a6b1b341dacef70176b98aec85008aa8f239b` |
| `exmo.owl` | `fb50ade98271ed4e2fdd2f1e9f00010354fbd5743846f5f939edade225e49142` |
| `pain.owl` | `70e5c4209d5e0bb15763ba32a85cdcd7511cdc50075749b8fd1b39676c934b71` |
| `mondo.owl` | `afb2e699abf77082253ef51cca5f8531c8e4023ea0acc32ff3709818d0788a88` |
| `uberon.owl` | `938f51e7c3fc9fcbe5a2863eb346da8033737e568af5836958891c4c6bfb1192` |
| `hp.owl` | `8da35ec3b4cb494369b249acb9c2b3874a5a5839a91d5fae74b0d215b355138b` |

## Environment

| Item | Value |
|------|-------|
| OS | Darwin 27.2.0 arm64 (local) |
| Python | 3.9.0 |
| pytest | 8.4.2 |
| neo4j driver | 5.28.4 |
| Streamlit | 1.50.0 |
| Dashboard URL | `http://localhost:8501` |

## Evaluation results

All commands were run from the repository root against the rebuilt graph above.

| Suite | Command | Result |
|-------|---------|--------|
| Offline | `python3 -m pytest tests/ -q --ignore=tests/test_e2e.py --ignore=tests/test_graph.py` | **296 passed, 2 skipped** (18.80s) |
| Live graph | `python3 -m pytest tests/test_graph.py -q` | **112 passed** (1.42s) |
| Gold questions | `python3 eval/run_gold.py --json <path>` | **40/40 passed** |
| Dashboard E2E | `python3 -m pytest tests/test_e2e.py -q` | **44 passed** (238.58s) |
| Bulk parity | `REHABKG_BULK_PARITY=1 python3 -m pytest tests/test_bulk_parity.py -q` | **1 passed** (453.29s) |

Use cases: `python use_cases.py` ran start to finish with no errors on this
graph (10 use cases, the MOTU appendix and the patient-journey demo).

The gold JSON from this run is committed as `eval/gold_report.json`
(SHA-256 `86e1ffacb581aa0b70eba54c08ded9121fde0195201658f9d304eede63c09f1a`).

## Notes and limits

- **Offline test count rose from 270 to 296** because new tests were added
  (HPO→ICF pair checks and others) since 2026-11-05.
- **Bulk parity ran twice.** The first run matched every node, label/source and
  relationship count and then failed only on the gold total (40 on the graph
  versus 35 in the baseline) because the gold set had grown. After updating
  `eval/bulk_parity_baseline.json` (gold total 35 to 40) the second run passed.
  It ran on revision `0e3821f` plus that baseline edit; no code has changed
  since (later commits touch only the baseline and deck files).
- The parity test uses its own temporary container and directories. The graph
  evaluated above was rebuilt separately by `python import_bulk.py`, so the
  two builds were not the same database.
- **The refresh manifest was not regenerated.** It, and its
  `final_relationship_count` of 107,436, describe the 2026-11-06 focused
  Cypher-path refresh. The rebuilt graph has 147,691 relationships because the
  bulk path also loads 117,005 `SUBCLASS_OF` hierarchy edges (the parity test
  excludes `SUBCLASS_OF` for the same reason). Source hashes are unchanged.
- The gold questions are graph health checks (existence, bounds, provenance
  coverage); they show the graph is built correctly, not that it is clinically
  useful.
- **No recommendation or safety edge is approved.** All curated edges remain
  `unreviewed` research candidates; this report makes no clinical-readiness
  claim.
- Dashboard E2E depends on the dashboard process reading this same Neo4j
  instance; it was started for the run and stopped afterwards.
- Results are tied to the graph, manifest hash, source hashes, and environment
  above; rerun the suites after any graph or source change.

## Reproduction

1. Build and load: `python import_bulk.py` (replaces the `neo4j-test-serve`
   database; see `docs/bulk-import-architecture.md`).
2. Start the dashboard: `streamlit run dashboard/app.py --server.port 8501`.
3. Set `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD` (or use `.env`).
4. Run the commands in the evaluation table above, then `python use_cases.py`.
