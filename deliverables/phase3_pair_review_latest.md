# Phase 3 bridge-pair review worksheet

**Purpose:** choose which ontology-to-target pairs, if any, should proceed to bridge implementation. This is a review worksheet, not a mapping table: no graph edges are created by filling it in.

**Source snapshot:** read-only local ontology and live Neo4j inspection on 2026-10-23. The earlier inventory is in [`bridge_gap_report.md`](bridge_gap_report.md).

> **Draft status:** Decisions rest only on the evidence recorded in this worksheet (labels, ICF codes, xref notes). I did not open `frmo.owl` or the STO source, so I could not read concept definitions or parent classes. A human reviewer must confirm, and replace the reviewer name, before anything is implemented.

## Review rules

- Review each proposed match against the source concept, target concept/code, and intended semantics. Candidate counts are leads, not approved mappings.
- Prefer explicit source cross-references (`xref`, `exactMatch`) that resolve to a loaded target concept. Otherwise require exact normalized label equality and an unambiguous concept-level fit.
- Reject substring, broad lexical overlap, imported-class leakage, ambiguous identifiers, and overly generic concepts.
- Record `approve`, `reject`, or `needs_follow_up` for each candidate. Only explicitly approved candidates should move into implementation; all new bridge edges must remain `review_status=unreviewed` in the graph pending clinical/research review.
- The current work has not added any bridge edges.

## Pair-level decision

| Source ontology | Target | Evidence seen | Recommendation for reviewer | Decision (`proceed` / `defer` / `reject`) | Reviewer / date | Notes |
|---|---|---|---|---|---|---|
| FRMO | ICF | Six exact-label matches to coded ICF concepts; no explicit ICF xrefs found. Candidate rows below. | **Suggested first pilot.** Review each row; do not accept all six automatically. | **proceed** (approved rows only) | / 2026-10-23 | Proceed with 2 of 6 rows: Walking (d450) and Running (d4552). The other four need a look at the FRMO definition or parent class first (see row table). |
| STO | ICF | Two exact-label matches to coded ICF concepts; source concepts also carry SNOMED xrefs, not ICF xrefs. Candidate rows below. | **Suggested second pilot.** Small candidate set; confirm semantic equivalence. | **proceed** (approved rows only) | / 2026-10-23 | Proceed with 1 of 2 rows: Tremor (b7651). Body temperature is held for the same reason as the FRMO row, and should get the same decision in both ontologies. |
| STO | Mondo | Earlier report showed label intersections, but no exact match to a coded Mondo target remained after filtering. | Defer pending explicit Mondo xrefs or better candidate evidence. | **defer** | / 2026-10-23 | Agree. Revisit only if STO gains Mondo/DOID xrefs. The SNOMED xrefs cannot be used because SNOMED is not loaded. |
| TRAK | Mondo | No Mondo/DOID xrefs and no exact label matches to coded Mondo targets found. TRAK has 17 HP xrefs, which are a different target. | Defer. Do not treat HP refs as Mondo mappings. | **defer** | / 2026-10-23 | Agree. Separate suggestion: the 17 HP xrefs are explicit evidence for a TRAK→HPO pair, which is a better-evidenced candidate than anything above. See "Additional constraints". |
| KHMO | Uberon | Preliminary label scan reported 169 intersections, but KHMO contains imported ontology terms; candidates were not verified as native KHMO concepts. No explicit Uberon xrefs found in that scan. | Defer until source-native concepts and target IDs are verified. | **defer** | / 2026-10-23 | Agree. 169 is likely inflated by imported-class leakage. Re-run restricted to concepts in KHMO's own namespace before reconsidering. |
| KHMO | ICF | No coded exact-label matches found in the filtered comparison. | Defer. | **defer** | / 2026-10-23 | Agree. Nothing to review. |
| FRMO | Mondo | Earlier report showed label intersections, but no exact match to a coded Mondo target remained after filtering. | Defer pending stronger evidence. | **defer** | / 2026-10-23 | Agree. |
| FRMO | Uberon | Preliminary 16 label intersections did not survive the coded-target check; several candidates were generic anatomy/imported terms. | Defer pending explicit xrefs or a verified native candidate set. | **defer** | / 2026-10-23 | Agree. Generic anatomy terms are exactly the false-positive pattern the review rules exclude. |

## FRMO → ICF candidate decisions

These are exact normalized label matches only. **No explicit FRMO→ICF cross-references were found.** Review whether the concepts are equivalent in meaning, scope, and granularity—not just similarly named.

