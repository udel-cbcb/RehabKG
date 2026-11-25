# RehabKG

### A trusted rehabilitation knowledge layer for HAIC

**Rehabilitation Knowledge Graph · HAIC project update · November 2026**

Research integration platform · not clinical decision support

> **Presenter framing:** RehabKG is research infrastructure, not a clinical product. Graph node and relationship counts come from the graph rebuilt on 2026-11-17; evaluation figures come from `eval/snapshot_report_2026-11-17.md`. The keyword matcher changed on 2026-11-06; on 2026-11-17 the graph was rebuilt from a fresh bulk export and the gold set (40/40), live-graph tests, browser E2E, bulk parity test and use cases were rerun against it.

**Speaker notes:** One sentence pitch: RehabKG is the grounded, provenance-tracked graph that HAIC's AI teammates and digital twins can query and that clinicians can correct. Everything in this deck matches the repository as of mid-November 2026.

---

## Three asks for today

### What would move the project forward fastest

::: Clinician reviewer | Review the stroke-gait packet: 1 recommendation and 4 precautions. Decisions go in an auditable CSV; no Git needed.
::: HAIC data partner | A robotics or wearables team whose gait measures (gait speed, 6MWT, step counts) we can map to ICF concepts.
::: Licensing contact | Rulings on ICF (CC BY-ND), LOINC notice, ICF Core Set lists, and other sources before anything is shared beyond the lab.

> Candidate reviewer sources: UD Physical Therapy · Shirley Ryan AbilityLab · VA rehabilitation partners

**Speaker notes:** Lead with the asks so the discussion at the end has a target. Every one of these is blocking a concrete next step: approval of any edge, the digital-twin link, and sharing the graph. Nothing in the review packet is pre-filled.

---

## Why RehabKG fits HAIC

### HAIC: AI as an adaptive teammate, grounded in knowledge and evidence

**CONDITION**
→
**FUNCTION (ICF)**
→
**INTERVENTION**
→
**MEASURED OUTCOME**

- Rehabilitation evidence is split across ontologies, trials, exercise catalogs, and cohort data.
- HAIC's vision calls for integrating data "using grounded knowledge sources and evidence".
- RehabKG supplies that grounding: typed links that carry source, confidence, and review status.
- Proposed role: the knowledge layer that HAIC models and digital twins query, and clinicians correct.

**Speaker notes:** The quoted phrase is from HAIC's About page. Stroke is named as a HAIC focus area, which is why the pilot is stroke gait. The positioning is a proposal for discussion, not an agreed HAIC role.

---

## How the system fits together

### Sources → provenance-stamped graph → research access

>> SOURCES | ClinicalTrials.gov · Free Exercise DB · MOTU demo cohort · ICD-10-CM · 7 focused ontologies
>> ETL + PROVENANCE | Cypher and bulk loaders (parity-tested) · every clinical edge gets method, source, confidence, review status
>> CURATED LAYER | Git-versioned CSVs for recommendations, precautions, and contraindications · clinician decisions applied back
>> REHABKG | Neo4j 5.26 · read-only FastAPI service · Streamlit dashboard
>> RESEARCH USE | Candidate pathways · trial discovery · outcome queries · clinician review

**Speaker notes:** Main code paths: `rehabkg.py` (Cypher pipeline), `build_csvs.py` + `import_bulk.py` (bulk path), `bridges.py` (curated and cross-ontology links), `provenance.py` (edge contract), `api/app.py`, `dashboard/app.py`. `tests/test_bulk_parity.py` checks that the two loading paths produce the same graph.

---

## What's in the graph

### Rebuilt graph of 2026-11-17 · 153,069 nodes · 147,691 relationships

| Layer | Contents | Nodes |
|---|---|---:|
| Vocabulary | ICD-10-CM 92,694 · HPO 32,772 · Uberon 10,000 (subset) · Mondo 5,000 · ICF 1,509 · PAIN 623 · REHABO 310 · EXMO 220 | 143,128 |
| Clinical and dataset | 1,387 trials · 1,320 conditions · 949 exercises · 1,006 MOTU patients · 4,024 outcomes on 40 scales | 9,915 |
| Schema | NodeType / RelType bookkeeping | 26 |

> 93.5% of nodes are vocabulary. The clinical layer is the part that needs to grow.

