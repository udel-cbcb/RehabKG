#!/usr/bin/env python3
"""
ELT for rehabilitation datasets into Neo4j.

Imports:
  1. Rehabilitation Measures Database (RMD) - outcome measures
  2. REHAB stroke kinematics dataset metadata
  3. KneE-PAD knee rehabilitation dataset metadata
  4. MOTU amputation rehabilitation dataset metadata
  5. Free Exercise DB (enhanced with new fields)
  6. Curated outcome measures and assessment scales

Run: python elt_datasets.py
"""

from pathlib import Path
from dotenv import load_dotenv
from db import get_driver, get_session_config
from provenance import EXERCISE_PROGRESSES_TO, RMD_MEASURES

load_dotenv()

HERE = Path(__file__).parent
DATA_DIR = HERE / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

BATCH = 500


SCALE_ICF_LINKS = [
    ("ASM-001", "b235"), ("ASM-002", "d450"), ("ASM-003", "d450"),
    ("ASM-010", "b730"), ("ASM-011", "d440"), ("ASM-022", "b455"),
    ("ASM-030", "d570"), ("ASM-040", "b280"), ("ASM-050", "b710"),
]


# Curated exercise progression pairs. Names are exact Free Exercise DB
# display names (earlier names did not exist in the dataset, so those pairs
# never landed). Shared with build_csvs.py bulk export.
EXERCISE_PROGRESSIONS = [
    ("Bodyweight Squat", "Goblet Squat", "strength"),
    ("Bodyweight Squat", "Barbell Squat", "strength"),
    ("Bodyweight Walking Lunge", "Barbell Lunge", "strength"),
    ("Barbell Lunge", "Barbell Walking Lunge", "strength"),
    ("Plank", "Push Up to Side Plank", "stability"),
    ("Walking, Treadmill", "Jogging, Treadmill", "endurance"),
    ("Butt Lift (Bridge)", "Physioball Hip Bridge", "stability"),
]


