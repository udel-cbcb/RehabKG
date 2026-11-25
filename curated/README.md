# Curated clinical edges

This directory holds the **curated, review-tracked** parts of RehabKG.
These CSVs are the only place where condition→exercise recommendations
and safety statements enter the graph — Git is the system of record;
clinicians never need to touch Git or the database directly.

## Files

| File | Edge types | Purpose |
|------|-----------|---------|
| `condition_exercise.csv` | `RECOMMENDS_EXERCISE` | Condition → exercise recommendations, grouped by keyword match |
| `safety_contraindications.csv` | `PRECAUTION`, `CONTRAINDICATION` | Exercise safety statements (fall risk, fracture, …) |
| `condition_icd10_overrides.csv` | (Condition property) | Curated condition-name → ICD-10 code bindings; feeds `Condition.icd10_code` before the `match_type=icd10` rows bind |
| `observation_seed.csv` | `Observation` nodes + `MAPS_TO_ICF` | Synthetic gait-pilot demonstration observations (labeled `source=synthetic_demo`) |
| `scale_identifiers.csv` | (AssessmentScale properties) + `MAPS_TO_ICF` | External identifier register for the 40 RMD scales: LOINC / ICF / source URL per scale (all identifier cells ship **empty** — see HUMAN INPUT below) |
| `icf_core_sets.csv` | `HAS_CORE_SET_CATEGORY` | Header-only template for source-backed ICF Core Set categories; do not populate until redistribution terms are checked |

## Column contract

`condition_exercise.csv`:
`match_type, condition_key, exclude_keywords, exercise_name, category,
rationale, citation, reviewed_by, status, citation_doi, citation_pmid,
evidence_level, population, reviewed_on`

`safety_contraindications.csv` adds a leading `rel_type` column
(`PRECAUTION` or `CONTRAINDICATION`).

`icf_core_sets.csv` columns:
`core_set, condition_key, icf_code, component, source_url, review_status,
reviewed_by, reviewed_on`. The committed file is intentionally header-only.
Category lists are HUMAN INPUT from ICF Research Branch publications, and
redistribution terms must be confirmed before adding their contents. The
loader only creates exact condition-name matches and stamps every edge as
`method=curated`, `match_type=icf_core_set_register`,
`review_status=unreviewed`.

Key fields:

- `match_type` — how the row binds to graph conditions:
  - `keyword_group`: `condition_key` is a `;`-separated list of
    whole-word keywords; a row applies to every Condition whose name
    matches any keyword. `exclude_keywords` (also `;`-separated) removes
    false positives such as `stroke` matching `heat stroke`. Include
    plural/derived variants explicitly (for example `fracture` and
    `fractures`) because the match is whole-word.
  - `icd10`: matches on `Condition.icd10_code` (exact, one code per
    row). That property is populated by the shared
    `bridges.set_condition_icd10_codes` step before this loader runs:
    exact (case-insensitive) name matches against a coded Mondo disease
    (`icd10_source='mondo_exact_name'`), or the curated register below
    (`icd10_source='curated_override'`). The resulting edges are stamped
    `match_type=icd10_via_mondo` / `icd10_override` at `confidence=0.7`
    (not 1.0 — the code binding may be exact while the exercise
    recommendation itself is still an unreviewed seed).
  - `condition_icd10_overrides.csv` (register, not an edge file): one
    `condition_name,icd10_code` binding per row with `source`,
    `rationale`, `review_status` (must be `unreviewed` until a
    `reviewed_by` is recorded), `reviewed_by`, `reviewed_on`. Overrides
    always overwrite propagated codes; names matching no Condition are
    warned, and the live liveness test enforces presence on the
    canonical graph. Laterality caveats (e.g. Z96.641 is right-hip
    specific) belong in the `rationale` for reviewers.
