# RehabKG: Linking and Data-Expansion Implementation Plan

> **Status note (2026-11-05):** this plan predates the focused source refresh;
> source-scope statements below are historical. See
> `docs/PROJECT_RECOMMENDATIONS.md` and `docs/DATA_SOURCES.md` for current scope.
>
> **Resolved after this plan (2026-11-06):** `Condition.icd10_code` is now
> populated, so `match_type=icd10` rows are no longer a no-op. Curated
> `keyword_group` rows now use whole-word matching with `exclude_keywords`
> and `confidence=0.6`; see `curated/README.md`.

**Audience:** an autonomous coding agent (openwork) working in the `RehabKG-main` repo, with a human reviewer.
**Date written:** 2026-10-22
**Basis:** reading the repo docs, curated CSVs, `eval/audit_report.txt`, and key source files. Nothing here was run against a live Neo4j graph, so Phase 0 verifies every assumption before any code changes.

---

## 0. How to use this plan

1. Read these first: `docs/HAIC_PLAN.md`, `curated/README.md`, `docs/ADDING_ONTOLOGIES.md`, `docs/bulk-import-architecture.md`, `docs/DATASHEET.md`, `provenance.py`.
2. Work phases in order. Each phase ends with a **gate**: stop, summarize what changed, and wait for human sign-off before starting the next phase.
3. One commit per task, with tests. Follow the repo's existing style (ruff clean, Python 3.9 compatible).
4. Anything marked **HUMAN INPUT** is a blocker you cannot resolve yourself. Do not guess or invent the data. Write the loader and a CSV template, leave the data empty, and flag it.

### Non-negotiable constraints (from `HAIC_PLAN.md`)

- **Provenance contract.** Every new clinical edge must carry `method`, `match_type`, `confidence`, `source`, `review_status` via `provenance.py` (`edge_props`, named presets). Add new presets there rather than inlining dicts.
- **`review_status` defaults to `unreviewed`.** Never set `approved` in code. Approval happens only through `curated/apply_decisions.py` with a citation.
- **No clinical-readiness claims.** All outputs and docs stay "research-support examples, not validated guidance".
- **Two load paths must stay in parity:** the Cypher path (`rehabkg.py` + `etl_*.py`) and the bulk path (`build_csvs.py` + `import_bulk.py`). Every new node or edge type must work in both, with a test.
- **Synthetic data stays labeled** (`source=synthetic_demo`, never attached to MOTU patients).
- **Curated CSVs in `curated/` are the system of record** for anything a clinician might review.
- Do not auto-download anything that needs a licence or credentials. Stage files under `data/raw/` or `data/ontologies/` as the docs describe.

### Out of scope (do not start)

SNOMED CT loading, GraphRAG, link prediction, MCID tables, dose properties, FHIR/OMOP export, ingesting raw sensor time series into Neo4j, and any dataset licensed CC BY-NC or CC BY-NC-ND (GAITEX, GaitIntent, UCOPhyRehab++, REHAB24-6) or credentialed (MIMIC-IV).

---

## 1. Findings this plan responds to