| FRMO concept label | ICF code | ICF label | Initial assessment | Decision (`approve` / `reject` / `needs_follow_up`) | Reviewer notes |
|---|---|---|---|---|---|
| Walking | `d450` | Walking | Strong exact-label candidate; relevant to FRMO falls/mobility scope. | **approve** | Unambiguous activity concept, same name and scope, and central to fall risk. |
| Running | `d4552` | Running | Exact-label candidate; confirm relevance to FRMO’s intended domain. | **approve** | Unambiguous activity concept with an exact match. Relevance to falls is secondary, but equivalence is clear and the edge stays unreviewed. |
| Respiration Rate | `b4400` | Respiration rate | Exact normalized label; check whether same measurement concept and granularity. | **needs_follow_up** | Label match is clean, but FRMO may model this as a vital-sign measurement while ICF b4400 is a body function. Check the FRMO definition and parent class; approve if it is the same quantity. |
| Heart Rhythm | `b4101` | Heart rhythm | Exact normalized label; confirm it is the same concept, not a related clinical finding. | **needs_follow_up** | Highest risk of the physiological rows: FRMO may mean an arrhythmia finding rather than the rhythm function. Check the definition and parent class before approving. |
| Body Temperature | `b5500` | Body temperature | Exact normalized label; broad physiological concept, relevance needs confirmation. | **needs_follow_up** | Same measurement-vs-function question as Respiration Rate. Decide together with the STO row so both ontologies get the same answer. |
| Light | `e240` | Light | Exact normalized label; potentially broad environmental concept; review carefully. | **needs_follow_up** | Could be lighting as a fall hazard (fits ICF e240) or an unrelated sense such as light intensity or weight. Check the FRMO definition. Reject if it is not the environmental lighting concept. |

## STO → ICF candidate decisions

These are exact normalized label matches only. STO has SNOMED xrefs for the source concepts, but those xrefs do not establish an ICF mapping.

| STO concept label | ICF code | ICF label | Source xref evidence | Decision (`approve` / `reject` / `needs_follow_up`) | Reviewer notes |
|---|---|---|---|---|---|
| Tremor | `b7651` | Tremor | Source has SNOMEDCT xref `26079004`; no direct ICF xref. | **approve** | Same clinical concept in the stroke setting and in ICF (involuntary movement function). Label is specific, not generic. |
| Body temperature | `b5500` | Body temperature | Source has SNOMEDCT xref `386725007`; no direct ICF xref. | **needs_follow_up** | Same open question as the FRMO row. Confirm STO's concept is the temperature quantity or function, then apply the same decision to both. |

## Approval and provenance

If you approve a pair, state whether all listed candidate rows are approved or only specific rows. Please provide reviewer name and date. Implementation will preserve the project policy: new edges carry `method=rule_based`, `match_type=xref` or `exact_label`, `confidence=0.9` or `0.8` respectively, and remain `review_status=unreviewed` in the graph until a separate human approval workflow.

**Pairs approved to implement:** (proposed by AI draft; not effective until a human confirms below)

- [x] FRMO → ICF: **only** Walking → `d450` and Running → `d4552`
- [x] STO → ICF: **only** Tremor → `b7651`
- [ ] Other (specify): none

**Date:** 2026-10-23
**Additional constraints / exclusions:**

1. Implement only the three approved rows above (3 edges in total). Every `needs_follow_up` row is excluded until it is changed to `approve` in this worksheet.
2. All edges: `method=rule_based`, `match_type=exact_label`, `confidence=0.8`, `review_status=unreviewed`.
3. Verify that `d450`, `d4552` and `b7651` exist as coded concepts in the loaded ICF nodes before creating edges. Skip and report any that do not resolve.
4. Add tests pinning the three approved matches, plus negative tests that Light, Heart Rhythm, Respiration Rate and Body Temperature produce **no** edge until approved, so false positives stay visible.
5. Do not use SNOMED xrefs as ICF evidence, and do not treat HP xrefs as Mondo mappings.
6. Optional follow-up (new worksheet, not part of this approval): evaluate **TRAK → HPO** using TRAK's 17 explicit HP xrefs. Explicit xrefs to a loaded target are the preferred evidence type under the review rules, so this pair may be stronger than any exact-label pair here.
7. Before reconsidering KHMO → Uberon, re-run the comparison restricted to concepts in KHMO's own namespace to remove imported-class leakage.
