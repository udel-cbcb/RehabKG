# Phase 3 bridge-pair review worksheet

**Purpose:** choose which ontology-to-target pairs, if any, should proceed to bridge implementation. This is a review worksheet, not a mapping table: no graph edges are created by filling it in.

**Source snapshot:** read-only local ontology and live Neo4j inspection on 2026-10-23. The earlier inventory is in [`bridge_gap_report.md`](bridge_gap_report.md).

## Review rules

- Review each proposed match against the source concept, target concept/code, and intended semantics. Candidate counts are leads, not approved mappings.
- Prefer explicit source cross-references (`xref`, `exactMatch`) that resolve to a loaded target concept. Otherwise require exact normalized label equality and an unambiguous concept-level fit.
- Reject substring, broad lexical overlap, imported-class leakage, ambiguous identifiers, and overly generic concepts.
- Record `approve`, `reject`, or `needs_follow_up` for each candidate. Only explicitly approved candidates should move into implementation; all new bridge edges must remain `review_status=unreviewed` in the graph pending clinical/research review.
- The current work has not added any bridge edges.

## Pair-level decision

| Source ontology | Target | Evidence seen | Recommendation for reviewer | Decision (`proceed` / `defer` / `reject`) | Reviewer / date | Notes |
|---|---|---|---|---|---|---|
| FRMO | ICF | Six exact-label matches to coded ICF concepts; no explicit ICF xrefs found. Candidate rows below. | **Suggested first pilot.** Review each row; do not accept all six automatically. |  |  |  |
| STO | ICF | Two exact-label matches to coded ICF concepts; source concepts also carry SNOMED xrefs, not ICF xrefs. Candidate rows below. | **Suggested second pilot.** Small candidate set; confirm semantic equivalence. |  |  |  |
| STO | Mondo | Earlier report showed label intersections, but no exact match to a coded Mondo target remained after filtering. | Defer pending explicit Mondo xrefs or better candidate evidence. |  |  |  |
| TRAK | Mondo | No Mondo/DOID xrefs and no exact label matches to coded Mondo targets found. TRAK has 17 HP xrefs, which are a different target. | Defer. Do not treat HP refs as Mondo mappings. |  |  |  |
| KHMO | Uberon | Preliminary label scan reported 169 intersections, but KHMO contains imported ontology terms; candidates were not verified as native KHMO concepts. No explicit Uberon xrefs found in that scan. | Defer until source-native concepts and target IDs are verified. |  |  |  |
| KHMO | ICF | No coded exact-label matches found in the filtered comparison. | Defer. |  |  |  |
| FRMO | Mondo | Earlier report showed label intersections, but no exact match to a coded Mondo target remained after filtering. | Defer pending stronger evidence. |  |  |  |
| FRMO | Uberon | Preliminary 16 label intersections did not survive the coded-target check; several candidates were generic anatomy/imported terms. | Defer pending explicit xrefs or a verified native candidate set. |  |  |  |

## FRMO → ICF candidate decisions

These are exact normalized label matches only. **No explicit FRMO→ICF cross-references were found.** Review whether the concepts are equivalent in meaning, scope, and granularity—not just similarly named.

| FRMO concept label | ICF code | ICF label | Initial assessment | Decision (`approve` / `reject` / `needs_follow_up`) | Reviewer notes |
|---|---|---|---|---|---|
| Walking | `d450` | Walking | Strong exact-label candidate; relevant to FRMO falls/mobility scope. |  |  |
| Running | `d4552` | Running | Exact-label candidate; confirm relevance to FRMO’s intended domain. |  |  |
| Respiration Rate | `b4400` | Respiration rate | Exact normalized label; check whether same measurement concept and granularity. |  |  |
| Heart Rhythm | `b4101` | Heart rhythm | Exact normalized label; confirm it is the same concept, not a related clinical finding. |  |  |
| Body Temperature | `b5500` | Body temperature | Exact normalized label; broad physiological concept, relevance needs confirmation. |  |  |
| Light | `e240` | Light | Exact normalized label; potentially broad environmental concept; review carefully. |  |  |

## STO → ICF candidate decisions

These are exact normalized label matches only. STO has SNOMED xrefs for the source concepts, but those xrefs do not establish an ICF mapping.

| STO concept label | ICF code | ICF label | Source xref evidence | Decision (`approve` / `reject` / `needs_follow_up`) | Reviewer notes |
|---|---|---|---|---|---|
| Tremor | `b7651` | Tremor | Source has SNOMEDCT xref `26079004`; no direct ICF xref. |  |  |
| Body temperature | `b5500` | Body temperature | Source has SNOMEDCT xref `386725007`; no direct ICF xref. |  |  |

## Approval and provenance

If you approve a pair, state whether all listed candidate rows are approved or only specific rows. Please provide reviewer name and date. Implementation will preserve the project policy: new edges carry `method=rule_based`, `match_type=xref` or `exact_label`, `confidence=0.9` or `0.8` respectively, and remain `review_status=unreviewed` in the graph until a separate human approval workflow.

**Pairs approved to implement:**

- [ ] FRMO → ICF
- [ ] STO → ICF
- [ ] Other (specify):

**Reviewer:**  
**Date:**  
**Additional constraints / exclusions:**  
