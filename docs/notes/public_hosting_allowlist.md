# Proposed public-hosting allowlist (review required)

This is a **proposal**, not a permission determination. It was prepared before
the subsequent user-directed live graph cleanup. The earlier “14” figure was not a
verified allowlist and should not be used as an automatic filter.

## Clearer candidates to include, subject to attribution

| Source | Live nodes¹ | License / source terms to inspect | Review notes |
|---|---:|---|---|
| REHABO | 310 | [Local staged `rehabo.owl`](../../data/ontologies/rehabo.owl) · [BioPortal REHABO](https://bioportal.bioontology.org/ontologies/REHABO) · [CC0 deed](https://creativecommons.org/public-domain/cc0/) | Local file declares CC0; included in the focused ontology refresh. |
| EXMO | 220 | [Local staged `exmo.owl`](../../data/ontologies/exmo.owl) · [EXMO GitHub repository](https://github.com/Exercise-Medicine-Ontology/EXMO) · [CC BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode) | Staged OWL explicitly declares CC BY 4.0 and version `2025-06-05`; included in the focused refresh. `exmo_new.owl` is not the file the loader uses. |
| COPPER | 362 (pre-refresh) | [Local staged `copper.owl`](../../data/ontologies/copper.owl) · [upstream repository](https://github.com/EBehaviourChange-COPPER/ontology) | **No license annotation found** in the staged `copper.owl` (the grep match was only from `exmo_new.owl`). The upstream current `COPPER.owl` also showed no visible license annotation. Excluded from the focused ontology refresh pending explicit terms from maintainers; do not assume CC BY 4.0. |
| Mondo | 5,000 | [Local staged `mondo.owl`](../../data/ontologies/mondo.owl) · [Mondo license and reuse information](https://mondo.monarchinitiative.org/pages/license/) · [CC BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode) | Local file declares CC BY 4.0; included in the focused ontology refresh. |
| Uberon | 10,000 | [Local staged `uberon.owl`](../../data/ontologies/uberon.owl) · [Uberon GitHub repository](https://github.com/obophenotype/uberon) | Included in the focused refresh at user direction. Local file has both CC BY 3.0 and CC BY 4.0 annotations; distinguish ontology-level from imported-term annotations and follow applicable attribution. |
| PAIN | 623 | [Local staged `pain.owl`](../../data/ontologies/pain.owl) · [PAIN GitHub repository](https://github.com/obophenotype/pain-ontology) · [CC BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode) | Local file declares CC BY 4.0; included in the focused ontology refresh. |
| KHMO | 1,753 (pre-refresh) | [Local staged `khmo.owl`](../../data/ontologies/khmo.owl) · [KHMO GitHub repository](https://github.com/KHMOntology/KHMO) · [CC BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode) | Local file declares CC BY 4.0 at ontology level and is versioned `2026-02-10`; it also has annotations on imported terms, including CC BY 3.0. Excluded from focused refresh pending per-term provenance review. |
| Free Exercise DB | 902 | [Free Exercise DB GitHub repository](https://github.com/yuhonas/free-exercise-db) · [repository license file](https://github.com/yuhonas/free-exercise-db/blob/main/LICENSE) | Upstream README says Unlicense; exclude image assets unless separately cleared. |
| synthetic_demo | 7 | [Project-generated demo data](../../README.md) | Project-created; keep separate from MOTU and retain the explicit synthetic source label. |

¹ These are historical pre-cleanup counts from the audit snapshot, not current
live counts. The source set and available files can change.

**Subtotal: 19,778 source-labeled nodes (historical).** This is a source-labeled subtotal,
not a complete safe-public graph: shared/derived nodes and relationship
endpoints still need provenance/licence filtering.

## Conditional; include only after compliance checks

- [ClinicalTrials.gov](https://clinicaltrials.gov/data-api/about-api): prefer factual fields and source links;
  review current API terms and contributed record text.
- MOTU (6,183 nodes): confirm exact CC BY 4.0 release, attribution, and
  de-identification documentation. Check [Zenodo search for MOTU rehabilitation](https://zenodo.org/search?q=MOTU%20rehabilitation) and verify the exact package record before use.
- [CDC ICD-10-CM](https://www.cdc.gov/nchs/icd/icd-10-cm/index.html) (92,694 nodes): public-domain status is jurisdiction-specific;
  verify for the intended service regions and exact release.
- [Human Phenotype Ontology](https://hpo.jax.org/app/license) (32,772 nodes): check imported third-party vocabularies and preserve
  notices/version.
- [WHO ICF / ICD-11 classification platform](https://icd.who.int/) · [WHO copyright and licensing](https://www.who.int/about/policies/publishing/copyright) · [CC BY-ND 3.0 IGO legal code](https://creativecommons.org/licenses/by-nd/3.0/igo/): **user-confirmed terms** for core ICF classification and standard digital formats permit commercial and non-commercial use, require no adaptations, require WHO attribution, and prohibit implying WHO endorsement. The local `icf.owl` has no license annotation; confirm that this exact BioPortal OWL snapshot is covered and whether graph transformation (labels/properties/bridges) constitutes a prohibited adaptation before public release.
- [Open Rehab Exercises source search](https://github.com/search?q=%22Open+Rehab+Exercises%22&type=repositories) (76) and [Rehabilitation Measures Database](https://www.sralab.org/rehabilitation-measures) (40 scales): confirm exact archive/database terms for the staged data and text; web access is not redistribution permission.
- Any LOINC-derived scale fields: publish only with the required online notice,
  code and display name, and third-party terms. See [LOINC terms](https://loinc.org/license/) and [LOINC FAQ](https://loinc.org/license/). Do not publish the raw LOINC package by default.

## Exclude pending permission / verification — links to check

For BioPortal ontologies, inspect both the ontology page and the **exact loaded
submission's** license/metadata. A generic project or repository license may
not cover imported third-party terms.

| Source | License / submission to inspect | Current blocker |
|---|---|---|
| PMR | [BioPortal PMR](https://bioportal.bioontology.org/ontologies/PMR) | Exact loaded submission and license not verified. |
| MELLO-D | [BioPortal MELLO-D](https://bioportal.bioontology.org/ontologies/MELLOD) | Exact loaded submission and license not verified. |
| OPE | [BioPortal OPE](https://bioportal.bioontology.org/ontologies/OPE) | Exact loaded submission and license not verified. |
| PHY | [BioPortal PHY](https://bioportal.bioontology.org/ontologies/PHY) | Exact loaded submission and license not verified. |
| ONTOLOCO | [BioPortal ONTOLOCO](https://bioportal.bioontology.org/ontologies/ONTOLOCO) | Exact loaded submission and license not verified. |
| TRAK | [BioPortal TRAK](https://bioportal.bioontology.org/ontologies/TRAK) | Submission license and third-party imports not verified. |
| FRMO | [Local staged `frmo.owl`](../../data/ontologies/frmo.owl) · [BioPortal FRMO](https://bioportal.bioontology.org/ontologies/FRMO) · [CC0 1.0 deed](https://creativecommons.org/publicdomain/zero/1.0/) | Local file declares CC0 1.0 and names Fatimah Altuhaifa in `dc:rights`; still verify it is the loaded release and review imported content. |
| BCIO | [BioPortal BCIO](https://bioportal.bioontology.org/ontologies/BCIO) | Submission license and imported content not verified. |
| BCTT | [BioPortal BCTT](https://bioportal.bioontology.org/ontologies/BCTT) | Exact submission license not verified. |
| STO | [Local staged `sto.owl`](../../data/ontologies/sto.owl) · [BioPortal STO](https://bioportal.bioontology.org/ontologies/STO) · [CC BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode) | Local file explicitly declares CC BY 4.0; verify exact loaded revision and imported content. |
| PACO | [Local staged `paco.owl`](../../data/ontologies/paco.owl) · [BioPortal PACO](https://bioportal.bioontology.org/ontologies/PACO) · [CC BY 3.0 legal code](https://creativecommons.org/licenses/by/3.0/legalcode) | Local file's `rdfs:license` says Creative Commons Attribution 3.0; verify exact submission and attribution details. |
| MSO | [BioPortal MSO](https://bioportal.bioontology.org/ontologies/MSO) | Submission license/imports not verified. |
| POEM | [BioPortal POEM](https://bioportal.bioontology.org/ontologies/POEM) | Submission license and third-party terms not verified. |
| PHENX | [BioPortal PHENX](https://bioportal.bioontology.org/ontologies/PHENX) | Submission license and toolkit terms not verified. |
| NIHSS | [Local staged `nihss.owl`](../../data/ontologies/nihss.owl) · [BioPortal NIHSS](https://bioportal.bioontology.org/ontologies/NIHSS) · [CC BY-NC 4.0 legal code](https://creativecommons.org/licenses/by-nc/4.0/legalcode) | Local file explicitly declares CC BY-NC 4.0. Exclude from commercial hosting; verify exact loaded revision and other terms. |
| ACVD | [BioPortal ACVD](https://bioportal.bioontology.org/ontologies/ACVD) · [local staged source](../../data/ontologies/acvd.owl) | Version and license are unverified; do not redistribute pending review. |

The Keraal local archive is not in Neo4j and is not assessed. Find its source
record via [Zenodo search](https://zenodo.org/search?q=Keraal%20Kinect); confirm
that this is the exact archive before relying on its terms.

Full source-by-source notes are in `docs/notes/data_hosting_license_audit.md`;
the machine-readable proposal is `docs/notes/proposed_public_sources.csv`.

The live graph now excludes the explicitly removed ontology sources. This
proposal remains a licensing screening only; do not use it as an automatic
allowlist until conditional sources, shared nodes, relationships, and notices
have been reviewed. Any public export should filter both nodes and
relationships and validate every endpoint.

## Focused ontology refresh (2026-11-05)

The user authorized a focused replacement on the configured local Neo4j graph
using `data/ontologies/`. Intended inclusion: REHABO, ICF, EXMO, PAIN, Mondo,
and the existing 10,000 named-class Uberon subset. Intended exclusions/removal:
COPPER, KHMO, CBHA (including its Compendium activity nodes), NIHSS, and the
other flagged ontology families. HPO and all clinical/dataset records are to be
retained. The refresh rebuilds selected ICF/Mondo/Uberon/REHABO/EXMO, HPO, and
assessment-scale bridges; it does not certify that every included source is
legally cleared for redistribution. See
`eval/public_ontology_refresh_manifest.json` for file hashes and final counts.

Post-run review: the replacement completed on `bolt://localhost:7688` and
removed all excluded-source nodes while retaining clinical/dataset nodes. The
first bridge pass left HPO unbridged; after inspection, the user authorized
restoring HPO from the staged `hp.owl` file and only the nine explicit
HPO-code→ICF-code mappings in the existing loader (not the broad
name-containment matcher). The follow-up completed: 32,772 HPO nodes are
present, with 9 `RELATED_TO_ICF` edges and all 9 carrying curated,
`explicit_code_pair`, confidence 1.0, `review_status=unreviewed` provenance.
Final live verification on `bolt://localhost:7688`: 153,069 nodes, 107,436
relationships, zero nodes from excluded ontology labels, 1,006 patient-stay
edges, and 4,024 outcome-scale edges. Full counts and source hashes are in
`eval/public_ontology_refresh_manifest.json`.

The focused graph has zero synthetic Observation→ICF links after ontology
refresh. The synthetic observation nodes remain, but do not assume an ICF
mapping until explicit seed edges are restored and provenance-validated.

The standard Cypher and bulk build entry points were updated after this live
snapshot to use the focused source set and default-source bridge policy. The
initial live run used an earlier helper that needed manual HPO recovery; the
current helper retains HPO and is covered by the deterministic E2E test. Full
Cypher-vs-bulk parity remains pending.

The refresh script was corrected after the live run to retain HPO and record
the staged HPO hash. Its deletion counters were collected in the same
transaction as recreations and therefore are net transaction counters, not
standalone deletion counts. The initial live run removed HPO/bridge edges;
recovery was performed manually and verified above. Do not use the manifest's
zero edge-deletion counters as evidence that no relationships were deleted.

**Update (2026-11-06):** Cypher-vs-bulk parity is now verified for the focused
snapshot by `tests/test_bulk_parity.py` and `eval/bulk_parity_baseline.json`
(node/label/source counts, bridge/clinical relationships, and gold 35/35).
