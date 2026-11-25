# RehabKG: improvements for HAIC alignment

**Status:** Recommendations · **Written:** 2026-11-16 · **Supersedes:** nothing.
This document builds on [HAIC_PLAN.md](HAIC_PLAN.md) and
[PROJECT_RECOMMENDATIONS.md](PROJECT_RECOMMENDATIONS.md).

## Why this document exists

The NSF AI Institute for Human-AI Cooperation (HAIC) describes its goal as making AI
"an adaptive teammate for human-centered personalized decision-making". It wants to
integrate data across time scales "using grounded knowledge sources and evidence", with
stroke and Parkinson's disease named as focus areas. RehabKG fits that topic well, and its
provenance, review, and evaluation work is solid. As of the 2026-11-05 snapshot, though,
RehabKG is a curated knowledge graph that has no AI component:

- 93.5% of nodes are vocabulary or ontology terms. The clinical layer has 35
  recommendation rows and 5 safety rows.
- **0 relationships are approved**, and no clinician reviewer has been named yet.
- GraphRAG, link prediction, and model-generated edges are all deferred.
- There is no link to HAIC's sensor, robotics, or digital-twin work.
- Parkinson's disease is not covered.

**Proposed positioning:** *RehabKG is HAIC's trusted knowledge layer, the
provenance-tracked graph that AI teammates and digital twins query and that clinicians
correct.* The recommendations below are ordered to make that claim true with the least
new machinery.

---

## Priority summary

| # | Recommendation | Effort | HAIC theme served | Depends on |
|---|---|---|---|---|
| 1 | Complete the clinician review of the stroke-gait packet | S (human-bound) | Research embedded in clinical care | A named reviewer |
| 2 | Add an AI-proposes / clinician-decides loop and measure it | M | Human-AI cooperation, trustworthy AI | 1 (reviewer) |
| 3 | Map one HAIC sensor or robot data stream to graph concepts | M | Digital twins, multimodal integration | A HAIC data partner |
| 4 | Make the clinical layer for stroke deeper, not wider | M | Neurologic rehab, decision support | 1 |
| 5 | Add a Parkinson's disease slice | M | Neurologic rehab | 4 (reuse its template) |
| 6 | Grounded question answering through the API, with citations | M | Clinical decision support, trustworthy AI | 2, 4 |
| 7 | Resolve the licensing items that block sharing the graph | S–M (legal-bound) | Partnerships, translational research | none |
| 8 | Package the project as shared infrastructure | M | Team science, workforce | none |
| 9 | Run the evaluation as research, not only as tests | S–M | Scientific discovery | 2 |
| 10 | Build education and onboarding materials | S | Education and workforce, HBCU partners | 8 |

S = days, M = 1–3 weeks of focused work.

---

## 1. Complete the clinician review of the stroke-gait packet

**Gap.** `deliverables/stroke_gait_review_packet.csv` (1 recommendation row and
4 precaution rows) is ready, but no reviewer has been found. Until rows are approved,
every claim that the graph is "trustworthy" is hypothetical.

**Do:**
- Ask HAIC clinical partners for one reviewer, plus a second reviewer for safety rows.
  Candidates: UD Physical Therapy, Shirley Ryan AbilityLab, and VA rehabilitation staff.
- Expand the packet to every stroke-related curated row, not just the 5 seed rows.
- Apply decisions with `curated/apply_decisions.py --dry-run`, then `--update-graph`.
  Rerun the gold questions and the graph tests.

**Done when:** at least one reviewer has submitted decisions, every approval carries a
citation, the approved-edge count is above 0, and a short summary is added to
`PROJECT_RECOMMENDATIONS.md`.

## 2. Add an AI-proposes / clinician-decides loop and measure it

**Gap.** This is the central missing piece for HAIC. The provenance contract already
reserves `method='model_generated'`, but nothing produces such edges.

**Do:**
- Write `propose/` (or `scripts/propose_edges.py`). It generates candidate edges for
  one narrow relationship type, for example stroke Condition → Exercise or HPO → ICF.
  Use one or both of these sources:
  - an LLM that sees only text retrieved from the graph and must return a cited rationale;
  - a simple link-prediction baseline (node embeddings over the current graph).
- Write candidates as `method=model_generated`, `review_status=unreviewed`,
  `confidence=<model score>`, and a new `model_id` / `prompt_version` property.