# Full RMD scale set (37 historical + 3 balance instruments; single
# source of truth shared with build_csvs.py bulk export)
RMD_SCALES = [
        # Balance & Falls
        {"scale_id": "ASM-001", "name": "Berg Balance Scale", "domain": "balance", 
         "scoring_range": "0-56", "mcid": "4 points", "population": "stroke, elderly, neurological",
         "description": "14-item scale assessing balance through functional tasks"},
        {"scale_id": "ASM-002", "name": "Timed Up and Go", "domain": "balance",
         "scoring_range": "seconds (lower=better)", "mcid": "3.6 seconds", "population": "elderly, neurological",
         "description": "Measures mobility, balance, and fall risk"},
        {"scale_id": "ASM-003", "name": "Functional Gait Assessment", "domain": "gait",
         "scoring_range": "0-30", "mcid": "6 points", "population": "neurological, vestibular",
         "description": "10-item test evaluating gait and balance"},
        {"scale_id": "ASM-004", "name": "Tinetti Performance Oriented Mobility", "domain": "balance",
         "scoring_range": "0-28", "mcid": "N/A", "population": "elderly",
         "description": "Balance and gait assessment for fall risk"},
        {"scale_id": "ASM-005", "name": "Dynamic Gait Index", "domain": "gait",
         "scoring_range": "0-24", "mcid": "N/A", "population": "neurological",
         "description": "Assesses gait during various mobility tasks"},
        
        # Upper Extremity
        {"scale_id": "ASM-010", "name": "Fugl-Meyer Assessment Upper Extremity", "domain": "upper_limb",
         "scoring_range": "0-66", "mcid": "5.25 points", "population": "stroke",
         "description": "Evaluates motor function, balance, sensation in upper extremity"},
        {"scale_id": "ASM-011", "name": "Action Research Arm Test", "domain": "upper_limb",
         "scoring_range": "0-57", "mcid": "5.7 points", "population": "stroke",
         "description": "Assesses upper limb function through grasp, grip, pinch, gross movement"},
        {"scale_id": "ASM-012", "name": "Box and Block Test", "domain": "upper_limb",
         "scoring_range": "blocks/minute", "mcid": "5.5 blocks", "population": "stroke",
         "description": "Measures gross manual dexterity"},
        {"scale_id": "ASM-013", "name": "Nine Hole Peg Test", "domain": "upper_limb",
         "scoring_range": "seconds (lower=better)", "mcid": "N/A", "population": "neurological",
         "description": "Assesses finger dexterity"},
        {"scale_id": "ASM-014", "name": "DASH", "domain": "upper_limb",
         "scoring_range": "0-100", "mcid": "10 points", "population": "musculoskeletal",
         "description": "Disabilities of Arm, Shoulder and Hand questionnaire"},
        
        # Lower Extremity
        {"scale_id": "ASM-020", "name": "Fugl-Meyer Assessment Lower Extremity", "domain": "lower_limb",
         "scoring_range": "0-34", "mcid": "N/A", "population": "stroke",
         "description": "Evaluates motor function in lower extremity"},
        {"scale_id": "ASM-021", "name": "Timed 10 Meter Walk Test", "domain": "gait",
         "scoring_range": "m/s", "mcid": "0.13 m/s", "population": "neurological",
         "description": "Measures walking speed"},
        {"scale_id": "ASM-022", "name": "6 Minute Walk Test", "domain": "endurance",
         "scoring_range": "meters", "mcid": "30 meters", "population": "cardiac, pulmonary, neurological",
         "description": "Assesses functional exercise capacity"},
        {"scale_id": "ASM-023", "name": "10 Meter Walk Test", "domain": "gait",
         "scoring_range": "m/s", "mcid": "0.10 m/s", "population": "neurological",
         "description": "Measures comfortable and fast walking speed"},
        
        # ADL/Functional
        {"scale_id": "ASM-030", "name": "Barthel Index", "domain": "adl",
         "scoring_range": "0-100", "mcid": "1.85 points", "population": "stroke, general rehab",
         "description": "Measures activities of daily living"},
        {"scale_id": "ASM-031", "name": "Functional Independence Measure", "domain": "adl",
         "scoring_range": "18-126", "mcid": "22 points", "population": "general rehab",
         "description": "Comprehensive ADL and cognitive assessment"},
        {"scale_id": "ASM-032", "name": "Katz Index of Independence in ADLs", "domain": "adl",
         "scoring_range": "0-6", "mcid": "N/A", "population": "elderly",
         "description": "Assesses basic ADL performance"},
        {"scale_id": "ASM-033", "name": "Lawton IADL Scale", "domain": "adl",
         "scoring_range": "0-8", "mcid": "N/A", "population": "elderly",
         "description": "Assesses instrumental activities of daily living"},
        
        # Pain
        {"scale_id": "ASM-040", "name": "Visual Analog Scale Pain", "domain": "pain",
         "scoring_range": "0-10", "mcid": "1.5 points", "population": "general",
         "description": "Self-reported pain intensity"},
        {"scale_id": "ASM-041", "name": "Numerical Rating Scale Pain", "domain": "pain",
         "scoring_range": "0-10", "mcid": "2 points", "population": "general",
         "description": "Self-reported pain intensity using numbers"},
        {"scale_id": "ASM-042", "name": "McGill Pain Questionnaire", "domain": "pain",
         "scoring_range": "0-78", "mcid": "N/A", "population": "chronic pain",
         "description": "Multidimensional pain assessment"},
        
        # Knee-Specific
        {"scale_id": "ASM-050", "name": "Lysholm Knee Score", "domain": "knee",
         "scoring_range": "0-100", "mcid": "8 points", "population": "knee injuries",
         "description": "Evaluates knee ligament injuries"},
        {"scale_id": "ASM-051", "name": "KOOS", "domain": "knee",
         "scoring_range": "0-100", "mcid": "8-10 points", "population": "knee osteoarthritis",
         "description": "Knee Injury and Osteoarthritis Outcome Score"},
        {"scale_id": "ASM-052", "name": "International Knee Documentation Committee", "domain": "knee",
         "scoring_range": "0-100", "mcid": "N/A", "population": "knee injuries",
         "description": "Evaluates knee function after ligament injuries"},
        
        # Hip-Specific
        {"scale_id": "ASM-060", "name": "Harris Hip Score", "domain": "hip",
         "scoring_range": "0-100", "mcid": "8 points", "population": "hip replacement",
         "description": "Evaluates hip function after replacement"},
        {"scale_id": "ASM-061", "name": "HOOS", "domain": "hip",
         "scoring_range": "0-100", "mcid": "10 points", "population": "hip osteoarthritis",
         "description": "Hip Injury and Osteoarthritis Outcome Score"},
        
        # Shoulder
        {"scale_id": "ASM-070", "name": "Constant-Murley Score", "domain": "shoulder",
         "scoring_range": "0-100", "mcid": "N/A", "population": "shoulder pathologies",
         "description": "Evaluates shoulder function"},
        {"scale_id": "ASM-071", "name": "American Shoulder and Elbow Surgeons Score", "domain": "shoulder",
         "scoring_range": "0-100", "mcid": "6.2 points", "population": "shoulder",
         "description": "Shoulder function assessment"},
        
        # Neurological
        {"scale_id": "ASM-080", "name": "Modified Ashworth Scale", "domain": "spasticity",
         "scoring_range": "0-4", "mcid": "N/A", "population": "neurological",
         "description": "Assesses muscle spasticity"},
        {"scale_id": "ASM-081", "name": "Modified Rankin Scale", "domain": "disability",
         "scoring_range": "0-6", "mcid": "N/A", "population": "stroke",
         "description": "Measures overall disability after stroke"},
        {"scale_id": "ASM-082", "name": "Glasgow Coma Scale", "domain": "consciousness",
         "scoring_range": "3-15", "mcid": "N/A", "population": "traumatic brain injury",
         "description": "Assesses level of consciousness"},
        
        # Pediatric
        {"scale_id": "ASM-090", "name": "Pediatric Evaluation of Disability Inventory", "domain": "pediatric",
         "scoring_range": "0-100", "mcid": "N/A", "population": "pediatric",
         "description": "Assesses functional skills in children"},
        {"scale_id": "ASM-091", "name": "Alberta Infant Motor Scale", "domain": "pediatric",
         "scoring_range": "0-47", "mcid": "N/A", "population": "infants",
         "description": "Assesses infant gross motor development"},
        
        # Respiratory
        {"scale_id": "ASM-100", "name": "Forced Vital Capacity", "domain": "respiratory",
         "scoring_range": "liters", "mcid": "N/A", "population": "pulmonary",
         "description": "Measures lung capacity"},
        {"scale_id": "ASM-101", "name": "6 Minute Walk Distance", "domain": "respiratory",
         "scoring_range": "meters", "mcid": "30 meters", "population": "pulmonary",
         "description": "Assesses functional exercise capacity in pulmonary rehab"},
        
        # Stroke-Specific
        {"scale_id": "ASM-110", "name": "National Institutes of Health Stroke Scale", "domain": "stroke",
         "scoring_range": "0-42", "mcid": "N/A", "population": "stroke",
         "description": "Neurological deficit assessment"},
        {"scale_id": "ASM-111", "name": "Stroke Impact Scale", "domain": "stroke",
         "scoring_range": "0-100", "mcid": "N/A", "population": "stroke",
         "description": "Health-related quality of life after stroke"},

    # Additional real balance instruments (bring balance-domain count to 6
    # for the UC5 use case; RMD-style curated entries like the rest)
    {"scale_id": "ASM-120", "name": "Mini-BESTest", "domain": "balance",
     "scoring_range": "0-28", "mcid": "4 points", "population": "elderly, neurological"},
    {"scale_id": "ASM-121", "name": "Functional Reach Test", "domain": "balance",
     "scoring_range": "centimeters", "mcid": "N/A", "population": "elderly, general rehab"},
    {"scale_id": "ASM-122", "name": "Activities-specific Balance Confidence Scale", "domain": "balance",
     "scoring_range": "0-100%", "mcid": "13 percentage points", "population": "elderly, community ambulation"},
]


