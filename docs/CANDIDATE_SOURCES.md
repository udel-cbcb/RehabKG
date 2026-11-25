# Rehabilitation Knowledge Graph - Candidate Public Data Sources

This document catalogs publicly available datasets, ontologies, and resources for building a physical rehabilitation knowledge graph in Neo4j.

> Note: for the sources **currently loaded in the graph** (counts, loader scripts, and staging paths), see [`docs/DATA_SOURCES.md`](DATA_SOURCES.md). This file is the broader public-candidate catalog (moved from the repository root on 2026-10-22).

---

## 📊 Exercise & Movement Datasets

### 1. REHAB24-6: Multi-modal Physical Therapy Dataset (2024)
- **Source**: Zenodo
- **DOI**: 10.5281/zenodo.13305826
- **License**: CC BY-NC 4.0
- **Size**: ~668 MB
- **Contents**:
  - 65 recordings (184,825 frames, 30 FPS)
  - RGB videos from 2 cameras
  - 3D/2D positions of 41 motion capture markers
  - 3D/2D positions of 26 skeleton joints
  - 1,072 exercise repetitions with temporal segmentation
  - Binary correctness labels (~90 per category per exercise)
- **Download**: https://zenodo.org/records/13305826
- **Format**: CSV, ZIP (videos, markers, joints)
- **Use Case**: Exercise recognition, correctness assessment, pose estimation

### 2. IntelliRehabDS (IRDS) - Physical Therapy Movements (2022)
- **Source**: Zenodo / MDPI Data
- **DOI**: 10.5281/zenodo.4610859
- **License**: Open access
- **Contents**:
  - 3D skeleton joint positions from Kinect sensor
  - 15 patients + 14 healthy persons
  - 9 gesture types (0-8)
  - Correct/incorrect execution labels (annotated by 2 experts)
  - Sitting/standing positions
- **Format**: CSV files (one per exercise per person)
- **Naming**: `SubjectID_DateID_GestureLabel_RepetitionNumber_CorrectLabel_Position.txt`
- **Download**: https://zenodo.org/records/4610859
- **Paper**: Miron et al., Data 2021, 6(5), 46

### 3. UI-PRMD: University of Idaho Physical Therapy Movement Data (2018)
- **Source**: MDPI Data
- **DOI**: 10.3390/data3010002
- **Contents**:
  - 10 healthy subjects
  - 10 repetitions of 10 physical therapy movements
  - Vicon optical tracker + Microsoft Kinect
  - Full-body joint positions and angles
- **Download**: https://www.mdpi.com/2306-5729/3/1/2/pdf
- **Use Case**: Mathematical modeling of therapy movements, performance metrics

### 4. Free Exercise Database (800+ exercises)
- **Source**: GitHub (yuhonas/free-exercise-db)
- **License**: Unlicense (Public Domain)
- **Contents**:
  - 800+ exercises in JSON format
  - Fields: id, name, force, level, mechanic, equipment, primaryMuscles, secondaryMuscles, instructions, category, images
  - Searchable frontend available
- **Download**: https://github.com/yuhonas/free-exercise-db
- **Raw JSON**: https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json
- **Schema**: https://github.com/yuhonas/free-exercise-db/blob/main/schema.json

### 5. RepDB Exercise Dataset (250 exercises)
- **Source**: GitHub (RepDB/exercise-dataset)
- **License**: Commercial use with attribution
- **Contents**:
  - 250 exercises with 512px WebP images
  - Muscles, equipment, MET values
  - EN/DE/ES instructions
- **Download**: https://github.com/RepDB/exercise-dataset

### 6. StrokeRehab Dataset
- **Source**: GitHub Pages (strokerehabdata.github.io)
- **Focus**: Quantifying rehabilitation therapy
- **Use Case**: ML/DL models for therapy quantification
- **Website**: https://strokerehabdata.github.io/dataset.html

### 7. UL-RED: University of Liverpool Rehabilitation Exercise Dataset (2024)
- **Source**: DataCat Liverpool
- **Record**: https://datacat.liverpool.ac.uk/2729
- **Formats**: RDF, CSV, JSON, XML, N-Triples

