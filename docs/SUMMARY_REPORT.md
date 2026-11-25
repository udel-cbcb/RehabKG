# RehabKG Summary Report

**Date**: 2026-09-10

> **Current graph (rebuilt 2026-11-17, `bolt://localhost:7688`)**: the bulk
> pipeline produced **153,069 nodes** and **147,691 relationships** (117,005 are
> `SUBCLASS_OF` ontology hierarchy edges; the 2026-11-05 deterministic focused
> ontology refresh had **107,436 relationships** without them). Counts below
> are from that focused refresh and are unchanged on the rebuilt graph unless
> stated. See `eval/snapshot_report_2026-11-17.md`.
>
> The focused refresh: It retains the 1,387 trials, 1,320 conditions, 40 scales,
> 32,772 HPO nodes, 5,000 Mondo nodes, 10,000 Uberon nodes, 1,509 ICF concepts,
> 220 EXMO concepts, 623 PAIN concepts, and 310 REHABO source nodes (63 labeled
> `REHABOConcept`). Current focused bridges include 14 `MAPS_TO_UBERON` and
> 776 `TARGETS_ANATOMY`; the graph has 92,694 `ICD10Code` nodes. COPPER, KHMO,
> CBHA and its activities, and other flagged
> ontology families are excluded from this snapshot. HPO has nine explicit
> `RELATED_TO_ICF` edges, each marked curated and unreviewed. Clinical/dataset
> data were preserved. This is a local graph snapshot, not public-hosting
> clearance; source hashes are in `eval/public_ontology_refresh_manifest.json`.
> The synthetic observation nodes are present, but their former Observation→ICF
> edges were not restored (current count: 0); do not infer those mappings.

> **Rebuild status:** the default Cypher and bulk ontology builders target the
> focused source selection and default bridge policy. The focused refresh now
> sorts the Uberon/Mondo subsets before slicing, and two consecutive live runs
> produced identical graphs (153,069 nodes, 107,436 relationships). A full
> generated-CSV `neo4j-admin` reload now matches that snapshot on all
> node/label/source counts, the bridge/clinical relationship contract, and gold
> **35/35** (`tests/test_bulk_parity.py`, baseline
> `eval/bulk_parity_baseline.json`). Validation on 2026-11-05: offline **270
> passed, 2 skipped**; graph **112 passed**; gold **35/35**; dashboard E2E
> **44/44** (`eval/snapshot_report_2026-11-05.md`).
>
> **Update (2026-11-17)**: graph rebuilt from a fresh bulk export. Offline **296
> passed, 2 skipped**; graph **112 passed**; gold **40/40** (5 use-case
> checks added); dashboard E2E **44/44**; bulk parity **passed** (baseline gold
> total raised to 40). Report: `eval/snapshot_report_2026-11-17.md`.
>
> **Update (2026-11-06)**: curated recommendation/safety `keyword_group`
> rows now use whole-word matching with an optional `exclude_keywords`
> column (stroke rows exclude `heat stroke`) and explicit plural variants
> (`fractures`). Keyword-group edges are stamped at `confidence=0.6` with
> `curation_basis=keyword_group`; the 1,320-condition snapshot keeps the
> keyword subset at 165 recommendation and 144 safety edges. Composition
> reporting is available via `scripts/graph_composition.py`:
> **143,128 vocabulary / 9,915 dataset / 26 schema** nodes.
>
> **Update (2026-10-22)**: Condition→Exercise recommendations now load from
> a single curated file (`curated/condition_exercise.csv`, all rows currently
> `status=unreviewed`); ICF keyword bridges use whole-word matching with
> reviewer-corrected codes, so `MAPS_TO_ICF` edge counts will shift slightly
> on the next rebuild. Offline suite at that time: **107/107**.
>
> **Update (2026-10-17)**: The tables below describe the 2026-09-10 reference
> build. An intermediate 2026-10-17 bulk-imported graph was larger after
> BioPortal shortlist additions, the API-expanded ClinicalTrials set, full HPO
> parity, and the bulk/Cypher bridge unification: **173,161 nodes**,
> **170,491 relationships**, 1,387 trials, 1,320 conditions, 40 assessment
> scales, 32,772 HPO concepts, 5,475 `MAPS_TO_ICF` edges (reference: 4,430),
> 2,302 `TARGETS_ANATOMY` edges (reference: 652). Validation as of 2026-10-17:
> `test_graph` 47/47, offline suite 87/87, dashboard e2e 44/44. The current
> focused graph is described in the 2026-11-05 snapshot block above.

> **Historical report:** everything below this point describes the 2026-09-10
> reference build unless noted; use the snapshot block above for current counts.

## Executive Summary (2026-09-10 reference build)

The Rehabilitation Knowledge Graph (RehabKG) has been built and enriched with clinical data and rehabilitation ontologies. The 2026-09-10 reference build contains **109,195 nodes** and **26,258 relationships**, with **12% clinical data** and **88% ontologies** (including ICD-10, Mondo, Uberon).