# ================================================================
# 1. REHABILITATION MEASURES DATABASE (RMD)
# ================================================================
def create_rmd_scales(session):
    """Create AssessmentScale nodes from curated RMD data.
    The RMD contains 600+ validated outcome measures for rehabilitation."""
    
    scales = RMD_SCALES
    
    session.run("MATCH (n:AssessmentScale) DETACH DELETE n").consume()
    
    for i in range(0, len(scales), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MERGE (a:AssessmentScale {scale_id: row.scale_id})
            SET a.name = row.name, a.domain = row.domain,
                a.scoring_range = row.scoring_range, a.mcid = row.mcid,
                a.population = row.population, a.description = row.description,
                a.source = 'RMD'
            """,
            rows=scales[i:i + BATCH],
        ).consume()
    
    print(f"RMD: {len(scales)} AssessmentScale nodes created")
    
    # Link assessment scales to ICF concepts
    _icf_link_notes = {
        ("ASM-001", "b235"): "balance functions",
        ("ASM-002", "d450"): "walking",
        ("ASM-003", "d450"): "walking",
        ("ASM-010", "b730"): "muscle power",
        ("ASM-011", "d440"): "fine hand use",
        ("ASM-022", "b455"): "exercise tolerance",
        ("ASM-030", "d570"): "looking after one's health",
        ("ASM-040", "b280"): "sensation of pain",
        ("ASM-050", "b710"): "mobility of joint",
    }
    icf_links = [(sid, code, _icf_link_notes.get((sid, code), ""))
                 for sid, code in SCALE_ICF_LINKS]    
    linked = 0
    for scale_id, icf_code, desc in icf_links:
        result = session.run(
            """
            MATCH (a:AssessmentScale {scale_id: $scale_id})
            MATCH (i:ICFConcept {code: $icf_code})
            MERGE (a)-[r:MEASURES]->(i)
            SET r += $props, r.description = $desc
            RETURN count(r) as c
            """,
            scale_id=scale_id, icf_code=icf_code, desc=desc,
            props=RMD_MEASURES,
        ).single()
        if result["c"] > 0:
            linked += 1
    
    print(f"  Linked {linked} AssessmentScale->ICF relationships")


# ================================================================
# 2. REHAB STROKE KINEMATICS METADATA
# ================================================================
def create_rehab_metadata(session):
    """Create metadata nodes for the REHAB stroke rehabilitation dataset."""
    
    # Dataset node
    session.run(
        """
        MERGE (d:Dataset {name: 'REHAB Stroke Kinematics'})
        SET d.description = 'Wearable sensor kinematic dataset for stroke rehabilitation',
            d.doi = '10.57760/sciencedb.37018',
            d.size = '120 patients, 43 movements',
            d.license = 'Open Access',
            d.download_url = 'https://www.scidb.cn/en/s/YrUnie',
            d.sensors = 'IMU + flex sensors (5 nodes)'
        """
    ).consume()
    
    # Assessment movements
    assessment_movements = [
        {"movement_id": "REHAB-A01", "name": "Shoulder Flexion", "body_region": "upper_limb", "joint": "shoulder", "type": "assessment"},
        {"movement_id": "REHAB-A02", "name": "Shoulder Abduction", "body_region": "upper_limb", "joint": "shoulder", "type": "assessment"},
        {"movement_id": "REHAB-A03", "name": "Elbow Flexion/Extension", "body_region": "upper_limb", "joint": "elbow", "type": "assessment"},
        {"movement_id": "REHAB-A04", "name": "Wrist Flexion/Extension", "body_region": "upper_limb", "joint": "wrist", "type": "assessment"},
        {"movement_id": "REHAB-A05", "name": "Grip Strength", "body_region": "upper_limb", "joint": "hand", "type": "assessment"},
        {"movement_id": "REHAB-A06", "name": "Finger Tap", "body_region": "upper_limb", "joint": "hand", "type": "assessment"},
        {"movement_id": "REHAB-A07", "name": "Pronation/Supination", "body_region": "upper_limb", "joint": "forearm", "type": "assessment"},
        {"movement_id": "REHAB-A08", "name": "Knee Flexion/Extension", "body_region": "lower_limb", "joint": "knee", "type": "assessment"},
        {"movement_id": "REHAB-A09", "name": "Ankle Dorsiflexion", "body_region": "lower_limb", "joint": "ankle", "type": "assessment"},
        {"movement_id": "REHAB-A10", "name": "Hip Flexion", "body_region": "lower_limb", "joint": "hip", "type": "assessment"},
    ]
    
    # Training movements
    training_movements = [
        {"movement_id": "REHAB-T01", "name": "Reaching Forward", "body_region": "upper_limb", "joint": "shoulder", "type": "training"},
        {"movement_id": "REHAB-T02", "name": "Reaching Overhead", "body_region": "upper_limb", "joint": "shoulder", "type": "training"},
        {"movement_id": "REHAB-T03", "name": "Hand to Mouth", "body_region": "upper_limb", "joint": "elbow", "type": "training"},
        {"movement_id": "REHAB-T04", "name": "Hand to Table", "body_region": "upper_limb", "joint": "shoulder", "type": "training"},
        {"movement_id": "REHAB-T05", "name": "Object Transfer", "body_region": "upper_limb", "joint": "hand", "type": "training"},
        {"movement_id": "REHAB-T06", "name": "Sit to Stand", "body_region": "lower_limb", "joint": "hip", "type": "training"},
        {"movement_id": "REHAB-T07", "name": "Weight Shifting", "body_region": "lower_limb", "joint": "hip", "type": "training"},
        {"movement_id": "REHAB-T08", "name": "Step Forward", "body_region": "lower_limb", "joint": "knee", "type": "training"},
    ]
    
    all_movements = assessment_movements + training_movements
    
    for i in range(0, len(all_movements), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MERGE (m:RehabMovement {movement_id: row.movement_id})
            SET m.name = row.name, m.body_region = row.body_region,
                m.joint = row.joint, m.type = row.type, m.source = 'REHAB'
            """,
            rows=all_movements[i:i + BATCH],
        ).consume()
    
    # Link movements to dataset
    session.run(
        """
        MATCH (d:Dataset {name: 'REHAB Stroke Kinematics'})
        MATCH (m:RehabMovement)
        MERGE (d)-[:CONTAINS_MOVEMENT]->(m)
        """
    ).consume()
    
    # Create sensor types
    sensors = [
        {"sensor_id": "sensor-imu", "name": "Inertial Measurement Unit", "type": "IMU", "measures": "acceleration, angular velocity"},
        {"sensor_id": "sensor-flex", "name": "Flex Sensor", "type": "flex", "measures": "joint angle"},
    ]
    
    session.run("UNWIND $rows AS row MERGE (s:Sensor {sensor_id: row.sensor_id}) SET s.name = row.name, s.type = row.type, s.measures = row.measures", rows=sensors).consume()
    
    print(f"REHAB metadata: {len(all_movements)} movements, {len(sensors)} sensor types")