**Speaker notes:** Composition comes from `scripts/graph_composition.py`; source file hashes and counts are in `eval/public_ontology_refresh_manifest.json`. COPPER, KHMO, CBHA and other flagged ontology families were excluded in the focused refresh pending licence review. ICD-10 codes link to conditions through Mondo. Node counts are unchanged from the 2026-11-05 snapshot and are not affected by the Nov 6 matcher change. The 147,691 relationships (107,436 in the Nov 5 snapshot) include 117,005 `SUBCLASS_OF` ontology hierarchy edges that the bulk build loads; the other 30,686 are clinical, dataset and bridge links. Counts from `scripts/graph_composition.py` on the rebuilt graph.

---

## What is real and what is synthetic

### Every layer is labeled so nobody over-reads the data

| Layer | Status | Caveat |
|---|---|---|
| Ontology concepts | Real, released versions | Licence review open for some |
| Clinical trials | Real ClinicalTrials.gov records | Keyword-linked to conditions |
| MOTU patients and outcomes | De-identified single-center demo cohort | Amputation cohort, not stroke |
| Observation seed | Fully synthetic, `source=synthetic_demo` | 1 patient, 6 observations |
| Curated recommendations and safety | 35 + 5 seed rows | All unreviewed |

**Speaker notes:** Source: `docs/PILOT_STROKE_GAIT.md` and `docs/DATASHEET.md`. Of the 35 recommendation rows, 29 bind through exact ICD-10 codes and 6 use keyword groups; all 5 safety rows use keyword groups. Rows fan out to many graph edges because one row can match many condition nodes. The synthetic observations currently have no ICF links.

---

## Trust layer: provenance on every clinical edge

### One contract, implemented once in `provenance.py`

::: method | `curated` or `rule_based` · `model_generated` reserved
::: confidence | Rule quality, not probability
::: source | File or `pipeline:rule` that made the edge
::: review_status | `unreviewed` · `approved` · `rejected`

| Edge origin | Confidence | Example |
|---|---|---|
| Exact ICD-10 binding | 0.7 | Condition → recommended exercise via ICD-10 code |
| Curated keyword group | 0.6 | `stroke` (excluding `heat stroke`) → Walking Program |
| Loose name-match bridges | ≤ 0.4 | Trial → ICF keyword links, flagged for review |

**Speaker notes:** Keyword matching is whole-word with an optional `exclude_keywords` column (introduced Nov 6). Approval requires a citation, enforced in `curated/apply_decisions.py`. Consumers see provenance on every edge; filtering on `review_status=approved` is opt-in. `model_generated` exists in the contract but no code produces it yet.

---

## Use case: stroke candidate review

### Question → traversal → result → provenance → limitation

> Which candidate exercises and safety links exist for stroke, and can I audit them?

```cypher
MATCH (c:Condition {name:'Stroke'})-[r:RECOMMENDS_EXERCISE]->(e:Exercise)
OPTIONAL MATCH (c)-[s:PRECAUTION|CONTRAINDICATION]->(e2:Exercise)
RETURN e.name, r.method, r.confidence, r.review_status, e2.name, type(s)
```

| Link | Target | Provenance |
|---|---|---|
| Recommendation | Walking Program (Progressive) | curated · 0.6 · keyword_group · unreviewed |
| Precautions (4) | Single-Leg Balance · Walking, Treadmill · Narrow Stance Squats · Balance Board | curated · 0.6 · keyword_group · unreviewed |

> Limit: a candidate, not guidance. No efficacy or patient-specific safety claim; 0 approved links.

**Speaker notes:** Rationale on the recommendation row: "progressive gait practice (motor relearning)". The 0.6 values were confirmed on the graph rebuilt on 2026-11-17 (keyword rows 0.6, ICD-10 rows 0.7, all unreviewed). Note that the graph holds one edge per matching Condition node, so the 5 safety rows and 1 stroke recommendation row expand to 210 precaution and 217 keyword-recommendation edges across all conditions. The same traversal is available through the API's `/conditions/{ref}/recommendations`, which always attaches safety edges.

---

## Use cases

### Ten runnable queries, all returning provenance

| Use case | What it shows |
|---|---|
| Safety-aware lookup | Recommendations and precautions returned together, with review status |
| Explain-this-path | Shortest path between two concepts, provenance on every edge |
| Review-queue triage | Unreviewed edges by rule and confidence |
| Gait concept resolver | HPO gait terms → ICF; shows the gap (2 of 27 linked) |
| Coverage audit | Which stroke conditions have no clinical edge |
| Synthetic measures | Gait speed and 6MWT observations; ICF links deliberately absent until validated |

> Also: recommendation/contraindication conflicts, scale selection, trial landscape, condition-exercise-muscle map. MOTU amputation cohort kept as a labeled descriptive appendix.

