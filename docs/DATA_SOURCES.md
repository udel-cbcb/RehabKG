# RehabKG Data Sources

Catalog of all data sources in the Rehabilitation Knowledge Graph.

## Loaded in Graph

### Clinical Datasets

| Dataset | Records | Description | Source | Download |
|---------|---------|-------------|--------|----------|
| Free Exercise DB | 949 nodes in the validated graph snapshot | Therapeutic exercises with muscle/equipment targets | GitHub | `download_data.py` downloads the JSON; graph loading is handled by `rehabkg.py` or the bulk-import path |
| Open Rehab Exercises | Source archive contains 76 exercise records | Post-surgical rehabilitation exercises (multilingual) | GitHub | Stage under `data/raw/rehab-exercises/`; not downloaded by the current `download_data.py` |
| MOTU | 1,006 patients in the validated graph snapshot | Trans-femoral amputation rehabilitation | Zenodo | Stage CSV files under `data/raw/motu/`; `etl_motu.py` loads patient, stay, outcome, knee and fall data |
| ClinicalTrials.gov | 1,387 trials in the validated graph snapshot | Physical rehabilitation clinical trials | API | `add_additional_data.py` can fetch/load expanded trials; `download_data.py` does not download them |
| ICD-10-CM | 92,694 code nodes in the validated graph snapshot | Disease classification codes; source distribution varies from graph-node count | CDC | Stage CSV under `data/raw/icd10/`; `download_data.py` does not download it |
| Assessment Scales | 40 nodes in the validated graph snapshot | Curated rehabilitation outcome measures | Curated/manual | `etl_datasets.py` creates scale metadata; do not treat this as an RMD download |

### Ontologies

| Ontology | Concepts | Bridges | Description | Status |
|----------|----------|---------|-------------|--------|
| ICF | 1,509 | 9 explicit HPO→ICF, 5 REHABO CLOSE_MATCH; other curated bridge counts in graph | WHO International Classification of Functioning | Loaded from staged `icf.owl`; snapshot/ND review noted below |
| EXMO | 220 | See manifest | Exercise medicine terminology | Loaded from staged `exmo.owl` |
| Mondo | 5,000 | 13,027 → ICD-10 (live snapshot) | Disease ontology | Loaded from staged `mondo.owl` |
| Uberon | 10,000 | 14 `MAPS_TO_UBERON`; 776 `TARGETS_ANATOMY` (live snapshot) | Cross-species anatomy | Deterministic named-class subset (sorted by URI); imported-term review pending |
| HPO | 32,772 | 9 explicit `RELATED_TO_ICF` links | Human Phenotype Ontology | Loaded from staged `hp.owl`; imported-term review pending |
| PAIN | 623 | 0 | The Pain Ontology (IASP) | Loaded from staged `pain.owl` |
| REHABO | 310 source nodes (63 `REHABOConcept`) | 5 `CLOSE_MATCH` → ICF | Rehabilitation ontology | Loaded from staged `rehabo.owl` |

> Counts/status above reflect the deterministic focused ontology refresh on
> 2026-11-05 (live Neo4j `bolt://localhost:7688`), unless marked otherwise. The
> 2026-11-05 graph had 153,069 nodes and 107,436 relationships; the graph
> rebuilt on 2026-11-17 has 153,069 nodes and 147,691 relationships (the extra
> 117,005 `SUBCLASS_OF` ontology hierarchy edges come from the bulk build;
> see `eval/snapshot_report_2026-11-17.md`). These
> counts are a dated snapshot, not a license determination; see
> `eval/public_ontology_refresh_manifest.json` and
> `docs/notes/data_hosting_license_audit.md`.
> The focused refresh removed COPPER, KHMO, CBHA (including its 1,210 activities),
> and the previously flagged ontology families. The regular ontology ETL and
> bulk CSV builder still contain legacy source extractors; do not treat a
> general reload as equivalent to this focused source set until the pipeline
> allowlists are reconciled.
> `scripts/refresh_public_ontologies.py` records the focused subset and supports
> `--dry-run`. The helper retains HPO, sorts the Uberon/Mondo subsets before
> slicing, and records final node/relationship counts. The focused refresh is
> covered by the opt-in E2E test and is deterministic across runs. Run
> `--dry-run` and the focused tests before relying on it for another graph
> replacement.
> The pre-refresh live data directory is backed up at
> `/Users/chenc/Documents/2026/Work/HAIC/RehabKG_backups/neo4j_test_data_2026-11-05`
> (outside the repository); the post-refresh/pre-swap state is at
> `..._refreshed`. The earlier 2026-10-27 source cleanup backup remains at
> `deliverables/public-graph-removal-backup-2026-10-27.json`. Retained sources
> still need source-release-specific license review before public hosting.
> Phase 5 provides a header-only ICF Core Set register and report tooling.
> Category lists and redistribution terms require human confirmation; no
> Core Set category edges are loaded while the register is empty.

