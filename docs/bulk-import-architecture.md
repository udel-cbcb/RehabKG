# Neo4j Bulk Import Architecture

> **Status (2026-11):** Phases 1–3 below are implemented: `build_csvs.py`
> (CSV generation), `import_bulk.py` (Docker `neo4j-admin import` +
> post-load), `export_csv.py` (live-graph CSV export), and `csv_writer.py`
> (shared CSV writing). The current focused graph snapshot uses
> `scripts/refresh_public_ontologies.py` for the ontology layer. The bulk
> importer is parity-checked against that snapshot by
> `tests/test_bulk_parity.py` (opt-in with `REHABKG_BULK_PARITY=1`, baseline
> `eval/bulk_parity_baseline.json`); it matches node/label/source counts, the
> bridge/clinical relationship contract, and gold **35/35**. `SUBCLASS_OF` is
> intentionally out of scope because the bulk path also emits source-owned
> hierarchy the focused refresh does not rebuild. The "Dual-mode" `--bulk`
> flag proposed for `rehabkg.py` is **not implemented** — invoke
> `python import_bulk.py` directly.

## Problem

The current ETL pipeline loads nodes and relationships via the Python Neo4j driver
(Cypher `MERGE`/`CREATE` statements). This works at ~143K nodes but will not scale
to millions of nodes from EHR data. Each Cypher statement has:
- Network round-trip overhead
- Query parsing overhead  
- Transaction commit overhead

`neo4j-admin import` reads CSV files directly into Neo4j's native store format,
bypassing the query engine entirely. Typical speedup: **10-50x**.

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│  Phase 1: CSV Generation (build_csvs.py)            │
│                                                     │
│  Parses source files (OWL, CSV, JSON)               │
│  Reuses extract_* functions from ETL modules         │
│  Writes CSVs to export/ directory                    │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  Phase 2: Bulk Import (Docker-based)                │
│                                                     │
│  1. Copy CSVs to neo4j_test_import/                 │
│  2. Mount volumes: /import, /data                   │
│  3. Run neo4j-admin database import full            │
│  4. Start Neo4j with imported data                  │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  Phase 3: Post-Load (DB online, Cypher)             │
│                                                     │
│  1. Multi-label assignment (ICF, Muscle)            │
│  2. Create constraints + indexes                     │
│  3. Bridge linking (ICF, MONDO, ICD10)               │
│  4. Provenance tagging                               │
└─────────────────────────────────────────────────────┘
```

## Phase 1: CSV Generation

### build_csvs.py

Parses source files directly (no Neo4j needed):

```bash
python build_csvs.py
```

Output: node + relationship CSVs under `export/` — 82 files (42 node + 40
relationship) as of the 2026-10 BioPortal shortlist; the count grows with
each added ontology.

### CSV Format

`neo4j-admin import` expects:
- **Node CSVs**: First column is `:ID`, then properties. Label specified via `--nodes=Label=file.csv` syntax.
- **Relationship CSVs**: `:START_ID`, `:END_ID`, then properties. Type specified via `--relationships=Type=file.csv` syntax.

Example (`nodes_exercise.csv`):
```csv
:ID,category,equipment,force,images,instructions,level,mechanic,name,source
ex_001,"strength","barbell",null,null,null,"intermediate","compound","Barbell Squat","Free Exercise DB"
```

Example (`rel_targets_primary.csv`):
```csv
:START_ID,:END_ID
ex_001,m_q721
```

### File Organization

> The tree below shows the legacy bulk path, including excluded-source CSVs
> retained in the extractor code. The focused default emits only the selected
> ontology set and does not include COPPER, KHMO, MELLO-D, ONTOLOCO, OPE, PHY,
> or PMR.

```
export/
├── nodes/                              # 29 node CSV files
│   ├── nodes_adverseevent.csv          # AdverseEvent
│   ├── nodes_assessmentscale.csv       # AssessmentScale
│   ├── nodes_clinicaltrial.csv         # ClinicalTrial
│   ├── nodes_copperconcept.csv         # COPPERConcept
│   ├── nodes_equipment.csv             # Equipment
│   ├── nodes_equipment_motu.csv        # Equipment (MOTU)
│   ├── nodes_exercise.csv              # Exercise (Free Exercise DB)
│   ├── nodes_exmoconcept.csv           # EXMOConcept
│   ├── nodes_hpoconcept.csv            # HPOConcept
│   ├── nodes_icd10code.csv             # ICD10Code
│   ├── nodes_icfconcept.csv            # ICFConcept
│   ├── nodes_khmoconcept.csv           # KHMOConcept
│   ├── nodes_mellodconcept.csv         # MELLODConcept
│   ├── nodes_mondodisease.csv          # MondoDisease
│   ├── nodes_muscle.csv                # Muscle
│   ├── nodes_nodetype.csv              # NodeType (schema)
│   ├── nodes_ontolococoncept.csv       # ONTOLOCOConcept
│   ├── nodes_ontologyclass.csv         # OntologyClass
│   ├── nodes_ontologyindividual.csv    # OntologyIndividual
│   ├── nodes_ontologyproperty.csv      # OntologyProperty
│   ├── nodes_opeconcept.csv            # OPEConcept
│   ├── nodes_openrehabexercise.csv     # Exercise (Open Rehab)
│   ├── nodes_outcome.csv               # Outcome
│   ├── nodes_patient.csv               # Patient
│   ├── nodes_phyconcept.csv            # PHYConcept
│   ├── nodes_pmrconcept.csv            # PMRConcept
│   ├── nodes_reltype.csv               # RelType (schema)
│   ├── nodes_session.csv               # Session
│   └── nodes_uberonconcept.csv         # UberonConcept
└── relationships/                      # 19 relationship CSV files
    ├── rel_experienced.csv             # Patient -> AdverseEvent
    ├── rel_from_node_type.csv          # RelType -> NodeType
    ├── rel_has_domain.csv              # OntologyProperty -> class
    ├── rel_has_outcome.csv             # Session -> Outcome
    ├── rel_has_range.csv               # OntologyProperty -> class
    ├── rel_has_stay.csv                # Patient -> Session
    ├── rel_requires.csv                # Exercise -> Equipment
    ├── rel_subclass_of_copper.csv      # COPPER hierarchy
    ├── rel_subclass_of_exmo.csv        # EXMO hierarchy
    ├── rel_subclass_of_icf.csv         # ICF hierarchy
    ├── rel_subclass_of_khmo.csv        # KHMO hierarchy
    ├── rel_subclass_of_mello_d.csv     # MELLO-D hierarchy
    ├── rel_subclass_of_ontoloco.csv    # ONTOLOCO hierarchy
    ├── rel_subclass_of_ope.csv         # OPE hierarchy
    ├── rel_subclass_of_pmr.csv         # PMR hierarchy
    ├── rel_subclass_of_rehabo.csv      # REHABO hierarchy
    ├── rel_targets_primary.csv         # Exercise -> Muscle (primary)
    ├── rel_targets_secondary.csv       # Exercise -> Muscle (secondary)
    └── rel_to_node_type.csv            # RelType -> NodeType
