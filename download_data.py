#!/usr/bin/env python3
"""
Download and prepare public datasets for the Rehabilitation Knowledge Graph.
Run: python download_data.py
"""

import os
import json
import requests
from pathlib import Path
import hashlib
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
ONTOLOGY_DIR = DATA_DIR / "ontologies"

for d in [RAW_DIR, PROCESSED_DIR, ONTOLOGY_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def download_file(url: str, dest: Path, expected_hash: str = None) -> bool:
    """Download a file with progress and optional hash verification."""
    if dest.exists():
        print(f"✓ Already exists: {dest.name}")
        if expected_hash:
            with open(dest, 'rb') as f:
                actual = hashlib.sha256(f.read()).hexdigest()
            if actual == expected_hash:
                print("  Hash verified")
                return True
            else:
                print("  Hash mismatch, re-downloading...")
                dest.unlink()
        else:
            return True

    print(f"⬇ Downloading: {dest.name}")
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        total = int(response.headers.get('content-length', 0))
        
        with open(dest, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = downloaded * 100 / total
                        print(f"\r  Progress: {pct:.1f}%", end="", flush=True)
        print()
        
        if expected_hash:
            with open(dest, 'rb') as f:
                actual = hashlib.sha256(f.read()).hexdigest()
            if actual != expected_hash:
                print(f"  ⚠ Hash mismatch! Expected {expected_hash}, got {actual}")
                return False
            print("  Hash verified")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        if dest.exists():
            dest.unlink()
        return False


def download_ontologies():
    """Download the focused default-set OWL/RDF ontology sources only."""
    print("\n=== Downloading Ontologies ===")
    
    ontologies = [
        {
            "name": "REHABO",
            "url": "https://data.bioontology.org/ontologies/REHABO/submissions/1/download?apikey={BIOPORTAL_API_KEY}",
            "dest": ONTOLOGY_DIR / "rehabo.owl",
            "format": "OWL"
        },
        {
            "name": "ICF",
            "url": "https://data.bioontology.org/ontologies/ICF/submissions/3/download?apikey={BIOPORTAL_API_KEY}",
            "dest": ONTOLOGY_DIR / "icf.owl",
            "format": "OWL"
        },
        {
            "name": "EXMO (Exercise Medicine Ontology)",
            "url": "https://raw.githubusercontent.com/Exercise-Medicine-Ontology/EXMO/master/exmo.owl",
            "dest": ONTOLOGY_DIR / "exmo.owl",
            "format": "OWL"
        },
        {
            "name": "PAIN (Pain Ontology)",
            "url": "https://raw.githubusercontent.com/obophenotype/pain-ontology/master/pain.owl",
            "dest": ONTOLOGY_DIR / "pain.owl",
            "format": "OWL"
        },
        {
            "name": "Mondo Disease Ontology",
            "url": "https://purl.obolibrary.org/obo/mondo.owl",
            "dest": ONTOLOGY_DIR / "mondo.owl",
            "format": "OWL"
        },
        {
            "name": "Uberon",
            "url": "https://purl.obolibrary.org/obo/uberon.owl",
            "dest": ONTOLOGY_DIR / "uberon.owl",
            "format": "OWL"
        },
        {
            "name": "Human Phenotype Ontology",
            "url": "https://purl.obolibrary.org/obo/hp.owl",
            "dest": ONTOLOGY_DIR / "hp.owl",
            "format": "OWL"
        },
    ]
    
    bioportal_key = os.getenv("BIOPORTAL_API_KEY", "")
    if not bioportal_key:
        print("  BioPortal downloads skipped: BIOPORTAL_API_KEY is not configured.")

    for onto in ontologies:
        print(f"\n{onto['name']} ({onto['format']})")
        if "data.bioontology.org" in onto["url"] and not bioportal_key:
            print("  Skipped (configure BIOPORTAL_API_KEY to download this source).")
            continue
        url = onto['url'].replace("{BIOPORTAL_API_KEY}", bioportal_key)
        download_file(url, onto['dest'])


def download_exercise_datasets():
    """Download exercise datasets (JSON/CSV)."""
    print("\n=== Downloading Exercise Datasets ===")
    
    datasets = [
        {
            "name": "Free Exercise DB (800+ exercises)",
            "url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json",
            "dest": RAW_DIR / "free-exercise-db" / "free_exercise_db.json",
        },
        {
            "name": "Free Exercise DB Schema",
            "url": "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/schema.json",
            "dest": RAW_DIR / "free-exercise-db" / "free_exercise_db_schema.json",
        },
    ]
    
    for ds in datasets:
        print(f"\n{ds['name']}")
        download_file(ds['url'], ds['dest'])


def download_manual_datasets():
    """Print instructions for manually downloaded datasets."""
    print("\n=== Manual Download Required ===")
    print("These datasets are too large or require acceptance of terms:")
    
    manual = [
        {
            "name": "REHAB24-6 (668 MB)",
            "url": "https://zenodo.org/records/13305826",
            "files": ["videos.zip", "3d_markers.zip", "2d_markers.zip", "3d_joints.zip", "2d_joints.zip", "Segmentation.csv", "joint_names.txt", "marker_names.txt"],
            "dest": RAW_DIR / "rehab24-6",
            "license": "CC BY-NC 4.0"
        },
        {
            "name": "IntelliRehabDS",
            "url": "https://zenodo.org/records/4610859",
            "files": ["Multiple CSV files (one per exercise per subject)"],
            "dest": RAW_DIR / "intellirehabds",
            "license": "Open Access"
        },
        {
            "name": "UI-PRMD",
            "url": "https://www.mdpi.com/2306-5729/3/1/2/pdf",
            "files": ["PDF paper + data supplement"],
            "dest": RAW_DIR / "ui-prmd",
            "license": "Open Access"
        },
        {
            "name": "REHAB Stroke Kinematics",
            "url": "https://www.scidb.cn/en/s/YrUnie",
            "files": ["REHAB (level-1).zip"],
            "dest": RAW_DIR / "rehab-stroke",
            "license": "Open Access"
        },
        {
            "name": "KneE-PAD Knee Rehabilitation",
            "url": "https://zenodo.org/records/...",
            "files": ["sEMG and IMU data for 31 patients"],
            "dest": RAW_DIR / "knee-pad",
            "license": "CC BY 4.0"
        },
        {
            "name": "GAITEX Gait & Rehab Exercises",
            "url": "https://zenodo.org/records/15729055",
            "files": ["IMU + MoCap data for 19 subjects"],
            "dest": RAW_DIR / "gaitex",
            "license": "CC BY-NC-ND 4.0"
        },
        {
            "name": "MOTU Amputation Rehabilitation",
            "url": "https://zenodo.org/records/...",
            "files": ["MOTU_fhir.zip", "MOTU_csv.zip"],
            "dest": RAW_DIR / "motu",
            "license": "CC BY 4.0"
        },
        {
            "name": "MIMIC-IV (Clinical EHR)",
            "url": "https://physionet.org/content/mimiciv/",
            "files": ["Requires PhysioNet credentialing"],
            "dest": RAW_DIR / "mimic-iv",
            "license": "PhysioNet DUA"
        },
        {
            "name": "San Raffaele Rehab Dataset",
            "url": "https://figshare.com/s/7aab7ad2d351f53dbe2f",
            "files": ["Dataset.csv"],
            "dest": RAW_DIR / "san-raffaele",
            "license": "CC BY 4.0"
        },
    ]
    
    for ds in manual:
        print(f"\n{ds['name']} [{ds['license']}]")
        print(f"  URL: {ds['url']}")
        print(f"  Save to: {ds['dest']}/")
        print(f"  Files: {', '.join(ds['files'])}")


def process_free_exercise_db():
    """Process the free exercise DB into Neo4j-ready format."""
    print("\n=== Processing Free Exercise DB ===")
    
    input_file = RAW_DIR / "free-exercise-db" / "free_exercise_db.json"
    if not input_file.exists():
        print("  Source file not found, skipping")
        return
    
    with open(input_file) as f:
        exercises = json.load(f)
    
    print(f"  Loaded {len(exercises)} exercises")
    
    # Transform for Neo4j import
    nodes = []
    relationships = []
    
    for ex in exercises:
        # Exercise node
        exercise_id = ex.get('id', '').replace(' ', '_')
        nodes.append({
            "id": exercise_id,
            "labels": ["Exercise"],
            "properties": {
                "name": ex.get('name'),
                "force": ex.get('force'),
                "level": ex.get('level'),
                "mechanic": ex.get('mechanic'),
                "equipment": ex.get('equipment'),
                "category": ex.get('category'),
                "instructions": ex.get('instructions', []),
                "images": ex.get('images', []),
            }
        })
        
        # Primary muscles
        for muscle in ex.get('primaryMuscles', []):
            muscle_id = f"muscle_{muscle.lower().replace(' ', '_')}"
            nodes.append({
                "id": muscle_id,
                "labels": ["Muscle", "BodyPart"],
                "properties": {"name": muscle, "type": "primary"}
            })
            relationships.append({
                "start": exercise_id,
                "end": muscle_id,
                "type": "TARGETS_PRIMARY",
                "properties": {}
            })
        
        # Secondary muscles
        for muscle in ex.get('secondaryMuscles', []):
            muscle_id = f"muscle_{muscle.lower().replace(' ', '_')}"
            nodes.append({
                "id": muscle_id,
                "labels": ["Muscle", "BodyPart"],
                "properties": {"name": muscle, "type": "secondary"}
            })
            relationships.append({
                "start": exercise_id,
                "end": muscle_id,
                "type": "TARGETS_SECONDARY",
                "properties": {}
            })
        
        # Equipment
        if ex.get('equipment'):
            equip_id = f"equipment_{ex['equipment'].lower().replace(' ', '_')}"
            nodes.append({
                "id": equip_id,
                "labels": ["Equipment"],
                "properties": {"name": ex['equipment']}
            })
            relationships.append({
                "start": exercise_id,
                "end": equip_id,
                "type": "REQUIRES",
                "properties": {}
            })
    
    # Deduplicate nodes
    seen = {}
    unique_nodes = []
    for n in nodes:
        key = (n['id'], tuple(sorted(n['labels'])))
        if key not in seen:
            seen[key] = n
            unique_nodes.append(n)
    
    print(f"  Unique nodes: {len(unique_nodes)}")
    print(f"  Relationships: {len(relationships)}")
    
    # Save as CSV for Neo4j LOAD CSV
    import csv
    
    # Nodes CSV
    with open(PROCESSED_DIR / "free-exercise-db" / "exercises_nodes.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['id:ID', 'labels:LABEL', 'name', 'force', 'level', 'mechanic', 'equipment', 'category', 'instructions', 'images', 'type'])
        for n in unique_nodes:
            props = n['properties']
            writer.writerow([
                n['id'],
                ';'.join(n['labels']),
                props.get('name', ''),
                props.get('force', ''),
                props.get('level', ''),
                props.get('mechanic', ''),
                props.get('equipment', ''),
                props.get('category', ''),
                '|'.join(props.get('instructions', [])),
                '|'.join(props.get('images', [])),
                props.get('type', '')
            ])
    
    # Relationships CSV
    with open(PROCESSED_DIR / "free-exercise-db" / "exercises_relationships.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([':START_ID', ':END_ID', ':TYPE'])
        for r in relationships:
            writer.writerow([r['start'], r['end'], r['type']])
    
    print(f"  Saved to {PROCESSED_DIR}/exercises_nodes.csv")
    print(f"  Saved to {PROCESSED_DIR}/exercises_relationships.csv")


def main():
    print("Rehabilitation KG - Data Downloader")
    print("=" * 50)
    
    download_ontologies()
    download_exercise_datasets()
    download_manual_datasets()
    process_free_exercise_db()
    
    print("\n=== Summary ===")
    print(f"Data directory: {DATA_DIR}")
    print(f"  Raw: {RAW_DIR}")
    print(f"  Processed: {PROCESSED_DIR}")
    print(f"  Ontologies: {ONTOLOGY_DIR}")
    print("\nNext steps:")
    print("1. Manually download large datasets (REHAB24-6, IntelliRehabDS)")
    print("2. Run: python setup_neo4j_schema.py")
    print("3. Import CSVs with Neo4j LOAD CSV")


if __name__ == "__main__":
    main()