## Key Achievements (2026-09-10 reference build)

### 1. Clinical Data Integration

| Dataset | Nodes | Relationships | Description |
|---------|-------|---------------|-------------|
| Free Exercise DB | 873 exercises | 3,379 | Therapeutic exercises with muscle/equipment targets |
| Open Rehab Exercises | 76 exercises | 76 | Post-surgical rehabilitation exercises (multilingual) |
| MOTU | 1,006 patients | 7,076 | Trans-femoral amputation rehabilitation (10-year) |
| ClinicalTrials.gov | 856 trials | 1,834 | Physical rehabilitation clinical trials |
| ICD-10-CM | 74,260 codes | 1,804 | Disease classification codes (April 2025) |
| Assessment Scales | 37 scales | 37 | Rehabilitation outcome measures |
| Exercise Progressions | 10 edges | 10 | Progressive exercise difficulty |
| Condition-Exercise Maps | 72 edges | 72 | Clinical exercise recommendations |

### 2. Ontology Integration

| Ontology | Concepts | Bridges | Description |
|----------|----------|---------|-------------|
| ICF | 191 | 4,430 incoming | WHO International Classification of Functioning |
| PMR | 1,597 | 336 → ICF | Physical Medicine & Rehabilitation |
| COPPER | 362 | 6 → ICF | Exercise behavior change techniques |
| EXMO | 220 | 0 → ICF | Exercise medicine terminology |
| REHABO | 29 | 5 → ICF | Rehabilitation ontology |
| Mondo | 5,000 | 1,804 → ICD-10 | Disease ontology |
| Uberon | 10,000 | 10 → Muscle | Cross-species anatomy |
| MELLO-D | 7,399 | 0 | Medical LifeLog Ontology for Disability |
| KHMO | 1,753 | 0 | Kinetic Human Movement Ontology |
| PHY | 5 | 0 | Physical therapy concepts |

### 3. Cross-Ontology Bridges (2026-09-10 reference build)

Total bridges created: **8,200+**

| Bridge Type | Count | From → To |
|-------------|-------|-----------|
| SUBCLASS_OF | 10,785 | Ontology hierarchy |
| MAPS_TO_ICF | 4,430 | PMR/COPPER/EXMO/PHY → ICF |
| HAS_ICD10 | 1,804 | Mondo Disease → ICD-10 Code |
| STUDIES_CONDITION | 1,762 | ClinicalTrial → Condition |
| TARGETS_ANATOMY | 652 | Exercise → Uberon (via Muscle) |
| RECOMMENDS_EXERCISE | 72 | Condition → Exercise |
| MAPS_TO_UBERON | 10 | Muscle → Uberon Anatomy |
| PROGRESSES_TO | 10 | Exercise → Exercise (difficulty progression) |
| MEASURES | 37 | AssessmentScale → ICFConcept |

## Graph Composition (2026-09-10 reference build)

### Node Distribution

```
Ontologies (88%)
├── ICD10Code: 74,260 (68%)
├── UberonConcept: 10,000 (9%)
├── MELLODConcept: 7,399 (7%)
├── MondoDisease: 5,000 (5%)
├── KHMOConcept: 1,753 (2%)
├── PMRConcept: 1,597 (1%)
├── BodyFunction: 445 (<1%)
├── Activity: 393 (<1%)
├── COPPERConcept: 362 (<1%)
├── EnvironmentalFactor: 258 (<1%)
├── BodyStructure: 222 (<1%)
├── EXMOConcept: 220 (<1%)
├── ICFConcept: 191 (<1%)
├── OntologyClass: 82 (<1%)
├── OntologyProperty: 32 (<1%)
├── REHABOConcept: 29 (<1%)
├── OntologyIndividual: 23 (<1%)
├── PHYConcept: 5 (<1%)

Clinical Data (12%)
├── Outcome: 2,012 (2%)
├── Patient: 1,006 (1%)
├── Session: 1,006 (1%)
├── Exercise: 949 (1%)
├── ClinicalTrial: 856 (1%)
├── Condition: 853 (1%)
├── AdverseEvent: 144 (<1%)
├── AssessmentScale: 37 (<1%)
├── BodyPart: 17 (<1%)
├── Equipment: 12 (<1%)
```

## Key Pathways

### Exercise → Anatomy → ICD-10

```
Exercise → Muscle → Uberon → ICF
Barbell Squat → quadriceps → quadriceps femoris → [s750] Structure of lower extremity
```

### Condition → Exercise → Muscle

```
Condition → RECOMMENDS_EXERCISE → Exercise → TARGETS_PRIMARY → Muscle
Osteoarthritis → Leg Extensions → quadriceps
```

### Patient → Outcome → Assessment