# ================================================================
# 3. KNEE-PAD KNEE REHABILITATION METADATA
# ================================================================
def create_knee_pad_metadata(session):
    """Create metadata for the KneE-PAD knee rehabilitation dataset."""
    
    session.run(
        """
        MERGE (d:Dataset {name: 'KneE-PAD Knee Rehabilitation'})
        SET d.description = 'Knee rehabilitation exercises dataset for postural assessment',
            d.doi = '10.1038/s41597-025-04963-4',
            d.size = '31 patients, 2086 files',
            d.license = 'CC BY 4.0',
            d.sensors = '8 sEMG + 8 IMU',
            d.github = 'https://github.com/ospanas/KneE-PAD'
        """
    ).consume()
    
    # Knee exercises
    knee_exercises = [
        {"movement_id": "KNEE-SQ", "name": "Squats", "body_region": "lower_limb", "joint": "knee", "muscles": "quadriceps, glutes, hamstrings", "correct_variations": 1, "wrong_variations": 2},
        {"movement_id": "KNEE-LE", "name": "Leg Extension", "body_region": "lower_limb", "joint": "knee", "muscles": "quadriceps", "correct_variations": 1, "wrong_variations": 2},
        {"movement_id": "KNEE-WK", "name": "Walking", "body_region": "lower_limb", "joint": "knee", "muscles": "quadriceps, hamstrings, calves", "correct_variations": 1, "wrong_variations": 2},
    ]
    
    for ex in knee_exercises:
        session.run(
            """
            MERGE (m:RehabMovement {movement_id: $movement_id})
            SET m.name = $name, m.body_region = $body_region,
                m.joint = $joint, m.muscles = $muscles,
                m.correct_variations = $correct_variations,
                m.wrong_variations = $wrong_variations,
                m.source = 'KneE-PAD'
            """,
            **ex
        ).consume()
    
    # Common wrong variations
    wrong_patterns = [
        {"pattern_id": "WRONG-KNEE-VALGUS", "name": "Knee Valgus", "description": "Knee collapses inward during exercise"},
        {"pattern_id": "WRONG-TRUNK-LEAN", "name": "Excessive Trunk Lean", "description": "Compensatory trunk movement"},
        {"pattern_id": "WRONG-ASYMMETRY", "name": "Asymmetrical Weight Shift", "description": "Uneven weight distribution"},
    ]
    
    for wp in wrong_patterns:
        session.run(
            """
            MERGE (w:MovementError {pattern_id: $pattern_id})
            SET w.name = $name, w.description = $description
            """,
            **wp
        ).consume()
    
    print(f"KneE-PAD metadata: {len(knee_exercises)} exercises, {len(wrong_patterns)} error patterns")