| # | Finding | Evidence | Confidence |
|---|---------|----------|------------|
| F1 | 29 of 35 rows in `curated/condition_exercise.csv` use `match_type=icd10`, which is a documented no-op because `Condition` nodes have no `icd10_code`. Only the 6 `keyword_group` rows take effect. | `bridges.py` (~L415-480 docstring and `icd10` branch); `eval/audit_report.txt` "Known gaps" | High |
| F2 | Only 8 of 949 exercises are recommended at least once; 0 of 1,320 Conditions have an ICD-10 link. | `eval/audit_report.txt` | High |
| F3 | The audit reports `None: 2,012` for outcome scales. This is either an audit-query bug or missing `Outcome -[:MEASURED_BY]-> AssessmentScale` links. The bulk path *does* write `MEASURED_BY` to a Barthel scale (`build_csvs.py` ~L490-520), so the audit query is the first suspect. | `scripts/audit_coverage.py` (`top_scales`) | **Unverified: diagnose in Phase 0** |
| F4 | Many loaded ontologies have 0 bridges (KHMO, OPE, ONTOLOCO, TRAK, STO, MELLO-D, FRMO, PAIN, BCIO, BCTT, PACO, MSO, POEM, CBHA, PHENX, PHY, EXMO). Only PMR, COPPER and REHABO bridge to ICF. | `docs/DATA_SOURCES.md` ontology table | High |
| F5 | The 40 `AssessmentScale` nodes are hand-written in `etl_datasets.py` with no external identifiers. | `etl_datasets.py` scale list | High |
| F6 | The citation columns (`citation_doi`, `citation_pmid`, ...) are empty in every curated row, so there is nothing to validate yet. | `curated/*.csv` | High |
| F7 | `schema.cypher` L32 has `FOR (p:KneE PADPatient)` (a space in a label, so a Cypher syntax error). Nothing in the repo references `schema.cypher`, and `setup_neo4j_schema.py` does not contain it, so impact is probably limited to manual `cypher-shell -f` use. | `schema.cypher` | Medium |
| F8 | San Raffaele (3,928 patients, Barthel Index, CC BY 4.0) and REHAB / KneE-PAD are catalogued but not loaded. | `docs/DATA_SOURCES.md` "Manual Download Required" | High |

---

## Phase 0: Baseline and diagnosis (S)

**Goal:** establish the numbers every later phase is measured against, and resolve F3 and F7.

Tasks
1. Run the offline suite and record the result: `pytest -q` (expect ~243 passing). Run `ruff check .`.
2. If a populated Neo4j is available (**HUMAN INPUT:** connection details in `.env`), run `python scripts/audit_coverage.py --json eval/baseline_audit.json` and `python eval/run_gold.py`. Commit `eval/baseline_audit.json`. If no live graph is available, say so and skip the live steps; do not fabricate numbers.
3. **Diagnose F3.** Run these against the live graph and record results in `docs/notes/phase0_findings.md`:
   - `MATCH (o:Outcome) RETURN count(o)`
   - `MATCH (o:Outcome)-[:MEASURED_BY]->(a) RETURN labels(a), count(*)`
   - `MATCH (o:Outcome)-[:MEASURED_BY]->(a) RETURN a.name, a.scale_id, count(*) LIMIT 10`
   Compare with the `top_scales` query in `scripts/audit_coverage.py`. Determine which of three cases holds: (a) links exist and the audit reads the wrong property, (b) links are missing on the Cypher path only (`etl_motu.py` ~L168-179), or (c) links are missing on both paths.
4. **Check F1 preconditions.** Record: how many `Condition` nodes have a `MAPS_TO_MONDO` edge; how many of those Mondo nodes have `icd10_code`; whether each of the 8 distinct ICD-10 codes in `condition_exercise.csv` (I69.3, M17.9, M54.5, M72.2, M75.1, M75.4, R26.81, Z96.641) appears as a value in `DISEASE_TO_ICD10` (`import_ontologies.py` ~L49) or on any Mondo node.
5. **Fix F7:** in `schema.cypher` L32 rename the label to match whatever label the loaders actually use. Run `grep -rn "KneE\|KneePAD\|KNEE" *.py` first. If no loader uses it, use `KneEPADPatient` and note it in the commit. Add a syntax test to `tests/test_syntax.py` if it can cheaply catch labels containing spaces.

**Gate 0:** a short findings note listing F3's resolved cause and the F1 numbers. Human decides the F1 policy question in Phase 1.

---

## Phase 1: Make the ICD-10 curated rows land (M)

**Goal:** the 29 `icd10` rows produce `RECOMMENDS_EXERCISE` edges, without overstating confidence.

**Design risk to handle explicitly.** The only path from a `Condition` to an ICD-10 code is `Condition -[MAPS_TO_MONDO]-> MondoDisease` (name matching) followed by `MondoDisease.icd10_code`. If `MAPS_TO_MONDO` is a fuzzy name match, populating `Condition.icd10_code` from it would make a fuzzy binding look exact, while the curated edge is stamped `confidence=1.0`.

