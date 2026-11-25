# RehabKG project recommendations

**Status:** Working plan · **Started:** 2026-11-01

## Goal

Prioritize dependable, reviewable research workflows over adding graph volume or AI features. RehabKG remains a research prototype—not clinical decision support.

## Ordered work plan

| # | Workstream | Why now | Completion evidence | Status |
|---|---|---|---|---|
| 1 | Run a focused stroke–gait clinician review pilot | The live graph has zero approved relationships; recommendations and safety statements are candidates only. | Named clinician reviewers; decisions and citations captured; review CSV validated; reviewed changes applied or deliberately left unreviewed; summary records scope and unresolved items. | **In progress — prepare review packet** |
| 2 | Resolve source permissions before public hosting | Technical availability does not grant redistribution rights; LOINC-derived fields have specific online notice requirements. | Source-by-source release, terms, attribution, third-party content, and LOINC notice decisions documented; public export filters nodes and relationships and checks endpoints. | **In progress — opt-in screening exporter implemented; terms review still required** |
| 3 | Make rebuilds reproducible | Source acquisition is partly manual and Cypher/bulk coverage may differ. | Versioned source manifest with checksums and import settings; parity test across loading paths; repeatable build instructions. | **Complete — focused-refresh E2E and generated-CSV bulk parity test pass against the committed baseline** |
| 4 | Keep evaluation current and snapshot-linked | Historical test reports do not establish current graph behavior. | Gold, live graph, and dashboard suites rerun after changes; each report identifies graph snapshot/date and environment. | **Complete for 2026-11-05 snapshot; rerun after any change** |
| 5 | Maintain the clinical boundary | MOTU and the observation seed are demo data with distinct status; edges are not validated care guidance. | Datasheet, UI, API, demos, and presentations consistently distinguish synthetic/de-identified data and unreviewed candidates; no clinical-readiness claims. | Ongoing |
| 6 | Defer GraphRAG and care recommendations | Natural-language answers can obscure provenance, uncertainty, and review status. | Reconsider only after source governance, clinician review, and snapshot-specific evaluation gates are dependable. | Deferred |

## Workstream 1 — stroke–gait review pilot

### Scope prepared from the repository

- Curated recommendation seed: `Stroke → Walking Program (Progressive)`; rationale: “progressive gait practice (motor relearning)”; status: `unreviewed`; source: `curated/condition_exercise.csv`.
- Stroke-related precaution seeds in `curated/safety_contraindications.csv` cover:
  - `Single-Leg Balance` — fall risk; supervision/guarding language needs review.
  - `Walking, Treadmill` — handrail/body-weight support and close supervision language needs review.
  - `Narrow Stance Squats` — mediolateral stability concern needs review.
  - `Balance Board` — acute/subacute stroke caution needs review.
- Reviewers should assess whether each statement is appropriately scoped, clinically reasonable, and supported by the cited source. They may approve, reject, or leave any row unreviewed. Approval requires a citation.
- This packet is not clinical advice and does not endorse any seed statement. No decisions or citations are fabricated here.

### Required human inputs / acceptance criteria

1. Identify a qualified clinician reviewer (and, if possible, a second reviewer for safety rows).
2. Reviewer completes one decision per in-scope curated row: `approved`, `rejected`, or blank to leave unchanged; enters reviewer name/date and evidence citation for approvals; adds comments for requested edits.
3. A maintainer validates decisions with `curated/apply_decisions.py --dry-run`, resolves any rationales/row-key issues, and applies only explicitly authorized decisions with `--update-graph`.
4. Rerun focused graph and gold checks; record decision counts, citations, graph snapshot, and any rows left unresolved.

### Progress log

- **2026-11-01 — prepared:** Confirmed curated recommendation and safety seed rows and reviewed the clinician contribution instructions. Live Neo4j snapshot has 0 approved reviewable relationships. Review packet content is ready; execution is blocked on a clinician reviewer and their evidence-backed decisions.
- **2026-11-01 — handoff artifact:** `deliverables/stroke_gait_review_packet.csv` contains the one stroke→walking recommendation plus four stroke-related PRECAUTION rows. Decision, reviewer, date, citation, and comment fields are intentionally blank; no judgments were inferred.

## Workstream 2 — public-hosting permissions and export screening

- **2026-11-01 — engineering aid:** `export_csv.py --step all --public-candidate` now filters exported nodes to the proposed candidate source set, excludes source-less nodes, drops relationships with either endpoint excluded, and writes a count/source manifest. The option is opt-in and explicitly does not assert legal clearance.
- **2026-11-05 — focused graph refresh:** staged REHABO, ICF, EXMO, PAIN, Mondo, Uberon subset, and HPO were loaded on `bolt://localhost:7688`; COPPER, KHMO, CBHA and flagged ontology families were removed. The nine explicit HPO→ICF links now carry curated, unreviewed provenance. Final counts and file hashes: `eval/public_ontology_refresh_manifest.json`. Initial refresh needed manual HPO recovery, now fixed and covered by checks.
- **Pipeline follow-up:** default Cypher and bulk ontology paths now target the focused source set, broad bridge invocation is replaced with `bridge_default_sources`, and downloader/exporter source lists were narrowed. Focused tests cover source membership and bridge policy. The offline CSV build is validated by the E2E test; live Cypher-vs-bulk parity is validated by `tests/test_bulk_parity.py` against `eval/bulk_parity_baseline.json`.
- **2026-11-05 — slide deck:** `deliverables/RehabKG_project_presentation.pptx` and its Markdown source now use the Nov 5 graph counts/source scope, show nine explicit unreviewed HPO→ICF links, disclose zero Observation→ICF edges, and report fresh graph, gold, and dashboard results.
- **Still blocked:** source-by-source release/terms and third-party-content review, LOINC online notice and field compliance, jurisdictional review, and approval of any actual public-hosting allowlist. `docs/notes/public_hosting_allowlist.md` remains a proposal and is not consumed automatically by default exports.
- **Validation:** covered by `tests/test_export_public_filter.py`; no live export or public release was run.