---

## Data Pipeline

### Download helper (partial)

```bash
python download_data.py
```

The current `download_data.py` downloads the ontology entries explicitly listed in its `download_ontologies()` function and the Free Exercise DB JSON/schema. It can print manual-download guidance and processes the Free Exercise DB JSON when available. It does **not** automatically download every source listed in this catalog: in particular, stage MOTU, ICD-10-CM, Mondo, Uberon, HPO, Open Rehab Exercises and clinical-trial files as required by the selected pipeline step. BioPortal downloads need `BIOPORTAL_API_KEY`.

### Load into Neo4j (unified pipeline)

```bash
python rehabkg.py                  # Schema, core ontologies, datasets, anatomy,
                                # additional HPO/trials, provenance + linking
python etl_motu.py              # Optional standalone CSV loader for MOTU data
```

`etl_datasets.py` creates curated assessment/movement metadata, progression and recommendation relationships; it is not the MOTU patient CSV loader and does not fetch trials or ICD-10. `import_ontologies.py` loads Mondo and Uberon in the focused source set. For offline CSV generation and Neo4j admin import, see `build_csvs.py`, `import_bulk.py` and [bulk-import-architecture.md](bulk-import-architecture.md). Default Cypher/bulk ontology paths use the focused source set; experimental extractors remain in the repository but are not invoked by default. Full-path parity is checked by `tests/test_bulk_parity.py` against `eval/bulk_parity_baseline.json` (`REHABKG_BULK_PARITY=1`); re-run it after changing a loader or the focused source set.

### Manual Download Required

| Dataset | Size | URL | License |
|---------|------|-----|---------|
| San Raffaele | 3,928 patients | https://figshare.com/s/7aab7ad2d351f53dbe2f | CC BY 4.0 |
| REHAB24-6 | 668 MB | https://zenodo.org/records/13305826 | CC BY-NC 4.0 |
| IntelliRehabDS | - | https://zenodo.org/records/4610859 | Open Access |
| KneE-PAD | - | https://doi.org/10.1038/s41597-025-04963-4 | CC BY 4.0 |
| GAITEX | - | https://zenodo.org/records/15729055 | CC BY-NC-ND 4.0 |
| MIMIC-IV | - | https://physionet.org/content/mimiciv/ | PhysioNet DUA |

---

## Ontology Sources

### BioPortal (API Key Required)

| Ontology | Download URL |
|----------|--------------|
| REHABO | https://data.bioontology.org/ontologies/REHABO/submissions/2/download |
| ICF | https://data.bioontology.org/ontologies/ICF/submissions/3/download |

### Public Downloads (No API Key)

| Ontology | Download URL |
|----------|--------------|
| EXMO | https://raw.githubusercontent.com/Exercise-Medicine-Ontology/EXMO/master/exmo.owl |
| PAIN | https://raw.githubusercontent.com/obophenotype/pain-ontology/master/pain.owl |
| Mondo | https://purl.obolibrary.org/obo/mondo.owl |
| Uberon | https://purl.obolibrary.org/obo/uberon.owl |
| HPO | https://purl.obolibrary.org/obo/hp.owl |

---

## Historical ClinicalTrials.gov query counts

The following table records query counts for a previously prepared source snapshot. It is not an assertion that the current download helper fetches these query results or that counts exactly match the graph:

| Query | Trials |
|-------|--------|
| physical rehabilitation exercise | 100 |
| physical therapy musculoskeletal | 100 |
| rehabilitation stroke exercise | 100 |
| exercise therapy knee osteoarthritis | 100 |
| physical therapy shoulder | 100 |
| rehabilitation hip replacement | 54 |
| exercise therapy low back pain | 100 |
| physical therapy balance gait | 59 |
| rehabilitation spinal cord injury | 100 |
| exercise therapy cardiac rehabilitation | 100 |

**Total**: 856 unique trials

---

## Example local file structure (not a download manifest)

Paths shown below are illustrative; files are present only when acquired for the selected ETL steps. Counts and sizes can change between source releases.

