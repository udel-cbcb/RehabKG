# RehabKG Use Cases

## Overview

RehabKG is positioned as a trusted, provenance-tracked knowledge layer that AI
components and clinicians can query and correct. These use cases are organised
around that role: each one returns provenance (`review_status`, `confidence`,
`method`, `source`) so a consumer can see how much to trust each row.

**Research prototype only:** curated links are candidate associations, not
clinical advice. Most rows are `unreviewed`, and recommendation or safety
edges must not be used for patient care without clinician review. Result sizes
are small because the curated clinical layer is small (see
[PILOT_STROKE_GAIT.md](PILOT_STROKE_GAIT.md)). Run the queries against your own
graph rather than relying on any numbers quoted elsewhere.

**Run all use cases:**
```bash
python use_cases.py
```

| # | Use case | Theme | Needs new data? |
|---|----------|-------|-----------------|
| 1 | Safety-aware exercise lookup | Trust, decision support | No |
| 2 | Explain-this-path | Grounded, auditable answers | No |
| 3 | Review-queue triage | AI proposes, clinician decides | No |
| 4 | Gait concept resolver and link-gap view | Ontology bridging | No |
| 5 | Stroke coverage and gap audit | Evaluation | No |
| 6 | Recommendation/contraindication conflicts | Graph-native safety check | No |
| 7 | Assessment scale selection | Outcome measurement | No |
| 8 | Trial landscape | Research linkage | No |
| 9 | Condition-exercise-muscle map | Education | No |
| 10 | Synthetic measures (sensor-measure starting point) | Digital twin vocabulary | Synthetic seed |
| A | Amputation cohort appendix | Patient/outcome layer demo | MOTU |
| 11-14 | Proposed | See bottom | Yes |

---

## UC1: Safety-aware exercise lookup

**Goal:** For a condition, return candidate exercises together with
precautions and contraindications, so a consumer (a clinician or an AI agent)
never sees a recommendation without its caveats.

```cypher
MATCH (c:Condition)-[r:RECOMMENDS_EXERCISE|PRECAUTION|CONTRAINDICATION]->(e:Exercise)
WHERE toLower(c.name) CONTAINS toLower($condition)
  AND NOT toLower(c.name) CONTAINS 'heat stroke'
RETURN type(r) AS relation, e.name AS exercise, count(DISTINCT c) AS conditions,
       collect(DISTINCT r.review_status) AS review_status,
       collect(DISTINCT r.confidence) AS confidence,
       collect(DISTINCT c.name)[..2] AS example_conditions
ORDER BY CASE relation WHEN 'CONTRAINDICATION' THEN 0 WHEN 'PRECAUTION' THEN 1 ELSE 2 END, e.name
LIMIT 40;
```

**Shows:** safety edges sort first; every row carries review status and
confidence. Results are grouped per exercise because a keyword such as
'stroke' matches dozens of trial-derived Condition nodes (40 in the test graph). **Limit:** the stroke safety layer is 5-6 seed rows.

*Fix note:* the earlier version placed `WHERE c.name = $condition` after an
`OPTIONAL MATCH`, which filtered only the optional match, so exercises for all
conditions were returned.

## UC2: Explain-this-path

**Goal:** Show how the graph connects two concepts, with provenance on every
edge, which is the basis of grounded answers with citations. Also available as
`GET /paths?start_name=...&end_name=...` in the API.

```cypher
MATCH (a {name: $start}), (b {name: $end})
WITH a, b LIMIT 1
MATCH p = shortestPath((a)-[*..4]-(b))
UNWIND relationships(p) AS r
RETURN startNode(r).name AS from_node, type(r) AS relation, endNode(r).name AS to_node,
       r.method AS method, r.match_type AS match_type,
       r.confidence AS confidence, r.review_status AS review_status;
```

**Limit:** ontology edges (for example `IS_A`) may carry no provenance fields,
which is itself informative. Use specific start and end names, since matching
is by name only.

## UC3: Review-queue triage

**Goal:** Support the AI-proposes / clinician-decides loop by showing what is
awaiting review, by rule and confidence.