# ================================================================
# 4. MOTU AMPUTATION REHABILITATION METADATA
# ================================================================
def create_motu_metadata(session):
    """Create metadata for the MOTU amputation rehabilitation dataset."""
    
    session.run(
        """
        MERGE (d:Dataset {name: 'MOTU Amputation Rehabilitation'})
        SET d.description = 'Trans-femoral amputation rehabilitation dataset (FHIR format)',
            d.doi = '10.5281/zenodo.14800465',
            d.size = '1006 patients, 1962 hospital stays',
            d.license = 'CC BY 4.0',
            d.format = 'CSV + HL7 FHIR',
            d.time_span = '2015-2024'
        """
    ).consume()
    
    # Prosthetic knee types
    prosthetic_knees = [
        {"equipment_id": "PROSTH-001", "name": "Single-Axis Knee", "category": "prosthetic", "type": "mechanical"},
        {"equipment_id": "PROSTH-002", "name": "Polycentric Knee", "category": "prosthetic", "type": "mechanical"},
        {"equipment_id": "PROSTH-003", "name": "Stance-Control Knee", "category": "prosthetic", "type": "microprocessor"},
        {"equipment_id": "PROSTH-004", "name": "C-Leg", "category": "prosthetic", "type": "microprocessor"},
        {"equipment_id": "PROSTH-005", "name": "Rheo Knee", "category": "prosthetic", "type": "microprocessor"},
        {"equipment_id": "PROSTH-006", "name": "Power Knee", "category": "prosthetic", "type": "powered"},
    ]
    
    for knee in prosthetic_knees:
        session.run(
            """
            MERGE (e:Equipment {equipment_id: $equipment_id})
            SET e.name = $name, e.category = $category, e.type = $type
            """,
            **knee
        ).consume()
    
    # Mobility levels (K-levels)
    mobility_levels = [
        {"level": "K0", "description": "Non-ambulatory"},
        {"level": "K1", "description": "Household ambulator"},
        {"level": "K2", "description": "Limited community ambulator"},
        {"level": "K3", "description": "Community ambulator"},
        {"level": "K4", "description": "High activity ambulator"},
    ]
    
    for ml in mobility_levels:
        session.run(
            """
            MERGE (m:MobilityLevel {level: $level})
            SET m.description = $description
            """,
            **ml
        ).consume()
    
    print(f"MOTU metadata: {len(prosthetic_knees)} prosthetic knees, {len(mobility_levels)} mobility levels")


