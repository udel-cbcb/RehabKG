# RehabKG Setup Guide

This guide describes the current source pipeline and its local prerequisites. Source data, Neo4j state, and credentials are local and are not committed to Git.

## Prerequisites

- Python 3.9 or later
- Docker Desktop or another Docker Engine
- Neo4j Community 5.26 (for example `neo4j:5.26.29-community`)
- Enough disk space for the selected ontology and clinical source files

Install dependencies and configure local settings:

```bash
python -m pip install -r requirements.txt
cp .env.example .env
```

Set `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD` in `.env` to match the database. The default URI in the example is `bolt://localhost:7687`. Use an individual BioPortal API key in `BIOPORTAL_API_KEY` to download BioPortal ontologies; do not commit `.env`.

## Start Neo4j

For a disposable local database, use the same password in Docker and `.env`:

```bash
docker run -d --name neo4j-rehabkg \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password_here \
  neo4j:5.26.29-community
```

Check startup with `docker logs -f neo4j-rehabkg` and browse to <http://localhost:7474>. Persist data with a Docker volume only if you want the graph to survive container recreation. Avoid mounting the live database directory into version control; `docker/data/` is ignored.

## Prepare source data

Run the download helper:

```bash
python download_data.py
```

It downloads the ontology and Free Exercise DB files currently listed in `download_data.py`, processes the exercise JSON when present, and prints manual-download instructions. BioPortal downloads require `BIOPORTAL_API_KEY`. Downloads are not the same as a full source-data acquisition step: the helper does **not** currently fetch every input used by the pipeline.

Depending on which steps you run, place these files in their expected locations:

| Input | Expected location | Preparation |
|---|---|---|
| Free Exercise DB JSON | `data/raw/free-exercise-db/free_exercise_db.json` | `download_data.py` |
| Core OWL files | `data/ontologies/` | `download_data.py` where listed; see `download_data.py` for exact list |
| Mondo and Uberon OWL | `data/ontologies/mondo.owl`, `data/ontologies/uberon.owl` | Download from the public OBO PURLs listed in [DATA_SOURCES.md](DATA_SOURCES.md) |
| HPO OWL | `data/ontologies/hp.owl` | Download from the HPO/OBO source listed in [DATA_SOURCES.md](DATA_SOURCES.md) |
| MOTU CSV files | `data/raw/motu/` | Download from the dataset record listed in [DATA_SOURCES.md](DATA_SOURCES.md) |
| ICD-10-CM CSV | `data/raw/icd10/icd10cm_data.csv` | Obtain from the CDC source listed in [DATA_SOURCES.md](DATA_SOURCES.md) |
| ClinicalTrials.gov JSON | `data/raw/clinicaltrials/` | The additional-data loader can fetch trials; existing raw/extracted JSON may also be used |
| Open Rehab Exercises archive | `data/raw/rehab-exercises/open-rehab-exercises-main/` | Obtain from its source if using the corresponding loader/import path |

Files are optional only where the associated loader permits a missing input; some ETL entry points require their source file and will fail if it is absent. Check each script's expected input paths before launching a long run.

## Run the unified Cypher pipeline

```bash
python rehabkg.py
```

The ordered steps in `rehabkg.py` are:

| Step | Work |
|---|---|
| `schema` | Constraints, indexes, and schema documentation |
| `ontologies` | Core ontology loading and ontology-level bridges |
| `datasets` | Curated assessment, movement, exercise progression, and recommendation metadata |
| `anatomy` | Mondo and Uberon imports and anatomy links |
| `additional` | HPO and expanded clinical-trial loading |
| `provenance` | Source/SAB metadata |

Post-load linking is run for the relevant selected steps: Muscle→ICF after `datasets`, disease→ICD-10 after `anatomy`, and Condition/trial/ontology bridges after `additional`. `etl_motu.py` is a separate MOTU ETL entry point; `etl_datasets.py` creates MOTU metadata but is not the patient/stay CSV loader. Run only after staging its inputs:

```bash
python etl_motu.py
```

### Select pipeline steps

```bash
python rehabkg.py --status
python rehabkg.py --only ontologies datasets
python rehabkg.py --skip additional provenance
python rehabkg.py --add hpo
python rehabkg.py --add trials
python rehabkg.py --reset-label HPOConcept
```

The accepted step names and resettable labels are defined in `rehabkg.py` and can be inspected with `python rehabkg.py --help`. `--add hpo` and `--add trials` perform only their incremental loader and return; they do not execute the full pipeline.

**Destructive operation:** `python rehabkg.py --fresh` deletes all nodes and relationships from the configured database before loading. Confirm the target database and create a backup before using it.

## Bulk import path

The alternative bulk route generates CSV files locally and imports them with Neo4j admin tools:

```bash
python build_csvs.py
python import_bulk.py
```

It depends on the source inputs used by the builders and Docker access. Review [bulk-import-architecture.md](bulk-import-architecture.md) and the script options before running: bulk import can replace a database, and its container/data paths may be configured independently from the ordinary Cypher setup. Generated `export/` CSVs and temporary import directories are ignored by Git.

## Dashboard and browser tests

The Streamlit dashboard is in `dashboard/app.py`. Install its requirements and run it with:

```bash
python -m pip install -r dashboard/requirements.txt
python -m streamlit run dashboard/app.py
```

Then open <http://localhost:8501>. The Playwright suite also needs the browser packages and Chromium installed:

```bash
python -m pip install playwright pytest-playwright
python -m playwright install chromium
python -m pytest tests/test_e2e.py -v
```

## Tests

Fast tests that do not require a populated Neo4j service:

```bash
python -m pytest tests/ -q --ignore=tests/test_e2e.py --ignore=tests/test_graph.py
```

Data-dependent tests self-skip when ignored source files are missing. The graph integrity tests need a running, populated Neo4j instance. The browser E2E suite needs the dashboard and its Neo4j backend running.

## Troubleshooting

- **Neo4j connection refused:** check `docker ps`, container logs, port bindings, and `.env` URI.
- **Authentication failure:** ensure Docker's `NEO4J_AUTH` and `.env` username/password match. Repeated incorrect logins can temporarily trigger the server's authentication rate limit.
- **Missing ontology/data file:** inspect the corresponding loader's path constants and stage that source; `download_data.py` does not fetch every input.
- **BioPortal download failure:** confirm the personal API key and retry after rate limits clear.
- **Inspect graph counts:** run `python rehabkg.py --status`.