### 8. REHAB: Wearable Sensor Kinematic Dataset for Stroke Rehabilitation (2026)
- **Source**: Science Data Bank / Nature Scientific Data
- **DOI**: 10.57760/sciencedb.37018
- **License**: Open Access
- **Contents**: 120 post-stroke patients, 27 assessment + 16 training movements, IMU+flex sensors
- **Download**: https://www.scidb.cn/en/s/YrUnie
- **GitHub**: https://github.com/zzzzz-123/REHAB

### 9. KneE-PAD: Knee Rehabilitation Exercises Dataset (2025)
- **Source**: Zenodo / Nature Scientific Data
- **DOI**: 10.1038/s41597-025-04963-4
- **License**: CC BY 4.0
- **Contents**: 31 patients, squats/leg extension/walking, 8 sEMG + 8 IMU sensors
- **GitHub**: https://github.com/ospanas/KneE-PAD

### 10. GAITEX: Gait & Rehabilitation Exercises (2025)
- **Source**: Zenodo / Nature Scientific Data
- **DOI**: 10.1038/s41597-025-06439-x
- **License**: CC BY-NC-ND 4.0
- **Contents**: 19 subjects, 9 IMUs + 68 MoCap markers, foot drop rehab exercises
- **Download**: https://zenodo.org/records/15729055
- **GitHub**: https://github.com/ai-for-sensor-data-analytics-ulm/aisd_ortho_ki_dataset

### 11. GaitIntent: Transitional Locomotion Dataset (2026)
- **Source**: Figshare / Nature Scientific Data
- **DOI**: 10.1038/s41597-026-07799-8
- **License**: CC BY-NC-ND 4.0
- **Contents**: 11 subjects, 13 locomotion modes, 8 transitional movements
- **Download**: https://doi.org/10.6084/m9.figshare.31436731

### 12. UCOPhyRehab++: Multi-modal Rehab Video (2025)
- **Source**: Zenodo / Nature Scientific Data
- **DOI**: 10.1038/s41597-026-07362-5
- **License**: CC BY-NC-ND 4.0
- **Contents**: Multi-view video, expert quality scores, demographic metadata
- **Download**: https://doi.org/10.5281/zenodo.17935736
- **GitHub**: https://github.com/AVAuco/ucophyrehabpp

### 13. K2MUSE: Lower-Limb Multimodal Dataset (2025)
- **Source**: Kaggle / arXiv
- **License**: Open Access
- **Contents**: 30 subjects, kinematics+kinetics+sEMG+ultrasound, various walking conditions
- **Download**: https://k2muse.github.io/datasets/

### 14. ExoMove: Lower-Limb Exoskeleton Kinematics (2024)
- **Source**: Zenodo
- **License**: Open Access
- **Size**: 500 MB
- **Contents**: Daily activities with 2 exoskeletons (eWalk, Autonomyo)
- **Download**: https://zenodo.org/records/14076104

### 15. ARMin 5 Fusion Therapy Dataset (2025)
- **Source**: Zenodo
- **License**: Open Access
- **Contents**: EMG + arm angle, able-bodied + stroke patients, rehab robot
- **Download**: https://zenodo.org/records/14800465
- **GitHub**: https://github.com/fabianjust/FusionTherapy

### 16. MOTU: Amputation Rehabilitation (FHIR) (2024)
- **Source**: Zenodo / Nature Scientific Data
- **License**: CC BY 4.0
- **Size**: 1,006 trans-femoral amputees, 10-year dataset
- **Contents**: Clinical features, mobility, prosthetic knees, CSV + FHIR format
- **GitLab**: https://gitlab.com/almahealthdb/ahdb-mapping-service/

### 17. San Raffaele Rehabilitation Dataset (2020)
- **Source**: Figshare / ScienceDirect
- **License**: CC BY 4.0
- **Size**: 3,928 patients (orthopedic + neurological)
- **Contents**: Barthel Index, ICD-9-CM codes, demographics
- **Download**: https://figshare.com/s/7aab7ad2d351f53dbe2f