```

### ID Scheme

All node IDs must be **strings** and **unique across all files**. Use a prefix convention:

| Label | ID prefix | Example |
|-------|-----------|---------|
| Exercise | `ex_` | `ex_001` |
| Muscle | `m_` | `m_q721` |
| Equipment | `eq_` | `eq_001` |
| ICFConcept | `icf_` | `icf_b710` |
| MondoDisease | `mondo_` | `mondo_001` |
| UberonConcept | `uberon_` | `uberon_001` |
| HPOConcept | `hpo_` | `hpo_001` |
| ICD10Code | `icd_` | `icd_M17` |
| ClinicalTrial | `ct_` | `ct_NCT001` |
| Patient | `pt_` | `pt_001` |
| Session | `ses_` | `ses_001` |
| Outcome | `oc_` | `oc_001` |
| AssessmentScale | `as_` | `as_001` |
| AdverseEvent | `ae_` | `ae_001` |
| NodeType | `nt_` | `nt_patient` |
| RelType | `rt_` | `rt_has_outcome` |
| OntologyClass | `oclass_` | `oclass_rehabo_001` |
| OntologyProperty | `oprop_` | `oprop_001` |
| OntologyIndividual | `oind_` | `oind_001` |

### Multi-Label Handling

`neo4j-admin import` only supports **one label per node file**. For dual-labeled
nodes (e.g., `ICFConcept` + `BodyFunction`), use post-load Cypher:

```cypher
MATCH (n:ICFConcept) WHERE n.uri CONTAINS '#b' SET n:BodyFunction;
MATCH (n:ICFConcept) WHERE n.uri CONTAINS '#s' SET n:BodyStructure;
MATCH (n:ICFConcept) WHERE n.uri CONTAINS '#d' SET n:Activity;
MATCH (n:ICFConcept) WHERE n.uri CONTAINS '#e' SET n:EnvironmentalFactor;
MATCH (n:Muscle) SET n:BodyPart;
```

## Phase 2: Bulk Import

### import_bulk.py

Orchestrates the full import process:

```bash
python import_bulk.py
```

This script:
1. Runs `build_csvs.py` to generate CSVs
2. Copies CSVs to `neo4j_test_import/`
3. Starts Docker with volume mounts
4. Runs `neo4j-admin database import full`
5. Starts Neo4j with imported data
6. Runs post-load Cypher (multi-labels, constraints, indexes)

### Docker Volumes

| Volume | Host Path | Container Path | Purpose |
|--------|-----------|----------------|---------|
| CSV files | `neo4j_test_import/` | `/import` | Source CSV files for import |
| Database | `neo4j_test_data/` | `/data` | Neo4j data directory |

### Import Command

```bash
docker run --tty \
    --volume=$(pwd)/neo4j_test_import:/import \
    --volume=$(pwd)/neo4j_test_data:/data \
    neo4j:5.26.29-community \
    sh -c '
        neo4j-admin database import full \
            --overwrite-destination \
            --verbose \
            --id-type=string \
            --skip-bad-relationships \
            --skip-duplicate-nodes \
            --multiline-fields=true \
            --nodes=Exercise=/import/nodes_exercise.csv \
            --nodes=ICFConcept=/import/nodes_icfconcept.csv \
            ... (all node files with labels) ...
            --relationships=SUBCLASS_OF=/import/rel_subclass_of_icf.csv \
            ... (all relationship files with types) ...
            -- neo4j
    '
