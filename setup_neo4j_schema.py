#!/usr/bin/env python3
"""
Neo4j Schema Setup for Rehabilitation Knowledge Graph.
Run: python setup_neo4j_schema.py
"""

from dotenv import load_dotenv

from db import get_driver, get_uri, get_session_config

load_dotenv()


def run_cypher(session, query, description=""):
    """Execute a Cypher query with error handling."""
    if description:
        print(f"  {description}...")
    try:
        result = session.run(query)
        summary = result.consume()
        print(f"    ✓ {summary.counters}")
        return True
    except Exception as e:
        print(f"    ✗ Failed: {e}")
        return False


def create_constraints(session):
    """Create uniqueness constraints for core node types."""
    print("\n=== Creating Constraints ===")
    
    constraints = [
        # Core entities
        ("Patient", "patient_id"),
        ("Condition", "code"),
        ("Exercise", "exercise_id"),
        ("BodyPart", "part_id"),
        ("Muscle", "muscle_id"),
        ("BodyFunction", "function_id"),
        ("BodyStructure", "structure_id"),
        ("Activity", "activity_id"),
        ("EnvironmentalFactor", "factor_id"),
        ("Assessment", "assessment_id"),
        ("Intervention", "intervention_id"),
        ("Session", "session_id"),
        ("Outcome", "outcome_id"),
        ("Observation", "observation_id"),
        ("Clinician", "clinician_id"),
        ("Facility", "facility_id"),
        ("Equipment", "equipment_id"),
        ("AnatomicalPlane", "plane_id"),
        ("Movement", "movement_id"),
        # Ontology concepts
        ("ICFConcept", "code"),
        ("SNOMEDConcept", "concept_id"),
        ("REHABOConcept", "concept_id"),
        ("UMLSConcept", "cui"),
    ]
    
    for label, prop in constraints:
        query = f"CREATE CONSTRAINT {label.lower()}_{prop}_unique IF NOT EXISTS FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
        run_cypher(session, query, f"Constraint {label}.{prop}")


def create_indexes(session):
    """Create indexes for common query patterns."""
    print("\n=== Creating Indexes ===")
    
    indexes = [
        # Patient indexes
        ("Patient", "name"),
        ("Patient", "date_of_birth"),
        
        # Condition indexes
        ("Condition", "name"),
        ("Condition", "icd10_code"),
        ("Condition", "snomed_code"),
        
        # Exercise indexes
        ("Exercise", "name"),
        ("Exercise", "category"),
        ("Exercise", "level"),
        ("Exercise", "equipment"),
        
        # BodyPart indexes
        ("BodyPart", "name"),
        ("BodyPart", "laterality"),
        
        # Assessment indexes
        ("Assessment", "name"),
        ("Assessment", "domain"),
        
        # Session indexes
        ("Session", "date"),
        ("Session", "patient_id"),
        
        # Outcome indexes
        ("Outcome", "value"),
        ("Outcome", "assessment_id"),
        
        # Full-text search indexes
        ("Exercise", "description", "fulltext"),
        ("Condition", "description", "fulltext"),
        ("Intervention", "description", "fulltext"),
    ]
    
    for item in indexes:
        if len(item) == 3 and item[2] == "fulltext":
            label, prop, _ = item
            query = f"CREATE FULLTEXT INDEX {label.lower()}_{prop}_fulltext IF NOT EXISTS FOR (n:{label}) ON EACH [n.{prop}]"
        else:
            label, prop = item
            query = f"CREATE INDEX {label.lower()}_{prop}_idx IF NOT EXISTS FOR (n:{label}) ON (n.{prop})"
        run_cypher(session, query, f"Index {label}.{prop}")