### 18. EEG-EMG-WristMotion Dataset (2025)
- **Source**: Figshare / Nature Scientific Data
- **DOI**: 10.1038/s41597-026-07287-z
- **License**: CC BY 4.0
- **Contents**: 45 subjects, synchronized EEG+EMG+kinematics, wrist motor tasks
- **Download**: https://doi.org/10.6084/M9.FIGSHARE.29666735.v3

### 19. BATEX: Biarticular Thigh Exosuit Biomechanics (2024)
- **Source**: TU Darmstadt
- **DOI**: 10.48328/tudatalib-1588
- **License**: Open Access
- **Contents**: Motion capture, GRF, EMG, respiratory data, exosuit torque
- **Download**: https://doi.org/10.48328/tudatalib-1588

### 20. DATASET_SDALLE: Lower Limb HAR for Exoskeletons (2025)
- **Source**: Zenodo
- **License**: Open Access
- **Contents**: 9 subjects, EMG+IMU, walking/jumping/stairs
- **Download**: https://zenodo.org/records/14841611

---

## 📊 Clinical Outcome Measures Databases

### 1. Rehabilitation Measures Database (RMD)
- **Source**: Shirley Ryan AbilityLab
- **URL**: https://www.sralab.org/rehabilitation-measures
- **License**: Free
- **Contents**: 600+ validated outcome measures with psychometric properties, scoring instructions
- **Use Case**: Assessment selection, benchmarking, outcome tracking

### 2. Rehab-scales
- **Source**: rehab-scales.org
- **URL**: https://www.rehab-scales.org/
- **License**: Personal/Therapist/Clinical trial licenses
- **Contents**: ICF-mapped evaluation scales for various pathologies
- **Use Case**: Functional status assessment, treatment planning

### 3. PROQOLID (Mapi Research Trust)
- **Source**: Mapi Research Trust
- **URL**: https://www.mapi-trust.org/services/eprovide/proqolid
- **License**: Registration required
- **Contents**: 9,000+ Clinical Outcome Assessments (COAs) described
- **Use Case**: COA selection for clinical research

### 4. MeasuReIT
- **Source**: Italian Society of Physiotherapy
- **URL**: https://database.sif-fisioterapia.it/en/about-measureit/
- **License**: SIF members
- **Contents**: 400+ validated instruments (Italian version)
- **Use Case**: Physiotherapy measurement instrument selection

---

## 🧠 Ontologies & Knowledge Organization Systems

### 1. REHABO - The Rehabilitation Ontology (2026)
- **Source**: NCBO BioPortal / OBO Foundry
- **IRI**: http://purl.obolibrary.org/obo/rehabo.owl
- **License**: CC0 (Public Domain)
- **Format**: OWL, RDF/XML, CSV
- **Stats**: 112 classes, 23 individuals, 32 properties, max depth 11
- **Scope**: Physical medicine & rehabilitation, physical therapy, occupational therapy, speech therapy
- **Download**: https://data.bioontology.org/ontologies/REHABO/submissions/1/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb
- **Version**: 2026-04-22

### 2. ICF - International Classification of Functioning, Disability and Health
- **Source**: WHO / NCBO BioPortal
- **IRI**: http://who.int/icf
- **Format**: OWL, RDF/XML, CSV
- **Stats**: 1,596 classes, 4,807 individuals, 67 properties
- **Components**:
  - Body Functions (b)
  - Body Structures (s)
  - Activities & Participation (d)
  - Environmental Factors (e)
  - Personal Factors
- **Download**: https://data.bioontology.org/ontologies/ICF/submissions/3/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb
- **WHO Browser**: https://icd.who.int/browse/releases/icf/en
- **ICF Core Sets for Rehabilitation**: https://www.icf-research-branch.org/icf-core-sets

### 3. SNOMED CT (Systematized Nomenclature of Medicine - Clinical Terms)
- **Source**: NLM / NCBO BioPortal
- **IRI**: http://purl.bioontology.org/ontology/SNOMEDCT
- **Format**: UMLS, RDF/OWL (via UMLS2RDF)
- **Size**: 300,000+ concepts, 1M+ descriptions, 903,000+ relationships
- **US Edition**: https://www.nlm.nih.gov/healthit/snomedct/us_edition.html
- **BioPortal**: https://bioportal.bioontology.org/ontologies/SNOMEDCT
- **Note**: Requires UMLS license (free for research)