**HUMAN INPUT (decision):** choose a policy at Gate 0. The recommended default is:
- Only copy `icd10_code` onto a `Condition` when the `MAPS_TO_MONDO` match is an exact (case-insensitive) name match, or when a curated alias CSV says so.
- Stamp the new property's origin (`icd10_source = 'mondo_exact_name'`) and stamp the resulting `RECOMMENDS_EXERCISE` edges with a lower `confidence` (suggest 0.7) and `match_type='icd10_via_mondo'` rather than `icd10`.

Tasks
1. Add a postload step in **both** `rehabkg.py` (`link_post_additional`) and `import_bulk.py` (postload, ~L340-390) that sets `Condition.icd10_code` per the chosen policy. Put the Cypher in one shared function (the repo already does this for bridges, see the `bridges.py` docstring) so the two paths cannot diverge.
2. Extend `DISEASE_TO_ICD10` or add a small curated `curated/condition_icd10_overrides.csv` for the 8 codes the curated rows need, **only if** Phase 0 shows Mondo does not already cover them. Overrides need `source` and `review_status=unreviewed`.
3. Update the `icd10` branch in `bridges.py` to match the policy and the new `match_type`/`confidence`. Keep `provenance.py` as the single source for the property maps. Update the docstring that says "currently a no-op".
4. Tests: extend `tests/test_bridges.py` (offline: rows parse, unknown `match_type` still raises) and `tests/test_graph.py` (live: at least one `icd10` row now yields an edge, all new edges carry full provenance).
5. Add 3 to 5 gold questions to `eval/gold_questions.jsonl` with count bounds, for example "stroke → Walking Program (Progressive) still returns 5 PRECAUTION edges" and "osteoarthritis condition has ≥1 recommendation via icd10_via_mondo". Re-run `eval/run_gold.py`; all existing 30 must still pass.
6. Re-run the audit and record before/after for: Conditions with an ICD-10 link, RECOMMENDS edge count, exercises recommended at least once.

**Acceptance:** `Known gaps` in the audit report no longer lists the `icd10` no-op; no existing gold question regresses; every new edge is `unreviewed` with full provenance; both load paths produce identical counts (add a parity assertion).

**Gate 1:** show before/after audit numbers and 5 sample new edges for human spot check.

---

## Phase 2: Outcome-to-scale linkage and scale identifiers (M)

**Goal:** make "Outcome → AssessmentScale → ICF" real and give scales external identifiers.

Tasks
1. **Resolve F3** per Phase 0: fix the audit query, or add the missing `MEASURED_BY` creation to `etl_motu.py` (Cypher path) so it matches `build_csvs.py` (bulk path). Add a test that both paths yield the same `MEASURED_BY` count.
2. Add `curated/scale_identifiers.csv` with columns `scale_id, loinc_code, loinc_long_name, icf_codes, source_url, review_status, reviewed_by, reviewed_on`. Prefill `scale_id` and `name` for all 40 scales from `etl_datasets.py`. **Leave `loinc_code` empty.** **HUMAN INPUT:** LOINC codes must be looked up from the official LOINC download (free account). Do not infer codes from memory.
3. Add a loader (new function in `bridges.py` alongside the other curated loaders) that writes non-empty values onto `AssessmentScale` nodes and creates `MAPS_TO_ICF` edges for any `icf_codes` listed (provenance: `method=curated`). Empty cells stay NULL, as `evidence_props()` already does elsewhere.
4. Load the **NIHSS** ontology (19 classes, Tier 1 in `docs/BIO_PORTAL_CANDIDATES.md`) following `docs/ADDING_ONTOLOGIES.md`: download entry in `download_data.py`, extractor in `etl_ontologies.py`, CSV writer in `build_csvs.py`, schema constraint in `setup_neo4j_schema.py`, bridge to the existing NIHSS `AssessmentScale` if one exists (check `etl_datasets.py`; add one only if absent). Needs `BIOPORTAL_API_KEY` (**HUMAN INPUT**).
5. Update `curated/README.md` (new file, column contract) and `docs/DATA_SOURCES.md`.

