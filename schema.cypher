// ============================================================
// Rehabilitation Knowledge Graph - Neo4j Schema
// Run in Neo4j Browser or: cypher-shell -f schema.cypher
// ============================================================

// ============================================================
// CONSTRAINTS - Uniqueness
// ============================================================

// Core domain entities
CREATE CONSTRAINT patient_id_unique IF NOT EXISTS FOR (p:Patient) REQUIRE p.patient_id IS UNIQUE;
CREATE CONSTRAINT condition_code_unique IF NOT EXISTS FOR (c:Condition) REQUIRE c.code IS UNIQUE;
CREATE CONSTRAINT exercise_id_unique IF NOT EXISTS FOR (e:Exercise) REQUIRE e.exercise_id IS UNIQUE;
CREATE CONSTRAINT bodypart_id_unique IF NOT EXISTS FOR (bp:BodyPart) REQUIRE bp.part_id IS UNIQUE;
CREATE CONSTRAINT muscle_id_unique IF NOT EXISTS FOR (m:Muscle) REQUIRE m.muscle_id IS UNIQUE;
CREATE CONSTRAINT bodyfunction_id_unique IF NOT EXISTS FOR (bf:BodyFunction) REQUIRE bf.function_id IS UNIQUE;
CREATE CONSTRAINT bodystructure_id_unique IF NOT EXISTS FOR (bs:BodyStructure) REQUIRE bs.structure_id IS UNIQUE;
CREATE CONSTRAINT activity_id_unique IF NOT EXISTS FOR (a:Activity) REQUIRE a.activity_id IS UNIQUE;
CREATE CONSTRAINT envfactor_id_unique IF NOT EXISTS FOR (ef:EnvironmentalFactor) REQUIRE ef.factor_id IS UNIQUE;
CREATE CONSTRAINT assessment_id_unique IF NOT EXISTS FOR (a:Assessment) REQUIRE a.assessment_id IS UNIQUE;
CREATE CONSTRAINT intervention_id_unique IF NOT EXISTS FOR (i:Intervention) REQUIRE i.intervention_id IS UNIQUE;
CREATE CONSTRAINT session_id_unique IF NOT EXISTS FOR (s:Session) REQUIRE s.session_id IS UNIQUE;
CREATE CONSTRAINT outcome_id_unique IF NOT EXISTS FOR (o:Outcome) REQUIRE o.outcome_id IS UNIQUE;
CREATE CONSTRAINT clinician_id_unique IF NOT EXISTS FOR (c:Clinician) REQUIRE c.clinician_id IS UNIQUE;
CREATE CONSTRAINT facility_id_unique IF NOT EXISTS FOR (f:Facility) REQUIRE f.facility_id IS UNIQUE;
CREATE CONSTRAINT equipment_id_unique IF NOT EXISTS FOR (e:Equipment) REQUIRE e.equipment_id IS UNIQUE;
CREATE CONSTRAINT plane_id_unique IF NOT EXISTS FOR (p:AnatomicalPlane) REQUIRE p.plane_id IS UNIQUE;
CREATE CONSTRAINT movement_id_unique IF NOT EXISTS FOR (m:Movement) REQUIRE m.movement_id IS UNIQUE;

// Dataset-specific entities
CREATE CONSTRAINT rehab_patient_id_unique IF NOT EXISTS FOR (p:REHABPatient) REQUIRE p.patient_id IS UNIQUE;
CREATE CONSTRAINT knee_patient_id_unique IF NOT EXISTS FOR (p:KneEPADPatient) REQUIRE p.patient_id IS UNIQUE;
CREATE CONSTRAINT motu_patient_id_unique IF NOT EXISTS FOR (p:MOTUPatient) REQUIRE p.patient_id IS UNIQUE;
CREATE CONSTRAINT assessment_scale_id_unique IF NOT EXISTS FOR (a:AssessmentScale) REQUIRE a.scale_id IS UNIQUE;
CREATE CONSTRAINT rehab_movement_id_unique IF NOT EXISTS FOR (m:RehabMovement) REQUIRE m.movement_id IS UNIQUE;
CREATE CONSTRAINT sensor_id_unique IF NOT EXISTS FOR (s:Sensor) REQUIRE s.sensor_id IS UNIQUE;
CREATE CONSTRAINT trial_id_unique IF NOT EXISTS FOR (t:Trial) REQUIRE t.trial_id IS UNIQUE;