def create_schema_nodes(session):
    """Create schema/documentation nodes for the graph model."""
    print("\n=== Creating Schema Documentation ===")
    
    # Node type definitions
    node_types = [
        {
            "type": "NodeType",
            "name": "Patient",
            "description": "A person receiving rehabilitation therapy",
            "key_properties": ["patient_id", "name", "date_of_birth", "sex", "diagnosis_codes"],
            "example": '{"patient_id": "PAT-001", "name": "John Doe", "date_of_birth": "1980-05-15", "sex": "M"}'
        },
        {
            "type": "NodeType",
            "name": "Condition",
            "description": "Medical condition/diagnosis (ICD-10, SNOMED CT)",
            "key_properties": ["code", "name", "icd10_code", "snomed_code", "description"],
            "example": '{"code": "M54.5", "name": "Low back pain", "icd10_code": "M54.5", "snomed_code": "161891005"}'
        },
        {
            "type": "NodeType",
            "name": "Exercise",
            "description": "Therapeutic exercise or movement",
            "key_properties": ["exercise_id", "name", "category", "level", "force", "mechanic", "equipment", "instructions", "primary_muscles", "secondary_muscles"],
            "example": '{"exercise_id": "EX-001", "name": "Bridge", "category": "strengthening", "level": "beginner", "primary_muscles": ["gluteus maximus"]}'
        },
        {
            "type": "NodeType",
            "name": "BodyPart",
            "description": "Anatomical body part (UBERON, FMA, SNOMED)",
            "key_properties": ["part_id", "name", "laterality", "anatomical_system"],
            "example": '{"part_id": "BP-001", "name": "Knee joint", "laterality": "bilateral", "anatomical_system": "musculoskeletal"}'
        },
        {
            "type": "NodeType",
            "name": "BodyFunction",
            "description": "ICF Body Function (b codes)",
            "key_properties": ["function_id", "code", "name", "chapter"],
            "example": '{"function_id": "BF-001", "code": "b710", "name": "Mobility of joint functions", "chapter": "Chapter 7"}'
        },
        {
            "type": "NodeType",
            "name": "Activity",
            "description": "ICF Activity/Participation (d codes)",
            "key_properties": ["activity_id", "code", "name", "chapter", "qualifier_performance", "qualifier_capacity"],
            "example": '{"activity_id": "ACT-001", "code": "d450", "name": "Walking", "chapter": "Chapter 4"}'
        },
        {
            "type": "NodeType",
            "name": "Assessment",
            "description": "Standardized outcome measure",
            "key_properties": ["assessment_id", "name", "domain", "scoring_range", "mcmid"],
            "example": '{"assessment_id": "ASM-001", "name": "Berg Balance Scale", "domain": "balance", "scoring_range": "0-56"}'
        },
        {
            "type": "NodeType",
            "name": "Session",
            "description": "Therapy session record",
            "key_properties": ["session_id", "date", "duration_minutes", "setting", "clinician_id"],
            "example": '{"session_id": "SES-001", "date": "2024-01-15", "duration_minutes": 45, "setting": "outpatient"}'
        },
    ]
    
    for nt in node_types:
        query = """
        MERGE (n:NodeType {name: $name})
        SET n.description = $description,
            n.key_properties = $key_properties,
            n.example = $example
        """
        session.run(query, **nt)
    
    # Relationship type definitions
    rel_types = [
        {"type": "RelType", "name": "HAS_CONDITION", "description": "Patient has a medical condition", "from": "Patient", "to": "Condition"},
        {"type": "RelType", "name": "PERFORMED", "description": "Patient performed a therapy session", "from": "Patient", "to": "Session"},
        {"type": "RelType", "name": "INCLUDES", "description": "Session includes an exercise", "from": "Session", "to": "Exercise"},
        {"type": "RelType", "name": "TARGETS_PRIMARY", "description": "Exercise primarily targets a muscle/body part", "from": "Exercise", "to": "BodyPart"},
        {"type": "RelType", "name": "TARGETS_SECONDARY", "description": "Exercise secondarily targets a muscle/body part", "from": "Exercise", "to": "BodyPart"},
        {"type": "RelType", "name": "IMPROVES", "description": "Exercise improves a body function", "from": "Exercise", "to": "BodyFunction"},
        {"type": "RelType", "name": "REQUIRES", "description": "Exercise requires equipment", "from": "Exercise", "to": "Equipment"},
        {"type": "RelType", "name": "HAS_MOVEMENT", "description": "Exercise involves a movement pattern", "from": "Exercise", "to": "Movement"},
        {"type": "RelType", "name": "AFFECTS", "description": "Condition affects body function/structure", "from": "Condition", "to": "BodyFunction"},
        {"type": "RelType", "name": "MEASURES", "description": "Assessment measures a body function/activity", "from": "Assessment", "to": "BodyFunction"},
        {"type": "RelType", "name": "HAS_OUTCOME", "description": "Session has a measured outcome", "from": "Session", "to": "Outcome"},
        {"type": "RelType", "name": "MEASURED_BY", "description": "Outcome measured by assessment", "from": "Outcome", "to": "Assessment"},
        {"type": "RelType", "name": "TREATED_BY", "description": "Condition treated by intervention", "from": "Condition", "to": "Intervention"},
        {"type": "RelType", "name": "INCLUDES_EXERCISE", "description": "Intervention includes exercise", "from": "Intervention", "to": "Exercise"},
        {"type": "RelType", "name": "MAPS_TO_ICF", "description": "Concept maps to ICF code", "from": "Exercise", "to": "ICFConcept"},
        {"type": "RelType", "name": "MAPS_TO_SNOMED", "description": "Concept maps to SNOMED CT", "from": "Condition", "to": "SNOMEDConcept"},
    ]
    
    for rt in rel_types:
        query = """
        MERGE (r:RelType {name: $name})
        SET r.description = $description,
            r.from_type = $from,
            r.to_type = $to
        """
        session.run(query, **rt)
    
    print("  ✓ Schema documentation created")