# ================================================================
# 5. ENHANCED EXERCISE DATABASE WITH PROGRESSIONS
# ================================================================
def create_exercise_progressions(session):
    """Create exercise progression relationships based on clinical guidelines."""
    
    progressions = [
        # Lower limb progressions
        ("Bridge", "Single Leg Bridge", "strength"),
        ("Bridge", "Hip Thrust", "strength"),
        ("Squat", "Goblet Squat", "strength"),
        ("Squat", "Barbell Back Squat", "strength"),
        ("Lunge", "Walking Lunge", "strength"),
        ("Lunge", "Bulgarian Split Squat", "strength"),
        ("Step Up", "Step Down", "eccentric"),
        
        # Upper limb progressions
        ("Bench Press", "Incline Bench Press", "strength"),
        ("Shoulder Press", "Arnold Press", "strength"),
        ("Bicep Curl", "Hammer Curl", "strength"),
        ("Tricep Extension", "Skull Crushers", "strength"),
        
        # Core progressions
        ("Plank", "Side Plank", "stability"),
        ("Plank", "Dead Bug", "stability"),
        ("Crunch", "Bicycle Crunch", "strength"),
        ("Russian Twist", "Weighted Russian Twist", "strength"),
        
        # Balance progressions
        ("Single Leg Stand", "Single Leg Reach", "balance"),
        ("Balance Board", "BOSU Ball Squat", "balance"),
        ("Tandem Walk", "Heel-to-Toe Walk", "balance"),
        
        # Cardio progressions
        ("Walking", "Brisk Walking", "endurance"),
        ("Brisk Walking", "Jogging", "endurance"),
        ("Stationary Bike", "Outdoor Cycling", "endurance"),
        ("Elliptical", "Stair Climber", "endurance"),
    ]
    
    linked = 0
    for from_ex, to_ex, category in progressions:
        result = session.run(
            """
            MATCH (e1:Exercise {name: $from_name})
            MATCH (e2:Exercise {name: $to_name})
            MERGE (e1)-[r:PROGRESSES_TO]->(e2)
            SET r += $props, r.category = $category
            RETURN count(r) as c
            """,
            from_name=from_ex, to_name=to_ex, category=category,
            props=EXERCISE_PROGRESSES_TO,
        ).single()
        if result["c"] > 0:
            linked += 1
    
    print(f"Exercise progressions: {linked} PROGRESSES_TO relationships")


