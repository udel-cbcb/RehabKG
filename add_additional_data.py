#!/usr/bin/env python3
"""
Add additional publicly accessible ontologies and data to RehabKG.

Adds:
1. HPO (Human Phenotype Ontology) - 32K concepts
2. Expanded ClinicalTrials.gov - broader rehab queries
3. Updated EXMO bridges (if new)
"""

import json
import subprocess
import time
import os
from pathlib import Path
from dotenv import load_dotenv
from rdflib import Graph, RDFS, OWL, RDF

from db import get_driver, get_session_config

load_dotenv()

DATA_DIR = Path(os.getenv("REHABKG_DATA_DIR", "data"))
RAW_DIR = DATA_DIR / "raw"
ONTO_DIR = DATA_DIR / "ontologies"
BATCH = 500


def download_file(url, dest):
    """Download a file using curl."""
    subprocess.run(["curl", "-skL", url, "-o", str(dest)], check=True, timeout=120)
    return dest.exists()


# ================================================================
# 1. HPO - Human Phenotype Ontology
# ================================================================
def load_hpo(session):
    """Load HPO and connect to ICF where possible."""
    hp_file = ONTO_DIR / "hp.owl"
    
    if not hp_file.exists():
        print("  Downloading HPO...")
        download_file("https://purl.obolibrary.org/obo/hp.owl", hp_file)
    
    print(f"  Parsing HPO ({hp_file.stat().st_size / 1e6:.1f} MB)...")
    g = Graph()
    g.parse(str(hp_file), format="xml")
    
    # Extract classes with labels
    classes = {}
    for s in g.subjects(RDF.type, OWL.Class):
        label = None
        for _, _, lbl in g.triples((s, RDFS.label, None)):
            label = str(lbl)
            break
        if label:
            # Create a short code from URI
            uri = str(s)
            code = uri.split("/")[-1].replace("_", ":")
            classes[code] = {"uri": uri, "name": label}
    
    print(f"  HPO classes: {len(classes)}")
    
    # Load in batches (limit to manageable subset for PT relevance)
    # Focus on phenotypic abnormality subtree
    rows = []
    for code, info in classes.items():
        rows.append({"code": code, "name": info["name"], "uri": info["uri"]})
    
    loaded = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i+BATCH]
        session.run("""
            UNWIND $rows AS row
            MERGE (h:HPOConcept {code: row.code})
            SET h.name = row.name, h.uri = row.uri, h.source = 'Human Phenotype Ontology'
        """, rows=batch).consume()
        loaded += len(batch)
        if loaded % 5000 == 0:
            print(f"    Loaded {loaded}/{len(rows)}", flush=True)
    
    print(f"  HPO: {loaded} concepts loaded")
    
    # Connect HPO to ICF via the curated explicit code pairs
    # (bridges.HPO_ICF_PAIRS). They remain unreviewed candidates until an
    # identified reviewer completes the graph review workflow.
    from bridges import sync_hpo_icf_pairs
    icf_count = sync_hpo_icf_pairs(session)
    print(f"  HPO→ICF bridges: {icf_count}")
    return loaded