```
data/
├── raw/
│   ├── clinicaltrials/
│   │   ├── clinicaltrials_raw.json          (16 MB)
│   │   └── clinicaltrials_extracted.json    (861 KB)
│   ├── free-exercise-db/
│   │   ├── free_exercise_db.json            (978 KB)
│   │   └── free_exercise_db_schema.json
│   ├── motu/
│   │   ├── Patient.csv                      (20 KB)
│   │   ├── HospitalStay.csv                 (931 KB)
│   │   ├── Drug.csv                         (158 KB)
│   │   ├── Fall.csv                         (6.8 KB)
│   │   └── Knee.csv                         (4.4 KB)
│   ├── rehab-exercises/
│   │   └── open-rehab-exercises-main/       (76 exercises)
│   └── icd10/
│       └── icd10cm_data.csv                 (3.5 MB)
├── processed/
│   └── free-exercise-db/
│       ├── exercises_nodes.csv              (695 KB)
│       └── exercises_relationships.csv      (180 KB)
├── ontologies/
│   ├── icf.owl                              (2.8 MB)
│   ├── pmr.owl                              (1.3 MB)
│   ├── copper.owl                           (864 KB)
│   ├── exmo.owl                             (1.6 MB)
│   ├── rehabo.owl                           (364 KB)
│   ├── mondo.owl                            (242 MB)
│   ├── uberon.owl                           (91 MB)
│   ├── phy.owl                              (14 KB)
│   ├── mello_d.owl                          (5.1 MB)
│   ├── khmo.owl                             (3.2 MB)
│   ├── ontoloco.owl                         (309 KB)
│   ├── ope.owl                              (1.0 MB)
│   ├── trak.owl                             (443 KB, OBO text)
│   ├── frmo.owl                             (846 KB)
│   ├── pain.owl                             (1.3 MB)
│   ├── bcio.owl                             (1.9 MB)
│   ├── bctt.owl                             (36 KB)
│   ├── sto.owl                              (2.4 MB)
│   └── paco.owl                             (272 KB)
└── export/                                  (Bulk import CSVs)
    ├── nodes/
    │   ├── nodes_adverseevent.csv
    │   ├── nodes_assessmentscale.csv
    │   ├── nodes_clinicaltrial.csv
    │   ├── nodes_copperconcept.csv
    │   ├── nodes_equipment.csv
    │   ├── nodes_equipment_motu.csv
    │   ├── nodes_exercise.csv
    │   ├── nodes_exmoconcept.csv
    │   ├── nodes_hpoconcept.csv
    │   ├── nodes_icd10code.csv
    │   ├── nodes_icfconcept.csv
    │   ├── nodes_khmoconcept.csv
    │   ├── nodes_mellodconcept.csv
    │   ├── nodes_mondodisease.csv
    │   ├── nodes_muscle.csv
    │   ├── nodes_nodetype.csv
    │   ├── nodes_ontolococoncept.csv
    │   ├── nodes_ontologyclass.csv
    │   ├── nodes_ontologyindividual.csv
    │   ├── nodes_ontologyproperty.csv
    │   ├── nodes_opeconcept.csv
    │   ├── nodes_openrehabexercise.csv
    │   ├── nodes_outcome.csv
    │   ├── nodes_patient.csv
    │   ├── nodes_phyconcept.csv
    │   ├── nodes_pmrconcept.csv
    │   ├── nodes_reltype.csv
    │   ├── nodes_session.csv
    │   └── nodes_uberonconcept.csv
    └── relationships/
        ├── rel_experienced.csv
        ├── rel_from_node_type.csv
        ├── rel_has_domain.csv
        ├── rel_has_outcome.csv
        ├── rel_has_range.csv
        ├── rel_has_stay.csv
        ├── rel_requires.csv
        ├── rel_subclass_of_copper.csv
        ├── rel_subclass_of_exmo.csv
        ├── rel_subclass_of_icf.csv
        ├── rel_subclass_of_khmo.csv
        ├── rel_subclass_of_mello_d.csv
        ├── rel_subclass_of_ontoloco.csv
        ├── rel_subclass_of_ope.csv
        ├── rel_subclass_of_pmr.csv
        ├── rel_subclass_of_rehabo.csv
        ├── rel_targets_primary.csv
        ├── rel_targets_secondary.csv
        └── rel_to_node_type.csv
```

---

## Licensing

| Resource | License | Commercial Use |
|----------|---------|----------------|
| Free Exercise DB | Unlicense | Yes |
| Open Rehab Exercises | CC BY 4.0 | Yes |
| MOTU | CC BY 4.0 | Yes |
| ClinicalTrials.gov | Public Domain | Yes |
| ICD-10-CM | Public Domain | Yes |
| ICF | CC BY-ND 3.0 IGO per user-provided WHO terms | Yes, with WHO attribution; no derivatives/adaptations; do not imply endorsement. Confirm the local BioPortal OWL snapshot is covered. |
| REHABO | CC0 | Yes |
| EXMO | CC BY 4.0 | Yes |
| COPPER | Not established in staged file | Do not redistribute pending explicit terms |
| KHMO | CC BY 4.0 ontology-level; mixed imported-term annotations | Verify term-level provenance before redistribution |
| Mondo | CC BY 4.0 | Yes |
| Uberon | CC BY 4.0 | Yes |
| PAIN | CC BY 4.0 (OBO) | Yes |
| CBHA | Academic (Compendium of Physical Activities-derived) | Verify before commercial use |

---

*Last updated: 2026-10-27*