// Ontology concepts
CREATE CONSTRAINT icf_code_unique IF NOT EXISTS FOR (i:ICFConcept) REQUIRE i.code IS UNIQUE;
CREATE CONSTRAINT snomed_id_unique IF NOT EXISTS FOR (s:SNOMEDConcept) REQUIRE s.concept_id IS UNIQUE;
CREATE CONSTRAINT rehabo_id_unique IF NOT EXISTS FOR (r:REHABOConcept) REQUIRE r.concept_id IS UNIQUE;
CREATE CONSTRAINT umls_cui_unique IF NOT EXISTS FOR (u:UMLSConcept) REQUIRE u.cui IS UNIQUE;
CREATE CONSTRAINT exmo_code_unique IF NOT EXISTS FOR (e:EXMOConcept) REQUIRE e.code IS UNIQUE;
CREATE CONSTRAINT pmr_code_unique IF NOT EXISTS FOR (p:PMRConcept) REQUIRE p.code IS UNIQUE;
CREATE CONSTRAINT mellod_code_unique IF NOT EXISTS FOR (m:MELLODConcept) REQUIRE m.code IS UNIQUE;
CREATE CONSTRAINT copper_code_unique IF NOT EXISTS FOR (c:COPPERConcept) REQUIRE c.code IS UNIQUE;
CREATE CONSTRAINT khmo_code_unique IF NOT EXISTS FOR (k:KHMOConcept) REQUIRE k.code IS UNIQUE;
CREATE CONSTRAINT ope_code_unique IF NOT EXISTS FOR (o:OPEConcept) REQUIRE o.code IS UNIQUE;
CREATE CONSTRAINT phy_code_unique IF NOT EXISTS FOR (p:PHYConcept) REQUIRE p.code IS UNIQUE;
CREATE CONSTRAINT ontoloco_code_unique IF NOT EXISTS FOR (o:ONTOLOCOConcept) REQUIRE o.code IS UNIQUE;

// ============================================================
// INDEXES - Query Performance
// ============================================================

// Patient
CREATE INDEX patient_name_idx IF NOT EXISTS FOR (p:Patient) ON (p.name);
CREATE INDEX patient_dob_idx IF NOT EXISTS FOR (p:Patient) ON (p.date_of_birth);

// Condition
CREATE INDEX condition_name_idx IF NOT EXISTS FOR (c:Condition) ON (c.name);
CREATE INDEX condition_icd10_idx IF NOT EXISTS FOR (c:Condition) ON (c.icd10_code);
CREATE INDEX condition_snomed_idx IF NOT EXISTS FOR (c:Condition) ON (c.snomed_code);

// Exercise
CREATE INDEX exercise_name_idx IF NOT EXISTS FOR (e:Exercise) ON (e.name);
CREATE INDEX exercise_category_idx IF NOT EXISTS FOR (e:Exercise) ON (e.category);
CREATE INDEX exercise_level_idx IF NOT EXISTS FOR (e:Exercise) ON (e.level);
CREATE INDEX exercise_equipment_idx IF NOT EXISTS FOR (e:Exercise) ON (e.equipment);

// BodyPart
CREATE INDEX bodypart_name_idx IF NOT EXISTS FOR (bp:BodyPart) ON (bp.name);
CREATE INDEX bodypart_laterality_idx IF NOT EXISTS FOR (bp:BodyPart) ON (bp.laterality);

// Assessment
CREATE INDEX assessment_name_idx IF NOT EXISTS FOR (a:Assessment) ON (a.name);
CREATE INDEX assessment_domain_idx IF NOT EXISTS FOR (a:Assessment) ON (a.domain);

// Session
CREATE INDEX session_date_idx IF NOT EXISTS FOR (s:Session) ON (s.date);
CREATE INDEX session_patient_idx IF NOT EXISTS FOR (s:Session) ON (s.patient_id);

// Outcome
CREATE INDEX outcome_value_idx IF NOT EXISTS FOR (o:Outcome) ON (o.value);
CREATE INDEX outcome_assessment_idx IF NOT EXISTS FOR (o:Outcome) ON (o.assessment_id);

// Full-text search indexes
CREATE FULLTEXT INDEX exercise_description_fulltext IF NOT EXISTS FOR (e:Exercise) ON EACH [e.description, e.instructions];
CREATE FULLTEXT INDEX condition_description_fulltext IF NOT EXISTS FOR (c:Condition) ON EACH [c.name, c.description];
CREATE FULLTEXT INDEX intervention_description_fulltext IF NOT EXISTS FOR (i:Intervention) ON EACH [i.name, i.description];