### 4. EXMO - Exercise Medicine Ontology (OBO Foundry)
- **Source**: OBO Foundry / GitHub
- **IRI**: http://purl.obolibrary.org/obo/exmo.owl
- **License**: CC BY 4.0
- **Format**: OWL, OBO
- **GitHub**: https://github.com/Exercise-Medicine-Ontology/EXMO
- **Focus**: Exercise medicine for healthy people, chronic conditions, and disability
- **Download**: https://raw.githubusercontent.com/Exercise-Medicine-Ontology/EXMO/master/exmo.owl

### 5. PMR - Physical Medicine and Rehabilitation Ontology
- **Source**: NCBO BioPortal
- **IRI**: http://purl.bioontology.org/ontology/PMR.owl
- **License**: Open Access
- **Format**: OWL
- **Description**: Clinical decision support in rehabilitation, integrates ICD-11, ICF, SNOMED CT
- **Download**: https://data.bioontology.org/ontologies/PMR/submissions/6/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb

### 6. MELLO-D - Medical LifeLog Ontology for people with Disability
- **Source**: NCBO BioPortal
- **License**: Open Access
- **Format**: OWL
- **Stats**: 7,399 concepts (v2.0)
- **Focus**: LifeLog data for people with disability, exercise, sports, body regions
- **Download**: https://data.bioontology.org/ontologies/MELLO-D/submissions/14/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb

### 7. COPPER - COntextualised and Personalised Physical activity and Exercise Recommendations
- **Source**: OBO Foundry / GitHub
- **License**: CC BY 4.0
- **Format**: OWL
- **Stats**: 288 classes, 64 object properties, 9 data properties
- **GitHub**: https://github.com/EBehaviourChange-COPPER/ontology
- **Focus**: Physical activity action and coping plans for primary prevention
- **Download**: https://raw.githubusercontent.com/EBehaviourChange-COPPER/ontology/main/COPPER.owl
- **Paper**: Braun et al. (2025) Int J Behav Nutr Phys Act

### 8. KHMO - Kinetic Human Movement Ontology
- **Source**: GitHub / Zenodo
- **License**: CC BY 4.0
- **Format**: OWL2
- **Stats**: 1,954 classes, 42 properties, 1,921 logical axioms
- **GitHub**: https://github.com/KHMOntology/KHMO
- **Permanent URL**: http://w3id.org/khmo
- **Focus**: Anatomical movements and physiological entities during human movement
- **Download**: https://raw.githubusercontent.com/KHMOntology/KHMO/main/khmo.owl
- **Paper**: Amith et al. (2026) Scientific Data

### 9. OPE - Ontology of Physical Exercises
- **Source**: NCBO BioPortal
- **License**: Open Access
- **Format**: OWL
- **Focus**: Exercises, movements, muscles, equipment, health outcomes, target ailments
- **Download**: https://data.bioontology.org/ontologies/OPE/submissions/6/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb

### 10. PHY - Physiotherapy Ontology
- **Source**: NCBO BioPortal
- **License**: Open Access
- **Format**: OWL
- **Focus**: Physiotherapy exercises for lower limb rehabilitation (ankle pump, quad set, heel slide, straight leg raise, glute bridge)
- **Download**: https://data.bioontology.org/ontologies/PHY/submissions/2/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb

### 11. ONTOLOCO - Virtual Reality Ontology for Locomotion Rehabilitation Training of Stroke Injuries
- **Source**: NCBO BioPortal
- **License**: Open Access
- **Format**: OWL
- **Focus**: VR-based locomotion rehabilitation for stroke injuries
- **Download**: https://data.bioontology.org/ontologies/ONTOLOCO/submissions/2/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb

### 12. UMLS - Unified Medical Language System
- **Source**: NLM
- **Scope**: Metathesaurus (4M+ concepts), Semantic Network, SPECIALIST Lexicon
- **Includes**: SNOMED CT, ICD-10, ICF, RxNorm, MeSH, and 200+ other vocabularies
- **Access**: https://www.nlm.nih.gov/research/umls/ (free license required)
- **API**: UTS REST API for programmatic access