**Acceptance:** audit's outcome-scale section shows real scale names; `scale_identifiers.csv` loads idempotently with all-empty identifiers without error; NIHSS loads on both paths with matching counts.

**Gate 2.**

---

## Phase 3: Bridge the loaded ontologies (L)

**Goal:** reduce the "0 bridges" list in F4 using conservative, auditable matching. This is deliberately before adding more ontologies.

**Matching rules (strict, in priority order):**
1. Existing cross-references in the source file (`oboInOwl:hasDbXref`, `skos:exactMatch`, ICF/ICD/UBERON/HP ids in annotations).
2. Exact normalized label or synonym equality.
3. Nothing else. **Do not use substring or bidirectional-containment matching.** That is the pattern already flagged as loose in the HPO→ICF matcher.

Tasks
1. Write `scripts/bridge_gap_report.py` that lists, per loaded ontology, concept count, bridge count by target, and candidate matches under rules 1 and 2, without writing anything. Commit its output as `docs/notes/bridge_gap_report.md`. **Gate 3a:** human picks which ontologies to bridge.
2. For the chosen ontologies (suggested order: STO and TRAK to ICF/Mondo for the stroke and knee pilots; KHMO to Uberon/ICF movement concepts; FRMO to ICF for the falls precautions), implement bridges in `etl_ontologies.py` (Cypher) and `build_csvs.py`/`import_bulk.py` (bulk), with new presets in `provenance.py`: `method=rule_based`, `match_type` = `xref` or `exact_label`, `confidence` 0.9 and 0.8 respectively, `review_status=unreviewed`.
3. **Parity test** (also on your own roadmap): a test that runs both paths' bridge Cypher against the same fixture and asserts equal counts. Put the fixture under `tests/fixtures/`.
4. Add a gold question per bridged ontology pinning a known, correct match, and one pinning a known non-match so false positives are visible.

**Acceptance:** every new edge has full provenance and `unreviewed`; no substring matching introduced; parity test passes; `DATA_SOURCES.md` bridge counts updated from real runs.

**Gate 3b.**

---

## Phase 4: Additional ontologies (S per ontology)

Only after Phases 1 to 3. Follow `docs/ADDING_ONTOLOGIES.md` for each. For each, stop and report if the OWL fails to parse (OPE and ONTOLOCO already do; do not take on fixing those here).

| Order | Ontology | Why | Notes |
|-------|----------|-----|-------|
| 1 | ACVD_ONTOLOGY | Stroke-adjacent, pairs with STO | Check against CVAO/STO-DRAFT first; `BIO_PORTAL_CANDIDATES.md` flags CVAO as a likely duplicate. Do not load both. |
| 2 | AERO and ICPS (optional) | Grounds the safety edges (falls and patient-safety concepts) | Bridge to existing FRMO concepts only via Phase 3 rules. |
| not now | OAE (10,589 classes) | Oncology-heavy | Defer. |

Each addition must: add a constraint, extend the pipeline on both paths, add an `Ontology table` row to `docs/DATA_SOURCES.md` with the source version and licence, and add a count assertion to `tests/test_ontology_extract.py`.

---

## Phase 5: ICF Core Sets as a reference layer (M)

**Goal:** a curated reference of ICF categories relevant to the pilot conditions, used to *evaluate* (not change) the loose HPO→ICF matcher.

