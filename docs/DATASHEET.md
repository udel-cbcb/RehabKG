# RehabKG Datasheet

Datasheet-style documentation for the Rehabilitation Knowledge Graph,
covering motivation, composition, collection, biases, intended and
non-intended uses, and maintenance. Companion documents:
[DATA_SOURCES.md](DATA_SOURCES.md) (per-source catalog + licenses),
[CONTRIBUTING_CLINICIANS.md](CONTRIBUTING_CLINICIANS.md) (review loop),
[../curated/README.md](../curated/README.md) (curated edge contract).

## Motivation

RehabKG was built for rehabilitation knowledge-discovery research: to
connect rehabilitation ontologies (ICF, PMR, STO, MSO, …), clinical
datasets (MOTU outcomes, ClinicalTrials.gov records), and therapeutic
exercise catalogs (Free Exercise DB) in one queryable graph — so that
cross-domain questions (functioning concepts ↔ exercises ↔ trial
endpoints) can be asked with plain Cypher.

## Composition and sources

The graph integrates (source counts from the November 5, 2026 focused graph, node totals confirmed on the November 17 rebuild; see
DATA_SOURCES.md for the full catalog and licenses). The 2026-11-17
rebuilt graph has **153,069 nodes** and **147,691 relationships** (117,005 are
`SUBCLASS_OF` hierarchy edges; the Nov 5 focused refresh had 107,436
without them); by layer that is
**143,128 vocabulary/ontology nodes (93.5%)**, **9,915 dataset/clinical
nodes (6.5%)**, and **26 schema nodes**. The headline node count is therefore
vocabulary-dominated and is not a dataset or cohort size.

- **Ontologies**: retained sources include ICF (functioning), HPO
  (phenotypes), Uberon (anatomy), Mondo (diseases), EXMO (exercise medicine),
  REHABO (rehabilitation), and PAIN. COPPER, KHMO, CBHA (activity compendium),
  and other flagged families were removed on 2026-10-27/2026-11-05 for
  unresolved hosting terms; see `docs/notes/ontology_removal_2026-10-27.md`.
- **Clinical data**: MOTU (1,006 synthetic/de-identified trans-femoral
  amputation rehabilitation patients with admission/discharge outcomes,
  e.g. Barthel index), 1,387 physical-rehabilitation clinical trial
  records from ClinicalTrials.gov, 92,694 ICD-10-CM code nodes.
- **Exercises**: 949 exercises from Free Exercise DB (Unlicense),
  with muscle/equipment linkage via Uberon.
- **Curated clinical edges**: `curated/condition_exercise.csv`
  (condition → exercise recommendations), `curated/safety_contraindications.csv`
  (precautions/contraindications), `curated/observation_seed.csv`
  (synthetic demonstration observations). All curated edges are
  **unreviewed candidates until a clinician approves them** through the
  dashboard review loop. `match_type=keyword_group` rows use whole-word
  matching, an optional `exclude_keywords` column, `confidence=0.6`, and
  `curation_basis=keyword_group`; `match_type=icd10` rows bind on the
  populated `Condition.icd10_code` at `confidence=0.7`. Keyword matching is
  recall-oriented and must not be read as exact condition identification.
- **Synthetic seed layer**: patient `SYNTHETIC-GAIT-001` with labeled
  gait-speed / 6MWT / step-count / Berg observations
  (`source='synthetic_demo'`). Exists for demonstration only; never
  mixed with MOTU patients.

## Collection and preprocessing

Ontologies are pulled from BioPortal/OBO sources by
`download_data.py` + `etl_ontologies.py`/`import_bulk.py`. MOTU CSVs are
staged under `data/raw/motu/` and loaded by `etl_motu.py`
(`value_numeric` numeric backfill for scales). Clinical trials come from
the ClinicalTrials.gov API. Graph construction, provenance stamping and
postload linking are documented in
[bulk-import-architecture.md](bulk-import-architecture.md); every edge
carries a provenance contract (`method`, `match_type`, `confidence`,
`source`, `review_status` — see `provenance.py`).

## Biases and known limitations

- **MOTU is a single-center amputation cohort** (birth years ~1921–1999,
  heavily male in the demo snapshot). Outcome patterns do not
  generalize to other populations.
- **Free Exercise DB is fitness-oriented**, not clinical: rehab-style
  names often have no match; curated rows use real catalog names and
  are flagged for review. Curated condition coverage is intentionally
  narrow (stroke-gait pilot first).
- **Keyword-group edges are name matches, not exact condition bindings.**
  Whole-word matching and `exclude_keywords` reduce false positives (for
  example, `stroke` excludes `heat stroke`), but plural/derived variants
  must be listed explicitly and all matches remain unreviewed candidates.
- **HPO→ICF and trial→ICF links are rule-based loose matches** stamped
  with low confidence (≤ 0.4) and are explicitly *not* clinician
  validated.
- **ICD-10 linkage arrives via Mondo** (`HAS_ICD10` edges) and,
  since the Phase 1 Gate 0 policy, `Condition.icd10_code` is populated
  only by exact (case-insensitive) name matches against coded Mondo
  diseases (`icd10_source='mondo_exact_name'`) or the curated register
  `curated/condition_icd10_overrides.csv` (`icd10_source='curated_override'`).
  Curated `match_type=icd10` rows bind on this property at
  `confidence=0.7` with `match_type=icd10_via_mondo`/`icd10_override`;
  all such bindings are `review_status=unreviewed` candidates.
- **English-only** curated text; trial titles and ontologies skew toward
  English-language publications.
- Safety edges (precautions/contraindications) are **seed rows awaiting
  clinician review and citation** — they illustrate the review workflow,
  they are not a safety authority.

## Intended uses

- Research on rehabilitation knowledge graphs, graph-based retrieval,
  and human-in-the-loop curation.
- Teaching/demo of ontology integration and provenance-aware ETL.
- Pilot evaluation of clinician review workflows (HAIC pilot).

## Non-intended uses

- **Clinical decision support or patient care of any kind.** The data is
  not a medical device, not validated for care pathways, and unreviewed
  edges are research candidates only.
- Treating unreviewed or rule-based edges as expert consensus.
- Re-identifying or contacting MOTU individuals (synthetic/de-identified
  demo data).
- Redistribution of source datasets in violation of their licenses
  (several BioPortal ontologies are academic-use; see the license table
  in DATA_SOURCES.md).

## Maintenance

Maintained by the CBHB lab (UD) at
https://github.com/udel-cbcb/RehabKG. Graph rebuilds are reproducible
from `import_bulk.py`; curated decisions live in Git (system of record).
Review decisions are applied via `curated/apply_decisions.py`.
Issues and clinician contributions: see
[CONTRIBUTING_CLINICIANS.md](CONTRIBUTING_CLINICIANS.md).

*Last updated: 2026-10-27*