### 5. ICD-10 / ICD-11
- **Source**: WHO
- **ICD-10**: https://icd.who.int/browse10/2019/en
- **ICD-11**: https://icd.who.int/browse11/l-m/en
- **Use Case**: Disease/condition classification, billing codes

---

## 🏥 Clinical & Research Knowledge Bases

### 1. PubMed / MEDLINE
- **Source**: NCBI/NLM
- **Access**: E-utilities API, FTP bulk download
- **Size**: 36M+ citations
- **Use Case**: Literature-based knowledge extraction, evidence linking
- **API**: https://www.ncbi.nlm.nih.gov/books/NBK25501/

### 2. ClinicalTrials.gov
- **Source**: NIH
- **API**: https://clinicaltrials.gov/api/gui/
- **Use Case**: Rehabilitation intervention studies, outcome measures

### 3. Rehab-Pile (2025) - Aggregated Rehabilitation Datasets
- **Source**: Deep Learning for Skeleton Based Human Motion Rehabilitation Assessment
- **Paper**: Ismail-Fawaz et al. (2025)
- **Description**: Unified archive of existing rehabilitation datasets
- **Benchmark**: Classification and regression tasks for motion assessment

---

## 🔧 Neo4j-Specific Resources

### 1. Neo4j Example Graph Datasets
- **Repo**: https://github.com/neo4j-examples/neo4j-example-graph-datasets
- **Guide**: https://guides.neo4j.com/datasets/
- **Includes**: Load scripts, schema diagrams, example queries

### 2. PubMed Knowledge Graph Generation (Neo4j Field)
- **Repo**: https://github.com/neo4j-field/pubmed-knowledge-graph-generation
- **Features**: PDF processing, entity extraction, vector embeddings, LangGraph agent
- **Use Case**: Biomedical literature KG construction

### 3. Neo4j MCP Server (Cypher)
- **Repo**: https://github.com/neo4j-contrib/mcp-neo4j/tree/main/servers/mcp-neo4j-cypher
- **Use Case**: LLM-powered Cypher query generation

---

## 📐 Suggested Knowledge Graph Schema

### Core Node Types
```
(:Patient)
(:Condition) - ICD-10/ICD-11, SNOMED CT
(:Exercise) - from free-exercise-db, REHABO
(:BodyPart) - UBERON, FMA, SNOMED CT
(:Movement) - ICF Activities (d codes), REHABO
(:BodyFunction) - ICF Body Functions (b codes)
(:BodyStructure) - ICF Body Structures (s codes)
(:EnvironmentalFactor) - ICF Environmental Factors (e codes)
(:Assessment) - Outcome measures (FIM, Berg, 6MWT, etc.)
(:Intervention) - Treatment protocols
(:Session) - Therapy sessions
(:Outcome) - Measured outcomes
(:Clinician)
(:Facility)
```

### Core Relationships
```
(:Patient)-[:HAS_CONDITION]->(:Condition)
(:Patient)-[:PERFORMED]->(:Session)
(:Session)-[:INCLUDES]->(:Exercise)
(:Exercise)-[:TARGETS]->(:BodyPart)
(:Exercise)-[:IMPROVES]->(:BodyFunction)
(:Exercise)-[:REQUIRES]->(:Equipment)
(:Exercise)-[:HAS_MOVEMENT]->(:Movement)
(:Movement)-[:IN_PLANE]->(:AnatomicalPlane)
(:Condition)-[:AFFECTS]->(:BodyFunction)
(:Condition)-[:AFFECTS]->(:BodyStructure)
(:Assessment)-[:MEASURES]->(:BodyFunction)
(:Intervention)-[:INCLUDES]->(:Exercise)
(:Session)-[:HAS_OUTCOME]->(:Outcome)
(:Outcome)-[:MEASURED_BY]->(:Assessment)
```

---

## 🚀 Quick Start: Download Scripts

### Create data directory structure
```bash
mkdir -p data/{datasets,ontologies,raw,processed}
```

