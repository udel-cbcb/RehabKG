# Data and ontology hosting/licence audit

**Checked:** 2026-10-27 · **Scope:** current source-labeled Neo4j inventory,
current repo source/licence notes, and public source terms that could be
verified. This is an operational screening, not legal advice.

## Bottom line

“Publicly downloadable” is not the same as “may be republished in a hosted
graph.” The graph mixes permissively licensed content, source terms needing
verification, and derived records. A public instance should not expose the
whole graph until the flagged sources below have been reviewed and required
notices/access controls are in place. In particular, do not publish ACVD,
LOINC-derived values without the required LOINC notice, or any data derived
from restricted sources.

## Live Neo4j inventory checked

Connected read-only to `bolt://localhost:7688` on 2026-10-27 before removal. Distinct
`n.source` values observed: CDC ICD-10-CM April 2025; ClinicalTrials.gov and
expanded ClinicalTrials.gov; Free Exercise DB; HPO; MOTU; Open Rehab Exercises;
RMD; ACVD; BCIO; BCTT; CBHA; COPPER; EXMO; FRMO; ICF; KHMO; MELLO-D; Mondo;
MSO; NIHSS; ONTOLOCO; OPE; PACO; PAIN; PHENX; PHY; PMR; POEM; REHABO; STO;
synthetic_demo; TRAK; Uberon. ACVD was present live with 1,719 nodes. The graph
also contains 40 AssessmentScale nodes and 18 non-empty LOINC identifier rows
from the curated register. Source count is not a licence assertion.

## Removal follow-up (2026-10-27)

At the user's request, 11 ontology sources categorized for exact-release
or third-party licence verification, plus ACVD, were removed from the live
graph. A source-preserving JSON backup is stored at
`deliverables/public-graph-removal-backup-2026-10-27.json`. Removed source
labels: MELLO-D, TRAK, FRMO, BCIO, BCTT, STO, PACO, MSO, POEM, PHENX, NIHSS,
ACVD. PMR, OPE, PHY, and ONTOLOCO remain loaded, with terms still requiring
verification. Their incident relationships were removed too;
the cleanup was verified at zero remaining flagged-source nodes and zero
incident relationships. No dataset source was removed. This code/doc follow-up
updates rebuild paths so these ontologies are not silently reloaded.

## Local OWL annotation check (2026-11-05)

The staged files under `data/ontologies/` were checked for ontology-level
`license`/`rights` annotations. These annotations are useful evidence for the
specific staged file, but do not automatically clear imported third-party
content or prove that the live graph contains that exact revision.

| Staged file | License annotation observed | Notes |
|---|---|---|
| `exmo.owl`, `exmo_new.owl` | CC BY 4.0 | `terms:license` points to `creativecommons.org/licenses/by/4.0/`. Verify which file/revision was loaded. |
| `icf.owl` | No explicit license annotation found | User identifies this as the latest BioPortal file and supplied WHO ICF CC BY-ND 3.0 IGO terms; exact snapshot coverage and adaptation implications remain for user/legal confirmation. Included in the focused 2026-11-05 refresh at user direction. |
| `copper.owl` | No license annotation found | The initial combined grep output was from `exmo_new.owl`, not `copper.owl`; do not treat it as COPPER evidence. COPPER was excluded from the focused 2026-11-05 ontology refresh. Request explicit terms from the maintainers. |
| `frmo.owl` | CC0 1.0 | `terms:license` points to the Creative Commons public-domain dedication; author is named in `dc:rights`. |
| `hp.owl` | HPO license page | `dcterms:license` points to <https://hpo.jax.org/app/license>; imported vocabularies still need review. |
| `khmo.owl` | CC BY 4.0 at ontology level | Also contains license annotations on imported terms (including CC BY 3.0 and CC BY 4.0); inspect term provenance before redistribution. |
| `mondo.owl` | CC BY 4.0 | `terms:license` points to CC BY 4.0; preserve attribution and review the exact release. |
| `nihss.owl` | CC BY-NC 4.0 | Explicit `cc:license`/`dcterms:license`; non-commercial restriction means exclude from commercial hosting. |
| `paco.owl` | CC BY 3.0 | `rdfs:license` text says “Creative Commons Attribution 3.0”; check source and attribution details. |
| `pain.owl` | CC BY 4.0 | `terms:license`; check imported content. |
| `rehabo.owl` | CC0 | `dcterms:license` points to a CC0 public-domain URL. |
| `sto.owl` | CC BY 4.0 | `dc:license` text and license link are explicit. |
| `uberon.owl` | Mixed CC BY 3.0 / CC BY 4.0 annotations | Multiple values occur in the file; distinguish ontology-level from imported-term annotations and preserve source-specific attribution. |