Tasks
1. Add `curated/icf_core_sets.csv`: `core_set, condition_key, icf_code, component, source_url, review_status, reviewed_by, reviewed_on`. **HUMAN INPUT:** the category lists (stroke, low back pain, osteoarthritis) must come from the ICF Research Branch publications; confirm redistribution terms before committing the content. Ship the loader and an empty template with only the header and one clearly marked example row if the human does not supply data.
2. Loader creates `(Condition)-[:HAS_CORE_SET_CATEGORY {core_set, ...}]->(ICFConcept)` using the keyword-matching convention already used in `condition_exercise.csv`, with `method=curated`, `unreviewed`.
3. `scripts/eval_hpo_icf_vs_core_sets.py`: reports, per core set, how many of its ICF categories are reachable through the current HPO→ICF edges, and how many HPO→ICF edges point at ICF categories that are in no core set. **Report only. Do not alter the matcher.**
4. Add the report to `eval/` and mention it in `docs/PILOT_STROKE_GAIT.md`.

**Gate 5.**

---

## Phase 6: Clinical trials to scales, and evidence links (M)

**Goal:** use data you already load (1,387 trials) to link trials to assessment scales and to literature.

Tasks
1. In `add_additional_data.py`, extend trial parsing to keep outcome-measure text and any listed PMIDs. **Verify field names against a real API v2 response first** (expected `protocolSection.outcomesModule.primaryOutcomes[].measure` and `protocolSection.referencesModule.references[].pmid`; confirm before relying on them). Save one sample response under `tests/fixtures/`.
2. Add `curated/scale_aliases.csv` (`scale_id, alias`, e.g. common abbreviations) and match outcome text to `AssessmentScale` by exact normalized name or alias only. Create `(ClinicalTrial)-[:USES_OUTCOME_MEASURE]->(AssessmentScale)` with `method=rule_based`, `match_type=exact_alias`, `confidence=0.8`, `unreviewed`.
3. New node `:Publication {pmid}` and edge `(ClinicalTrial)-[:HAS_REFERENCE]->(Publication)` with `source='clinicaltrials.gov'`. Add constraint and bulk-path CSV support.
4. Gold questions: "trials whose outcome measure is the Berg Balance Scale" with count bounds taken from the real run.

**Acceptance:** counts reported from a real run; unmatched outcome text is written to `eval/unmatched_outcome_measures.txt` for human review rather than fuzzily matched.

**Gate 6.**

---

## Phase 7: San Raffaele rehabilitation dataset (L)

**Goal:** add named-scale (Barthel) outcomes for orthopedic and neurological patients, labeled separately from MOTU.

**HUMAN INPUT:** download from the Figshare link in `docs/DATA_SOURCES.md` into `data/raw/sanraffaele/`. Confirm the licence (CC BY 4.0) and add attribution to `CITATION.cff` and `docs/DATASHEET.md`. Provide the CMS ICD-9-CM to ICD-10-CM General Equivalence Mappings files if you want diagnosis codes crosswalked; otherwise keep ICD-9 codes as-is and label them.

Tasks
1. Inspect the real column layout before designing anything; write `docs/notes/sanraffaele_schema.md` with the columns and sample (non-identifying) values.
2. `etl_sanraffaele.py` (Cypher) and matching CSV generation in `build_csvs.py` (bulk). Use a **new patient label** (`SanRaffaelePatient`), as the schema already does for `REHABPatient`, `KneEPADPatient`, `MOTUPatient`. Do not mix cohorts.
3. Outcomes reuse the existing Barthel `AssessmentScale` node via `MEASURED_BY`. Preserve the typed numeric `value_numeric` convention from the MOTU path.
4. Every node and edge carries `source='sanraffaele'`. Add the dataset to `docs/DATASHEET.md` with its limitations (population, country, years, de-identification status as stated by the source). Do not describe it as synthetic or as validated.
5. Tests: offline loader test with a tiny hand-made fixture (not real records); live count assertions after a real load.
6. Dashboard: show the cohort on the Patients page with its source label. Minimal change only.

**Gate 7.**

---

## Phase 8: Citation tooling for the pilot rows (S)

**Goal:** help clinicians review, without ever auto-filling approvals.