# ================================================================
# 6. CONDITION-EXERCISE MAPPINGS
# ================================================================
def create_condition_exercise_mappings(session):
    """Condition→Exercise links from the shared curated CSV.

    Delegates to bridges.link_conditions_to_exercises, which reads
    curated/condition_exercise.csv — the single source of truth shared
    with the bulk-import postload. On a first-time datasets run the
    Condition nodes may not exist yet; the call is idempotent and the
    post-additional linking pass picks up any remaining edges.
    """
    from bridges import link_conditions_to_exercises
    link_conditions_to_exercises(session)


# ================================================================
# MAIN
# ================================================================
def main():
    driver = get_driver()
    try:
        with driver.session(**get_session_config()) as session:
            session.run("RETURN 1").consume()
            print("Connected.\n")

            print("=== Creating Assessment Scales (RMD) ===")
            create_rmd_scales(session)

            print("\n=== Creating REHAB Stroke Metadata ===")
            create_rehab_metadata(session)

            print("\n=== Creating KneE-PAD Metadata ===")
            create_knee_pad_metadata(session)

            print("\n=== Creating MOTU Amputation Metadata ===")
            create_motu_metadata(session)

            print("\n=== Creating Exercise Progressions ===")
            create_exercise_progressions(session)

            print("\n=== Creating Condition-Exercise Mappings ===")
            create_condition_exercise_mappings(session)

            # Final counts
            print("\n=== Final Counts ===")
            for label in ['AssessmentScale', 'RehabMovement', 'MovementError', 
                          'MobilityLevel', 'Dataset', 'Exercise', 'Condition']:
                r = session.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()
                print(f":{label}: {r['c']}")
            
            for rel in ['PROGRESSES_TO', 'RECOMMENDS_EXERCISE', 'MEASURES', 'CONTAINS_MOVEMENT']:
                r = session.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS c").single()
                print(f":{rel}: {r['c']}")
                
    finally:
        driver.close()


if __name__ == "__main__":
    main()