// Ontology indexes
CREATE INDEX icf_name_idx IF NOT EXISTS FOR (i:ICFConcept) ON (i.name);
CREATE INDEX icf_chapter_idx IF NOT EXISTS FOR (i:ICFConcept) ON (i.chapter);
CREATE INDEX exmo_name_idx IF NOT EXISTS FOR (e:EXMOConcept) ON (e.name);
CREATE INDEX pmr_name_idx IF NOT EXISTS FOR (p:PMRConcept) ON (p.name);
CREATE INDEX mellod_name_idx IF NOT EXISTS FOR (m:MELLODConcept) ON (m.name);
CREATE INDEX copper_name_idx IF NOT EXISTS FOR (c:COPPERConcept) ON (c.name);
CREATE INDEX khmo_name_idx IF NOT EXISTS FOR (k:KHMOConcept) ON (k.name);
CREATE INDEX ope_name_idx IF NOT EXISTS FOR (o:OPEConcept) ON (o.name);
CREATE INDEX phy_name_idx IF NOT EXISTS FOR (p:PHYConcept) ON (p.name);
CREATE INDEX ontoloco_name_idx IF NOT EXISTS FOR (o:ONTOLOCOConcept) ON (o.name);

// ============================================================
// SCHEMA DOCUMENTATION NODES
// ============================================================

// Node Types
MERGE (nt:NodeType {name: 'Patient'})
SET nt.description = 'A person receiving rehabilitation therapy',
    nt.key_properties = ['patient_id', 'name', 'date_of_birth', 'sex', 'diagnosis_codes'],
    nt.example = '{"patient_id": "PAT-001", "name": "John Doe", "date_of_birth": "1980-05-15", "sex": "M"}';

MERGE (nt:NodeType {name: 'Condition'})
SET nt.description = 'Medical condition/diagnosis (ICD-10, SNOMED CT)',
    nt.key_properties = ['code', 'name', 'icd10_code', 'snomed_code', 'description'],
    nt.example = '{"code": "M54.5", "name": "Low back pain", "icd10_code": "M54.5", "snomed_code": "161891005"}';

MERGE (nt:NodeType {name: 'Exercise'})
SET nt.description = 'Therapeutic exercise or movement',
    nt.key_properties = ['exercise_id', 'name', 'category', 'level', 'force', 'mechanic', 'equipment', 'instructions', 'primary_muscles', 'secondary_muscles'],
    nt.example = '{"exercise_id": "EX-001", "name": "Bridge", "category": "strengthening", "level": "beginner", "primary_muscles": ["gluteus maximus"]}';

MERGE (nt:NodeType {name: 'BodyPart'})
SET nt.description = 'Anatomical body part (UBERON, FMA, SNOMED)',
    nt.key_properties = ['part_id', 'name', 'laterality', 'anatomical_system'],
    nt.example = '{"part_id": "BP-001", "name": "Knee joint", "laterality": "bilateral", "anatomical_system": "musculoskeletal"}';

MERGE (nt:NodeType {name: 'BodyFunction'})
SET nt.description = 'ICF Body Function (b codes)',
    nt.key_properties = ['function_id', 'code', 'name', 'chapter'],
    nt.example = '{"function_id": "BF-001", "code": "b710", "name": "Mobility of joint functions", "chapter": "Chapter 7"}';

MERGE (nt:NodeType {name: 'Activity'})
SET nt.description = 'ICF Activity/Participation (d codes)',
    nt.key_properties = ['activity_id', 'code', 'name', 'chapter', 'qualifier_performance', 'qualifier_capacity'],
    nt.example = '{"activity_id": "ACT-001", "code": "d450", "name": "Walking", "chapter": "Chapter 4"}';

MERGE (nt:NodeType {name: 'Assessment'})
SET nt.description = 'Standardized outcome measure',
    nt.key_properties = ['assessment_id', 'name', 'domain', 'scoring_range', 'mcmid'],
    nt.example = '{"assessment_id": "ASM-001", "name": "Berg Balance Scale", "domain": "balance", "scoring_range": "0-56"}';

MERGE (nt:NodeType {name: 'Session'})
SET nt.description = 'Therapy session record',
    nt.key_properties = ['session_id', 'date', 'duration_minutes', 'setting', 'clinician_id'],
    nt.example = '{"session_id": "SES-001", "date": "2024-01-15", "duration_minutes": 45, "setting": "outpatient"}';

