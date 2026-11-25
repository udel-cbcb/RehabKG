# Add a BioPortal ontology to RehabKG

Follow this checklist for each new ontology. The 2026-10 shortlist additions
(TRAK…PHENX) all landed this way; copy an existing ontology's wiring as a
template (MSO = simple path, CBHA = custom individuals path). These loaders
remain structural templates; their ontologies are not part of the focused
2026-11-05 graph.

## 0. Pin the download

1. Find the latest submission: `GET https://data.bioontology.org/ontologies/{ACR}/submissions`
   (any key works; `.env` `BIOPORTAL_API_KEY` for repeat use). Note `submissionId`,
   `version`, `released`.
2. Download once with curl to `data/ontologies/{name}.owl` (gitignored) and
   check the serialization: RDF/XML → `format="xml"`, OWL/XML → xml.etree
   fallback, Turtle → `format="turtle"`. Count `owl:Class` / labels.
3. Add a pinned entry to `download_data.py` (URL form:
   `.../ontologies/{ACR}/submissions/{N}/download?apikey={BIOPORTAL_API_KEY}`).

## 1. Extract + load (etl_ontologies.py)

1. Constant `{NAME}_OWL = HERE / "data" / "ontologies" / "{name}.owl"`.
2. Extractor:
   - Simple class hierarchy → `extract_simple_ontology({NAME}_OWL, "{NAME}")`.
     OWL/XML files rdflib cannot parse (MSO) already work via the xml.etree
     fallback with xml:base resolution — verify codes are absolute URIs.
   - Named individuals with annotations (Compendium-style) → custom extractor
     modeled on `extract_cbha` (detect subjects via the annotation property).
3. Loader: simple path → `load_simple_ontology(session, ..., "{NAME}Concept", "{name}.owl")`
   (MERGEs by `code`, idempotent). Custom path → model on `load_cbha`.
4. Wire into `main()` before the `=== Bridges ===` block.

## 2. Bulk CSV path (build_csvs.py)

1. Add `(extract_{name}, "{name}Concept", "{ACR}")` to the generic loop —
   the `ns` argument namespaces `:ID` via `ontology_eid()` (short fragment
   codes collide across files in one neo4j-admin keyspace; CURIE codes like
   `TRAK:0000001` pass through).
2. Custom blocks (if any) modeled on the CBHA block: write node CSVs +
   rel CSVs with `:START_ID/:END_ID/:TYPE` columns.

## 3. Import + export plumbing

1. `import_bulk.py` LABEL_MAP: `"nodes_{name}concept": "{NAME}Concept"`.
2. `export_csv.py`: add the label to the node-export loop and `_ns_id` /
   `NS_LABELS` (so Cypher-path exports match bulk `:ID` namespacing).
3. `rehabkg.py` docstring ontology list.

## 4. Dashboard (dashboard/app.py)

1. `ontology_count` WHERE clause + `ontology_labels` set.
2. Ontologies-page table row.
3. Only add a selectbox browse branch if the ontology has a special shape
   (e.g. CBHA's MET-sorted activities); otherwise the generic label match
   branch is enough.

## 5. Tests (offline gate — must stay green)

1. `tests/test_ontology_extract.py` CASES entry:
   `(extract_{name}, "{name}.owl", min_concepts, min_edges)` — pick floors
   ~10-20% below the observed counts.
2. If curating cross-ontology bridges, put the table in `etl_ontologies.py`
   (module constant), mirror it in `build_csvs.py` as a rel CSV with hard
   asserts, and add a `TestCuratedBridges`-style test proving every source
   and target exists in the extracts.
3. Run: `python -m pytest tests/ -q --ignore=tests/test_e2e.py --ignore=tests/test_graph.py`

## 6. Docs

1. `docs/DATA_SOURCES.md`: concepts table row, download URL row, licensing
   row, note blurb.
2. `docs/BIO_PORTAL_CANDIDATES.md`: move the row from its tier to Section A
   shortlist (pinned submission URL), update the Totals line.
3. `README.md`: no table to update — it links `docs/DATA_SOURCES.md` for
   sources; only adjust README if the new ontology changes pipeline behavior
   worth calling out.

## 7. Validate

1. `python3 build_csvs.py` (full rebuild; assert-driven for curated bridges).
2. Bulk import: `docker stop neo4j-test-serve` → `python3 import_bulk.py
   --skip-export` (re-imports the CSVs from step 1, restarts the container,
   and runs post-load; the container must be stopped first for
   `neo4j-admin import` — the script does not stop it itself).
3. Live check: label counts match CSV row counts; spot-check one query.
4. Cypher-path idempotency: `python3 etl_ontologies.py` on the bulk graph,
   counts must not change.
5. Dashboard e2e (optional per-change, required before release):
   `python3 -m pytest tests/test_e2e.py -q` with the dashboard running.
