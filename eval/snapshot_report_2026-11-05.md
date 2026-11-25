# RehabKG Snapshot-Linked Evaluation Report

**Snapshot date:** 2026-11-05 (local)
**Report generated:** 2026-11-06T03:45:27Z
**Evaluated git revision:** `17b3228` (`main`)
**Graph:** `bolt://localhost:7688`, database `neo4j`
**Neo4j:** Kernel 5.26.29, Community edition
**Manifest:** `eval/public_ontology_refresh_manifest.json`
**Manifest SHA-256:** `4fa423408c8b88d411f584fe08d023040f4fcae547f465be10d9a026e9e40d63`
**Manifest generated:** 2026-11-06T00:42:44.358493+00:00

## Snapshot identity

| Metric | Value |
|--------|-------|
| Nodes | 153,069 |
| Relationships | 107,436 |
| `MAPS_TO_UBERON` | 14 |
| `TARGETS_ANATOMY` | 776 |
| `RELATED_TO_ICF` | 9 |
| `MEASURED_BY` | 4,024 |
| `HAS_ICD10` | 13,027 |
| `MAPS_TO_MONDO` | 673 |
| Excluded-source nodes remaining | 0 |
| Manifest `final_node_count` | 153,069 |
| Manifest `final_relationship_count` | 107,436 |

The snapshot is the deterministic focused ontology refresh. Retained ontology
sources are REHABO, ICF, EXMO, PAIN, Mondo, Uberon (10,000 named-class subset),
and HPO. COPPER, KHMO, CBHA, and other flagged families are excluded;
clinical/dataset nodes are retained. This is a local research snapshot, not a
public-hosting clearance.

## Graph composition

The headline node count is vocabulary-dominated. It is not a clinical cohort
size; the dataset/clinical layer is only ~6.5% of nodes.

| Layer | Nodes | Share |
|-------|-------|-------|
| Vocabulary/ontology (ICD-10, HPO, Uberon, Mondo, ICF, EXMO, PAIN, REHABO) | 143,128 | 93.5% |
| Dataset/clinical records and exercise metadata | 9,915 | 6.5% |
| Schema bookkeeping (`NodeType`, `RelType`) | 26 | <0.1% |
| **Total** | **153,069** | **100%** |

Relationships: **107,436**. Generate this table from a live graph with
`python scripts/graph_composition.py`; the script classifies each node once
even when it carries multiple labels.

## Source hashes

The manifest is canonical. Current staged source hashes:

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
| OS | Darwin 25.6.0 arm64 (local) |
| Python | 3.9.11 |
| pytest | 7.4.3 |
| neo4j driver | 5.11.0 |
| Streamlit | 1.28.0 |
| Dashboard URL | `http://localhost:8501` |

## Evaluation results

All commands were run from the repository root against the snapshot above.

| Suite | Command | Result |
|-------|---------|--------|
| Offline | `python3 -m pytest tests/ -q --ignore=tests/test_e2e.py --ignore=tests/test_graph.py` | **270 passed, 2 skipped** (15.07s) |
| Live graph | `NEO4J_URI=bolt://localhost:7688 NEO4J_PASSWORD=... python3 -m pytest tests/test_graph.py -q` | **112 passed** (1.15s) |
| Gold questions | `NEO4J_URI=bolt://localhost:7688 NEO4J_PASSWORD=... python3 eval/run_gold.py --json /tmp/rehabkg_gold_report.json` | **35/35 passed** |
| Dashboard E2E | `python3 -m pytest tests/test_e2e.py -q` | **44 passed** (236.67s) |
| Bulk parity | `REHABKG_BULK_PARITY=1 python3 -m pytest tests/test_bulk_parity.py -q` | **1 passed** (440.87s) |

The gold JSON produced by the run is identical to `eval/gold_report.json`
(SHA-256 `fe8229d3e4e913f227a15a19f8cc8b2761e6bdb627ad5a770b4390675becc873`).

## Notes and limits

- The offline command excludes `tests/test_graph.py` (requires live Neo4j) and
  `tests/test_e2e.py` (requires a running dashboard).
- Dashboard E2E results depend on the dashboard process at
  `http://localhost:8501` reading this same Neo4j snapshot.
- The bulk parity test builds a generated-CSV export, imports it with
  `neo4j-admin`, runs the bulk post-load bridges, and compares against
  `eval/bulk_parity_baseline.json`. It matches all node/label/source counts,
  the bridge/clinical relationship contract, and gold **35/35**. `SUBCLASS_OF`
  is intentionally excluded because the bulk path also emits source-owned
  Mondo/Uberon/HPO/EXMO hierarchy that the focused refresh does not rebuild.
- Results are tied to the graph snapshot, manifest hash, source hashes, and
  environment above; rerun the suites after any graph or source change.

## Reproduction

1. Start Neo4j and load the snapshot.
2. Start the dashboard: `streamlit run dashboard/app.py --server.port 8501`.
3. Set `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD`.
4. Run the four commands in the evaluation table above.