The user directed that the local Uberon file be included in the focused
ontology refresh using the existing loader's 10,000 named-class subset, despite
the mixed imported-term annotations. This records the scope decision only;
per-term applicability and attribution remain unresolved.

The deterministic focused 2026-11-05 refresh completed on `bolt://localhost:7688`.
The graph contains the selected staged files and 32,772 HPO nodes. The final
node/relationship counts and source-file SHA-256 values are recorded in
`eval/public_ontology_refresh_manifest.json`; zero nodes remain for the
excluded ontology labels. The live `neo4j` store was later loaded from a dump of
the disposable E2E `test` database, and the post-load snapshot matches the E2E
result. This is an operational snapshot, not legal clearance.

The user reports that WHO's core ICF classification and standard digital
formats are licensed CC BY-ND 3.0 IGO: commercial and non-commercial use is
allowed, adaptations are prohibited, WHO attribution is required, and WHO
endorsement must not be implied. This is recorded as user-provided licensing
information, not independently confirmed for the local BioPortal `icf.owl`
snapshot. Verify snapshot coverage and whether RehabKG's extraction or graph
representation is an adaptation before public release.

This is a metadata inventory, not legal advice or a determination that the
entire merged graph is distributable. The proposed allowlist was updated with
the verified local-file observations where relevant.

## Ontologies / terminologies

| Sources | Hosting assessment | Notes / action |
|---|---|---|
| REHABO | **Likely okay** | Repo records CC0. Retain source attribution/provenance. |
| EXMO, COPPER, Mondo, Uberon, PAIN | **Likely okay with attribution** | Repo records CC BY 4.0 (PAIN OBO); preserve attribution/version and check for imported third-party terms in the exact release. |
| KHMO | **Likely okay with attribution** | Repo records CC BY 4.0; preserve attribution/version. |
| PMR, MELLO-D, OPE, PHY, ONTOLOCO | **Verify exact release terms** | Repo says open access, but no explicit licence in this audit for the loaded snapshots. Public BioPortal access alone is not a redistribution grant. |
| ICF | **Conditional / verify format terms** | WHO’s current policy identifies ICF as CC BY-ND 3.0 IGO for the ICD-11-platform classification and permits commercial/non-commercial use without adaptation, with citation. The actual BioPortal OWL snapshot’s applicable terms and modifications must be checked; do not assume every export is covered. |
| TRAK, FRMO, BCIO, BCTT, STO, PACO, MSO, POEM, PHENX, NIHSS | **Verify exact submission and third-party content** | Repo itself says academic or BioPortal-specific terms need verification. Record the exact submission/version, licence, required attribution, and imported content before public hosting. |
| ACVD | **Do not redistribute yet** | Live graph has 1,719 concepts, but source file version is user-reported, BioPortal submission is unpinned, and licence/duplicate review is unresolved. Keep private/restricted until cleared. |
| HPO | **Likely okay with attribution; check imports** | HPO is publicly released, but loaded file includes imported concepts (GO/CHEBI/UBERON etc.). Confirm each shipped component’s licence and preserve notices/version. |
| NIH ICD-10-CM | **Likely okay in US, with jurisdiction caveat** | Repo identifies CDC release as public domain. Verify non-US jurisdictions and any non-US national modifications before global service. |
| LOINC values on AssessmentScale | **Host only with compliance notice and field rules** | Local LOINC 2.83 licence permits commercial/non-commercial distribution subject to conditions. For online service the LOINC notice must be accessible in terms/license; extracted info must retain LOINC ID and display name; comply with third-party notices and restrictions. The current app has no LOINC notice surfaced (code search found none): add it before public exposure, or remove LOINC names/codes from the public graph until compliant. |

