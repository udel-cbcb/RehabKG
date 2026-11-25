# Phase 4 findings — ACVD ontology

**Date:** 2026-10-26 · **Scope:** integrate the already staged ACVD ontology
without downloading or reimporting the live database.

## Source status

- `data/ontologies/acvd.owl` is user-staged OWL/XML. The local OWLAPI adapter
  parses **1,719 labeled classes** and **1,911 named subclass edges**.
- Version **2.0 is user-reported**, not embedded in the ontology metadata.
- BioPortal submission is unpinned. Licence and duplicate comparison against
  CVAO/STO-DRAFT remain unverified; do not redistribute the source until the
  licence is confirmed. No source refresh/download was performed.

## Pipeline coverage

- Cypher path: extractor and `ACVDConcept` loader are wired in
  `etl_ontologies.py`.
- Bulk path: namespaced node/relationship exports, import label mapping,
  export support, and `ACVDConcept.code` uniqueness constraint are wired.
- Dashboard ontology count and browse view include ACVD with metadata caveats.
- The staged ontology has no external bridge mappings; **0 bridges** is
  expected. No Phase 3 matching rule was applied to ACVD.

## Validation

- ACVD extractor count: **1,719 concepts / 1,911 named hierarchy edges**.
- Focused offline tests and full bulk CSV build/ID validation are recorded in
  the Gate 4 summary. Live graph was not reimported; no live ACVD count is
  claimed.

## Gate 4

ACVD integration is ready for review subject to the explicit source caveats
above. Optional AERO/ICPS additions and deferred OAE are not included.