```cypher
MATCH ()-[r]->()
WHERE type(r) IN ['RECOMMENDS_EXERCISE', 'PRECAUTION', 'CONTRAINDICATION']
RETURN type(r) AS relation, coalesce(r.review_status, 'missing') AS review_status,
       coalesce(r.match_type, 'n/a') AS match_type,
       count(r) AS edges, round(avg(r.confidence), 2) AS avg_confidence
ORDER BY review_status, relation, avg_confidence;
```

**Later:** once a reviewer exists, track approval rate and time-to-review from
`apply_decisions.py` output. Any `missing` status row is a provenance bug.

## UC4: Gait concept resolver

**Goal:** Resolve HPO gait terms to ICF concepts and show where links are
missing. HPO-to-ICF links are only the nine curated explicit code pairs
(`RELATED_TO_ICF`, `confidence=1.0`, `unreviewed`); the pipeline deliberately
does not use name matching. Unlinked terms are returned too, since the gap is
the finding.

```cypher
MATCH (h:HPOConcept)
WHERE toLower(h.name) CONTAINS toLower($term)
OPTIONAL MATCH (h)-[r:RELATED_TO_ICF]->(i:ICFConcept)
OPTIONAL MATCH (a:AssessmentScale)-[:MEASURES]->(i)
RETURN h.code AS hpo_code, h.name AS hpo_term, i.code AS icf_code, i.name AS icf_name,
       r.review_status AS review_status, collect(DISTINCT a.name) AS scales
ORDER BY icf_code IS NULL, hpo_term LIMIT 15;
```

**Finding (test graph):** of 27 HPO terms containing "gait", only *Gait
disturbance* and *Gait ataxia* are linked (both to b770, Gait pattern
functions). Pairs were corrected on 2026-11-17: the earlier set contained
mismatches such as Respiratory insufficiency to d450 Walking, Seizure to b235
Vestibular functions and Gait ataxia to b455 Exercise tolerance. The corrected
pairs are still `unreviewed` and were chosen by the developer, not a clinician.
The broad pairs (Abnormality of the musculature to b730, Seizure to b765) are
the most debatable.

## UC5: Stroke coverage and gap audit

**Goal:** Measure how much of the stroke condition set has any clinical edge.
This is a quality view of the graph itself.

```cypher
MATCH (c:Condition)
WHERE (toLower(c.name) CONTAINS 'stroke' OR toLower(c.name) CONTAINS 'hemipleg'
       OR toLower(c.name) CONTAINS 'hemipares') AND NOT toLower(c.name) CONTAINS 'heat stroke'
OPTIONAL MATCH (c)-[rec:RECOMMENDS_EXERCISE]->()
OPTIONAL MATCH (c)-[saf:PRECAUTION|CONTRAINDICATION]->()
WITH c, count(DISTINCT rec) AS recs, count(DISTINCT saf) AS safety
RETURN CASE WHEN recs = 0 AND safety = 0 THEN 'no clinical edges'
            WHEN safety = 0 THEN 'recommendations only'
            ELSE 'has safety edges' END AS coverage,
       count(c) AS conditions, collect(c.name)[..3] AS examples
ORDER BY conditions DESC;
```

See also `scripts/audit_coverage.py` for the fuller report.

## UC6: Recommendation vs. contraindication conflicts

**Goal:** Find exercises that one condition recommends and another
contraindicates. This is a relationship check that a flat table does not give
you, and the basis for comorbidity warnings.

```cypher
MATCH (c1:Condition)-[r1:RECOMMENDS_EXERCISE]->(e:Exercise)<-[r2:CONTRAINDICATION]-(c2:Condition)
WHERE c1 <> c2
RETURN e.name AS exercise, count(DISTINCT c1) AS recommending_conditions,
       collect(DISTINCT c1.name)[..2] AS recommended_for_examples,
       collect(DISTINCT c2.name)[..2] AS contraindicated_for
ORDER BY recommending_conditions DESC, e.name LIMIT 25;
```

**Finding (test graph):** one conflict, Bodyweight Squat: recommended for
knee osteoarthritis and other conditions, contraindicated for hip fractures.
That is a comorbidity warning, not a true contradiction. With only a few
contraindication rows this can legitimately return nothing. An empty result is not proof of safety.

## UC7: Assessment scale selection

**Goal:** Choose scales for a functional domain, with ICF links and curated
LOINC codes where available.