```
Patient → Session → Outcome (outcome_id contains assessment name)
MOTU-1 → MOTU-STAY-1 → MOTU-STAY-1-BARTEL-ADM (68.0, admission)
```

### Mondo Disease → ICD-10 → Condition

```
MondoDisease → HAS_ICD10 → ICD10Code
knee osteoarthritis → M179 → Condition
```

## Data Quality

### Verified

- ✅ 873 + 76 = 949 exercises linked to muscles/equipment
- ✅ 10 muscles mapped to Uberon anatomy
- ✅ 652 exercises connected to Uberon via muscles
- ✅ 4,430 ICF bridges from PMR/COPPER/EXMO
- ✅ 5,000 Mondo diseases loaded
- ✅ 1,804 Mondo → ICD-10 connections
- ✅ 853 conditions from ClinicalTrials linked to 856 trials
- ✅ 1,006 MOTU patients with 2,012 outcomes
- ✅ 74,260 ICD-10-CM disease codes
- ✅ 37 assessment scales with ICF mappings
- ✅ 10 exercise progression edges
- ✅ 72 condition-exercise recommendation edges

### Known Issues

- ⚠️ ICF ontology has b730/b740 swapped vs WHO standard
- ⚠️ San Raffaele dataset requires browser authentication (not programmatically accessible)
- ⚠️ PEDro has no public API or CSV download
- ⚠️ TRAK.owl and ope.owl have malformed OWL syntax
- ⚠️ MELLO-D and KHMO ontologies are loaded but have no bridges to other layers
- ⚠️ ICD-10 re-loading via MERGE is slow (~5 min for 74K codes on fresh database)

## Example Use Cases

The full set (10 use cases plus an appendix, with runnable Cypher and limits)
is in [USE_CASES.md](USE_CASES.md); run them with `python use_cases.py`. Each
returns provenance (`review_status`, `confidence`, `method`) so results can be
audited. Curated links are unreviewed research candidates, not clinical advice.

### 1. Safety-aware exercise lookup

```cypher
MATCH (c:Condition)-[r:RECOMMENDS_EXERCISE|PRECAUTION|CONTRAINDICATION]->(e:Exercise)
WHERE toLower(c.name) CONTAINS 'stroke' AND NOT toLower(c.name) CONTAINS 'heat stroke'
RETURN type(r), c.name, e.name, r.review_status, r.confidence
LIMIT 20;
```

### 2. Gait concept resolver and link-gap view (HPO to ICF)

```cypher
MATCH (h:HPOConcept) WHERE toLower(h.name) CONTAINS 'gait'
OPTIONAL MATCH (h)-[r:RELATED_TO_ICF]->(i:ICFConcept)
RETURN h.name, i.code, r.review_status
ORDER BY i.code IS NULL;
```

Only nine curated HPO-to-ICF code pairs exist; most gait terms are unlinked.

### 3. Review-queue triage

```cypher
MATCH ()-[r]->()
WHERE type(r) IN ['RECOMMENDS_EXERCISE', 'PRECAUTION', 'CONTRAINDICATION']
RETURN type(r), coalesce(r.review_status, 'missing'), count(r);
```

### 4. Assessment scales by domain

```cypher
MATCH (a:AssessmentScale)-[:MEASURES]->(i:ICFConcept)
WHERE a.domain = 'balance'
RETURN a.name, a.scoring_range, collect(i.code) AS icf_codes;
```

Other use cases: explain-this-path, stroke coverage audit,
recommendation/contraindication conflicts, trial landscape, condition-exercise-muscle
map, and the synthetic gait observations (no ICF links yet by design). The MOTU amputation cohort
(1,006 patients, 2,012 outcomes) is kept as a descriptive appendix only.

## Next Steps

### Potential Improvements

1. **Add more clinical data**
   - San Raffaele dataset (3,928 patients) - requires manual download
   - Additional ClinicalTrials.gov queries
   - PEDro systematic reviews (if API becomes available)

2. **Enhance ontology bridges**
   - Add SNOMED CT mappings
   - Add LOINC assessment mappings
   - Connect MELLO-D and KHMO to other ontology layers

3. **Graph analytics**
   - Run GDS algorithms (PageRank, community detection)
   - Generate exercise embeddings
   - Build recommendation system

4. **Visualization**
   - Create Neo4j Bloom screens
   - Build interactive dashboards
   - Generate graph visualizations

## Conclusion

The 2026-09-10 reference build is a well-connected knowledge graph with strong clinical data foundations. With 109,195 nodes and 26,258 relationships, it supports:

- Candidate exercise lookup with safety edges and provenance (949 exercises, 72 condition-exercise links, all unreviewed)
- Clinical trial landscape queries by condition name (856 trials, 853 conditions)
- Descriptive outcome queries on a synthetic amputation demo cohort (1,006 patients, 2,012 outcomes); no prediction claims
- ICD-10 disease classification (74,260 codes)
- Cross-ontology semantic queries (4,430 ICF bridges)