### Download ontologies (OWL/RDF)
```bash
# REHABO
curl -L -o data/ontologies/rehabo.owl "https://data.bioontology.org/ontologies/REHABO/submissions/1/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb"

# ICF
curl -L -o data/ontologies/icf.owl "https://data.bioontology.org/ontologies/ICF/submissions/3/download?apikey=8b5b7825-538d-40e0-9e9e-5ab9274a9aeb"
```

### Download exercise datasets
```bash
# Free Exercise DB (800+ exercises)
curl -L -o data/datasets/exercises.json "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json"

# REHAB24-6 (large - 668MB)
# Manual download from: https://zenodo.org/records/13305826

# IntelliRehabDS
# Manual download from: https://zenodo.org/records/4610859
```

---

## 📋 Next Steps for Implementation

1. **Set up Neo4j** (local or Aura)
2. **Load ontologies** using `apoc.import.rdf` or custom Cypher
3. **Create constraints & indexes** for core node types
4. **Import exercise datasets** as `:Exercise` nodes with properties
5. **Map to ICF/REHABO** using ontology alignment
6. **Add SNOMED CT** mappings for conditions
7. **Build ETL pipelines** for clinical data integration
8. **Create GraphRAG** layer for Q&A over the KG

---

## 📚 Key References

1. **REHABO Paper**: Hogan et al. "The Rehabilitation Ontology" (2026)
2. **ICF in Rehabilitation**: Steiner et al. "Use of the ICF model as a clinical problem-solving tool" (2002)
3. **Knowledge Graphs in Rehab**: KGSCS paper (2024) - Neo4j-based chronic disease care
4. **Exercise Ontology**: "Ontologies and Knowledge Graphs for Exercise Medicine" (Springer, 2022)
5. **Rehab-Pile**: Ismail-Fawaz et al. "Deep Learning for Skeleton Based Human Motion Rehabilitation Assessment" (2025)

---

## ⚖️ Licensing Notes

| Resource | License | Commercial Use |
|----------|---------|----------------|
| REHABO | CC0 | ✅ Yes |
| ICF | WHO | ✅ Yes (with attribution) |
| SNOMED CT | SNOMED International | ⚠️ Requires license |
| UMLS | NLM | ✅ Research (free license) |
| Free Exercise DB | Unlicense | ✅ Yes |
| REHAB24-6 | CC BY-NC 4.0 | ❌ Non-commercial only |
| IntelliRehabDS | Open Access | ✅ Yes |
| UI-PRMD | MDPI | ✅ Yes |
| EXMO | CC BY 4.0 | ✅ Yes |
| PMR | Open Access | ✅ Yes |
| MELLO-D | Open Access | ✅ Yes |
| COPPER | CC BY 4.0 | ✅ Yes |
| KHMO | CC BY 4.0 | ✅ Yes |
| OPE | Open Access | ✅ Yes |
| PHY | Open Access | ✅ Yes |
| ONTOLOCO | Open Access | ✅ Yes |
| REHAB (stroke kinematics) | Open Access | ✅ Yes |
| KneE-PAD | CC BY 4.0 | ✅ Yes |
| GAITEX | CC BY-NC-ND 4.0 | ❌ Non-commercial only |
| GaitIntent | CC BY-NC-ND 4.0 | ❌ Non-commercial only |
| UCOPhyRehab++ | CC BY-NC-ND 4.0 | ❌ Non-commercial only |
| K2MUSE | Open Access | ✅ Yes |
| ExoMove | Open Access | ✅ Yes |
| ARMin 5 Fusion | Open Access | ✅ Yes |
| MOTU (FHIR) | CC BY 4.0 | ✅ Yes |
| San Raffaele Rehab | CC BY 4.0 | ✅ Yes |
| EEG-EMG-WristMotion | CC BY 4.0 | ✅ Yes |
| BATEX | Open Access | ✅ Yes |
| SDALLE | Open Access | ✅ Yes |
| RMD | Free | ✅ Yes |
| MIMIC-IV | PhysioNet DUA | ⚠️ Research only |

---

*Last updated: 2026-08-21*
*Workspace: /Users/chenc/Documents/2026/Work/HAIC/RehabKG*