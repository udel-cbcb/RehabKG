# Rehabilitation Knowledge Graph (RehabKG)

RehabKG is a Neo4j knowledge graph that combines rehabilitation and movement ontologies with exercise, patient, outcome, and clinical-trial data. It supports graph queries and an interactive Streamlit dashboard.

## Quick start

Requirements: Python 3.9+, Docker, and Neo4j 5.26. Configure the Neo4j credentials in `.env` (start from `.env.example`), then install the Python dependencies:

```bash
python -m pip install -r requirements.txt
cp .env.example .env
```

Start a local Neo4j 5.26 instance using the same password you set in `.env`. For example:

```bash
docker run -d --name neo4j-rehabkg \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password_here \
  neo4j:5.26.29-community
```

Wait for Neo4j to finish starting, then download source files and run the unified pipeline:

```bash
python download_data.py
python rehabkg.py
```

`download_data.py` fetches the configured ontology and Free Exercise DB source files and prints manual-download guidance for other datasets. Set `BIOPORTAL_API_KEY` in `.env` for BioPortal downloads. Sources not handled by that script (including Mondo, Uberon, HPO, MOTU, ICD-10-CM and clinical trials) must be downloaded or prepared through their documented data-specific paths before running the pipeline; see [docs/SETUP.md](docs/SETUP.md) and [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md). The pipeline expects those files under `data/raw/` and `data/ontologies/`.

**Ontology source set:** the default source set is REHABO, ICF, EXMO, PAIN,
Mondo, Uberon (the existing 10,000 named-class subset), and HPO. Use
`python scripts/refresh_public_ontologies.py --dry-run` to validate staged
files and inspect the refresh plan. The default Cypher and bulk ontology
builders now target this source set and use the default-source bridge policy.
Full-path live parity is verified by `tests/test_bulk_parity.py` against
`eval/bulk_parity_baseline.json`; re-run it after changing a loader or the
focused source set, and check `eval/public_ontology_refresh_manifest.json`
before rebuilding. COPPER, KHMO,
CBHA, and other flagged ontology families are not part of the focused default
set. This is a technical source selection, not license clearance.

The main source-loading pipeline is `rehabkg.py`. It runs schema setup, core ontologies, curated dataset metadata, anatomy ontologies, additional HPO/trial data, and provenance tagging, with post-load relationship linking. The standalone `etl_motu.py` can load the MOTU patient/stay CSVs after they have been staged. Some source files are optional for tests or individual steps; the relevant loaders report or skip absent data as implemented.

## Pipeline commands

```bash
python rehabkg.py --status                         # inspect graph counts and disconnected nodes
python rehabkg.py --only ontologies                # run selected pipeline step(s)
python rehabkg.py --skip datasets anatomy          # omit selected step(s)
python rehabkg.py --add hpo                        # incremental HPO load
python rehabkg.py --add trials                     # incremental expanded trials load
python rehabkg.py --fresh                          # delete graph contents, then reload
```

**Caution:** `--fresh` deletes all graph nodes and relationships before reloading. Review the selected Neo4j database and ensure anything important is backed up before using it.

For offline bulk-import CSV generation and Neo4j admin import, see `build_csvs.py`, `import_bulk.py`, and [docs/bulk-import-architecture.md](docs/bulk-import-architecture.md). The bulk-import flow has separate runtime requirements and can replace the imported database; consult its docs before running it.

Curated recommendation and safety rows are the review system of record. `match_type=keyword_group` rows use whole-word matches with an optional `exclude_keywords` column (for example, `stroke` excludes `heat stroke`), and are stamped at `confidence=0.6` with `curation_basis=keyword_group`; exact `match_type=icd10` bindings use `confidence=0.7`. See [curated/README.md](curated/README.md) for the column contract and review workflow.

### Public-hosting screening export

`export_csv.py --public-candidate` is an **opt-in screening aid**, not a legal
approval or a production publishing workflow. It filters node rows to the
proposed candidate source set recorded in
`docs/notes/public_hosting_allowlist.md`, drops relationships unless both
endpoints remain, and writes `export/public_candidate_manifest.json`. Review
the source terms, notices, derived/shared nodes, and export contents before
redistribution. Override the default candidate set only deliberately with
`--public-sources SOURCE ...`; conditional or unresolved sources are not
automatically included.

```bash
python export_csv.py --step all --public-candidate
```

## Use cases

[docs/USE_CASES.md](docs/USE_CASES.md) describes ten runnable use cases built around the trusted-knowledge-layer role: safety-aware exercise lookup, explain-this-path, review-queue triage, a gait concept resolver, coverage audits and more. Every query returns provenance (`review_status`, `confidence`, `method`). Run them with `python use_cases.py`; `python eval/run_gold.py --category usecase` checks the data they depend on. Results are research candidates, not clinical advice.

## Dashboard

Install the dashboard dependencies from `dashboard/requirements.txt`, ensure the dashboard process can read the Neo4j settings in `.env`, and run:

```bash
python -m pip install -r dashboard/requirements.txt
python -m streamlit run dashboard/app.py
```

Open <http://localhost:8501>. Browser end-to-end tests require Playwright and Chromium in addition to a running dashboard and Neo4j service:

```bash
python -m pip install playwright pytest-playwright
python -m playwright install chromium
python -m pytest tests/test_e2e.py -v
```

## Tests

The fast offline checks need no Neo4j service:

```bash
python -m pytest tests/ -q --ignore=tests/test_e2e.py --ignore=tests/test_graph.py
```

Some data-dependent tests skip when their ignored source files are absent. Graph tests (`tests/test_graph.py`) require a populated Neo4j instance. Dashboard E2E tests require Neo4j, Streamlit, Playwright, and Chromium.

## Current graph snapshot

The graph rebuilt on 2026-11-17 with the bulk pipeline has **153,069 nodes** and **147,691 relationships**; 117,005 of those are `SUBCLASS_OF` ontology hierarchy edges that the bulk build loads. The earlier 2026-11-05 focused Cypher refresh had 107,436 relationships without them. Composition is vocabulary-heavy: **143,128 vocabulary/ontology nodes (93.5%)**, **9,915 dataset/clinical nodes (6.5%)**, and **26 schema nodes**. It is a snapshot, not a guaranteed count for every installation. See `eval/snapshot_report_2026-11-17.md` (earlier: `eval/snapshot_report_2026-11-05.md`) and `eval/public_ontology_refresh_manifest.json` (still the Nov 6 focused-refresh manifest), or run `python scripts/graph_composition.py` against the connected graph. Use `python rehabkg.py --status` for live counts.

## Project layout

```text
rehabkg.py                  Unified graph loading pipeline
download_data.py         Downloads configured ontology/exercise source files
etl_ontologies.py        Core ontology ETL and ontology bridges
etl_datasets.py          Curated assessment/dataset metadata ETL
etl_motu.py              MOTU patient/stay/outcome ETL
import_ontologies.py     Mondo and Uberon loading and mappings
add_additional_data.py   HPO and expanded clinical-trial ETL
build_csvs.py            Build bulk-import CSVs without Neo4j
import_bulk.py           Neo4j bulk import orchestration
dashboard/app.py         Streamlit dashboard
tests/                   Offline, graph, data, and browser E2E tests
docs/                    Setup, data source, use case, and architecture guides
```

## Data and licensing

Source datasets and ontologies have their own terms. Review [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) and the source license before redistributing or using data commercially. This repository's code is licensed under the MIT License — see [LICENSE](LICENSE).
