# LOINC fill review notes — `curated/scale_identifiers.csv`

- **Source of truth**: LOINC 2.83 (`data/raw/loinc/LoincTable/Loinc.csv`, 112,405 terms; released 2026-08-19, downloaded from https://loinc.org/downloads). Every code below was read from that file at fill time; `STATUS == ACTIVE` verified programmatically for all 17 filled codes; `loinc_long_name` is the file's `LONG_COMMON_NAME` verbatim.
- **Fill rule applied**: fill only when the LOINC term unambiguously *is* the instrument; leave empty when absent from LOINC 2.83 or ambiguous (acronym collision, generic panel, non-equivalent variant). Filled codes were taken from `scripts/lookup_loinc.py` suggestions (tier exact/acronym/contains/overlap), then confirmed by reading the full LOINC row (component, property, method, class, definition) — never from memory.
- **Review state**: all 40 rows remain `review_status=unreviewed`, `reviewed_by`/`reviewed_on` empty. This file is the decision trace for the human approval pass; approving = reviewer sets `review_status`/`reviewed_by` in the register (this file stays untracked per plan Section 0).

## Filled — 17 scales (high confidence, ACTIVE terms)

| scale_id | scale | loinc | why this term |
|---|---|---|---|
| ASM-002 | Timed Up and Go | 89423-8 | `METHOD=TUG`, `PROP=Time`, definition is verbatim the TUG measure. **Alt**: 89422-0 "Timed Up and Go test and physical findings of gait panel CDC" is the CDC panel but bundles extra gait-physical-findings items, so the pure time term was chosen. |
| ASM-013 | Nine Hole Peg Test | 83141-2 | Only 9-hole peg term in LOINC. **Flag**: it is the *NIH Toolbox* variant (own scoring/norms) — reviewer may empty this row if they consider it non-equivalent to the classic Mathiowitz 9HPT. |
| ASM-021 | Timed 10 Meter Walk Test | 104047-6 | `PROP=Time`, short name "Time to walk 10-m" — matches MOTU's seconds-valued TWT outcome. Sibling term 104046-8 is *steps* (`PROP=Num`), not time. |
| ASM-023 | 10 Meter Walk Test | 104047-6 | Same instrument family as ASM-021; no separate speed (m/s) term exists in 2.83. **Flag**: two RMD scales share one LOINC code — reviewer decides whether ASM-021/ASM-023 should be de-duplicated or distinguished (e.g. steps term 104046-8 for one of them). |
| ASM-030 | Barthel Index | 96762-0 | `METHOD=Barthel Index`, panel named "Barthel index panel"; definition describes the Barthel Index. **Alt**: 96761-2 is the generic total-score child term. |
| ASM-040 | VAS Pain | 38214-3 | `METHOD=Reported.visual analog score`, component "Pain severity" — exactly the VAS pain instrument. (38221-8 is Wong-Baker FACES, rejected.) |
| ASM-050 | Lysholm Knee Score | 99583-7 | Panel named "Lysholm Knee Scoring Scale [LKSS]", `METHOD=LKSS`, definition matches the 8-item scale. |
| ASM-051 | KOOS | 72091-2 | Panel, `METHOD=KOOS`, definition matches. |
| ASM-060 | Harris Hip Score | 100283-1 | Panel, `METHOD=Harris Hip Score`, definition (100-point, pain/function/deformity/ROM) matches. |
| ASM-061 | HOOS | 72092-0 | Panel, `METHOD=HOOS`, definition matches. |
| ASM-080 | Modified Ashworth Scale | 115586-0 | Panel, `METHOD=Reported.MAS`, definition names MAS + rehab populations. |
| ASM-081 | Modified Rankin Scale | 75859-9 | Component "Modified rankin scale", `PROP=Score`, `SCALE=Ord`, short name mRS. |
| ASM-082 | Glasgow Coma Scale | 35088-4 | Panel named "Glasgow coma scale", definition matches. |
| ASM-100 | Forced Vital Capacity | 19868-9 | Standard spirometry FVC term (`PROP=Vol`, `METHOD=Spirometry`). |
| ASM-022 / ASM-101 | 6 Minute Walk Test / 6 Minute Walk Distance | 64098-7 | Component "Walking distance", `PROP=Len`, `TIME=6M`, definition "Total distance walked in 6 minutes". **Flag**: one LOINC term covers both RMD rows (test vs distance) — reviewer may keep both or de-duplicate. |
| ASM-110 | NIHSS | 70182-1 | Panel "NIH Stroke Scale", `METHOD=NIHSS`; **cross-check**: identical to the ontology's `owl:sameAs` on the NIHStrokeScale concept. |

## Left empty — 23 scales (absent or ambiguous in LOINC 2.83)

**Genuinely absent** (grep-verified against `LoincTable/Loinc.csv`, multiple spellings):

| scale | search evidence |
|---|---|
| ASM-001 Berg Balance Scale | "Berg balance" → 0 |
| ASM-003 Functional Gait Assessment | "functional gait" → 0 |
| ASM-004 Tinetti POMA | "Tinetti" → 0 |
| ASM-005 Dynamic Gait Index | "dynamic gait"/"gait index" → 0 |
| ASM-010/020 Fugl-Meyer UE/LE | "Fugl" → 0 |
| ASM-011 Action Research Arm Test | "action research"/`ARAT` → only activity-ratio hits |
| ASM-012 Box and Block Test | "box and block" → 0 |
| ASM-014 DASH | "disabilities of the arm" → 0; `DASH` → coagulation/chemistry junk |
| ASM-031 Functional Independence Measure | `FIM` → only IRF-PAI panels (instruments that *contain* FIM items, not FIM itself) |
| ASM-042 McGill Pain Questionnaire | "pain questionnaire" → only PhenX/FACIT protocols |
| ASM-052 IKDC | "International Knee"/`IKDC` → 0 |
| ASM-070 Constant-Murley | "murley"/"constant" → 0 |
| ASM-071 ASES | "shoulder and elbow" → 0 |
| ASM-090 PEDI | "disability inventory"/"pediatric evaluation" → 0 |
| ASM-111 Stroke Impact Scale | "stroke impact" → 0 |
| ASM-120 Mini-BESTest | "balance evaluation"/"bestest" → 0 |
| ASM-121 Functional Reach Test | "functional reach" → 0 |
| ASM-122 ABC Scale | "balance confidence" → 0 |

**Ambiguous / trap — deliberately empty**:

| scale | reason |
|---|---|
| ASM-032 Katz Index | 83180-0 mentions Katz only to say its terms are *"not specific to a particular assessment instrument (e.g. the Katz ADL scale, Lawton IADL scale…)"* — explicitly not the instrument. |
| ASM-033 Lawton IADL | Same 83180-0 generic self-care panel — rejected for the same reason. |
| ASM-041 NRS Pain | No dedicated numeric-rating pain term (only VAS 38214-3 and Wong-Baker FACES 38221-8). |
| ASM-091 Alberta Infant Motor Scale | **Acronym collision**: LOINC 111770-4 "Total score [AIMS]" has `METHOD=AIMS` but its definition (0–4 severity ratings across movement categories) is the *Abnormal Involuntary Movement Scale* (psychiatry), not the Alberta Infant Motor Scale. "infant motor" → 0 hits. |

## Reproduce

```bash
python3 scripts/lookup_loinc.py          # regenerates deliverables/loinc_suggestions.csv (advisory)
python3 -m pytest tests/test_bridges.py -q -k ScaleIdentifiers
python3 -m ruff check --select E9,F curated/ scripts/ tests/
```
