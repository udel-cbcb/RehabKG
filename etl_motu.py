#!/usr/bin/env python3
"""
ETL for MOTU Amputation Rehabilitation Dataset.
Loads patient data, hospital stays, outcomes into Neo4j.

Run: python etl_motu.py
"""

import csv
from pathlib import Path
from dotenv import load_dotenv
from db import get_driver, get_session_config

load_dotenv()

HERE = Path(__file__).parent
MOTU_DIR = HERE / "data" / "raw" / "motu"

BATCH = 500

# MOTU outcome specs — SINGLE SOURCE OF TRUTH for both load paths.
# The Cypher path (load_outcomes) and the bulk path (build_csvs.py)
# both build Outcome rows + MEASURED_BY links from this table via
# build_motu_outcomes(), so the two graphs cannot diverge on outcome
# content or MEASURED_BY counts (tests/test_motu_parity.py).
# (phase, HospitalStay.csv column, outcome-id suffix, assessment name,
#  scale_id, unit) — scale_id/name pairs must match RMD_SCALES.
MOTU_OUTCOME_SPECS = (
    ("admission", "BarthelAdmissionTotalScore", "BARTEL-ADM",
     "Barthel Index", "ASM-030", ""),
    ("discharge", "BarthelDischargeTotalScore", "BARTEL-DC",
     "Barthel Index", "ASM-030", ""),
    ("admission", "TWTInitialTime_m", "TWT-ADM",
     "10 Meter Walk Test", "ASM-023", "seconds"),
    ("discharge", "TWTDischargeTime_m", "TWT-DC",
     "10 Meter Walk Test", "ASM-023", "seconds"),
)


def build_motu_outcomes(rows):
    """Build deduplicated MOTU Outcome dicts from HospitalStay.csv rows.

    Pure function shared by both load paths: given the same input rows,
    both emit identical outcome_id → (phase, assessment, scale_id)
    mappings, so MEASURED_BY counts cannot diverge. Empty source columns
    are skipped; duplicate AnonymousIDs collapse keep-last (the raw file
    reuses IDs across stays, and Cypher MERGE / the bulk :ID dict both
    keep the last row's properties).
    """
    outcomes = {}
    for row in rows:
        stay_id = f"MOTU-STAY-{row['AnonymousID']}"
        for phase, col, suffix, assessment, scale_id, unit in MOTU_OUTCOME_SPECS:
            val = row.get(col, "")
            if not val:
                continue
            oid = f"{stay_id}-{suffix}"
            outcomes[oid] = {
                "outcome_id": oid,
                "stay_id": stay_id,
                "assessment": assessment,
                "scale_id": scale_id,
                "value": val,
                "unit": unit,
                "phase": phase,
            }
    return list(outcomes.values())