## Datasets / non-ontology sources

| Sources | Hosting assessment | Notes / action |
|---|---|---|
| Free Exercise DB | **Likely okay** | Upstream README identifies Unlicense/public domain. Preserve source attribution; review image/content third-party notices if including images (graph appears to hold records, not image assets). |
| ClinicalTrials.gov (base + expanded) | **Generally public facts/records; verify API terms and third-party text** | Registration data are publicly accessible, but records may contain copyrighted descriptions and links. Host factual fields with source/citation; check current API terms and avoid assuming every contributed text field is unrestricted. |
| MOTU | **Conditional; likely okay if exact CC BY 4.0 package and de-identification scope confirmed** | Repo lists CC BY 4.0 and says synthetic/de-identified. Current live graph has 1,006 Patient nodes and 6,183 MOTU-source nodes. Ensure attribution and that FHIR/ZIP/local source artefacts are the same licensed release; do not relabel as fully synthetic unless source says so. |
| Open Rehab Exercises | **Verify exact archive licence** | Repo says CC BY 4.0, but the source archive is not present in the currently listed `data/raw` files; confirm the actual archive/version and attribution/third-party media terms. |
| RMD scale metadata | **Verify terms; likely limited** | Source is a curated/manual subset of the Rehabilitation Measures Database. “Free” web access does not automatically authorize bulk scraping/redistribution of descriptions, psychometrics, or proprietary instrument text. Keep only independently authored names/metadata until permitted. |
| Synthetic observation seed | **Okay as project-authored demo data** | Clearly label `source=synthetic_demo`; do not attach it to MOTU people. |
| Keraal Kinect zip | **Not in live graph; not assessed for hosting** | Local archive is staged but no source/license verification is recorded. Exclude from a public package until checked. |
| LOINC distribution files under `data/raw/loinc` | **Do not publish raw package by default** | Local package contains licensed artifacts. The licence permits distribution only with notices/version and restrictions; review full package for third-party terms. Prefer serve only permitted codes/display names with required notice. |

## Sources not currently loaded

San Raffaele (CC BY 4.0), KneE-PAD (CC BY 4.0), REHAB24-6 (CC BY-NC 4.0),
GAITEX (CC BY-NC-ND 4.0), GaitIntent/UCOPhyRehab++ (CC BY-NC-ND 4.0), and
MIMIC-IV (credentialed PhysioNet DUA) are catalogued but not in the live source
inventory. Open access for some does not allow republishing all data: exclude
non-commercial/no-derivatives material from a public hosted graph unless a
specific permission is obtained. MIMIC-derived data/models must follow
PhysioNet’s credentialing and derived-data sharing terms; do not place raw or
derived patient data in a public graph.

## Recommended hosting decision

1. A public graph should initially include only rows whose exact source release
   and licence are verified; keep ACVD and unresolved BioPortal ontology
   sources out of public exports until cleared.
2. Add the LOINC online notice and retain identifier plus display name, or omit
   LOINC-derived fields from the public endpoint.
3. Keep `synthetic_demo` explicitly separated; treat MOTU according to its
   actual CC BY release and de-identification documentation.
4. Do not host restricted/non-commercial/no-derivatives datasets or any
   credentialed data/derivatives in an open endpoint.
5. Ask institutional counsel/licensing staff to review ambiguous academic,
   BioPortal, WHO snapshot, and RMD terms before commercial or public
   redistribution.