```

### Performance

For the 2026-11-05 focused snapshot (153,069 nodes + 107,436 relationships),
import took **~10 seconds**. The 2026-11-17 rebuild (147,691 relationships,
including 117,005 `SUBCLASS_OF` hierarchy edges) was not timed. For 1M+ nodes + 100K+ relationships, expect
**1-5 minutes**.

## Phase 3: Post-Load Cypher

After import, Neo4j starts and we run:

```cypher
-- 1. Multi-label assignment
MATCH (n:ICFConcept) WHERE n.uri CONTAINS '#b' SET n:BodyFunction;
MATCH (n:ICFConcept) WHERE n.uri CONTAINS '#s' SET n:BodyStructure;
MATCH (n:ICFConcept) WHERE n.uri CONTAINS '#d' SET n:Activity;
MATCH (n:ICFConcept) WHERE n.uri CONTAINS '#e' SET n:EnvironmentalFactor;
MATCH (n:Muscle) SET n:BodyPart;

-- 2. Constraints + indexes
CREATE CONSTRAINT patient_id IF NOT EXISTS FOR (p:Patient) REQUIRE p.patient_id IS UNIQUE;
CREATE CONSTRAINT session_id IF NOT EXISTS FOR (s:Session) REQUIRE s.session_id IS UNIQUE;
CREATE CONSTRAINT outcome_id IF NOT EXISTS FOR (o:Outcome) REQUIRE o.outcome_id IS UNIQUE;
CREATE CONSTRAINT exercise_id IF NOT EXISTS FOR (e:Exercise) REQUIRE e.exercise_id IS UNIQUE;
CREATE CONSTRAINT muscle_id IF NOT EXISTS FOR (m:Muscle) REQUIRE m.muscle_id IS UNIQUE;
CREATE CONSTRAINT equipment_id IF NOT EXISTS FOR (e:Equipment) REQUIRE e.equipment_id IS UNIQUE;
CREATE CONSTRAINT assessment_id IF NOT EXISTS FOR (a:AssessmentScale) REQUIRE a.scale_id IS UNIQUE;
CREATE CONSTRAINT adverse_event_id IF NOT EXISTS FOR (a:AdverseEvent) REQUIRE a.event_id IS UNIQUE;

-- 3. Indexes
CREATE INDEX icf_code IF NOT EXISTS FOR (n:ICFConcept) ON (n.code);
CREATE INDEX icf_name IF NOT EXISTS FOR (n:ICFConcept) ON (n.name);
CREATE INDEX mondo_name IF NOT EXISTS FOR (n:MondoDisease) ON (n.name);
CREATE INDEX icd10_code IF NOT EXISTS FOR (n:ICD10Code) ON (n.code);
CREATE INDEX exercise_name IF NOT EXISTS FOR (n:Exercise) ON (n.name);
CREATE INDEX muscle_name IF NOT EXISTS FOR (n:Muscle) ON (n.name);
CREATE INDEX condition_name IF NOT EXISTS FOR (n:Condition) ON (n.name);
CREATE INDEX trial_nct IF NOT EXISTS FOR (n:ClinicalTrial) ON (n.nct_id);
CREATE INDEX hpo_code IF NOT EXISTS FOR (n:HPOConcept) ON (n.code);
CREATE INDEX uberon_name IF NOT EXISTS FOR (n:UberonConcept) ON (n.name);
```

## Integration with Current Code

### Dual-mode (recommended)

Keep current Cypher loading as the default. Add `--bulk` flag to rehabkg.py:

```bash
python rehabkg.py --bulk          # CSV export + neo4j-admin import
python rehabkg.py --fresh         # Current Cypher approach (for dev/small data)
```

### Recommended

- Current Cypher approach is fine for development and testing
- Bulk import is for production / large datasets
- Both share the same post-load linking code

## File Changes

| File | Change |
|------|--------|
| `build_csvs.py` | **New** — parses source files → writes CSVs (no Neo4j needed) |
| `csv_writer.py` | **New** — CSV writing utilities with ID validation |
| `import_bulk.py` | **New** — orchestrator: build CSVs → Docker import → post-load Cypher |
| `export_csv.py` | **New** — export from live Neo4j (validation/backup) |

## Scaling for EHR Data

When EHR data arrives:

1. **Parser module** (`etl_ehr.py`) reads raw EHR files
2. **Export module** writes `nodes_ehr_patient.csv`, `nodes_ehr_observation.csv`, etc.
3. Bulk import loads everything in one pass
4. Post-load linking connects EHR nodes to existing ontologies

Expected volumes:
- Patients: 100K-1M nodes
- Observations: 10M-100M nodes
- Medications: 1M-10M nodes
- Lab results: 5M-50M nodes

At these volumes, `neo4j-admin import` is **essential** — Cypher loading would
take days.