## Workstream 3 — reproducible rebuilds

- **2026-11-05 — focused-refresh E2E:** `tests/test_pipeline_e2e.py` passed on a disposable seeded Neo4j Community database named `test` (seeded from `neo4j_test_data`, APOC mounted). The run covered the offline CSV build plus `scripts/refresh_public_ontologies.py`; the resulting graph matched the source graph on all node/label/source counts and clinical contract metrics.
- **Determinism fix:** the refresh selected the 10k Uberon and 5k Mondo subsets by slicing an unsorted list built from a Python `set`, so hash randomization changed the subset per run. Both selections are now sorted before slicing (`uri` as the final Mondo tiebreaker). Selection hashes are identical across `PYTHONHASHSEED=1,2,3`; two consecutive full E2E runs produced identical snapshots: 153,069 nodes and 107,436 relationships.
- **Existing graph aligned (2026-11-05):** backed up `neo4j_test_data` to `/Users/chenc/Documents/2026/Work/HAIC/RehabKG_backups/neo4j_test_data_2026-11-05` and refreshed `bolt://localhost:7688` with the fixed script. The live graph now matches the deterministic E2E snapshot: 153,069 nodes and 107,436 relationships, `MAPS_TO_UBERON` 14, `TARGETS_ANATOMY` 776. A second refresh was idempotent. Clinical counts (`MEASURED_BY` 4,024, stays 1,006, `HAS_ICD10` 13,027, `MAPS_TO_MONDO` 673) are unchanged. The manifest now records `final_node_count` and `final_relationship_count`.
- **2026-11-06 — Cypher-vs-bulk parity:** a full generated-CSV `neo4j-admin` import into a disposable Neo4j container now matches the focused snapshot on all node/label/source counts, the bridge/clinical relationship contract, and gold **35/35**. The opt-in test is `tests/test_bulk_parity.py`; expected values live in `eval/bulk_parity_baseline.json`. The test requires `REHABKG_BULK_PARITY=1`, Docker, and staged source data. Ontology `SUBCLASS_OF` is intentionally out of scope because the bulk path also emits source-owned Mondo/Uberon/HPO/EXMO hierarchy that the focused refresh does not rebuild.

## Workstream 4 — current evaluation

- **2026-11-05 — rerun:** graph tests **112 passed**, gold **35/35** (`eval/gold_report.json`), and dashboard E2E **44/44**, all against the focused November 5 graph. The presentation reports these results.
- **2026-11-05 — snapshot report:** `eval/snapshot_report_2026-11-05.md` records the Neo4j version/edition, database, source and manifest hashes, environment, commands, and results. Offline suite: **270 passed, 2 skipped**.
- **2026-11-06 — curated keyword matching + composition:** recommendation/safety `keyword_group` rows now use whole-word matching with `exclude_keywords` (stroke rows exclude `heat stroke`) and plural variants (`fractures`) to preserve recall. Keyword-group edges are stamped `confidence=0.6` and `curation_basis=keyword_group`; the 1,320-condition simulation kept **165 recommendation / 144 safety keyword edges** unchanged. `scripts/graph_composition.py` reports **143,128 vocabulary / 9,915 dataset / 26 schema** nodes. Targeted tests **116 passed**; full offline suite **248 passed, 38 skipped** because live Neo4j and opt-in suites were unavailable. Commit `d3677d7`.
- **2026-11-17 — rebuild and rerun:** graph rebuilt from a fresh bulk export (153,069 nodes, 147,691 relationships). Offline **296 passed, 2 skipped**, graph tests **112 passed**, gold **40/40**, dashboard E2E **44/44**, bulk parity **passed** (`eval/snapshot_report_2026-11-17.md`). Also: corrected the nine HPO→ICF code pairs, typed `Outcome.value_numeric`, and reworked the use cases.
- **Ongoing:** rerun the four suites and update the snapshot report after any graph or source change.

## Operating rules

- Never approve a relationship without a citation and an identified reviewer.
- Do not invent ICF Core Set categories, LOINC identifiers, permissions, or clinical evidence.
- Keep synthetic observation data separate from MOTU records.
- Keep API/dashboard read-only behavior and research-only scope unless the project explicitly approves a governed change.
- For each completed workstream, update its status here with evidence and unresolved risks before moving to the next item.

## References

- `docs/CONTRIBUTING_CLINICIANS.md`
- `curated/README.md`
- `curated/condition_exercise.csv`
- `curated/safety_contraindications.csv`
- `docs/notes/data_hosting_license_audit.md`
- `docs/notes/phase2_findings.md`
- `docs/notes/phase5_findings.md`