- Show these candidates on the existing dashboard "Evidence & Review" page, kept
  separate from curated rows.
- Log every decision (accept, reject, edit) with reviewer, time, and reason.
- Make sure consumers that filter on `review_status=approved` never see
  unreviewed model output. Add a live-graph test for this.

**Measure:** reviewer acceptance rate by model and confidence band; agreement between
two reviewers (Cohen's κ); time per decision; and how often rejected candidates had
high model confidence (calibration).

**Done when:** at least 100 model candidates have been reviewed, the metrics above are
reported in `eval/`, and rejected rows feed back as negative examples for the next round.
This becomes the project's central HAIC result: measured human-AI cooperation on
clinical knowledge.

## 3. Map one HAIC sensor or robot data stream to graph concepts

**Gap.** HAIC's work centers on wearables, rehabilitation robotics, and digital twins.
RehabKG deliberately leaves out raw sensor data, and that decision is correct. But it
currently provides no meaning for the measures derived from that data.

**Do:**
- Agree with one HAIC data team on a small set of measures they derive from sensors,
  for example gait speed, cadence, step asymmetry, 6-minute walk distance, or
  robot-assisted session dose.
- Add a `MeasureDefinition` node type. Each measure gets its unit, an expected range,
  a `MAPS_TO_ICF` link (`d450`, `b770`, …), and, where licensing allows, a LOINC code.
- Extend the `Observation` layer so that each observation can refer to the
  `MeasureDefinition` it reports. Only summary values go into the graph.
- Provide one API endpoint that answers: given a measure and a value, which ICF
  function it informs, which assessment scales are related, and which curated
  precautions apply.

**Done when:** a HAIC digital-twin or robotics prototype can resolve its gait measures
through the API. This makes the graph's role as "shared vocabulary for the digital twin"
something people can demonstrate.

## 4. Make the clinical layer for stroke deeper, not wider

**Gap.** Six safety rows and one stroke recommendation do not make a pilot that is
useful for decision support. Adding more ontologies will not help: the vocabulary layer
is already 93.5% of the graph.

**Do:**
- Seed stroke-gait rows from guideline sources, each with a citation and evidence level.
  An example source is the AHA/ASA adult stroke rehabilitation guideline, if its terms
  allow this use.
- Add dose properties (frequency, intensity, duration) and MCID values for the pilot
  scales: gait speed, 6MWT, Berg, and the 10-metre walk test. These are deferred
  items in `HAIC_PLAN.md` item 10, and they are what a clinician needs.
- Add the stroke ICF Core Set once its redistribution terms are confirmed
  (`curated/icf_core_sets.csv` is currently header-only).
- Find, or acknowledge the lack of, a stroke patient cohort. MOTU covers amputation
  patients and does not test a stroke pilot.

**Done when:** at least 30 cited stroke-gait rows exist, at least half of them have been
reviewed, and the gold question set includes clinically phrased questions written with
the reviewer.

## 5. Add a Parkinson's disease slice

**Gap.** HAIC names Parkinson's disease next to stroke, and RehabKG has no Parkinson's
pilot.

**Do:** reuse the stroke-gait template: a scope document, curated rows, a review packet,
and gold questions. Gait and freezing of gait, balance, falls, and cueing are natural
overlaps with the stroke work. Check that the needed Mondo, HPO, and ICF terms are
already loaded before adding any source.

**Done when:** `docs/PILOT_PARKINSONS_GAIT.md` exists with the same "what is real vs
synthetic" table and a passing gold-question category.

## 6. Grounded question answering through the API, with citations

**Gap.** "Defer GraphRAG" was the right call while the graph had no approved content.
After items 2 and 4, a narrowly scoped version becomes defensible.

**Do:**
- Answer questions only through fixed, parameterized Cypher templates. Do not let a
  model write free-form Cypher.
- Every answer returns the edges it relied on, each with its `review_status`, source,
  and citation.
- Default to approved edges only, and label any unreviewed content explicitly.
- Evaluate against the gold set and the clinician-written questions. Report the rate of
  unsupported statements, not only accuracy.

**Done when:** a demo answers the pilot questions with complete citations and the
faithfulness metric is reported.

## 7. Resolve the licensing items that block sharing the graph

**Gap.** See `docs/notes/data_hosting_license_audit.md`. These items block sharing the
graph with HAIC partners or hosting it publicly:
- **ICF (CC BY-ND 3.0 IGO).** It is unclear whether bridging and extending ICF counts as
  a "derivative". Get a written determination.
- **LOINC.** The required notice is not shown in the dashboard or the API. Add it, or
  remove LOINC fields from shared exports.
- **RMD scale metadata, PMR, MELLO-D, OPE, PHY, ONTOLOCO, ACVD.** Their terms are
  unverified.
- **MOTU.** Confirm the exact CC BY 4.0 release and the scope of its de-identification.

**Do:** ask the UD technology transfer office or HAIC administration for a source-by-source
ruling. Record the outcomes in `public_hosting_allowlist.md`, and make the
`--public-candidate` export the default for anything that leaves the lab.

## 8. Package the project as shared infrastructure

**Gap.** For an institute-wide resource, the project's current setup gets in the way of
other contributors.

**Do:**
- Move the top-level scripts into a `rehabkg/` package with a `pyproject.toml` and
  console entry points (`rehabkg build`, `rehabkg status`, `rehabkg serve`).
- Upgrade from Python 3.9, which reached end of life in October 2025, to 3.11 or 3.12.
  Re-pin `requirements-api.txt`. FastAPI currently fails to import on Apple Silicon
  because of an x86_64 `pydantic_core` wheel.
- Publish versioned graph snapshots (a Neo4j dump or the bulk CSVs plus the manifest)
  so that collaborators do not need to run the source-download steps.
- Provide a single `docker compose up` that starts Neo4j, the API, and the dashboard,
  loaded with a public-candidate snapshot.
- Clean up `deliverables/`: keep one deck plus its Markdown source and tag releases.
  Remove the tracked `__pycache__` and `.DS_Store` files.
- Add a `CONTRIBUTING.md` for developers. `CONTRIBUTING_CLINICIANS.md` already covers
  clinicians.
- Add live-graph tests to CI using a small fixture graph, so that coverage is not
  limited to offline tests.

**Done when:** a new contributor can go from clone to a running API in one command and
under 15 minutes.

## 9. Run the evaluation as research, not only as tests

**Gap.** The gold questions check graph health (counts, existence, provenance). They
show that the graph is built correctly. They do not show that it is clinically useful.

**Do:**
- Keep the current suite as regression tests.
- Add a separate set of clinically meaningful tasks, built from the questions clinicians
  actually ask and with answers judged by the reviewer.
- Compare against simple baselines: keyword search over the same sources, and an LLM
  without the graph. This shows whether the graph adds value.
- Report the edge-audit precision from `scripts/sample_edges_for_audit.py` for each
  rule-based bridge type. The HPO→ICF bridge at confidence 0.4 is a known weak spot.

**Done when:** a short evaluation write-up exists that could serve as a workshop paper,
for example for AMIA or a KG and health workshop.

## 10. Build education and onboarding materials

**Gap.** Education and workforce development is one of HAIC's stated pillars, including
partnerships with HBCUs. RehabKG is a good teaching vehicle that has not been packaged
for teaching.

**Do:** build a small "teaching subgraph" (deferred in `HAIC_PLAN.md`) that uses only
public-candidate sources. Add 3–4 notebooks covering ontologies and ICF basics, Cypher
over clinical data, provenance and review, and a model-proposes / human-decides exercise
based on item 2. These could be offered to HAIC summer research students.

---

## Suggested sequencing

| Window | Focus |
|---|---|
| Next 2–4 weeks | Item 1 (find a reviewer), item 7 (send the licensing questions), and the Python and packaging parts of item 8. These steps mostly mean waiting on other people, so start them first. |
| 1–2 months | Items 2 and 4 together: the model proposes candidates, and the reviewer judges both the model's candidates and the guideline-seeded rows in the same sessions. |
| 2–4 months | Item 3 with a HAIC data partner, item 9 (evaluation write-up), and item 5 (Parkinson's). |
| Later | Item 6 (grounded question answering) and item 10 (teaching materials). |

## What not to do

- Do not add more ontologies or vocabulary nodes. Graph size is not the bottleneck.
- Do not ingest raw sensor time series into Neo4j. Store derived measures and links to
  where the raw data lives.
- Do not present unreviewed or model-generated edges as recommendations, in demos or in
  papers. Keep the boundaries described in `DATASHEET.md`.
- Do not run any pilot against real patient data without IRB review and a data use
  agreement.