**Speaker notes:** Full list with Cypher and limits: `docs/USE_CASES.md`; run `python use_cases.py`. Use cases were reworked in November 2026 to match the trusted-knowledge-layer positioning: the old outcome-prediction and equipment queries were dropped or relabeled, and the exercise lookup bug (condition filter applied to the optional match) was fixed. Verified on the graph rebuilt from a fresh bulk export on 2026-11-17: all queries execute with no errors and the gold set passes 40/40. Findings: only 2 of 27 HPO gait terms have an ICF link (9 curated pairs total; mismatched pairs were corrected on 2026-11-17 and remain unreviewed); Observation-to-ICF links are deliberately removed by the bulk import; the one recommendation/contraindication conflict (Bodyweight Squat) is a comorbidity warning, not a contradiction. The synthetic measures are the starting point for the sensor-measure resolver in the roadmap.

---

## Clinician review loop

### No link counts as approved without a citation

**CANDIDATE EDGE**
→
**DASHBOARD REVIEW PAGE**
→
**DECISION CSV + CITATION**
→
**APPLIED TO GRAPH**

- The dashboard's "Evidence & Review" page lists unreviewed edges by type and exports a decision template.
- `curated/apply_decisions.py` validates decisions, refuses approvals without a citation, and updates the graph.
- Clinicians never touch Git or Neo4j; the curated CSVs in Git remain the system of record.
- Pilot packet ready: `deliverables/stroke_gait_review_packet.csv` (1 recommendation + 4 precautions).

> Today: 0 approved relationships · reviewer not yet identified

**Speaker notes:** Contributor guide for clinicians: `docs/CONTRIBUTING_CLINICIANS.md`. The loop was exercised end to end in a live smoke test (one decision flipped 41 edges to approved, then was restored), so the machinery works; what is missing is a reviewer.

---

## Access: API and dashboard

### Read-only by design

| Endpoint | Returns |
|---|---|
| `/health` · `/stats` | Service check · graph size and provenance coverage |
| `/conditions?q=` | Condition search |
| `/conditions/{ref}/recommendations` | Candidate exercises with safety edges always attached |
| `/paths` | Bounded graph traversal with provenance on every hop |

- Dashboard (Streamlit): Overview · Exercises · Clinical Trials · Patients · Ontologies · Knowledge Discovery · Evidence & Review.
- No write endpoints; natural-language querying is a later, gated step.

**Speaker notes:** API code: `api/app.py`; dependencies in `requirements-api.txt`. The API binds to localhost by default. The dashboard screenshot in `deliverables/` predates the focused refresh and should be retaken before reuse.

---

## Evaluation and reproducibility

### Tests are tied to a dated graph

::: CI offline tests | Pass on every push · Python 3.9 and 3.12
::: Gold questions | 40/40 · rebuilt graph, Nov 17
::: Live-graph tests | 112 passed · rebuilt graph, Nov 17
::: Dashboard E2E | 44 passed · rebuilt graph, Nov 17

- Cypher and bulk loading paths produce matching graphs (`tests/test_bulk_parity.py`, passed Nov 17).
- Every source file is pinned by SHA-256 in the refresh manifest.

> All suites rerun Nov 17 on a graph rebuilt from a fresh bulk export. Gold set grew from 35 to 40 questions (5 use-case checks).

**Speaker notes:** Report: `eval/snapshot_report_2026-11-17.md` (supersedes `eval/snapshot_report_2026-11-05.md`). Bulk parity passed on the second run, after the baseline's gold total was raised from 35 to 40. The gold questions are graph health checks (existence, bounds, provenance coverage); they show the graph is built correctly, not that it is clinically useful. Live-graph, E2E, and parity tests run on demand, not in CI. ICF Core Set recall cannot be measured until licensed category lists are supplied.

---

## Source governance

### Technical availability is not redistribution permission

| Source | Status |
|---|---|
| REHABO · Mondo · PAIN · EXMO · HPO · Free Exercise DB | Open licences (CC0 / CC BY / HPO terms / Unlicense) · attribution required |
| ICF | CC BY-ND 3.0 IGO · whether bridging counts as a derivative is unresolved |
| LOINC fields on scales | Allowed only with the LOINC notice, which is not yet shown |
| MOTU | CC BY 4.0 · confirm exact release and de-identification scope |
| COPPER · KHMO · CBHA · other flagged | Excluded from the graph pending terms |

> Public hosting: not cleared. `export_csv.py --public-candidate` is a screening aid, not approval.

**Speaker notes:** Full audit: `docs/notes/data_hosting_license_audit.md`; proposed allowlist: `docs/notes/public_hosting_allowlist.md`. This is operational screening, not legal advice.

---

## Honest gaps

### What the project does not do yet

