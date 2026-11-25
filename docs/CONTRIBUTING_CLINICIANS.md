# Contributing as a clinician reviewer

Thank you for reviewing RehabKG's curated clinical edges. This guide is
for clinicians and clinical researchers — **no Git, SQL, or Cypher
required**.

## What you are reviewing

RehabKG contains rule-generated and curated edges. Your job is the
**curated** ones — condition→exercise recommendations and safety
statements (precautions/contraindications) in `curated/*.csv`. Each one
is a *candidate* until you approve it. Everything unreviewed is labeled
as such on every API/dashboard surface.

You may also audit sampled machine-generated edges (HPO→ICF bridges,
trial keyword matches) exported by
`scripts/sample_edges_for_audit.py` — feedback on those goes back to the
maintainers as issues or PRs.

## The 10-minute review loop

1. **Open the dashboard**:

   ```bash
   streamlit run dashboard/app.py
   ```

   Navigate to **✅ Evidence & Review**.

2. **Read the unreviewed tables** (recommendations, precautions,
   contraindications), or open the CSVs directly:
   `curated/condition_exercise.csv`, `curated/safety_contraindications.csv`.

3. **Download the decisions template** from the page (one row per
   curated row). Fill only:

   | Column | Meaning |
   |--------|---------|
   | `decision` | `approved` or `rejected` (leave blank to skip) |
   | `reviewed_by` | Your name |
   | `reviewed_on` | Date, `YYYY-MM-DD` |
   | `citation` | DOI/PMID/URL of the evidence (**required to approve**) |
   | `comment` | Optional note for maintainers |

4. **Apply your decisions** (ask a maintainer if you don't have shell
   access — they run exactly this):

   ```bash
   python curated/apply_decisions.py review_decisions.csv --update-graph
   ```

   Rows with unknown keys are refused loudly; nothing is silently
   skipped. `--dry-run` previews without writing.

## Review guidance

- **Recommendations** (`RECOMMENDS_EXERCISE`): Is the exercise a
  plausible option for at least some patients with this condition?
  Approving means "reasonable candidate to offer under supervision",
  not "universally indicated".
- **Precautions** (`PRECAUTION`): Would a competent therapist modify
  supervision, screening, or setup before this exercise? Stroke
  fall-risk rows (e.g. single-leg stance in hemiplegia) are the pilot
  set.
- **Contraindications** (`CONTRAINDICATION`): Is there a hard reason to
  withhold the exercise for the stated condition (e.g. weight-bearing
  restrictions after fracture)?
- **Evidence**: approvals need a citation (DOI, PMID, guideline URL, or
  textbook edition). If you cannot cite it, leave it unreviewed or
  reject with a comment — the graph will show it as unreviewed, which is
  the honest state.
- **Rationales**: seed rationales are placeholders; suggest better text
  in the `comment` field and maintainers will fold it in.

## Safety and scope

- This graph is a **research prototype**, not a clinical decision
  support system. Approved edges mean "reviewed as plausible", not
  "validated care pathway".
- MOTU patient data and observation seeds are synthetic/de-identified
  demo data.
- If you find an edge that could cause harm if trusted, reject it and
  open an issue titled `SAFETY:` — maintainers prioritize those.

## Questions

Open an issue at https://github.com/udel-cbcb/RehabKG or contact the
maintainers (CBHB lab, University of Delaware).