MERGE (nt:NodeType {name: 'Intervention'})
SET nt.description = 'Treatment protocol or plan',
    nt.key_properties = ['intervention_id', 'name', 'description', 'frequency', 'duration_weeks'],
    nt.example = '{"intervention_id": "INT-001", "name": "Post-op knee protocol", "frequency": "3x/week", "duration_weeks": 12}';

MERGE (nt:NodeType {name: 'Outcome'})
SET nt.description = 'Measured outcome from assessment',
    nt.key_properties = ['outcome_id', 'value', 'unit', 'date', 'assessment_id'],
    nt.example = '{"outcome_id": "OUT-001", "value": 48, "unit": "points", "date": "2024-01-15", "assessment_id": "ASM-001"}';

// Relationship Types
MERGE (rt:RelType {name: 'HAS_CONDITION'})
SET rt.description = 'Patient has a medical condition', rt.from_type = 'Patient', rt.to_type = 'Condition';

MERGE (rt:RelType {name: 'PERFORMED'})
SET rt.description = 'Patient performed a therapy session', rt.from_type = 'Patient', rt.to_type = 'Session';

MERGE (rt:RelType {name: 'INCLUDES'})
SET rt.description = 'Session includes an exercise', rt.from_type = 'Session', rt.to_type = 'Exercise';

MERGE (rt:RelType {name: 'TARGETS_PRIMARY'})
SET rt.description = 'Exercise primarily targets a muscle/body part', rt.from_type = 'Exercise', rt.to_type = 'BodyPart';

MERGE (rt:RelType {name: 'TARGETS_SECONDARY'})
SET rt.description = 'Exercise secondarily targets a muscle/body part', rt.from_type = 'Exercise', rt.to_type = 'BodyPart';

MERGE (rt:RelType {name: 'IMPROVES'})
SET rt.description = 'Exercise improves a body function', rt.from_type = 'Exercise', rt.to_type = 'BodyFunction';

MERGE (rt:RelType {name: 'REQUIRES'})
SET rt.description = 'Exercise requires equipment', rt.from_type = 'Exercise', rt.to_type = 'Equipment';

MERGE (rt:RelType {name: 'HAS_MOVEMENT'})
SET rt.description = 'Exercise involves a movement pattern', rt.from_type = 'Exercise', rt.to_type = 'Movement';

MERGE (rt:RelType {name: 'AFFECTS'})
SET rt.description = 'Condition affects body function/structure', rt.from_type = 'Condition', rt.to_type = 'BodyFunction';

MERGE (rt:RelType {name: 'MEASURES'})
SET rt.description = 'Assessment measures a body function/activity', rt.from_type = 'Assessment', rt.to_type = 'BodyFunction';

MERGE (rt:RelType {name: 'HAS_OUTCOME'})
SET rt.description = 'Session has a measured outcome', rt.from_type = 'Session', rt.to_type = 'Outcome';

MERGE (rt:RelType {name: 'MEASURED_BY'})
SET rt.description = 'Outcome measured by assessment', rt.from_type = 'Outcome', rt.to_type = 'Assessment';

MERGE (rt:RelType {name: 'TREATED_BY'})
SET rt.description = 'Condition treated by intervention', rt.from_type = 'Condition', rt.to_type = 'Intervention';

MERGE (rt:RelType {name: 'INCLUDES_EXERCISE'})
SET rt.description = 'Intervention includes exercise', rt.from_type = 'Intervention', rt.to_type = 'Exercise';

MERGE (rt:RelType {name: 'MAPS_TO_ICF'})
SET rt.description = 'Concept maps to ICF code', rt.from_type = 'Exercise', rt.to_type = 'ICFConcept';

MERGE (rt:RelType {name: 'MAPS_TO_SNOMED'})
SET rt.description = 'Concept maps to SNOMED CT', rt.from_type = 'Condition', rt.to_type = 'SNOMEDConcept';

MERGE (rt:RelType {name: 'MAPS_TO_REHABO'})
SET rt.description = 'Concept maps to REHABO', rt.from_type = 'Exercise', rt.to_type = 'REHABOConcept';

MERGE (rt:RelType {name: 'MAPS_TO_EXMO'})
SET rt.description = 'Concept maps to EXMO (Exercise Medicine)', rt.from_type = 'Exercise', rt.to_type = 'EXMOConcept';