def load_exercise_data(session):
    """Load processed exercise CSV data."""
    print("\n=== Loading Exercise Data ===")

    # Note: For LOAD CSV, files must be in Neo4j import directory
    # This is a template - adjust paths for your Neo4j instance
    
    print("  To load exercise data, copy CSV files to Neo4j import directory and run:")
    print("""
  // Load Exercise nodes
  LOAD CSV WITH HEADERS FROM 'file:///exercises_nodes.csv' AS row
  CALL apoc.create.node(split(row.labels, ';'), apoc.map.clean(row, ['id', 'labels'], [])) YIELD node
  SET node.exercise_id = row.id
  RETURN count(*);
  
  // Load Relationships
  LOAD CSV WITH HEADERS FROM 'file:///exercises_relationships.csv' AS row
  MATCH (a {exercise_id: row.start_id}), (b {exercise_id: row.end_id})
  CALL apoc.create.relationship(a, row.type, {}, b) YIELD rel
  RETURN count(*);
    """)


def verify_schema(session):
    """Verify the created schema."""
    print("\n=== Verifying Schema ===")
    
    # Check constraints
    result = session.run("SHOW CONSTRAINTS")
    constraints = list(result)
    print(f"  Constraints: {len(constraints)}")
    for c in constraints:
        print(f"    - {c['name']}: {c['labelsOrTypes']} {c['properties']}")
    
    # Check indexes
    result = session.run("SHOW INDEXES")
    indexes = list(result)
    print(f"  Indexes: {len(indexes)}")
    for i in indexes:
        print(f"    - {i['name']}: {i['labelsOrTypes']} {i['properties']}")
    
    # Check node types
    result = session.run("MATCH (n:NodeType) RETURN count(n) as cnt")
    print(f"  NodeType definitions: {result.single()['cnt']}")
    
    # Check rel types
    result = session.run("MATCH (r:RelType) RETURN count(r) as cnt")
    print(f"  RelType definitions: {result.single()['cnt']}")


def main():
    print("Rehabilitation KG - Neo4j Schema Setup")
    print("=" * 50)
    print(f"Connecting to: {get_uri()}")

    driver = get_driver()
    try:
        with driver.session(**get_session_config()) as session:
            # Test connection
            result = session.run("RETURN 1 as test")
            print(f"  Connected: {result.single()['test'] == 1}")

            create_constraints(session)
            create_indexes(session)
            create_schema_nodes(session)
            load_exercise_data(session)
            verify_schema(session)

    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nMake sure Neo4j is running and credentials are set in .env:")
        print("  NEO4J_URI=bolt://localhost:7687")
        print("  NEO4J_USER=neo4j")
        print("  NEO4J_PASSWORD=your_password")
        return 1
    finally:
        driver.close()

    print("\n✓ Schema setup complete!")
    return 0


if __name__ == "__main__":
    exit(main())