```cypher
MATCH (a:AssessmentScale) WHERE a.domain = $domain
OPTIONAL MATCH (a)-[:MEASURES]->(i:ICFConcept)
RETURN a.name AS scale, a.domain AS domain, a.scoring_range AS range,
       a.loinc_code AS loinc, collect(i.code) AS icf_codes
ORDER BY a.name;
```

Try `balance`, `gait`, or any domain present in your graph. MCID, ceiling
effects and population fit are not yet modelled.

## UC8: Trial landscape

**Goal:** See recruiting trials that study a condition. This is a name-based
landscape query and is **not** eligibility matching.

```cypher
MATCH (t:ClinicalTrial)-[:STUDIES_CONDITION]->(c:Condition)
WHERE toLower(c.name) CONTAINS toLower($condition)
  AND t.status IN ['RECRUITING', 'NOT_YET_RECRUITING', 'ENROLLING_BY_INVITATION']
RETURN t.nct_id AS nct_id, substring(t.title, 0, 60) AS title,
       t.enrollment AS enrollment, t.start_date AS start_date, c.name AS condition
ORDER BY t.enrollment DESC LIMIT 10;
```

## UC9: Condition-exercise-muscle map

**Goal:** Education: which candidate exercises and muscles relate to a
condition. Merges the former UC4 (shoulder impingement) and UC8 (all
conditions) queries, which were the same traversal.

```cypher
MATCH (c:Condition)-[r:RECOMMENDS_EXERCISE]->(e:Exercise)
WHERE toLower(c.name) CONTAINS toLower($condition)
OPTIONAL MATCH (e)-[:TARGETS_PRIMARY]->(m:Muscle)
RETURN e.name AS exercise, collect(DISTINCT m.name) AS muscles,
       count(DISTINCT c) AS conditions, collect(DISTINCT r.review_status) AS review_status
ORDER BY conditions DESC, e.name LIMIT 25;
```

Muscles are empty for exercises such as walking programs that have no
`TARGETS_PRIMARY` link.

## UC10: Measure context (sensor-measure prototype)

**Goal:** Starting point for the shared-vocabulary role for HAIC sensor and
robot data. It lists the **fully synthetic** observation seed
(`SYNTHETIC-GAIT-001`): gait speed, 6-minute walk, step count and Berg score.

```cypher
MATCH (:Patient {patient_id: $pid})-[:HAS_OBSERVATION]->(o:Observation)
RETURN o.feature, o.value, o.unit, o.observed_at, o.source
ORDER BY o.feature, o.observed_at;
```

**Limit:** Observation-to-ICF links are deliberately absent. The bulk import
deletes them until they are restored and provenance-validated, and the gold
question `observation-maps-to-icf` asserts they are absent. So today this
returns raw measures only. **Next step:** add a `MeasureDefinition` node (unit,
expected range, ICF code, LOINC) and an API endpoint; see
[HAIC_IMPROVEMENTS.md](HAIC_IMPROVEMENTS.md) item 3.

## Appendix: amputation cohort (MOTU)

The former "Outcome Prediction" and "Cohort Analysis" use cases are now one
descriptive query, `appendix_amputation_cohort`, comparing admission and
discharge Barthel scores by amputation cause. MOTU is a single-center
synthetic/de-identified **amputation** cohort. It is not a stroke cohort and
supports no prediction or expectation-setting claims; its role is to show the
Patient/Session/Outcome layer. `demo_full_journey` shows one patient's stays.

Removed: the equipment-usage use case, which was a generic count query with no
rehabilitation or HAIC link.

---

## Proposed next use cases

These need new data or code; none is implemented yet.

11. **Sensor-measure resolver endpoint**: `MeasureDefinition` nodes plus an API
    call returning ICF function, related scales, MCID and applicable
    precautions for a (measure, value) pair.
12. **Parkinson's freezing-of-gait slice**: cueing, balance and falls, reusing
    the stroke-gait template.
13. **Grounded question answering**: an LLM answers only from returned edges,
    cites them, and refuses when nothing is approved. Evaluate refusal and
    citation accuracy against the gold set.
14. **Teaching subgraph**: packaged ICF pathway views for students.

## Running the use cases

1. **Neo4j Browser**: http://localhost:7474
2. **Python**: `python use_cases.py`
3. **API**: `/conditions/{ref}/recommendations`, `/paths`
4. **Gold set**: `python eval/run_gold.py --category usecase` checks that the
   data each use case depends on exists.