MERGE (rt:RelType {name: 'MAPS_TO_PMR'})
SET rt.description = 'Concept maps to PMR (Physical Medicine and Rehabilitation)', rt.from_type = 'Condition', rt.to_type = 'PMRConcept';

MERGE (rt:RelType {name: 'MAPS_TO_KHMO'})
SET rt.description = 'Concept maps to KHMO (Kinetic Human Movement)', rt.from_type = 'Exercise', rt.to_type = 'KHMOConcept';

MERGE (rt:RelType {name: 'MAPS_TO_COPPER'})
SET rt.description = 'Concept maps to COPPER (Physical Activity Recommendations)', rt.from_type = 'Exercise', rt.to_type = 'COPPERConcept';

MERGE (rt:RelType {name: 'MAPS_TO_OPE'})
SET rt.description = 'Concept maps to OPE (Ontology of Physical Exercises)', rt.from_type = 'Exercise', rt.to_type = 'OPEConcept';

MERGE (rt:RelType {name: 'MAPS_TO_PHY'})
SET rt.description = 'Concept maps to PHY (Physiotherapy Ontology)', rt.from_type = 'Exercise', rt.to_type = 'PHYConcept';

MERGE (rt:RelType {name: 'MAPS_TO_ONTOLOCO'})
SET rt.description = 'Concept maps to ONTOLOCO (VR Locomotion Rehabilitation)', rt.from_type = 'Exercise', rt.to_type = 'ONTOLOCOConcept';

MERGE (rt:RelType {name: 'MAPS_TO_MELLOD'})
SET rt.description = 'Concept maps to MELLO-D (Medical LifeLog for Disability)', rt.from_type = 'Exercise', rt.to_type = 'MELLODConcept';

MERGE (rt:RelType {name: 'HAS_ICF_CODE'})
SET rt.description = 'Entity has ICF classification code', rt.from_type = 'BodyFunction', rt.to_type = 'ICFConcept';

MERGE (rt:RelType {name: 'PART_OF'})
SET rt.description = 'Anatomical part-of hierarchy', rt.from_type = 'BodyPart', rt.to_type = 'BodyPart';

MERGE (rt:RelType {name: 'IN_PLANE'})
SET rt.description = 'Movement occurs in anatomical plane', rt.from_type = 'Movement', rt.to_type = 'AnatomicalPlane';

MERGE (rt:RelType {name: 'CONTRAINDICATED_FOR'})
SET rt.description = 'Exercise contraindicated for condition', rt.from_type = 'Exercise', rt.to_type = 'Condition';

MERGE (rt:RelType {name: 'PROGRESSES_TO'})
SET rt.description = 'Exercise progression relationship', rt.from_type = 'Exercise', rt.to_type = 'Exercise';

MERGE (rt:RelType {name: 'SIMILAR_TO'})
SET rt.description = 'Similar exercise alternative', rt.from_type = 'Exercise', rt.to_type = 'Exercise';

// ============================================================
// REFERENCE DATA - Anatomical Planes
// ============================================================

MERGE (p:AnatomicalPlane {plane_id: 'sagittal', name: 'Sagittal Plane', description: 'Divides body into left and right portions'});
MERGE (p:AnatomicalPlane {plane_id: 'frontal', name: 'Frontal (Coronal) Plane', description: 'Divides body into anterior and posterior portions'});
MERGE (p:AnatomicalPlane {plane_id: 'transverse', name: 'Transverse (Axial) Plane', description: 'Divides body into superior and inferior portions'});

// ============================================================
// REFERENCE DATA - Common Equipment
// ============================================================