# ================================================================
# 2. Expanded ClinicalTrials.gov
# ================================================================
def load_expanded_clinicaltrials(session):
    """Fetch additional rehab trials from ClinicalTrials.gov API v2."""
    # Check existing trials
    result = session.run("MATCH (n:ClinicalTrial) RETURN count(n) AS cnt").single()
    existing = result["cnt"]
    print(f"  Existing trials: {existing}")
    
    queries = [
        "physical+therapy+rehabilitation",
        "exercise+therapy+musculoskeletal",
        "rehabilitation+stroke+exercise",
        "physical+therapy+balance+gait",
        "exercise+therapy+knee+hip",
        "rehabilitation+spinal+cord",
        "physical+therapy+shoulder+rotator",
        "exercise+therapy+back+pain",
        "rehabilitation+cardiac+exercise",
        "physical+therapy+neurological",
    ]
    
    all_studies = {}
    for q in queries:
        url = f"https://clinicaltrials.gov/api/v2/studies?query.cond={q}&pageSize=100&format=json"
        try:
            result = subprocess.run(["curl", "-sk", url], capture_output=True, text=True, timeout=30)
            data = json.loads(result.stdout)
            studies = data.get("studies", [])
            for s in studies:
                proto = s.get("protocolSection", {})
                nct = proto.get("identificationModule", {}).get("nctId", "")
                if nct and nct not in all_studies:
                    all_studies[nct] = proto
            print(f"    {q}: {len(studies)} studies", flush=True)
        except Exception as e:
            print(f"    {q}: ERROR {e}", flush=True)
        time.sleep(0.5)
    
    print(f"  Total unique trials found: {len(all_studies)}")
    
    # Load new trials only
    new_count = 0
    for nct, proto in all_studies.items():
        # Check if already exists
        result = session.run("MATCH (t:ClinicalTrial {nct_id: $nct}) RETURN count(t) AS c", nct=nct).single()
        if result["c"] > 0:
            continue
        
        title = proto.get("identificationModule", {}).get("briefTitle", "")
        status = proto.get("statusModule", {}).get("overallStatus", "")
        start = proto.get("statusModule", {}).get("startDateStruct", {}).get("date", "")
        completion = proto.get("statusModule", {}).get("completionDateStruct", {}).get("date", "")
        study_type = proto.get("designModule", {}).get("studyType", "")
        enrollment = proto.get("designModule", {}).get("enrollmentInfo", {}).get("count", 0)
        conditions = proto.get("conditionsModule", {}).get("conditions", [])
        
        session.run("""
            MERGE (t:ClinicalTrial {nct_id: $nct})
            SET t.title = $title, t.status = $status,
                t.start_date = $start, t.completion_date = $completion,
                t.study_type = $study_type, t.enrollment = toInteger($enrollment),
                t.source = 'ClinicalTrials.gov (expanded)'
        """, nct=nct, title=title, status=status, start=start or "",
             completion=completion or "", study_type=study_type,
             enrollment=enrollment or 0).consume()
        
        # Link to conditions
        for cond in conditions:
            normalized = cond.strip().lower()
            session.run("""
                MATCH (t:ClinicalTrial {nct_id: $nct})
                MERGE (c:Condition {name: $cond})
                SET c.source = 'ClinicalTrials.gov', c.name_normalized = $normalized
                MERGE (t)-[:STUDIES_CONDITION]->(c)
            """, nct=nct, cond=cond, normalized=normalized).consume()
        
        new_count += 1
    
    result = session.run("MATCH (n:ClinicalTrial) RETURN count(n) AS cnt").single()
    print(f"  New trials added: {new_count}, total: {result['cnt']}")
    return new_count


# ================================================================
# 3. EXMO bridges (verify/update)
# ================================================================
def verify_exmo_bridges(session):
    """Check and update EXMO→ICF bridges."""
    result = session.run("MATCH ()-[:MAPS_TO_ICF]->(:ICFConcept) RETURN count(*) AS cnt").single()
    existing = result["cnt"]
    print(f"  Existing MAPS_TO_ICF edges: {existing}")
    
    # Check EXMO concepts
    result = session.run("MATCH (n:EXMOConcept) RETURN count(n) AS cnt").single()
    print(f"  EXMO concepts: {result['cnt']}")
    
    return existing


# ================================================================
# Main
# ================================================================
def main():
    print("=" * 60)
    print("  Adding Additional Data to RehabKG")
    print("=" * 60)
    
    driver = get_driver()
    
    try:
        with driver.session(**get_session_config()) as session:
            # Test connection
            result = session.run("RETURN 1 AS test").single()
            print(f"\nConnected to Neo4j: {result['test'] == 1}")
            
            # 1. HPO
            print("\n=== 1. HPO (Human Phenotype Ontology) ===")
            load_hpo(session)
            
            # 2. Expanded ClinicalTrials
            print("\n=== 2. Expanded ClinicalTrials.gov ===")
            load_expanded_clinicaltrials(session)
            
            # 3. Verify EXMO
            print("\n=== 3. EXMO Bridge Verification ===")
            verify_exmo_bridges(session)
            
            # Final counts
            print("\n=== Final Counts ===")
            result = session.run("""
                MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count 
                ORDER BY count DESC LIMIT 25
            """)
            for r in result:
                print(f"  {r['label']}: {r['count']}")
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) AS rels").single()
            print(f"  Total relationships: {result['rels']}")
    
    finally:
        driver.close()
    
    print("\nDone!")


if __name__ == "__main__":
    main()