::: No approvals | 0 reviewed edges; every curated link is a candidate
::: Thin clinical layer | 35 recommendation and 5 safety rows; no stroke cohort
::: No AI component | `model_generated` edges, link prediction, and GraphRAG not built
::: Not linked to HAIC data | No sensor, robot, or digital-twin measures mapped
::: Stroke only | No Parkinson's slice, though HAIC names it as a focus
::: Sharing blocked | Licensing review open; Python 3.9 floor; manual source downloads

**Speaker notes:** Being explicit here is deliberate: these gaps define the roadmap on the next two slides. Details and acceptance criteria for each fix: `docs/HAIC_IMPROVEMENTS.md`.

---

## Proposal: AI proposes, clinicians decide

### The human-AI cooperation result HAIC is looking for

**MODEL PROPOSES**
→
**TAGGED model_generated**
→
**CLINICIAN DECIDES**
→
**METRICS + FEEDBACK**

- Start with one narrow edge type, for example stroke condition → exercise.
- Proposers: an LLM limited to graph-retrieved text with a required citation, and a link-prediction baseline.
- Candidates stay `unreviewed` and out of any approved-only view until a clinician decides.
- Measure: acceptance rate by confidence band, agreement between two reviewers, time per decision, and calibration.
- Rejections become negative examples for the next round.

**Speaker notes:** Most of the machinery exists: the provenance contract reserves `model_generated`, and the review page and decision CSV already work. The new pieces are the proposer and decision logging with reasons. Target: at least 100 reviewed candidates, with metrics written up in `eval/`.

---

## Roadmap

### Ordered by what unblocks what · proposed, not committed

| When | Work |
|---|---|
| Next 2–4 weeks | Find a reviewer · send licensing questions · rerun suites after the matcher change · move off the Python 3.9 floor |
| 1–2 months | AI-proposes / clinician-decides loop · cited, guideline-seeded stroke-gait rows with dose and MCID values |
| 2–4 months | Map one HAIC sensor or robot gait stream to ICF concepts · evaluation against baselines · Parkinson's slice |
| Later | Grounded question answering with citations · teaching notebooks for HAIC students · one-command Docker deployment |

> Not planned: more ontologies, raw sensor time series in Neo4j, or any clinical-readiness claim.

**Speaker notes:** Full plan with acceptance criteria: `docs/HAIC_IMPROVEMENTS.md`, building on `docs/HAIC_PLAN.md` and `docs/PROJECT_RECOMMENDATIONS.md`. Any work with real patient data needs IRB review and a data use agreement first.

---

## Discussion

### Who can help with the three asks?

::: Clinician reviewer | Stroke-gait packet: 1 recommendation + 4 precautions
::: HAIC data partner | Gait measures to map onto ICF and outcome concepts
::: Licensing contact | ICF, LOINC, Core Sets, and remaining source terms

**Questions · Feedback · Collaboration**

**Speaker notes:** Close by restating the asks. If a reviewer volunteers, the packet and the clinician guide can be sent the same day.

## Presenter source notes

- Graph snapshot: `eval/snapshot_report_2026-11-17.md` (Neo4j 5.26.29, `bolt://localhost:7688`; earlier snapshot `eval/snapshot_report_2026-11-05.md`); manifest `eval/public_ontology_refresh_manifest.json`.
- Matcher change: commit `d3677d7` (2026-11-06) introduced whole-word keyword matching, `exclude_keywords`, and `KEYWORD_GROUP_CONFIDENCE=0.6`. The snapshot's curated-edge counts and test results predate it; the gold, live-graph, parity and use-case runs on 2026-11-17 used a graph rebuilt after it.
- Curated rows: `curated/condition_exercise.csv` (35 rows: 29 `icd10`, 6 `keyword_group`), `curated/safety_contraindications.csv` (5 rows: 4 stroke precautions, 1 fracture contraindication); all `unreviewed`.
- Confidence constants: `bridges.py` `KEYWORD_GROUP_CONFIDENCE=0.6`; `provenance.py` `ICD10_BIND_CONFIDENCE=0.7`.
- CI: `.github/workflows/offline-tests.yml`, Python 3.9 and 3.12.
- Plans: `docs/HAIC_IMPROVEMENTS.md`, `docs/HAIC_PLAN.md`, `docs/PROJECT_RECOMMENDATIONS.md`; pilot `docs/PILOT_STROKE_GAIT.md`; governance `docs/DATASHEET.md`, `docs/notes/data_hosting_license_audit.md`.
- HAIC quotes: haicinstitute.org home and About pages (read November 2026).
- Rebuild: `python3 deliverables/build_slides.py`.