Tasks
1. `scripts/suggest_citations.py`: for each row in `curated/condition_exercise.csv` and `curated/safety_contraindications.csv`, query NCBI PubMed E-utilities (read-only, rate-limited, no API key required for low volume) and write **suggestions** to `eval/citation_suggestions.csv` (`row_ref, query, pmid, title, year, publication_type`). Never write into `curated/*.csv`.
2. `tests/test_citations.py`: for every non-empty `citation_pmid` in the curated CSVs, assert it is numeric. A separate live-marked test (skipped offline) checks the PMID resolves. Today this passes vacuously because the columns are empty (F6); keep it so it begins to guard once clinicians fill them.
3. Document in `docs/CONTRIBUTING_CLINICIANS.md` how to use the suggestions file in a review session.

---

## Phase 9: Documentation and housekeeping (S)

1. Update `docs/DATA_SOURCES.md` (new sources, bridge counts, snapshot date), `docs/DATASHEET.md`, `docs/HAIC_PLAN.md` (add this work as a new tracked section), `curated/README.md`, and `CITATION.cff` for any new dataset.
2. Re-run `scripts/audit_coverage.py` and `eval/run_gold.py`; commit the new reports.
3. Update the presentation counts only from real post-run numbers. The deck currently says patient datasets capture "real-world trajectories"; `DATASHEET.md` says MOTU is synthetic/de-identified. Keep wording consistent with the datasheet.
4. Note: `docs/CANDIDATE_SOURCES.md` contains a BioPortal API key in plain text. `BIO_PORTAL_CANDIDATES.md` says it is BioPortal's public anonymous key, but replace it with `YOUR_KEY` anyway so contributors register their own.

---

## Cross-cutting definition of done (every phase)

- [ ] `pytest -q` passes (offline suite); `ruff check .` clean; compatible with Python 3.9 and 3.12 (CI matrix).
- [ ] New live tests added to `tests/test_graph.py` and marked so CI without Neo4j skips them.
- [ ] Gold questions added or updated with count bounds from a **real run**; all existing questions still pass.
- [ ] Every new edge has the full provenance contract and is `unreviewed`.
- [ ] Cypher path and bulk path produce the same counts (parity assertion).
- [ ] Docs updated; numbers in docs come from a dated run, not estimates.

## Human inputs required (collect these up front)

1. Neo4j connection for live tests (`.env`).
2. `BIOPORTAL_API_KEY` for ontology downloads.
3. Policy decision for ICD-10 binding confidence (Phase 1).
4. LOINC code lookups (Phase 2); free LOINC account needed.
5. ICF Core Sets category lists and a redistribution check (Phase 5).
6. San Raffaele download and licence confirmation (Phase 7); optional CMS GEMs files.

## Suggested order and rough sizing

| Phase | Size | Depends on |
|-------|------|-----------|
| 0 Baseline and diagnosis | S | none |
| 1 ICD-10 rows land | M | 0 |
| 2 Outcome to scale and scale IDs, NIHSS | M | 0 |
| 3 Bridge loaded ontologies | L | 0, 1 helpful |
| 4 More ontologies | S each | 3 |
| 5 ICF Core Sets | M | human input |
| 6 Trials to scales and PMIDs | M | 2 |
| 7 San Raffaele | L | 2, human input |
| 8 Citation tooling | S | none |
| 9 Docs and housekeeping | S | all |

Phases 1, 2 and 8 are independent after Phase 0 and can run in parallel branches.

---

## Kickoff prompt (paste this into openwork)

> You are working in the RehabKG repo. Read `RehabKG_implementation_plan.md` in full, then read the files listed in Section 0. Execute the plan phase by phase, starting with Phase 0. Respect the non-negotiable constraints in Section 0: every new clinical edge carries the full provenance contract and is `unreviewed`, both load paths stay in parity, no fuzzy substring matching, and never invent data marked HUMAN INPUT. Commit per task with tests. At the end of each phase, stop at the gate and give me a short summary of what changed, the before/after numbers, and any decisions you need from me. Do not start the next phase until I confirm. If a live Neo4j instance is not available, say so and skip live steps rather than estimating results.