def load_patients(session):
    """Load MOTU patient data."""
    patients = []
    with open(MOTU_DIR / "Patient.csv", newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            patients.append({
                "patient_id": f"MOTU-{row['AnonymousID']}",
                "sex": row["Sex"],
                "birth_year": row["BirthDate"].split("-")[0] if row["BirthDate"] else None,
            })
    
    for i in range(0, len(patients), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MERGE (p:Patient {patient_id: row.patient_id})
            SET p.sex = row.sex, p.birth_year = row.birth_year, p.source = 'MOTU'
            """,
            rows=patients[i:i + BATCH],
        ).consume()
    
    print(f"MOTU patients: {len(patients)} loaded")
    return patients


def load_hospital_stays(session):
    """Load MOTU hospital stays with outcomes."""
    stays = []
    with open(MOTU_DIR / "HospitalStay.csv", newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stays.append({
                "patient_id": f"MOTU-{row['AnonymousID']}",
                "stay_id": f"MOTU-STAY-{row['AnonymousID']}",
                "admission_date": row.get("AdmissionDate"),
                "discharge_date": row.get("DischargeDate"),
                "los": row.get("LengthOfStay"),
                "amputation_side": row.get("AmputationSide"),
                "amputation_cause": row.get("AmputationCause"),
                "amputation_date": row.get("AmputationDate"),
                "height": row.get("Height"),
                "weight": row.get("Weight"),
                "n_comorbidities": row.get("NComorbidities"),
                "prosthetic_knee": row.get("ProstheticKnee"),
                "klevel_admission": row.get("KlevelAdmission"),
                "klevel_discharge": row.get("KlevelDischarge"),
                "barthel_admission": row.get("BarthelAdmissionTotalScore"),
                "barthel_discharge": row.get("BarthelDischargeTotalScore"),
                "twt_admission": row.get("TWTInitialTime_m"),
                "twt_discharge": row.get("TWTDischargeTime_m"),
                "morse_admission": row.get("MorseAdmissionTotalScore"),
                "morse_discharge": row.get("MorseDischargeTotalScore"),
                "hfall": row.get("HFall"),
                "diabetes": row.get("Diabetes"),
            })
    
    for i in range(0, len(stays), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MERGE (s:Session {session_id: row.stay_id})
            SET s.type = 'rehabilitation_hospital_stay',
                s.admission_date = row.admission_date,
                s.discharge_date = row.discharge_date,
                s.length_of_stay = toInteger(row.los),
                s.amputation_side = row.amputation_side,
                s.amputation_cause = row.amputation_cause,
                s.amputation_date = row.amputation_date,
                s.height = toFloat(row.height),
                s.weight = toFloat(row.weight),
                s.n_comorbidities = toInteger(row.n_comorbidities),
                s.prosthetic_knee = row.prosthetic_knee,
                s.klevel_admission = row.klevel_admission,
                s.klevel_discharge = row.klevel_discharge,
                s.source = 'MOTU'
            WITH s, row
            MATCH (p:Patient {patient_id: row.patient_id})
            MERGE (p)-[:HAS_STAY]->(s)
            """,
            rows=stays[i:i + BATCH],
        ).consume()
    
    print(f"MOTU hospital stays: {len(stays)} loaded")
    return stays


def load_outcomes(session):
    """Load MOTU clinical outcomes as Outcome nodes.

    Row building is delegated to the shared build_motu_outcomes() so the
    bulk path (build_csvs.py) writes the identical Outcome set and
    MEASURED_BY links.
    """
    with open(MOTU_DIR / "HospitalStay.csv", newline='') as f:
        outcomes = build_motu_outcomes(list(csv.DictReader(f)))

    for i in range(0, len(outcomes), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MERGE (o:Outcome {outcome_id: row.outcome_id})
            SET o.value = toFloat(row.value),
                o.value_numeric = toFloat(row.value),
                o.unit = row.unit,
                o.phase = row.phase,
                o.source = 'MOTU'
            WITH o, row
            MATCH (s:Session {session_id: row.stay_id})
            MERGE (s)-[:HAS_OUTCOME]->(o)
            WITH o, row
            MATCH (a:AssessmentScale {name: row.assessment})
            MERGE (o)-[:MEASURED_BY]->(a)
            """,
            rows=outcomes[i:i + BATCH],
        ).consume()
    
    print(f"MOTU outcomes: {len(outcomes)} loaded")


def load_knee_data(session):
    """Load prosthetic knee reference data."""
    knees = []
    with open(MOTU_DIR / "Knee.csv", newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            knees.append({
                "knee_code": row.get("Code", ""),
                "brand": row.get("Brand", ""),
                "model": row.get("Model", ""),
                "type": row.get("Type", ""),
                "category": row.get("Category", ""),
            })
    
    for knee in knees:
        if knee["knee_code"]:
            session.run(
                """
                MERGE (e:Equipment {equipment_id: $code})
                SET e.name = $brand + ' ' + $model,
                    e.brand = $brand, e.model = $model,
                    e.type = $type, e.category = $category,
                    e.source = 'MOTU'
                """,
                code=knee["knee_code"], brand=knee["brand"],
                model=knee["model"], type=knee["type"], category=knee["category"]
            ).consume()
    
    print(f"MOTU prosthetic knees: {len(knees)} loaded")


def load_fall_data(session):
    """Load fall incidents."""
    falls = []
    with open(MOTU_DIR / "Fall.csv", newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            falls.append({
                "fall_id": f"MOTU-FALL-{row.get('AnonymousID', '')}-{row.get('FallDate', '')}",
                "patient_id": f"MOTU-{row.get('AnonymousID', '')}",
                "date": row.get("FallDate"),
                "cause": row.get("FallCause"),
                "consequence": row.get("Consequence"),
            })
    
    for fall in falls:
        session.run(
            """
            MERGE (f:AdverseEvent {event_id: $fall_id})
            SET f.type = 'fall', f.date = $date,
                f.cause = $cause, f.consequence = $consequence,
                f.source = 'MOTU'
            WITH f
            MATCH (p:Patient {patient_id: $patient_id})
            MERGE (p)-[:EXPERIENCED]->(f)
            """,
            **fall
        ).consume()
    
    print(f"MOTU falls: {len(falls)} loaded")


def link_klevel_to_icf(session):
    """Link K-levels to ICF mobility concepts."""
    klevel_icf = [
        ("K0", "d450", "Walking"),
        ("K1", "d450", "Walking - household"),
        ("K2", "d450", "Walking - community"),
        ("K3", "d450", "Walking - community advanced"),
        ("K4", "d450", "Walking - high activity"),
    ]
    
    for klevel, icf_code, desc in klevel_icf:
        session.run(
            """
            MATCH (m:MobilityLevel {level: $klevel})
            MATCH (i:ICFConcept {code: $icf_code})
            MERGE (m)-[r:MAPS_TO_ICF]->(i)
            SET r.description = $desc
            """,
            klevel=klevel, icf_code=icf_code, desc=desc
        ).consume()
    
    print("K-level -> ICF links created")


def main():
    driver = get_driver()
    try:
        with driver.session(**get_session_config()) as session:
            session.run("RETURN 1").consume()
            print("Connected.\n")

            print("=== Loading MOTU Patients ===")
            load_patients(session)

            print("\n=== Loading MOTU Hospital Stays ===")
            load_hospital_stays(session)

            print("\n=== Loading MOTU Outcomes ===")
            load_outcomes(session)

            print("\n=== Loading MOTU Prosthetic Knees ===")
            load_knee_data(session)

            print("\n=== Loading MOTU Falls ===")
            load_fall_data(session)

            print("\n=== Linking K-levels to ICF ===")
            link_klevel_to_icf(session)

            # Final counts
            print("\n=== MOTU Final Counts ===")
            for label in ['Patient', 'Session', 'Outcome', 'AdverseEvent', 'Equipment', 'MobilityLevel']:
                r = session.run(f"MATCH (n:{label}) WHERE n.source = 'MOTU' OR n.source IS NULL RETURN count(n) AS c").single()
                print(f":{label}: {r['c']}")
            
            r = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()
            print(f"Total relationships: {r['c']}")
                
    finally:
        driver.close()


if __name__ == "__main__":
    main()