UNWIND [
  {equipment_id: 'eq-bodyweight', name: 'Body Weight', category: 'none'},
  {equipment_id: 'eq-dumbbell', name: 'Dumbbell', category: 'free_weight'},
  {equipment_id: 'eq-barbell', name: 'Barbell', category: 'free_weight'},
  {equipment_id: 'eq-kettlebell', name: 'Kettlebell', category: 'free_weight'},
  {equipment_id: 'eq-resistance-band', name: 'Resistance Band', category: 'elastic'},
  {equipment_id: 'eq-cable', name: 'Cable Machine', category: 'machine'},
  {equipment_id: 'eq-machine', name: 'Weight Machine', category: 'machine'},
  {equipment_id: 'eq-medicine-ball', name: 'Medicine Ball', category: 'free_weight'},
  {equipment_id: 'eq-foam-roller', name: 'Foam Roller', category: 'mobility'},
  {equipment_id: 'eq-balance-board', name: 'Balance Board', category: 'balance'},
  {equipment_id: 'eq-parallel-bars', name: 'Parallel Bars', category: 'gait'},
  {equipment_id: 'eq-treadmill', name: 'Treadmill', category: 'cardio'},
  {equipment_id: 'eq-bike', name: 'Stationary Bike', category: 'cardio'},
  {equipment_id: 'eq-elliptical', name: 'Elliptical', category: 'cardio'}
] AS eq
MERGE (e:Equipment {equipment_id: eq.equipment_id})
SET e.name = eq.name, e.category = eq.category;

// ============================================================
// REFERENCE DATA - Exercise Categories
// ============================================================

UNWIND [
  {category: 'strengthening', description: 'Resistance exercises to improve muscle strength'},
  {category: 'stretching', description: 'Flexibility and range of motion exercises'},
  {category: 'balance', description: 'Proprioception and postural control exercises'},
  {category: 'aerobic', description: 'Cardiovascular endurance exercises'},
  {category: 'neuromuscular', description: 'Motor control and coordination exercises'},
  {category: 'functional', description: 'Task-specific functional training'},
  {category: 'mobility', description: 'Joint mobility and soft tissue mobilization'},
  {category: 'breathing', description: 'Respiratory and diaphragmatic exercises'},
  {category: 'relaxation', description': 'Relaxation and stress reduction techniques'}
] AS cat
MERGE (c:ExerciseCategory {category: cat.category})
SET c.description = cat.description;

// ============================================================
// VERIFICATION QUERIES
// ============================================================

// Show all constraints
// SHOW CONSTRAINTS;

// Show all indexes
// SHOW INDEXES;

// Count schema documentation
// MATCH (n:NodeType) RETURN count(n) as node_types;
// MATCH (r:RelType) RETURN count(r) as rel_types;

// ============================================================
// SAMPLE DATA LOAD (after copying CSVs to import directory)
// ============================================================

/*
// Load Exercise nodes from CSV
LOAD CSV WITH HEADERS FROM 'file:///exercises_nodes.csv' AS row
CALL apoc.create.node(
  split(row.labels, ';'), 
  apoc.map.clean(row, ['id', 'labels'], [])
) YIELD node
SET node.exercise_id = row.id
RETURN count(*) as exercises_loaded;

// Load Relationships from CSV
LOAD CSV WITH HEADERS FROM 'file:///exercises_relationships.csv' AS row
MATCH (a {exercise_id: row.start_id}), (b {exercise_id: row.end_id})
CALL apoc.create.relationship(a, row.type, {}, b) YIELD rel
RETURN count(*) as relationships_loaded;
*/

// ============================================================
// USEFUL QUERY TEMPLATES
// ============================================================

/*
// Find exercises for a condition
MATCH (c:Condition {code: 'M54.5'})<-[:TREATED_BY]-(i:Intervention)-[:INCLUDES_EXERCISE]->(e:Exercise)
RETURN e.name, e.category, e.level, e.equipment, e.instructions;

// Patient exercise history
MATCH (p:Patient {patient_id: 'PAT-001'})-[:PERFORMED]->(s:Session)-[:INCLUDES]->(e:Exercise)
RETURN s.date, e.name, e.category
ORDER BY s.date;

// Outcome progression
MATCH (p:Patient {patient_id: 'PAT-001'})-[:PERFORMED]->(s:Session)-[:HAS_OUTCOME]->(o:Outcome)-[:MEASURED_BY]->(a:Assessment)
RETURN a.name, s.date, o.value, o.unit
ORDER BY s.date;

// Exercise progression chain
MATCH path = (e1:Exercise)-[:PROGRESSES_TO*]->(e2:Exercise)
WHERE e1.name = 'Bridge'
RETURN path;

// ICF-based exercise search
MATCH (e:Exercise)-[:MAPS_TO_ICF]->(icf:ICFConcept {code: 'b710'})
RETURN e.name, e.category, e.level;

// Contraindications check
MATCH (e:Exercise)-[:CONTRAINDICATED_FOR]->(c:Condition {code: 'M54.5'})
RETURN e.name, e.category, 'CONTRAINDICATED' as status;
*/

// ============================================================
// END OF SCHEMA
// ============================================================