- `scale_identifiers.csv` (register, not an edge file — Phase 2):
  `scale_id, name, loinc_code, loinc_long_name, icf_codes, source_url,
  review_status, reviewed_by, reviewed_on`. One row per `RMD_SCALES`
  scale (`scale_id` + `name` prefilled, mirror-tested against
  `etl_datasets.RMD_SCALES`). Loaded by the shared
  `bridges.apply_scale_identifiers` on **both** paths; it keys on
  `scale_id`, writes only **non-empty** cells (so an all-empty register
  loads idempotently with zero writes), and `icf_codes`
  (`;`-separated) additionally `MERGE`s `MAPS_TO_ICF` edges stamped
  `method=curated, match_type=scale_icf_register, confidence=1.0` with the
  row's `review_status`/`reviewed_by`/`reviewed_on`/`source_url`.
  - **HUMAN INPUT**: `loinc_code` / `loinc_long_name` / `source_url` must
    be looked up from the official LOINC distribution (free account) —
    never infer codes from memory. Cell format is enforced by
    `tests/test_bridges.py::TestScaleIdentifiersCSV` (LOINC `\d{1,6}-\d`,
    ICF `[a-z]\d{2}[0-9a-z]*`, URLs http(s)).
  - Unknown `scale_id`s or ICF codes warn instead of failing, so a
    partial fill never blocks a load.
- `exercise_name` — must match a real `Exercise.name` in the graph
  (Free Exercise DB catalog names, prefix match). Non-matching rows are
  dead rows and are rejected by the `TestCuratedCsvLiveness` live-graph
  test — check names against the dashboard Exercises page first.
- `status` — `unreviewed` (default), `approved`, or `rejected`.
  **Rows without a citation must remain `unreviewed`** (enforced by
  `tests/test_bridges.py`).
- `citation` / `citation_doi` / `citation_pmid` — evidence backing the
  row. Required for approval.
- `evidence_level`, `population`, `reviewed_by`, `reviewed_on` — review
  metadata carried onto the graph edge.

## Provenance mapping

Every row becomes edges stamped with the shared contract
(`provenance.py`):

| CSV field | Edge property |
|-----------|--------------|
| (loader) | `method='curated'` |
| `match_type` | `match_type` (`keyword_group` verbatim; `icd10` rewritten to `icd10_via_mondo`/`icd10_override` via `provenance.icd10_edge_props`) |
| `rationale` | `rationale` |
| `citation` | `citation` |
| `status` | `review_status` |
| (loader) | `source='curated/<file>.csv'` |
| keyword match | `confidence=0.6` (`KEYWORD_GROUP_CONFIDENCE`) + `curation_basis='keyword_group'` |
| icd10 match | `confidence=0.7` (`ICD10_BIND_CONFIDENCE`) + `icd10_code` |
| (loader, icd10) | `icd10_source` on Condition: `mondo_exact_name` / `curated_override` |

Register edges (`scale_identifiers.csv` → `MAPS_TO_ICF`) use the same
contract with `match_type='scale_icf_register'`, `confidence=1.0`,
`source='curated/scale_identifiers.csv'`, and `review_status` from the
row. AssessmentScale property writes (`loinc_code`, `loinc_long_name`,
`source_url`) carry no per-property provenance — they are flagged by
`review_status`/`reviewed_by`/`reviewed_on` on the register row itself.

## Review workflow

1. Browse unreviewed edges on the dashboard's **✅ Evidence & Review**
   page (or open the CSVs directly).
2. Download the decisions template from that page; fill `decision`
   (`approved`/`rejected`), `reviewed_by`, `reviewed_on`, and `citation`
   (required for approvals).
3. Apply:

   ```bash
   python curated/apply_decisions.py review_decisions.csv --update-graph
   ```

   Unknown rows are refused with a non-zero exit; `--dry-run` previews;
   `--update-graph` syncs the live database immediately (no full
   reimport needed).

## Notes on specific rows

- **DVT contraindication row was removed (2026-10-22)**: there is no
  DVT Condition node in the graph, so the row was a dead row (exercise
  names also did not exist in Free Exercise DB). Re-add it together
  with a DVT condition source if one lands.
- **Fracture contraindication** remains: it matches several fracture
  conditions. Its rationale still mentions DVT phrasing from the seed —
  reviewers should rewrite it via the decisions `comment` field or a
  direct CSV edit in the same PR as their citation.
- **Stroke fall-risk precaution rows** are seed rows for the stroke-gait
  pilot: impaired balance in hemiplegia raises fall risk on static
  single-leg stance. They explicitly request supervision/guarding
  language review.
- **Dead-row audit (2026-10-22)**: 18 recommendation rows + 3 safety
  rows referenced exercises absent from Free Exercise DB (e.g. "Bird
  Dog", "Tandem Stance") and were remapped to real catalog names
  (Plank, Single-Leg Balance, Walking Treadmill, …). Keep names in sync
  with the catalog; the liveness test enforces it.
