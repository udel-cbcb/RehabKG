# BioPortal Ontology Candidates for RehabKG

> **Historical research catalogue.** It documents candidate discovery and
> releases considered during 2026. The current loaded set has since been
> reduced; removed sources are not enabled by default. See
> `docs/notes/ontology_removal_2026-10-27.md` and `docs/DATA_SOURCES.md` for
> the current retained graph.

**Date**: 2026-10-16  
**Method**: Full BioPortal catalog sweep via the REST API (1,297 unique ontologies), filtered against ~90 physical-therapy / rehabilitation keywords (domain, outcomes, anatomy, modalities, behaviour change, measurement tech), then descriptions + class counts were fetched for every hit and curated manually.

**Access note**: BioPortal's REST API requires an API key. This sweep used BioPortal's public anonymous key (embedded in its own website download links) so the catalog would not depend on a personal key. For your own downloads, register a free personal key at [bioportal.bioontology.org/account](https://bioportal.bioontology.org/account) and put it in `.env` as `BIOPORTAL_API_KEY`. In the URLs below, replace `YOUR_KEY` with your API key.

**Totals**: 98 candidates reviewed — 3 retained in the pipeline at the time of this sweep (PAIN, CBHA, plus other previously retained sources), 7 Tier 1, 36 Tier 2, 43 not recommended. Historical candidate counts are unchanged.

> **Status update (2026-11-05):** the focused graph retains PAIN, REHABO, EXMO,
> Mondo, Uberon, ICF, and HPO. CBHA, COPPER, KHMO, and other flagged sources
> were removed; the rows below preserve the 2026-10-16/17 candidate and pipeline
> status at that time.

**BioPortal page**: `https://bioportal.bioontology.org/ontologies/{ACRONYM}` — every row's acronym links that page; description/versions/metrics live there too.

---

## A. Historical shortlist — removed sources noted

Wired into download_data.py / etl_ontologies.py / build_csvs.py in this change. Download URLs pin the exact BioPortal submission used.

This table records historical candidate research, not the current loaded set.
On 2026-10-27, the user requested removal of unverified/non-public ontology
sources from live Neo4j. The following table entries are no longer loaded by
the default Cypher or bulk pipelines; see the removal note below.

| Acronym | Name | Classes | Ver | License | Description | Download URL |
|---------|------|--------:|-----|---------|-------------|--------------|
| **BCIO** | Behaviour Change Intervention Ontology | 2,524 | — | — | The Human Behaviour Change Project (HBCP) funded by the Wellcome Trust, and the Advancing Prevention Research in Cancer through Ontology Tools (APRICOT) Project funded by the US National Institutes of Health, are developing the Behaviour Ch | `https://data.bioontology.org/ontologies/BCIO/submissions/1/download?apikey=YOUR_KEY` |
| **STO-DRAFT** | The Stroke Ontology | 1,712 | 2017-11-01 | — | The Stroke Ontology (STO) covers the knowledge domain of stroke based on expert views and translational continuum of stroke research. | `https://data.bioontology.org/ontologies/STO-DRAFT/submissions/1/download?apikey=YOUR_KEY` |
| **TRAK** | Taxonomy for Rehabilitation of Knee Conditions | 1,619 | unknown | — | TRAK (Taxonomy for RehAbilitation of Knee conditions) is an ontology that formally models information relevant for the rehabilitation of knee conditions. TRAK provides the framework that can be used to collect coded data in sufficient detai | `https://data.bioontology.org/ontologies/TRAK/submissions/5/download?apikey=YOUR_KEY` |
| **FRMO** | Fall Risk Management Ontology | 890 | 09.10 | — | We have developed an ontology representing major fall risk management entities to support approaches to text mining, data descriptions and linkage in the context of fall risk management. This ontology contains concepts related to fall risk  | `https://data.bioontology.org/ontologies/FRMO/submissions/19/download?apikey=YOUR_KEY` |
| **PAIN** | The Pain Ontology | 623 | 2026-10-01 | — | The Pain Ontology contains terms for representing pain as defined by the International Association For the Study of Pain (IASP), meaning that pain is both an unpleasant physical sensation and unpleasant emotional experience. It includes ter | `https://data.bioontology.org/ontologies/PAIN/submissions/12/download?apikey=YOUR_KEY` |
| **PACO** | Physical Activity Ontology | 224 | 0.2 | — | Physical Activity Concept Ontology (PACO) contains various concepts that are required to describe one's physical activity. | `https://data.bioontology.org/ontologies/PACO/submissions/2/download?apikey=YOUR_KEY` |
| **BCTT** | Behaviour Change Technique Taxonomy | 110 | 0.4 | — | BCT Taxonomy v0.4 | `https://data.bioontology.org/ontologies/BCTT/submissions/6/download?apikey=YOUR_KEY` |
| **MSO** | Multiple sclerosis ontology | 1,170 | — | — | Multiple sclerosis ontology integrated with Basic Formal Ontology (BFO). Fills the MS caseload gap (movement disorders covered by PMDO, spinal cord by SCIO, brain injury by CABRO). Wired 2026-10-17 from Tier 1; rdflib cannot parse its OWL/XML so the xml.etree fallback (with xml:base resolution) is used. | `https://data.bioontology.org/ontologies/MSO/submissions/2/download?apikey=YOUR_KEY` |
| **POEM** | Psychometric Ontology of Experiences and Measures | 56 (standalone file) | 1.0 | — | Instrument-representation schema (PsychometricQuestionnaire, QuestionnaireScale, Item, ResponseOption, Construct...) plus the SNOMED symptom/disorder constructs it references. BioPortal's 1,636 class metric counts SNOMEDCT/STATO/... imports that are NOT bundled in the downloadable submission. Wired 2026-10-17 from Tier 1. | `https://data.bioontology.org/ontologies/POEM/submissions/8/download?apikey=YOUR_KEY` |
| **CBHA** | CalendarBench Human Activities | 37 categories + 1,210 activities | 2026.05.03 | — | Hierarchy of the Compendium of Physical Activities (doi:10.1016/j.jshs.2023.10.001), grouped by seven top-level event categories (Sports, Work, Social, Education, Everyday Tasks, Health, Leisure). Each activity is a named resource with its Activity Code and MET value preserved verbatim. Turtle ontology; activities are detected via their ha:activityCode annotations (not owl:NamedIndividual). Wired 2026-10-17 from Tier 1. | `https://data.bioontology.org/ontologies/CBHA/submissions/1/download?apikey=YOUR_KEY` |
| **PHENX** | PhenX Phenotypic Terms | 533 | 1.2 | — | Standard measures related to complex diseases, phenotypic traits and environmental exposures (genetics, behaviour, environment, lifestyle). RDF/XML with numeric codes; completes the outcome-measure story alongside POEM's instrument schema. Wired 2026-10-18 from Tier 1. | `https://data.bioontology.org/ontologies/PHENX/submissions/16/download?apikey=YOUR_KEY` |
| **NIHSS** | National Institutes of Health Stroke Scale Ontology | 19 | 2024/06 | — | Domain ontology for National Institutes of Health Stroke Scale (NIHSS). Scores range from 0-42. Patients are given more points for greater deficiencies. A score of 0 indicates that the test is normal. Extracts to 18 labeled classes (report root, Instruction parent of the 15 numbered scored items, Interval); 15 hierarchy edges. Bridged to scale ASM-110 via INSTANCE_OF. Wired 2026-10-22 from Tier 1. | `https://data.bioontology.org/ontologies/NIHSS/submissions/15/download?apikey=YOUR_KEY` |
| **ACVD_ONTOLOGY** | Atherosclerotic Cerebrovascular Disease Ontology | 1,719 | 2.0 (user-reported; not embedded) | Unverified | User-staged OWL/XML; OWLAPI parses 1,719 labeled classes and 1,911 named hierarchy edges. BioPortal submission is unpinned; licence and duplicate comparison against CVAO/STO-DRAFT remain unverified. Wired in Phase 4 using the staged source only. | `https://data.bioontology.org/ontologies/ACVD_ONTOLOGY/download?apikey=YOUR_KEY` (unpinned; existing staged file is not overwritten) |

## B. Tier 1 — recommended follow-ups

High-value additions that fit existing bridge patterns (AssessmentScale, AdverseEvent, ICF functions). Left out of this batch to keep the change reviewable.

| Acronym | Name | Classes | Ver | License | Description | Download URL |
|---------|------|--------:|-----|---------|-------------|--------------|
| **OAE** | Ontology of Adverse Events | 10,589 | 1.2.54 | — | The Ontology of Adverse Events (OAE) is a community-based biomedical ontology in the domain of adverse events. OAE is developed to standardize adverse event annotation, integrate various adverse event data, and support computer-assisted rea | `https://data.bioontology.org/ontologies/OAE/download?apikey=YOUR_KEY` |
| **CTCAE** | Common Terminology Criteria for Adverse Events | 4,112 | 6.0 | — | Common Terminology Criteria for Adverse Events (CTCAE) is widely accepted throughout the oncology community as the standard classification and severity grading scale for adverse events in cancer therapy clinical trials and other oncology se | `https://data.bioontology.org/ontologies/CTCAE/download?apikey=YOUR_KEY` |
| **PMDO** | Parkinson and Movement Disorder Ontology | 629 | 1.1 | — | The Parkinson Movement Disorder Ontology (PMDO) uses a systematic analysis of movement disorder instruments, extensive review of literature led by movement disorder specialists, and the AMP PD knowledge portal with an iterative ontology eng | `https://data.bioontology.org/ontologies/PMDO/download?apikey=YOUR_KEY` |
| **MF** | Mental Functioning Ontology | 401 | 2025-07-08 | — | The Mental Functioning Ontology is an ontology for mental functioning, including mental processes such as cognition and traits such as intelligence, and related diseases and disorders. It is developed in the context of the Ontology for Gene | `https://data.bioontology.org/ontologies/MF/download?apikey=YOUR_KEY` |
| **SCIO** | Spinal Cord Injury Ontology | 320 | 1 | — | Representation of pre-clinical studies in the domain of spinal cord injury therapies | `https://data.bioontology.org/ontologies/SCIO/download?apikey=YOUR_KEY` |
| **OPTIMAL** | OPTImAL: An ontology for patient adherence modeling in  | 142 | 1 | — | OPTImAL is a reusable formal model of factors affecting CVD patient adherence to physical activity and exercise. The basis for this model relies on the analysis of data/evidence published in the scientific literature and enables identificat | `https://data.bioontology.org/ontologies/OPTIMAL/download?apikey=YOUR_KEY` |

## C. Tier 2 — worth considering

Moderate fit or specialised scope; evaluate if a use case arises.

| Acronym | Name | Classes | Ver | License | Description | Download URL |
|---------|------|--------:|-----|---------|-------------|--------------|
| **FTC** | Functional Therapeutic Chemical Classification System | 61,426 | 1 | — | The Functional Therapeutic Chemical Classification System (FTC) defines over 20'000 mechanisms and modes of action for approuved drugs. The resource abstracts away from the traditional chemical structure-based approach and focuses solely on | `https://data.bioontology.org/ontologies/FTC/download?apikey=YOUR_KEY` |
| **DOVES** | Digital medicine Outcomes Value Set (DOVeS) Ontology | 36,412 | v1.0.0 | — | The Digital medicine Outcomes Value Set (DOVeS) ontology aims to provide users with a set of ontologically structured healthcare outcomes (clinical, operational, economic, technical, and others) tailored to digital medicine and digital ther | `https://data.bioontology.org/ontologies/DOVES/download?apikey=YOUR_KEY` |
| **PATO** | Phenotypic Quality Ontology | 8,713 | 2026-10-01 | — | Phenotypic qualities (properties). This ontology can be used in conjunction with other ontologies such as GO or anatomical ontologies to refer to phenotypes. Examples of qualities are red, ectopic, high temperature, fused, small, edematous  | `https://data.bioontology.org/ontologies/PATO/download?apikey=YOUR_KEY` |
| **ICPC2P** | International Classification of Primary Care - 2 PLUS | 7,537 | ICPC2P_2005 | — | Australian Modification of ICPC-2, known as ICPC-2 Plus. ICPC-2 Plus is primarily used in Australia and provides greater specificity for data input than ICPC-2. | `https://data.bioontology.org/ontologies/ICPC2P/download?apikey=YOUR_KEY` |
| **LSFO** | Lifestyle Factor Ontology | 5,598 | 1.01 | — | In this ontology, we defined nine distinct categories that encompass various aspects of lifestyle factors (LSFs), creating a unified Lifestyle Factors Ontology (LSFO) across these categories. Within the context of lifestyle, we have identif | `https://data.bioontology.org/ontologies/LSFO/download?apikey=YOUR_KEY` |
| **ICNP** | International Classification for Nursing Practice | 4,476 | classified | — | International Classification for Nursing Practice | `https://data.bioontology.org/ontologies/ICNP/download?apikey=YOUR_KEY` |
| **CMO** | Clinical Measurement Ontology | 4,199 | 2026-10-10 | — | Standardizes morphological and physiological measurement records from clinical research and health programs; candidate for gait/EMG-style measurement provenance. Added 2026-10-17 second-pass gap analysis. | `https://data.bioontology.org/ontologies/CMO/download?apikey=YOUR_KEY` |
| **MIO** | Myocardial Infarction Ontology | 3,090 | V1.0.0 | — | Disease-specific ontology for myocardial infarction; cardiac-rehab-adjacent caseload (diagnosis side, not rehab interventions). Added 2026-10-17 second-pass gap analysis. | `https://data.bioontology.org/ontologies/MIO/download?apikey=YOUR_KEY` |
| **CVAO** | STO (catalog name; CerebroVascular Anatomy Ontology) | 1,712 | 2017-11-01 | — | Catalog description "Stroke ontology"; same version date and class count as STO-DRAFT — likely a duplicate/successor record of the same resource. Verify before loading. Added 2026-10-17 second-pass gap analysis. | `https://data.bioontology.org/ontologies/CVAO/download?apikey=YOUR_KEY` |
| **ICDO** | International Classification of Diseases Ontology | 1,388 | 1.0.83 | — | A biomedical ontology for logical representation of the terms and relations related to the International Classification of Diseases (ICD) | `https://data.bioontology.org/ontologies/ICDO/download?apikey=YOUR_KEY` |
| **SATO** | SATO (IDEAS expAnded wiTh BCIO): workflow for designers | 1,264 | v2 | — | Designing effective theory-driven digital behaviour change interventions (DBCI) is a challenging task. To ease the design process, and assist with knowledge sharing and evaluation of the DBCI, we propose the SATO (IDEASexpAnded wiTh BCIO) d | `https://data.bioontology.org/ontologies/SATO/download?apikey=YOUR_KEY` |
| **PDON** | Parkinson's Disease Ontology | 632 | 1.0 | — | Comprehensive semantic framework for the Parkinson's knowledge domain; complements PMDO (Tier 1) with a second Parkinson resource. Added 2026-10-17 second-pass gap analysis. | `https://data.bioontology.org/ontologies/PDON/download?apikey=YOUR_KEY` |
| **STMSO** | symptomatic treatment of multiple sclerosis ontology | 626 | — | — | Semantic representation of MS symptomatic treatment, CDSS-oriented; pairs with MSO (Tier 1). Added 2026-10-17 second-pass gap analysis. | `https://data.bioontology.org/ontologies/STMSO/download?apikey=YOUR_KEY` |

### Historical Phase 4 ACVD review status

- ACVD integration proceeds using the staged local file. Duplicate comparison
  against **STO-DRAFT/CVAO** and licence confirmation remain unverified; these
  risks are not considered cleared.
- User-staged `data/ontologies/acvd.owl` is reported by the user as version
  2.0 and was parsed with the locally bundled
  OWLAPI on 2026-10-23: 1,719 classes, all labeled. Its ontology header has
  IRI `http://www.ustb.edu.cn/thesauri/tocr/v1/data#`, but no explicit
  `owl:versionIRI` or `owl:versionInfo`; version 2.0 is user-provided metadata,
  not confirmed by the file header. RDFLib and Owlready2 reject this file's
  OWL/XML serialization, so the extractor and Phase 4 preflight use the local
  OWLAPI bundle. ACVD is wired on the Cypher and bulk paths using the staged
  file. The BioPortal endpoint below remains unpinned; `download_file()` skips
  the existing local file, so no network refresh is performed implicitly.
  Duplicate and licence confirmation remain unverified; do not redistribute
  the staged ontology until the licence is confirmed.
  ACVD was removed from the live graph on 2026-10-27 and its loader wiring was
  removed. A data backup is recorded in
  `deliverables/public-graph-removal-backup-2026-10-27.json`.
| **OHEO** | Outcomes Health Economics Ontology | 594 | 0.2.0 (alpha) | — | OHEO, the Outcomes Health Economics Ontology, describes health outcomes as health economics and health technology assessment specify, measure, value and summarise them. It keeps four kinds of thing apart. These are outcome domains (what is  | `https://data.bioontology.org/ontologies/OHEO/download?apikey=YOUR_KEY` |
| **AERO** | Adverse Event Reporting Ontology | 497 | unknown | — | The Adverse Event Reporting Ontology (AERO) is an ontology aimed at supporting clinicians at the time of data entry, increasing quality and accuracy of reported adverse events. | `https://data.bioontology.org/ontologies/AERO/download?apikey=YOUR_KEY` |
| **HIO** | Hearing Impairment Ontology | 496 | 1 | — | Controlled vocabulary for hearing impairment; audiology/rehab-adjacent, marginal to core PT scope. Added 2026-10-17 second-pass gap analysis. | `https://data.bioontology.org/ontologies/HIO/download?apikey=YOUR_KEY` |
| **ICOP** | International Classification of Orofacial Pain Ontology | 437 | 2026-10-01 | — | The International Classification of Orofacial Pain Ontology (ICOP) contains terms for defining and classifying orofacial pain. The ICOP’s classes and relations facilitate the development of tools and resources capable of enhancing our under | `https://data.bioontology.org/ontologies/ICOP/download?apikey=YOUR_KEY` |
| **NCCO** | Nursing Care Coordination Ontology | 400 | 1.0 | — | Nursing Care Coordination Ontology contains activities that nurses use while coordinating care among patients. | `https://data.bioontology.org/ontologies/NCCO/download?apikey=YOUR_KEY` |
| **ICPS** | International Classification for Patient Safety | 398 | Created by Aldo Gangemi and  | — | Ontology network about Patient Safety Incident. This work has been carried out by the Ontological Engineering Group, using sources from the University of Saint Etienne and the Australian Patient Safety Foundation, and supported by the World | `https://data.bioontology.org/ontologies/ICPS/download?apikey=YOUR_KEY` |
| **PCALION** | Prostate Cancer Lifestyle Ontology | 397 | 3.0 | — | PCLiON:Prostate Cancer Lifestyle Ontology | `https://data.bioontology.org/ontologies/PCALION/download?apikey=YOUR_KEY` |
| **RAO** | Rheumatoid Arthritis ontology | 280 | 1.0 | — | Controlled vocabulary of RA-relevant information (treatment only); RA is a common PT caseload. Added 2026-10-17 second-pass gap analysis. | `https://data.bioontology.org/ontologies/RAO/download?apikey=YOUR_KEY` |
| **CTO** | Clinical Trials Ontology | 273 | Version Release: 1.0.0 | — | Clinical Trial Ontology (CTO) is designed to formally represent and integrate all terms used to describe and register the clinical trials. The development of CTO was done as a collaborative project among Fraunhofer SCAI, Germany; University | `https://data.bioontology.org/ontologies/CTO/download?apikey=YOUR_KEY` |
| **NIRS** | Non-invasive Respiratory Support Ontology | 145 | — | — | Managing patients with respiratory failure increasingly involves non-invasive respiratory support (NIRS) strategies as alternatives to traditional ventilation methods. However, despite the rapidly expanding use of NIRS, there is a significa | `https://data.bioontology.org/ontologies/NIRS/download?apikey=YOUR_KEY` |
| **S4EHAW** | SAREF4EHAW: an extension of SAREF for eHealth Ageing We | 137 | v1.1.1 | — | The objective of SAREF4EHAW is to extend SAREF ontology for the eHealth/Ageing-well (EHAW) vertical. Clause 4.1 of the present document shortly introduces a high level view of the envisioned SAREF4EHAW semantic model and modular ontology, w | `https://data.bioontology.org/ontologies/S4EHAW/download?apikey=YOUR_KEY` |
| **COPDO** | COPD Ontology | 108 | 1 | — | COPD concepts from routine clinical databases; pulmonary-rehab adjacent. Added 2026-10-17 second-pass gap analysis. | `https://data.bioontology.org/ontologies/COPDO/download?apikey=YOUR_KEY` |
| **PHASES** | Promoting Health Aging through Semantic Enrichment of S | 85 | 2026-02-25 | — | PHASES provides an ontology for integrating research in solitude and gerotranscendence. By integrating these areas of study, we aim to deepen our understanding of each and how they promote healthy aging. | `https://data.bioontology.org/ontologies/PHASES/download?apikey=YOUR_KEY` |
| **CABRO** | Computer Assisted Brain Injury Rehabilitation Ontology | 59 | 0.5 | — | a web ontology for the semantic representation of the computer assisted brain trauma rehabilitation domain. This is a novel and emerging domain, since it employs the use of robotic devices, adaptation software and machine learning to facili | `https://data.bioontology.org/ontologies/CABRO/download?apikey=YOUR_KEY` |
| **FALL** | MyOntoServiceFull_FallDetection | 51 | 1 | — | fall detection scenario | `https://data.bioontology.org/ontologies/FALL/download?apikey=YOUR_KEY` |
| **CWD** | Consumer Wearable Device | 46 | — | — | Consumer Wearable Devices (CWD) enable passive, low-burden, longitudinal collection of data relevant to health behaviors, human performance, and biometrics. Such data are increasingly used to tailor clinical and public health interventions  | `https://data.bioontology.org/ontologies/CWD/download?apikey=YOUR_KEY` |
| **NPI** | Non-Pharmacological Interventions (NPIs) | 45 | Version 8 | — | Terminologies of Non-Pharmacological Interventions | `https://data.bioontology.org/ontologies/NPI/download?apikey=YOUR_KEY` |
| **NEUMORE** | Neural Motor Recovery Ontology | 33 | 0.1 | — | Neural functional motor recovery; on-topic for neurorehab but very small (33 classes) and early (v0.1). Added 2026-10-17 second-pass gap analysis. | `https://data.bioontology.org/ontologies/NEUMORE/download?apikey=YOUR_KEY` |
| **ECP** | Electronic Care Plan | 32 | 0.6 | — | Our focus in this work is to define in a formal way (ontology-based) and platform independent representative metadata and relationships of care plans. This approach has as goal to work as an umbrella over all these systems and provides some | `https://data.bioontology.org/ontologies/ECP/download?apikey=YOUR_KEY` |
| **FALLS** | falls prevention | 30 | 0.1 | — | This ontology is about a falls prevention intervention record. | `https://data.bioontology.org/ontologies/FALLS/download?apikey=YOUR_KEY` |
| **YOGA** | Yoga Ontology | 17 | 0.1 | — | Yoga Ontology is the list of vocabularies that define the yogic practice. Where Yoga is the union of the mind and body. | `https://data.bioontology.org/ontologies/YOGA/download?apikey=YOUR_KEY` |
| **LONGCOVID** | Long Covid Phenotype Ontology | 9 | 20220106 | — | Oxford-RCGP RSC Long COVID-19 (LC) Phenotype Ontology | `https://data.bioontology.org/ontologies/LONGCOVID/download?apikey=YOUR_KEY` |
| **ECDO** | Elderly Care Dementia Ontology | 2 | — | — | This is an ontology for elderly dementia care in the Netherlands. | `https://data.bioontology.org/ontologies/ECDO/download?apikey=YOUR_KEY` |

## D. Not recommended

Matched keyword filters but is out of PT/rehab scope (oncology, model organisms, imaging, agriculture, basic science), duplicates an already-loaded resource, or has licensing concerns.

| Acronym | Name | Classes | Ver | License | Description | Download URL |
|---------|------|--------:|-----|---------|-------------|--------------|
| **UPHENO** | Combined Phenotype Ontology | 193,297 | 2025-10-12 | — | Combined phenotype ontology, The Unified Phenotype Ontology (uPheno) is an ontology that integrates other species-specific phenotype ontologies. | `https://data.bioontology.org/ontologies/UPHENO/download?apikey=YOUR_KEY` |
| **RADLEX** | Radiology Lexicon | 46,900 | 4.3 | — | RadLex OWL, as downloaded from BioPortal, includes a set of puns in order to facilitate browsing and display. For the base RadLex ontology alone, without puns, and release notes for the latest version, please see http://radlex.org/ | `https://data.bioontology.org/ontologies/RADLEX/download?apikey=YOUR_KEY` |
| **FLOPO** | Flora Phenotype Ontology | 30,739 | 2026-10-05 | — | The Flora Phenotype Ontology is an ontology of phenotypes reported in Floras. The original version was developed at the pro-iBiosphere Hackathon in Leiden. This is the pre-classified version of the ontology; the original OWL file is at http | `https://data.bioontology.org/ontologies/FLOPO/download?apikey=YOUR_KEY` |
| **HP** | Human Phenotype Ontology | 23,927 | 2026-09-01 | — | The Human Phenotype Ontology is being developed to provide a structured and controlled vocabulary for the phenotypic features encountered in human hereditary and other disease. Our goal is to provide resource for the computational analysis  | `https://data.bioontology.org/ontologies/HP/download?apikey=YOUR_KEY` |
| **OMCO** | OligoMetastatic Cancer Ontology | 15,314 | — | — | The OligoMetastatic Cancer Ontology(OMCO) is a disease-specific ontology that characterizes the knowledge field of oligometastatic cancer. | `https://data.bioontology.org/ontologies/OMCO/download?apikey=YOUR_KEY` |
| **PHIPO** | Pathogen Host Interaction Phenotype Ontology | 10,728 | 2026-08-06 | — | PHIPO is a formal ontology of species-neutral phenotypes observed in pathogen-host interactions. PHIPO is being developed to support the comprehensive and detailed representation of phenotypes in PHI-base, the multi-species Pathogen-Host In | `https://data.bioontology.org/ontologies/PHIPO/download?apikey=YOUR_KEY` |
| **PLOSTHES** | PLOS Thesaurus | 10,716 | plosthes.2017-1 | — | Name looks prosthetics-related ("PLOSTHES") but it is the PLOS journals' subject-area thesaurus — a false-positive keyword match, not a prosthetics ontology. Added 2026-10-17 second-pass gap analysis. | `https://data.bioontology.org/ontologies/PLOSTHES/download?apikey=YOUR_KEY` |
| **NPOKB** | Neuron Phenotype Ontology | 6,875 | 2026-03-19 | — | An ontology of neuron types based on the phenotypic dimensions of cells that can be measure experimentally. | `https://data.bioontology.org/ontologies/NPOKB/download?apikey=YOUR_KEY` |
| **ODAE** | Ontology of Drug Adverse Events | 3,672 | Vision Release: 1.0.08 | — | The Ontology of Drug Adverse Events (ODAE) is a biomedical ontology in the area of drug adverse events, developed by following OBO Foundry principles (e.g., openness, collaboration). | `https://data.bioontology.org/ontologies/ODAE/download?apikey=YOUR_KEY` |
| **PLANP** | Planarian Phenotype Ontology | 3,562 | — | — | Planarian Phenotype Ontology is an ontology of phenotypes observed in the planarian Schmidtea mediterranea. Many of the phenotypes were seen durning RNAi experiments. | `https://data.bioontology.org/ontologies/PLANP/download?apikey=YOUR_KEY` |
| **ICD-O-3** | International Classification of Diseases for Oncology,  | 2,753 | OCD-O Revision 3.2 (complete | — | Ontology used for oncology research derived from the European Cancer Information System (ECIS) | `https://data.bioontology.org/ontologies/ICD-O-3/download?apikey=YOUR_KEY` |
| **WB-PHENOTYPE** | C. elegans Phenotype Vocabulary | 2,712 | 2026-04-15 | — | A structured controlled vocabulary of <i>Caenorhabditis elegans</i> phenotypes | `https://data.bioontology.org/ontologies/WB-PHENOTYPE/download?apikey=YOUR_KEY` |
| **OMP** | Ontology of Microbial Phenotypes | 2,309 | releases/2019-06-07 | — | OMP is a formal ontology of phenotypes observed in all microbes: bacteria, archaea, protists, fungi, and viruses. OMP is being developed to be compatible with other microbial phenotype ontologies, such as the Fission Yeast Phenotype Ontolog | `https://data.bioontology.org/ontologies/OMP/download?apikey=YOUR_KEY` |
| **O3** | Operational Ontology for Oncology | 2,108 | 2.0 | — | The Operational Ontology for Oncology is formalized, machine-readable knowledge representation that defines and standardizes the concepts, terms, value sets and relationships used in cancer care. O3 is an operational ontology, meaning that  | `https://data.bioontology.org/ontologies/O3/download?apikey=YOUR_KEY` |
| **TAON** | Therapeutic Antibody Ontology | 1,964 | 1.1 | — | TAON is a comprehensive ontology of the therapeutic antibody, which included antibody terms and drug terms. | `https://data.bioontology.org/ontologies/TAON/download?apikey=YOUR_KEY` |
| **HENECON** | Head and Neck Cancer Ontology | 1,841 | 2.0 | — | HeNeCOn (Head and Neck Cancer Ontology) is the first ontology specifically focused on the Head and Neck Cancer (HNC) domain. It provides a clinically reliable data model for HNC processes during all phases of the disease: prognosis, treatme | `https://data.bioontology.org/ontologies/HENECON/download?apikey=YOUR_KEY` |
| **ODNAE** | Ontology of Drug Neuropathy Adverse Events | 1,544 | Vision Release; 1.0.13 | — | ODNAE is an extension of OAE with a focus on drug-associated neuropathy adverse events. | `https://data.bioontology.org/ontologies/ODNAE/download?apikey=YOUR_KEY` |
| **ROO** | Radiation Oncology Ontology | 1,307 | 0.5 | — | The Radiation Oncology Ontology aims to cover the radiation oncology domain with a strong focus on re-using existing ontologies. From release 0.5 forward the ROO has changed its naming scheme from all entities starting with numbers to all e | `https://data.bioontology.org/ontologies/ROO/download?apikey=YOUR_KEY` |
| **CCTOO** | Cancer Care: Treatment Outcome Ontology | 1,133 | releases/2018-05-11 | — | The Cancer Care: Treatment Outcomes Ontology (CCTOO) catalogues various clinical endpoints used in evaluating outcomes of cancer treatment. In addition to a vocabulary list, CCTOO also curates the dependencies between individual concepts, i | `https://data.bioontology.org/ontologies/CCTOO/download?apikey=YOUR_KEY` |
| **IRAEO** | Immune-Related Adverse Event Ontology | 862 | — | — | irAEO (Immune-Related Adverse Event Ontology) irAEO is a biomedical ontology that standardizes the representation of immune-related adverse events (irAEs) following cancer immunotherapy, especially immune checkpoint inhibitor (ICI) treatmen | `https://data.bioontology.org/ontologies/IRAEO/download?apikey=YOUR_KEY` |
| **CMPO** | Cellular microscopy phenotype ontology | 813 | 1.3 | — | The Cellular Microscopy Phenotype Ontology (CMPO) is a species neutral ontology for describing general phenotypic observations relating to the whole cell, cellular components, cellular processes and cell populations. CMPO is an application  | `https://data.bioontology.org/ontologies/CMPO/download?apikey=YOUR_KEY` |
| **APO** | Ascomycete Phenotype Ontology | 619 | 2026-09-30 | — | A structured controlled vocabulary for the phenotypes of Ascomycete fungi, A structured controlled vocabulary for the phenotypes of Ascomycete fungi. | `https://data.bioontology.org/ontologies/APO/download?apikey=YOUR_KEY` |
| **BHO** | Bleeding History Phenotype Ontology | 544 | 0.4 | — | An application ontology devoted to the standardized recording of phenotypic data related to hemorrhagic disorders. | `https://data.bioontology.org/ontologies/BHO/download?apikey=YOUR_KEY` |
| **SPTO** | Solanaceae Phenotype Ontology | 501 | unknown | — | Solanaceae crop phenotypes and traits, developed in collaboration with the research community, especially for breeder traits of agronomic importance. | `https://data.bioontology.org/ontologies/SPTO/download?apikey=YOUR_KEY` |
| **CTO-NDD** | Clinical Trials Ontology - Neurodegenerative Diseases | 377 | 0.6 | — | The CTO-NDD stands for Clinical Trial Ontology-Neurodegenerative Diseases, which was built with the purpose of organizing the knowledge domain of clinical trials in neurodegeneration field. This resource has been created for use in the IMI- | `https://data.bioontology.org/ontologies/CTO-NDD/download?apikey=YOUR_KEY` |
| **NEOMARK4** | Neomark Oral Cancer Ontology, version 4 | 325 | 4.1 | — | Ontology that describes the medical information necessary for early detection of the oral cancer reoccurrence extracted from the NeoMark Project. | `https://data.bioontology.org/ontologies/NEOMARK4/download?apikey=YOUR_KEY` |
| **ASDPTO** | Autism Spectrum Disorder Phenotype Ontology | 284 | 1 | — | Autism Spectrum Disorder Phenotype Ontology encapsulates the Autism Spectrum Disorder behavioral phenotype, informed by the standard ASD assessment instruments and the currently known characteristics of this disorder. http://www.ncbi.nlm.ni | `https://data.bioontology.org/ontologies/ASDPTO/download?apikey=YOUR_KEY` |
| **MFMO** | Mammalian Feeding Muscle Ontology | 268 | — | — | An antomy ontology for the muscles of the head and neck that participate in feeding, swallowing, and other oral-pharyngeal behaviors. | `https://data.bioontology.org/ontologies/MFMO/download?apikey=YOUR_KEY` |
| **DILON** | Dietary lifestyle ontology | 261 | 2 | — | DILON was created to represent dietary lifestyle data. Concepts were pulled from Korean dietary assessment scales and English assessment scales. Concepts are labeled in English and Korean translations are also provided. | `https://data.bioontology.org/ontologies/DILON/download?apikey=YOUR_KEY` |
| **CST** | Cancer Staging Terms | 168 | — | — | This ontology consists of cancer staging terms that specify higher-level terms that are useful in classifying cancer, specifically breast cancer, according to the AJCC 7th and 8th editions. | `https://data.bioontology.org/ontologies/CST/download?apikey=YOUR_KEY` |
| **CANCO** | Cancer Chemoprevention Ontology | 127 | 0.3 | — | The Cancer Chemoprevention Ontology constitutes a vocabulary that is able to describe and semantically interconnect the different paradigms of the cancer chemoprevention domain. | `https://data.bioontology.org/ontologies/CANCO/download?apikey=YOUR_KEY` |
| **CTGO** | Clinical Trials Gov Ontology | 121 | 1.0 | — | The Clinical Trials Gov Ontology (CTGO) is based on the AACT database schema for Aggregate Analysis of ClinicalTrials.gov. AACT contains information about clinical studies that have been registered at ClinicalTrials.gov. AACT includes all o | `https://data.bioontology.org/ontologies/CTGO/download?apikey=YOUR_KEY` |
| **PE** | Pulmonary Embolism Ontology | 97 | version 1.0 | — | A controlled vocabulary of PE-relevant information. Currently, only treatment information is available. | `https://data.bioontology.org/ontologies/PE/download?apikey=YOUR_KEY` |
| **CANONT** | Upper-Level Cancer Ontology | 56 | unknown | — | Providing an upper-level ontology for cancer. | `https://data.bioontology.org/ontologies/CANONT/download?apikey=YOUR_KEY` |
| **NEOMARK3** | Neomark Oral Cancer Ontology, version 3 | 55 | 3.1 | — | Ontology that describes the medical information necessary for early detection of the oral cancer reoccurrence extracted from the NeoMark Project. | `https://data.bioontology.org/ontologies/NEOMARK3/download?apikey=YOUR_KEY` |
| **PTRO** | Preclinical Trials in Radiation Oncology Ontology | 43 | 0.1 alpha | — | PTRO focuses on preclinical data standardized according to SEND, with emphasis on radiation oncology studies. It is not intended to replace clinical trial ontologies or general-purpose biomedical ontologies but to complement them by address | `https://data.bioontology.org/ontologies/PTRO/download?apikey=YOUR_KEY` |
| **BCSR-ONTO** | Breast cancer screening recommendation ontology | 34 | 2.1 | — | BCSR-Onto represents knowledge about risk assessment and recommendations by diverse guidelines for breast cancer screening both for women at high and average risk of developing breast cancer. | `https://data.bioontology.org/ontologies/BCSR-ONTO/download?apikey=YOUR_KEY` |
| **BCS8** | Breast Cancer Staging - 8th Edition | 31 | version 0.1 | — | Breast Cancer Staging axioms as per the AJCC 8th Edition Guidelines. | `https://data.bioontology.org/ontologies/BCS8/download?apikey=YOUR_KEY` |
| **BCLION** | Breast Cancer Lifestyle Ontology | 30 | 1.0 | — | The Breast Cancer Lifestyle Ontology (BCLION) captures various factors related to lifestyle choices and behaviors that may influence the risk of developing breast cancer. It provides a structured representation of these factors in a hierarc | `https://data.bioontology.org/ontologies/BCLION/download?apikey=YOUR_KEY` |
| **BCS7** | Breast Cancer Staging - 7th Edition | 22 | version 0.1 | — | Breast Cancer Staging axioms as per the AJCC 7th Edition Guidelines. | `https://data.bioontology.org/ontologies/BCS7/download?apikey=YOUR_KEY` |
| **WEAVE** | WEAVE: Wind Energy ActiVitiEs | 21 | v0.1.0 | — | Wind-energy research-activity taxonomy (SKOS) from EERA JP WIND. Matched an "activit*" keyword search but is entirely out of PT/rehab scope. Added 2026-10-17 after a BioPortal search spot-check. | `https://data.bioontology.org/ontologies/WEAVE/submissions/1/download?apikey=YOUR_KEY` |
| **ONTOTOX** | Chemotherapy Toxicities Ontology | 16 | 1.0 | — | OntoTox is an ontology designed to represent chemotherapy toxicities extracted from various data in Clinical Data Warehouses. OntoTox can integrate toxicities and grading information extracted from heterogeneous sources. Examples of OntoTox | `https://data.bioontology.org/ontologies/ONTOTOX/download?apikey=YOUR_KEY` |
| **NIC** | Nursing Interventions Classification | — | — | — | Keyword match; no strong PT/rehab fit identified during review. | `https://data.bioontology.org/ontologies/NIC/download?apikey=YOUR_KEY` |

---

## Shortlist summary (what was wired into the pipeline)

| Acronym | BioPortal submission | Version | Pinned download |
|---------|---------------------:|---------|-----------------|
| TRAK | #5 | unknown | `https://data.bioontology.org/ontologies/TRAK/submissions/5/download?apikey=YOUR_KEY` |
| FRMO | #19 | 09.10 | `https://data.bioontology.org/ontologies/FRMO/submissions/19/download?apikey=YOUR_KEY` |
| PAIN | #12 | 2026-10-01 | `https://data.bioontology.org/ontologies/PAIN/submissions/12/download?apikey=YOUR_KEY` |
| BCIO | #1 | — | `https://data.bioontology.org/ontologies/BCIO/submissions/1/download?apikey=YOUR_KEY` |
| BCTT | #6 | 0.4 | `https://data.bioontology.org/ontologies/BCTT/submissions/6/download?apikey=YOUR_KEY` |
| STO-DRAFT | #1 | 2017-11-01 | `https://data.bioontology.org/ontologies/STO-DRAFT/submissions/1/download?apikey=YOUR_KEY` |
| PACO | #2 | 0.2 | `https://data.bioontology.org/ontologies/PACO/submissions/2/download?apikey=YOUR_KEY` |
| MSO | #2 | — | `https://data.bioontology.org/ontologies/MSO/submissions/2/download?apikey=YOUR_KEY` |
| POEM | #8 | 1.0 | `https://data.bioontology.org/ontologies/POEM/submissions/8/download?apikey=YOUR_KEY` |
| CBHA | #1 | 2026.05.03 | `https://data.bioontology.org/ontologies/CBHA/submissions/1/download?apikey=YOUR_KEY` |
| PHENX | #16 | 1.2 | `https://data.bioontology.org/ontologies/PHENX/submissions/16/download?apikey=YOUR_KEY` |
| NIHSS | #15 | 2024/06 | `https://data.bioontology.org/ontologies/NIHSS/submissions/15/download?apikey=YOUR_KEY` |

## Related: REHABO update

REHABO's current BioPortal release is submission **#2** (version `2026-09-29`, released 2026-09-29), **251 classes** — the pipeline previously pointed at submission #1 (29 concepts). `download_data.py` was re-pointed at the latest release in this change:

```
https://data.bioontology.org/ontologies/REHABO/download?apikey=YOUR_KEY   # latest (sub #2)
```

## Appendix: how URLs work

- **Pinned (shortlist)**: `https://data.bioontology.org/ontologies/{ACR}/submissions/{N}/download?apikey={KEY}` — reproducible, matches the repo's existing convention of pinning submissions (e.g. ICF #3, OPE #6).
- **Latest (other tiers)**: `https://data.bioontology.org/ontologies/{ACR}/download?apikey={KEY}` — resolves to the newest submission at download time.
- All shortlisted ontologies are **not** "summary only" in BioPortal, so their classes are indexable and their OWL is downloadable.
- Class counts come from each ontology's BioPortal `metrics` endpoint (latest submission).
- BioPortal catalog: 1,297 unique ontologies as of 2026-10-16.

## Integration points

- `download_data.py` — new BioPortal download entries + REHABO re-pointed to the current release
- `etl_ontologies.py` — OWL parsing into Neo4j with `SUBCLASS_OF` hierarchies and new labels
- `build_csvs.py` — bulk-import CSVs for the new concept labels and subclass edges
- `docs/DATA_SOURCES.md` — catalog entries


## End-to-end validation notes (2026-10-16)

Full e2e (CSV build → neo4j-admin bulk import → live queries → dashboard
Playwright suite) surfaced and fixed the following:

**Fixed in this change**
- **`:ID` namespacing** — `neo4j-admin` treats `:ID` as one keyspace across all
  node files and silently drops later-file duplicates. Short/fragment codes
  collided across ontologies (268 nodes of the shortlist were being dropped,
  e.g. `MFOEM_000195` shared by BCIO and COPPER). `build_csvs.ontology_eid()`
  now prefixes short codes with the ontology acronym (`BCIO:MFOEM_000195`);
  CURIE codes like `TRAK:0000001` are kept. Collisions from the new files: 0.
- **`code` property on bulk-imported nodes** — node CSVs wrote the code only as
  `:ID`, leaving `n.code` null after bulk import. Curated bridges
  (`bridge_rehabo_to_icf`, `bridge_ontologies`) match `ICFConcept {code:…}` and
  `export_csv` exports `n.code`, so they silently matched nothing on bulk
  graphs. ICF and all 15 concept CSVs now carry a `code` column.
- **REHABO prop/individual `uri` column** — `load_rehabo` MERGEs by `uri`;
  without the column on `OntologyProperty`/`OntologyIndividual` rows, running
  the Cypher path after bulk import duplicated them (36→72, 23→46).
- **APOC on the test container** — `import_bulk.start_neo4j` now mounts
  `docker/plugins` (apoc jar) and sets `dbms.security.procedures.unrestricted=apoc.*`;
  `dedup_check` (`apoc.refactor.mergeNodes`) previously could never run there.
- **Dashboard empty-result crash** — the ICF→Exercise table raised
  `KeyError: ['icf_code',…] not in index` when the query returned no rows.

**Known limitations (pre-existing, not changed here)**
- 167 `:ID` collisions remain among the *older* files (102 REHABO↔Uberon and
  36 Mondo↔Uberon are legitimate same-concept merges; COPPER↔KHMO and
  MELLO-D↔OPE/ONTOLOCO are true cross-file duplicates). Only the 2026-10
  shortlist files were namespaced to avoid changing legacy behaviour.
- The bulk path and the Cypher path (`rehabkg.py --only ontologies`) are
  alternatives, not stages: mixing them creates a parallel node layer for
  concepts whose URIs span two ontology files (e.g. 102 Uberon classes
  referenced by REHABO), because `MERGE (n:OntologyClass {uri})` is
  label-scoped. Run one path per graph.
- STO-DRAFT is the 2017 draft of the Stroke Ontology and mixes stroke-specific
  terms (~14% obvious stroke/vascular names by regex) with broader
  stroke-context background terms (biomarkers, risk factors, mechanisms —
  e.g. "Nitric oxide synthesis", "Carotid Intima Media Thickness"). Review
  before using STOConcept for precision-sensitive retrieval.

**Validation status**: 65 offline tests + 43/43 dashboard Playwright e2e pass;
per-label node/edge counts in Neo4j match the CSVs exactly (TRAK 1,619/1,635,
FRMO 890/847, PAIN 623/711, BCIO 2,523/2,542, BCTT 109/93, STO 1,711/1,959,
PACO 224/217); curated REHABO→ICF CLOSE_MATCH 5/5 edges land.

## Search spot-check (2026-10-17)

Statuses below reflect the pipeline as of 2026-10-17; see the 2026-11-05 status
update above for the focused graph.

Manual BioPortal site searches for "physical", "rehab", "activity" — every
ontology in the autocomplete dropdowns, cross-checked against the pipeline:

| Ontology | Seen in | Status |
|----------|---------|--------|
| COPPER | physical, activity | ✅ In pipeline (`copper`, 362 concepts) |
| OPE | physical | ✅ In pipeline (`ope`, 632 concepts) |
| OPTIMAL (OPTImAL) | physical, activity | 📋 Tier 1 follow-up (142 classes) |
| PACO | physical, activity | ✅ In pipeline (2026-10 shortlist, 224 concepts) |
| PMR | physical, rehab | ✅ In pipeline (`pmr`, 1,597 concepts) |
| CABRO | rehab | 📋 Tier 2 (59 classes) |
| TRAK | rehab | ✅ In pipeline (2026-10 shortlist, 1,619 concepts) |
| REHABO | rehab | ✅ In pipeline, updated to sub #2 (251 classes) |
| CBHA | activity | ➕ Added to Tier 1 (was missed by the 2026-10-16 sweep's keyword filters) |
| WEAVE | activity | ➕ Added to Not recommended (wind-energy domain, out of scope) |

---

## Second-pass gap analysis (2026-10-17)

Follow-up sweep answering "what is still missing for PT/rehab?" beyond the
2026-10-16 catalog sweep and the site spot-check above.

**Method.** (1) A PT/rehab name lexicon (~40 term families: physical therap*,
rehab*, exercise*, gait, wheelchair, prosthe*, orthos*, fall*, specific
conditions/outcomes) re-filtered all 1,297 catalog names → 20 not already
documented. (2) 40 content queries against BioPortal's `/search` endpoint for
terms unlikely to appear in ontology *names* (telerehabilitation, exergaming,
GMFCS, Berg Balance, Timed Up and Go, WOMAC, Oswestry, prosthetic socket,
lymphedema, vestibular rehabilitation, mirror therapy, constraint-induced
movement, FES, Barthel index, PROMIS, pressure ulcer, spasticity, sarcopenia,
frailty index, fall prevention, …), collecting every ontology that surfaces.
(3) A supplementary name scan for outcome/guideline/condition terms. The union
(~48 acronyms) minus the 98 already documented was triaged by fetched
description + class count.

**Added.** Tier 1: MSO, POEM. Tier 2: PDON, STMSO, RAO, NEUMORE,
ACVD_ONTOLOGY, CVAO, CMO, MIO, COPDO, HIO. Not recommended: PLOSTHES
(false-positive name match).

**Excluded as out of scope.** Cognitive-science task/condition ontologies
(COGAT, COGPO, COGITO, COGMEMO, ONL-TASKS) — research-experiment tooling, not
clinical rehab; sleep ontologies (SDO, SLEEP, SL_DIS) — marginal outcome
factor; imaging ontologies (IBO, MIDO, EDAM-BIOIMAGING, FBbi); COVID/
senescence (HOIP); sickle cell (SCDO); physiology simulation (HUPSON);
neuroimaging provenance (NEUROBRG); endoscopy (MSTDE); wellness taxonomy
(ICW, low value); clinical-research study structure (OCRE); rheumatology
diagnosis helper (AI-RHEUM, UMLS-dependent).

**Residual content gaps (no dedicated BioPortal ontology exists).**
Intervention-domain terms searched but never surfaced in a relevant
ontology: telerehabilitation, exergaming/gamification, wheelchair
propulsion, manual therapy/mobilization, functional electrical stimulation,
mirror therapy, constraint-induced movement therapy, vestibular
rehabilitation, lymphedema management. These domains are represented in the
graph via the Exercise taxonomy and WikiRehabData instead. Outside BioPortal
entirely: SNOMED CT and LOINC (licensed, reachable via UMLS), PROMIS
instruments (HealthMeasures; POEM/PHENX partially cover the psychometric
structure), FIM/WeeFIM (licensed).
