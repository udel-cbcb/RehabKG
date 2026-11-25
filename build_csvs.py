"""
Build CSV files from source data for neo4j-admin bulk import.

Pipeline:  source files (OWL, CSV, JSON) → export/*.csv → neo4j-admin import

Usage:
    python build_csvs.py              # Build all CSVs
    python build_csvs.py --step ontologies  # One step only
    python build_csvs.py --validate   # Validate IDs after building
"""

import argparse
import csv
import json
import sys
import os
from pathlib import Path

from scripts.refresh_public_ontologies import (
    is_default_ontology_source,
    select_mondo_rows,
    select_uberon_rows,
)

from csv_writer import (
    ensure_dirs, write_node_csv, write_rel_csv, validate_ids,
    NODES_DIR, RELS_DIR,
)

RAW = Path(os.getenv("REHABKG_DATA_DIR", "data")) / "raw"
PROCESSED = Path(os.getenv("REHABKG_DATA_DIR", "data")) / "processed"
ONTO = Path(os.getenv("REHABKG_DATA_DIR", "data")) / "ontologies"

# ─── Helpers ──────────────────────────────────────────────────


def _clean(s):
    """Strip whitespace, return None for empty."""
    if s is None:
        return None
    s = str(s).strip()
    return s if s else None


def _id_exists(id_set, id_val):
    """Check if an ID exists; warn if not."""
    if id_val and id_val not in id_set:
        return False
    return True


def _read_node_rows(label):
    """Read IDs from a node CSV generated earlier in this build."""
    path = NODES_DIR / "nodes_{}.csv".format(label.lower())
    if not path.exists():
        raise FileNotFoundError("required node CSV missing: {}".format(path))
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ontology_eid(code, ns):
    """Globally-unique :ID for an ontology concept row.

    neo4j-admin import treats :ID as one keyspace across ALL node files and
    silently drops later-file duplicates (--skip-duplicate-nodes). Short or
    fragment-style codes ("MFOEM_000195", "Per_week") collide across
    ontologies, so they are prefixed with the ontology acronym when one is
    given. CURIE codes like "TRAK:0000001" already carry a namespace and are
    kept as-is.
    """
    if ns is None or ":" in code:
        return code
    return f"{ns}:{code}"


def _rehabo_id(kind, uri):
    """Namespaced CSV :ID for a REHABO node (keeps uri as a property)."""
    return f"REHABO_{kind}:{uri}"


# ─── 1. ONTOLOGIES ────────────────────────────────────────────


def build_ontologies():
    """Build ontology CSVs for the focused default source set only."""
    print("\n[1/5] Building ontology CSVs from OWL files...")

    # Import extract functions (they read OWL files directly)
    from etl_ontologies import extract_rehabo, extract_icf, extract_exmo, extract_pain

    # --- REHABO (OntologyClass, OntologyProperty, OntologyIndividual) ---
    # Props/individuals need the uri column too: load_rehabo MERGEs by uri,
    # so bulk-imported nodes without a uri property get duplicated when the
    # Cypher path is run on top of a bulk-loaded graph.
    rehabo = extract_rehabo()
    rehabo_class_uris = set(rehabo["classes"]) | set(rehabo.get("support", {}))
    class_rows = []
    for uri, c in {**rehabo["classes"], **rehabo.get("support", {})}.items():
        row = {
            ":ID": _rehabo_id("CLASS", uri),
            ":LABEL": "OntologyClass",
            "name": c.get("name", ""),
            "description": c.get("description", ""),
            "source": "rehabo.owl",
            "uri": uri,
        }
        if uri.startswith("http://purl.obolibrary.org/obo/REHABO_"):
            row[":LABEL"] = "OntologyClass;REHABOConcept"
            row["concept_id"] = uri
        class_rows.append(row)
    write_node_csv(
        "OntologyClass", class_rows,
        [":ID", ":LABEL", "name", "description", "source", "uri", "concept_id"],
    )

    prop_rows = []
    for uri, p in rehabo["props"].items():
        prop_rows.append({
            ":ID": _rehabo_id("PROP", uri),
            "name": p.get("name", ""),
            "description": p.get("description", ""),
            "source": "rehabo.owl",
            "uri": uri,
        })
    write_node_csv("OntologyProperty", prop_rows,
                   [":ID", "name", "description", "source", "uri"])

    ind_rows = []
    for uri, ind in rehabo["individuals"].items():
        ind_rows.append({
            ":ID": _rehabo_id("IND", uri),
            "name": ind.get("name", ""),
            "source": "rehabo.owl",
            "uri": uri,
        })
    write_node_csv("OntologyIndividual", ind_rows,
                   [":ID", "name", "source", "uri"])

    # SUBCLASS_OF for REHABO (only where both endpoints are in classes)
    subclass_rows = [{":START_ID": _rehabo_id("CLASS", s),
                      ":END_ID": _rehabo_id("CLASS", p), ":TYPE": "SUBCLASS_OF"}
                     for s, p in rehabo.get("subclass_of", [])
                     if s in rehabo_class_uris and p in rehabo_class_uris]
    write_rel_csv("SUBCLASS_OF_rehabo", subclass_rows)

    # HAS_DOMAIN, HAS_RANGE for REHABO
    prop_uris = set(rehabo["props"].keys())
    for rel_name, triples in [("HAS_DOMAIN", rehabo.get("domains", [])),
                               ("HAS_RANGE", rehabo.get("ranges", []))]:
        rows = [{":START_ID": _rehabo_id("PROP", s),
                 ":END_ID": _rehabo_id("CLASS", p), ":TYPE": rel_name}
                for s, p in triples
                if s in prop_uris and p in rehabo_class_uris]
        write_rel_csv(rel_name, rows)

    # INSTANCE_OF for REHABO individuals (focused path creates these too).
    inst_rows = [{":START_ID": _rehabo_id("IND", ind["uri"]),
                  ":END_ID": _rehabo_id("CLASS", target),
                  ":TYPE": "INSTANCE_OF"}
                 for ind in rehabo["individuals"].values()
                 for target in ind.get("types", [])
                 if target in rehabo_class_uris]
    write_rel_csv("INSTANCE_OF_rehabo", inst_rows)

    # --- ICF ---
    # code column: bridges (bridge_rehabo_to_icf, bridge_ontologies) and
    # export_csv match ICFConcept by {code}; :ID alone leaves code null on
    # bulk-imported nodes, so curated bridges silently match nothing.
    icf_concepts, icf_subclass = extract_icf()
    icf_uri_to_code = {}
    icf_rows = []
    for uri, c in icf_concepts.items():
        icf_uri_to_code[uri] = c["code"]
        icf_rows.append({":ID": c["code"], "code": c["code"], "name": c.get("name", ""),
                         "description": c.get("description", ""),
                         "chapter": c.get("chapter", ""), "domain": c.get("domain", ""),
                         "uri": uri, "source": "icf.owl"})
    write_node_csv("ICFConcept", icf_rows,
                   [":ID", "code", "name", "description", "chapter", "domain", "uri", "source"])

    rows = [{":START_ID": icf_uri_to_code.get(child, child), ":END_ID": icf_uri_to_code.get(parent, parent),
             ":TYPE": "SUBCLASS_OF"}
            for child, parent in icf_subclass
            if child in icf_uri_to_code and parent in icf_uri_to_code]
    write_rel_csv("SUBCLASS_OF_icf", rows)

    # --- Other ontologies ---
    # ns: acronym used to namespace :ID where a retained ontology has short
    # fragment codes that could collide with other node-file IDs.
    # Short/fragment IDs (e.g. "MFOEM_000195", "Per_week") collide across
    # ontology files because neo4j-admin treats :ID as one global keyspace
    # (--skip-duplicate-nodes silently drops the later file's node). CURIE
    # CURIE codes are preserved as-is.
    ontology_cache = {}  # name -> concepts dict (for curated bridges below)
    for name, extractor, label, ns in [
        ("exmo", extract_exmo, "EXMOConcept", None),
        ("pain", extract_pain, "PAINConcept", "PAIN"),
    ]:
        if not is_default_ontology_source(f"{name}.owl"):
            continue
        concepts, subclass = extractor()
        ontology_cache[name] = concepts
        uri_to_id = {}
        node_rows = []
        for uri, c in concepts.items():
            code = c.get("code") or uri
            eid = ontology_eid(code, ns)
            uri_to_id[uri] = eid
            node_rows.append({":ID": eid, "code": code,
                              "name": c.get("name", ""),
                              "description": c.get("description", ""),
                              "uri": uri, "source": f"{name}.owl"})
        write_node_csv(label, node_rows,
                       [":ID", "code", "name", "description", "uri", "source"])

        rows = [{":START_ID": uri_to_id[child], ":END_ID": uri_to_id[parent],
                 ":TYPE": "SUBCLASS_OF"}
                for child, parent in subclass
                if child in uri_to_id and parent in uri_to_id]
        write_rel_csv(f"SUBCLASS_OF_{name}", rows)

    from rdflib import Graph, RDFS

    # Mondo remains part of the default source set. Load a deterministic
    # labeled subset with lexical ICD-10 references and source-owned hierarchy.
    mondo_graph = Graph()
    mondo_graph.parse(str(ONTO / "mondo.owl"), format="xml")
    mondo_rows = select_mondo_rows(mondo_graph)
    write_node_csv("MondoDisease", [
        {":ID": r["uri"], "name": r["name"],
         "icd10_code": r.get("icd10_code") or "", "source": "mondo.owl"}
        for r in mondo_rows
    ], [":ID", "name", "icd10_code", "source"])
    mondo_ids = {r["uri"] for r in mondo_rows}
    write_rel_csv("SUBCLASS_OF_mondo", [
        {":START_ID": str(child), ":END_ID": str(parent), ":TYPE": "SUBCLASS_OF"}
        for child, parent in mondo_graph.subject_objects(RDFS.subClassOf)
        if str(child) in mondo_ids and str(parent) in mondo_ids
    ])

    # Uberon: reproduce the currently deployed loader's named UBERON class
    # subset (10,000 rows). This source is included by explicit user decision;
    # mixed imported-term annotations remain documented for review.
    uberon_graph = Graph()
    uberon_graph.parse(str(ONTO / "uberon.owl"), format="xml")
    uberon_rows = [
        {":ID": r["uri"], "uri": r["uri"], "name": r["name"],
         "source": "uberon.owl"}
        for r in select_uberon_rows(uberon_graph)
    ]
    write_node_csv("UberonConcept", uberon_rows, [":ID", "uri", "name", "source"])
    uberon_ids = {r[":ID"] for r in uberon_rows}
    write_rel_csv("SUBCLASS_OF_uberon", [
        {":START_ID": str(child), ":END_ID": str(parent), ":TYPE": "SUBCLASS_OF"}
        for child, parent in uberon_graph.subject_objects(RDFS.subClassOf)
        if str(child) in uberon_ids and str(parent) in uberon_ids
    ])

    print("  ✅ Ontology CSVs complete")


# ─── 2. ANATOMY ONTOLOGIES (Mondo, Uberon) ────────────────────


def build_anatomy():
    """Parse Mondo and Uberon OWL files, write CSVs."""
    print("\n[2/5] Building anatomy ontology CSVs...")

    # Mondo and Uberon remain in the focused default source set. Uberon is
    # deliberately capped at the same 10,000 named-class subset as the Cypher
    # loader.

    import rdflib
    from rdflib import RDFS

    # --- Mondo ---
    mondo_graph = rdflib.Graph()
    mondo_graph.parse(str(ONTO / "mondo.owl"), format="xml")
    mondo_rows = [
        {":ID": r["uri"], "name": r["name"],
         "icd10_code": r.get("icd10_code") or "", "source": "mondo.owl"}
        for r in select_mondo_rows(mondo_graph)
    ]
    write_node_csv("MondoDisease", mondo_rows, [":ID", "name", "icd10_code", "source"])

    # SUBCLASS_OF for Mondo (only where both endpoints are loaded)
    mondo_uris = {r[":ID"] for r in mondo_rows}
    mondo_subclass_rows = []
    for child, parent in mondo_graph.subject_objects(RDFS.subClassOf):
        child_str, parent_str = str(child), str(parent)
        if child_str in mondo_uris and parent_str in mondo_uris:
            mondo_subclass_rows.append({":START_ID": child_str, ":END_ID": parent_str, ":TYPE": "SUBCLASS_OF"})
    write_rel_csv("SUBCLASS_OF_mondo", mondo_subclass_rows)

    # --- Uberon ---
    uberon_graph = rdflib.Graph()
    uberon_graph.parse(str(ONTO / "uberon.owl"), format="xml")
    uberon_rows = [
        {":ID": r["uri"], "name": r["name"], "uri": r["uri"],
         "source": "uberon.owl"}
        for r in select_uberon_rows(uberon_graph)
    ]
    write_node_csv("UberonConcept", uberon_rows, [":ID", "name", "uri", "source"])

    # SUBCLASS_OF for UBERON (only where both endpoints are loaded)
    uberon_uris = {r[":ID"] for r in uberon_rows}
    uberon_subclass_rows = []
    for child, parent in uberon_graph.subject_objects(RDFS.subClassOf):
        child_str, parent_str = str(child), str(parent)
        if child_str in uberon_uris and parent_str in uberon_uris:
            uberon_subclass_rows.append({":START_ID": child_str, ":END_ID": parent_str, ":TYPE": "SUBCLASS_OF"})
    write_rel_csv("SUBCLASS_OF_uberon", uberon_subclass_rows)

    print("  ✅ Anatomy CSVs complete")


# ─── 3. CLINICAL DATASETS ─────────────────────────────────────


def build_datasets():
    """Parse clinical datasets and write CSVs."""
    print("\n[3/5] Building dataset CSVs...")

    # --- Free Exercise DB (reuse processed CSVs from download_data.py) ---
    nodes_file = PROCESSED / "free-exercise-db" / "exercises_nodes.csv"
    rels_file = PROCESSED / "free-exercise-db" / "exercises_relationships.csv"
    exercise_name_to_id = {}   # display name → :ID (for PROGRESSES_TO)
    exercise_rows = []
    muscle_rows = []
    equipment_rows = []

    if nodes_file.exists():
        META = {"id:ID", "labels:LABEL", ":START_ID", ":END_ID", ":TYPE"}

        # Parse nodes CSV (already has id:ID, labels:LABEL, etc.)
        with open(nodes_file, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                label = row["labels:LABEL"].split(";")[0].strip()
                rid = row["id:ID"]
                props = {k: v for k, v in row.items() if k not in META and v}

                if label == "Exercise":
                    props[":ID"] = rid
                    # business-key property: Cypher-path nodes carry
                    # exercise_id and queries MATCH on it; without the
                    # property bulk-loaded nodes silently fail those matches
                    props["exercise_id"] = rid
                    props["source"] = "Free Exercise DB"
                    exercise_rows.append(props)
                    # name → :ID for curated progressions (PROGRESSES_TO)
                    exercise_name_to_id.setdefault(props.get("name", ""), rid)
                elif label == "Muscle":
                    props[":ID"] = rid
                    props["part_id"] = rid
                    props["source"] = "Free Exercise DB"
                    muscle_rows.append(props)
                elif label == "Equipment":
                    props[":ID"] = rid
                    props["source"] = "Free Exercise DB"
                    equipment_rows.append(props)

        write_node_csv("Exercise", exercise_rows)
        write_node_csv("Muscle", muscle_rows)
        write_node_csv("Equipment", equipment_rows)

        # Parse relationships CSV
        if rels_file.exists():
            with open(rels_file, encoding="utf-8") as f:
                for rel_type, rows in _group_rels(csv.DictReader(f)).items():
                    csv_rows = [{":START_ID": r[":START_ID"], ":END_ID": r[":END_ID"],
                                 ":TYPE": rel_type} for r in rows]
                    write_rel_csv(rel_type, csv_rows)
    else:
        print(f"  ⚠️  {nodes_file} not found, run download_data.py first")

    # --- Open Rehab Exercises ---
    exercises_dir = RAW / "rehab-exercises" / "open-rehab-exercises-main"
    index_file = exercises_dir / "exercises" / "index.json"
    if index_file.exists():
        with open(index_file, encoding="utf-8") as f:
            index_data = json.load(f)

        exercise_list = index_data.get("exercises", index_data) if isinstance(index_data, dict) else index_data
        open_rehab_rows = []
        open_rehab_rels = []
        for ex in exercise_list:
            ex_id = ex.get("id", "") if isinstance(ex, dict) else ex
            locale_file = exercises_dir / "locales" / "en" / f"{ex_id}.json"
            name = ex_id
            if locale_file.exists():
                with open(locale_file, encoding="utf-8") as f:
                    loc = json.load(f)
                    name = loc.get("name", ex_id)

            open_rehab_rows.append({
                ":ID": ex_id, "name": name,
                "category": ex.get("category", ""),
                "body_region": ex.get("bodyRegion", ""),
                "tags": ",".join(ex.get("tags", [])),
                "default_sets": ex.get("defaultSets", ""),
                "default_reps": ex.get("defaultReps", ""),
                "default_hold_sec": ex.get("defaultHoldSec", ""),
                "source": "Open Rehab Exercises",
            })

            # TARGETS_BODY_PART relationships
            body_region = ex.get("bodyRegion", "")
            if body_region:
                open_rehab_rels.append({
                    ":START_ID": ex_id, ":END_ID": body_region.lower().replace(" ", "_"),
                    ":TYPE": "TARGETS_BODY_PART",
                })

        write_node_csv("OpenRehabExercise", open_rehab_rows)
        # Note: Open Rehab body regions ("ankle", "knee", etc.) don't match
        # existing Muscle node IDs. These relationships need post-load linking.
    else:
        print(f"  ⚠️  {index_file} not found")

    # --- MOTU (Patients, Sessions, Outcomes, Adverse Events, Equipment) ---
    motu = RAW / "motu"

    # --- Sessions from HospitalStay.csv ---
    # Ids/properties mirror etl_datasets.load_motu_data so the bulk graph
    # satisfies the same queries (MOTU-STAY-* session ids, outcome ids per
    # MOTU_OUTCOME_SPECS, AmputationCause values, MEASURED_BY links).
    stays_file = motu / "HospitalStay.csv"
    if stays_file.exists():
        # AnonymousID is reused across stays, so the same MOTU-STAY-* /
        # outcome :IDs repeat; Cypher's MERGE collapses them (last row's
        # properties win via SET). Mirror that: nodes dedupe by :ID
        # keep-last, rel rows by (start,end,type).
        session_map = {}
        outcome_map = {}
        has_stay_seen = set()
        has_outcome_seen = set()
        measured_by_seen = set()
        has_stay_rels = []
        has_outcome_rels = []
        measured_by_rels = []
        with open(stays_file, encoding="utf-8") as f:
            stay_rows = list(csv.DictReader(f))
        for r in stay_rows:
            anon = r["AnonymousID"]
            pid = f"MOTU-{anon}"
            sid = f"MOTU-STAY-{anon}"

            session_map[sid] = {
                ":ID": sid, "session_id": sid,
                "type": "rehabilitation_hospital_stay",
                "admission_date": r.get("AdmissionDate", ""),
                "discharge_date": r.get("DischargeDate", ""),
                "length_of_stay": r.get("LengthOfStay", ""),
                "amputation_side": r.get("AmputationSide", ""),
                "amputation_cause": r.get("AmputationCause", ""),
                "source": "MOTU",
            }

            stay_pair = (pid, sid, "HAS_STAY")
            if stay_pair not in has_stay_seen:
                has_stay_seen.add(stay_pair)
                has_stay_rels.append({":START_ID": pid, ":END_ID": sid, ":TYPE": "HAS_STAY"})

        # Outcomes + MEASURED_BY from the SHARED builder (etl_motu.py).
        # The old inline loop handled Barthel only and silently dropped
        # every 10m Walk Test outcome the Cypher path creates — since here
        # both paths consume build_motu_outcomes(), MEASURED_BY counts
        # cannot diverge (tests/test_motu_parity.py).
        from etl_motu import build_motu_outcomes
        for o in build_motu_outcomes(stay_rows):
            oid = o["outcome_id"]
            try:
                numeric = float(o["value"])
            except ValueError:
                numeric = ""
            outcome_map[oid] = {
                ":ID": oid, "outcome_id": oid, "value": o["value"],
                # value_numeric: typed column so AVG/MIN/MAX work
                # after bulk import (value itself stays the raw
                # string for display/compat).
                "value_numeric:float": numeric,
                "unit": o["unit"],
                "phase": o["phase"], "source": "MOTU",
            }
            pair = (o["stay_id"], oid, "HAS_OUTCOME")
            if pair not in has_outcome_seen:
                has_outcome_seen.add(pair)
                has_outcome_rels.append({":START_ID": o["stay_id"], ":END_ID": oid, ":TYPE": "HAS_OUTCOME"})
            mb = (oid, o["scale_id"], "MEASURED_BY")
            if mb not in measured_by_seen:
                measured_by_seen.add(mb)
                measured_by_rels.append({":START_ID": oid, ":END_ID": o["scale_id"], ":TYPE": "MEASURED_BY"})

        session_rows = list(session_map.values())
        outcome_rows = list(outcome_map.values())
        write_node_csv("Session", session_rows)
        if outcome_rows:
            write_node_csv("Outcome", outcome_rows)
        write_rel_csv("HAS_STAY", has_stay_rels)
        if has_outcome_rels:
            write_rel_csv("HAS_OUTCOME", has_outcome_rels)
        if measured_by_rels:
            write_rel_csv("MEASURED_BY", measured_by_rels)
        print(f"    MOTU: {len(session_rows)} stays, {len(outcome_rows)} outcomes (adm+dc)")

    # --- Patients ---
    patient_file = motu / "Patient.csv"
    if patient_file.exists():
        patient_rows = []
        with open(patient_file, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                pid = f"MOTU-{r['AnonymousID']}"
                patient_rows.append({
                    ":ID": pid, "patient_id": pid,
                    "sex": r.get("Sex", ""),
                    "birth_year": r.get("BirthDate", "")[:4],
                    "source": "MOTU",
                })
        write_node_csv("Patient", patient_rows)

    # --- Adverse Events from Fall.csv ---
    fall_file = motu / "Fall.csv"
    if fall_file.exists():
        adverse_rows = []
        experienced_rels = []
        with open(fall_file, encoding="utf-8") as f:
            for i, r in enumerate(csv.DictReader(f), 1):
                eid = f"fall_{i}"
                pid = f"MOTU-{r['AnonymousID']}"
                adverse_rows.append({
                    ":ID": eid, "event_id": eid, "type": "fall",
                    "date": r.get("Date", ""), "cause": r.get("Cause", ""),
                    "consequence": r.get("Consequence", ""), "source": "MOTU",
                })
                experienced_rels.append({":START_ID": pid, ":END_ID": eid, ":TYPE": "EXPERIENCED"})
        write_node_csv("AdverseEvent", adverse_rows)
        write_rel_csv("EXPERIENCED", experienced_rels)

    # --- MOTU Equipment from Knee.csv ---
    knee_file = motu / "Knee.csv"
    if knee_file.exists():
        eq_rows = []
        eq_seen = set()
        with open(knee_file, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                eid = f"eq_{r.get('Code', r.get('Brand', 'unknown'))}"
                # Code/Brand fallbacks repeat across rows; keep first per :ID
                # (multiple rows with the same :ID are dropped by neo4j-admin)
                if eid in eq_seen:
                    continue
                eq_seen.add(eid)
                eq_rows.append({
                    ":ID": eid,
                    "name": f"{r.get('Brand', '')} {r.get('Model', '')}".strip(),
                    "brand": r.get("Brand", ""), "model": r.get("Model", ""),
                    "type": r.get("Type", ""), "category": r.get("Category", ""),
                    "source": "MOTU",
                })
        write_node_csv("Equipment_motu", eq_rows)

    # --- Clinical Trials ---
    trials_file = RAW / "clinicaltrials" / "clinicaltrials_extracted.json"
    expanded_file = RAW / "clinicaltrials" / "clinicaltrials_expanded.json"
    if trials_file.exists():
        with open(trials_file, encoding="utf-8") as f:
            trials = json.load(f)

        # Merge the API-expanded trial set (output of
        # add_additional_data.load_expanded_clinicaltrials) so the bulk graph
        # matches the Cypher path (~1,387 trials / ~1,320 conditions).
        extracted_ncts = {t.get("nct_id") for t in trials}
        expanded_ncts = set()
        if expanded_file.exists():
            with open(expanded_file, encoding="utf-8") as f:
                expanded = json.load(f)
            expanded_ncts = {t.get("nct_id") for t in expanded}
            added = 0
            for t in expanded:
                if t.get("nct_id") and t["nct_id"] not in extracted_ncts:
                    trials.append(t)
                    added += 1
            print(f"    ClinicalTrials: merged {added} expanded trials "
                  f"({len(trials)} total)")

        trial_rows = []
        for t in trials:
            nct = t.get("nct_id", "")
            trial_rows.append({
                ":ID": nct, "nct_id": nct,
                "title": t.get("title", ""),
                "status": t.get("status", ""),
                "start_date": t.get("start_date", ""),
                "completion_date": t.get("completion_date", ""),
                "study_type": t.get("study_type", ""),
                "enrollment": t.get("enrollment", ""),
                "source": ("ClinicalTrials.gov (expanded)"
                           if nct in expanded_ncts - extracted_ncts
                           else "ClinicalTrials.gov"),
            })
        write_node_csv("ClinicalTrial", trial_rows)

        # Conditions: unique condition names across the extracted trials.
        # The Cypher path MERGEs these in add_additional_data.py / rehabkg.py;
        # without a CSV the bulk graph had zero Condition nodes and the
        # post-load bridges (MAPS_TO_MONDO, STUDIES_CONDITION,
        # RECOMMENDS_EXERCISE) silently matched nothing.
        cond_seen = set()
        cond_rows = []
        for t in trials:
            for c in t.get("conditions", []):
                name = c.strip()
                if not name or name in cond_seen:
                    continue
                cond_seen.add(name)
                cond_rows.append({
                    ":ID": name, "name": name,
                    "name_normalized": name.lower(),
                    "source": "ClinicalTrials.gov",
                })
        write_node_csv("Condition", cond_rows,
                       [":ID", "name", "name_normalized", "source"])

    # --- ICD-10 Codes ---
    icd10_file = RAW / "icd10" / "icd10cm_data.csv"
    if icd10_file.exists():
        icd_rows = []
        code_to_parent = {}  # code -> parent_code from Header field
        all_codes = set()
        with open(icd10_file, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                code = r.get("code", "")
                desc = r.get("description", "")
                all_codes.add(code)
                icd_rows.append({
                    ":ID": code,
                    "code": code,
                    "name": desc,
                    "description": desc,
                    "source": "CDC ICD-10-CM April 2025",
                })
                # Extract parent from "Header: A00 - ..." format
                if "Header:" in desc:
                    header_part = desc.split("Header:")[1].split("|")[0].strip()
                    # Extract code like "A00" from "A00 - Cholera"
                    parent_code = header_part.split("-")[0].strip() if "-" in header_part else header_part.split()[0]
                    if parent_code and parent_code != code:
                        code_to_parent[code] = parent_code
        
        # Create parent nodes that don't exist yet
        missing_parents = set(code_to_parent.values()) - all_codes
        for pc in sorted(missing_parents):
            icd_rows.append({
                ":ID": pc,
                "code": pc,
                "name": pc,
                "description": "",
                "source": "CDC ICD-10-CM April 2025",
            })
        
        write_node_csv("ICD10Code", icd_rows, [":ID", "code", "name", "description", "source"])
        
        # SUBCLASS_OF for ICD10 (parent from Header field)
        all_codes_full = {r[":ID"] for r in icd_rows}
        icd10_subclass_rows = []
        for child, parent in code_to_parent.items():
            if child in all_codes_full and parent in all_codes_full:
                icd10_subclass_rows.append({":START_ID": child, ":END_ID": parent, ":TYPE": "SUBCLASS_OF"})
        write_rel_csv("SUBCLASS_OF_icd10", icd10_subclass_rows)
        print(f"    ICD10: {len(icd10_subclass_rows)} subclass edges, {len(missing_parents)} parent nodes created")

    # --- Assessment Scales (shared 40-scale RMD set with etl_datasets) ---
    from etl_datasets import RMD_SCALES, EXERCISE_PROGRESSIONS
    scale_rows = [
        {":ID": s["scale_id"], "scale_id": s["scale_id"], "name": s["name"],
         "domain": s["domain"], "scoring_range": s["scoring_range"],
         "mcid": s["mcid"], "population": s["population"],
         "description": s.get("description", ""), "source": "RMD"}
        for s in RMD_SCALES
    ]
    write_node_csv("AssessmentScale", scale_rows)
    print(f"    AssessmentScale: {len(scale_rows)} scales")

    # MEASURES is rebuilt by bridges.bridge_assessment_scales in post_load.
    # The focused refresh clears curated MEASURES before that keyword bridge,
    # so both paths land the same 17 edges.

    # --- Exercise progressions (shared curated pairs → PROGRESSES_TO) ---
    prog_rels = []
    prog_missed = []
    for from_name, to_name, _category in EXERCISE_PROGRESSIONS:
        a = exercise_name_to_id.get(from_name)
        b = exercise_name_to_id.get(to_name)
        if a and b:
            prog_rels.append({":START_ID": a, ":END_ID": b,
                              ":TYPE": "PROGRESSES_TO"})
        else:
            prog_missed.append((from_name, to_name))
    write_rel_csv("PROGRESSES_TO", prog_rels)
    print(f"    Exercise progressions: {len(prog_rels)} pairs"
          + (f", missed {prog_missed}" if prog_missed else ""))

    print("  ✅ Dataset CSVs complete")


def _group_rels(reader):
    """Group relationship rows by type."""
    groups = {}
    for row in reader:
        t = row.get(":TYPE", "UNKNOWN")
        groups.setdefault(t, []).append(row)
    return groups


def _load_node_ids(label):
    """Load all :ID values from a node CSV."""
    path = NODES_DIR / f"nodes_{label.lower()}.csv"
    ids = set()
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                nid = row.get(":ID")
                if nid:
                    ids.add(nid)
    return ids


# ─── 4. HPO ONTOLOGY ──────────────────────────────────────────


def build_hpo():
    """Parse HPO OWL and write CSVs."""
    print("\n[4/5] Building HPO CSVs...")

    import rdflib
    from rdflib import RDF, RDFS, OWL

    hp_file = ONTO / "hp.owl"
    if not hp_file.exists():
        print(f"  ⚠️  {hp_file} not found")
        return

    g = rdflib.Graph()
    g.parse(str(hp_file), format="xml")

    hpo_rows = []
    for cls in g.subjects(RDF.type, OWL.Class):
        uri = str(cls)
        # code: last segment with _ -> :
        code = uri.split("/")[-1].replace("_", ":")
        labels = list(g.objects(cls, RDFS.label))
        # Parity with add_additional_data.load_hpo: every labelled owl:Class
        # in hp.owl becomes an HPOConcept (32.7K nodes incl. imported
        # UBERON/GO/CHEBI terms — the 30K test minimum counts these too).
        if not labels:
            continue
        name = str(labels[0])
        
        hpo_rows.append({":ID": code, "code": code, "name": name,
                         "uri": uri, "source": "Human Phenotype Ontology"})

    write_node_csv("HPOConcept", hpo_rows, [":ID", "code", "name", "uri", "source"])

    # SUBCLASS_OF for HPO: restricted to HP: ↔ HP: so imported terms (now
    # included as nodes for load_hpo parity) don't add cross-ontology
    # subclass edges under the HPOConcept label.
    hpo_uris = {r["uri"] for r in hpo_rows}
    hpo_subclass_rows = []
    for child, parent in g.subject_objects(RDFS.subClassOf):
        child_str, parent_str = str(child), str(parent)
        if child_str in hpo_uris and parent_str in hpo_uris:
            child_code = child_str.split("/")[-1].replace("_", ":")
            parent_code = parent_str.split("/")[-1].replace("_", ":")
            if child_code.startswith("HP:") and parent_code.startswith("HP:"):
                hpo_subclass_rows.append({":START_ID": child_code, ":END_ID": parent_code, ":TYPE": "SUBCLASS_OF"})
    write_rel_csv("SUBCLASS_OF_hpo", hpo_subclass_rows)

    # Only the reviewed-by-design explicit code pairs are emitted by default;
    # unlike broad lexical matching these do not infer new HPO/ICF links.
    from bridges import HPO_ICF_PAIRS
    explicit_hpo_icf = list(HPO_ICF_PAIRS)
    write_rel_csv("RELATED_TO_ICF_hpo_curated", [
        {":START_ID": hpo, ":END_ID": icf, ":TYPE": "RELATED_TO_ICF"}
        for hpo, icf in explicit_hpo_icf
    ])

    print(f"  ✅ HPO CSVs complete ({len(hpo_rows)} nodes, "
          f"{len(hpo_subclass_rows)} subclass edges)")


# ─── 5. SCHEMA (NodeType, RelType) ───────────────────────────


def build_schema():
    """Write schema nodes (NodeType, RelType) from curated definitions."""
    print("\n[5/5] Building schema CSVs...")

    node_types = [
        {":ID": "Patient", "name": "Patient", "description": "A patient receiving rehabilitation",
         "key_properties": "patient_id, sex, birth_year", "example": "MOTU-123"},
        {":ID": "Condition", "name": "Condition", "description": "A medical condition or diagnosis",
         "key_properties": "name", "example": "Low Back Pain"},
        {":ID": "Exercise", "name": "Exercise", "description": "A therapeutic exercise",
         "key_properties": "exercise_id, name, category, level", "example": "Barbell Squat"},
        {":ID": "BodyPart", "name": "BodyPart", "description": "An anatomical body part",
         "key_properties": "part_id, name", "example": "Quadriceps"},
        {":ID": "BodyFunction", "name": "BodyFunction", "description": "ICF body function",
         "key_properties": "code, name", "example": "b710 Range of joint motion"},
        {":ID": "Activity", "name": "Activity", "description": "ICF activity",
         "key_properties": "code, name", "example": "d450 Walking"},
        {":ID": "Assessment", "name": "Assessment", "description": "An assessment or outcome measure",
         "key_properties": "scale_id, name", "example": "Barthel Index"},
        {":ID": "Session", "name": "Session", "description": "A rehabilitation session or stay",
         "key_properties": "session_id, type", "example": "stay_123"},
        {":ID": "Intervention", "name": "Intervention", "description": "A treatment intervention",
         "key_properties": "name", "example": "Physical Therapy"},
        {":ID": "Outcome", "name": "Outcome", "description": "An outcome measurement",
         "key_properties": "outcome_id, value, phase", "example": "oc_123_barthel"},
    ]

    rel_types = [
        {":ID": "HAS_CONDITION", "name": "HAS_CONDITION", "description": "Patient has a condition",
         "from_type": "Patient", "to_type": "Condition"},
        {":ID": "PERFORMED", "name": "PERFORMED", "description": "Patient performed an exercise",
         "from_type": "Patient", "to_type": "Exercise"},
        {":ID": "INCLUDES", "name": "INCLUDES", "description": "Session includes an exercise",
         "from_type": "Session", "to_type": "Exercise"},
        {":ID": "TARGETS_PRIMARY", "name": "TARGETS_PRIMARY", "description": "Exercise primarily targets a muscle",
         "from_type": "Exercise", "to_type": "BodyPart"},
        {":ID": "TARGETS_SECONDARY", "name": "TARGETS_SECONDARY", "description": "Exercise secondarily targets a muscle",
         "from_type": "Exercise", "to_type": "BodyPart"},
        {":ID": "IMPROVES", "name": "IMPROVES", "description": "Exercise improves a body function",
         "from_type": "Exercise", "to_type": "BodyFunction"},
        {":ID": "REQUIRES", "name": "REQUIRES", "description": "Exercise requires equipment",
         "from_type": "Exercise", "to_type": "Equipment"},
        {":ID": "HAS_MOVEMENT", "name": "HAS_MOVEMENT", "description": "Exercise involves a movement",
         "from_type": "Exercise", "to_type": "Movement"},
        {":ID": "AFFECTS", "name": "AFFECTS", "description": "Condition affects a body function",
         "from_type": "Condition", "to_type": "BodyFunction"},
        {":ID": "MEASURES", "name": "MEASURES", "description": "Assessment measures a body function",
         "from_type": "Assessment", "to_type": "BodyFunction"},
        {":ID": "HAS_OUTCOME", "name": "HAS_OUTCOME", "description": "Session has an outcome",
         "from_type": "Session", "to_type": "Outcome"},
        {":ID": "MEASURED_BY", "name": "MEASURED_BY", "description": "Outcome measured by an assessment",
         "from_type": "Outcome", "to_type": "Assessment"},
        {":ID": "TREATED_BY", "name": "TREATED_BY", "description": "Condition treated by intervention",
         "from_type": "Condition", "to_type": "Intervention"},
        {":ID": "INCLUDES_EXERCISE", "name": "INCLUDES_EXERCISE", "description": "Intervention includes exercise",
         "from_type": "Intervention", "to_type": "Exercise"},
        {":ID": "MAPS_TO_ICF", "name": "MAPS_TO_ICF", "description": "Concept maps to ICF",
         "from_type": "Any", "to_type": "ICFConcept"},
        {":ID": "MAPS_TO_SNOMED", "name": "MAPS_TO_SNOMED", "description": "Concept maps to SNOMED",
         "from_type": "Any", "to_type": "SNOMEDConcept"},
    ]

    write_node_csv("NodeType", node_types)
    write_node_csv("RelType", rel_types)

    # FROM_NODE_TYPE and TO_NODE_TYPE relationships
    node_type_ids = {r[":ID"] for r in node_types}
    from_rels = [{":START_ID": r[":ID"], ":END_ID": r["from_type"], ":TYPE": "FROM_NODE_TYPE"}
                 for r in rel_types if r["from_type"] in node_type_ids]
    to_rels = [{":START_ID": r[":ID"], ":END_ID": r["to_type"], ":TYPE": "TO_NODE_TYPE"}
               for r in rel_types if r["to_type"] in node_type_ids]
    write_rel_csv("FROM_NODE_TYPE", from_rels)
    write_rel_csv("TO_NODE_TYPE", to_rels)

    print("  ✅ Schema CSVs complete")


# ─── Main ──────────────────────────────────────────────────────


STEPS = {
    "ontologies": build_ontologies,
    "anatomy": build_anatomy,
    "datasets": build_datasets,
    "hpo": build_hpo,
    "schema": build_schema,
}


# ─── Cross-file :ID collision resolution ─────────────────────
# neo4j-admin import treats :ID as ONE keyspace across all node files and
# --skip-duplicate-nodes silently drops later-file duplicates. Several
# ontologies import foreign classes (REHABO and Mondo reference Uberon;
# MELLOD references OPE/ONTOLOCO/PMR/ICF; COPPER and KHMO share BFO/OBI
# imports; MELLOD and the NodeType meta-layer both have an "Exercise"
# node), so the same URI/code appears in multiple files and the later
# file's node was never loaded. resolve_id_collisions() keeps the
# alphabetically-first file's :ID (matching import glob order) and renames
# later copies to "<PREFIX>:<id>", then rewrites the relationship CSVs
# owned by each renamed node file so its edges still resolve.

# node file stem -> prefix for its renamed duplicate rows
COLLISION_PREFIX = {
    "nodes_icfconcept": "ICF",
    "nodes_mellodconcept": "MELLOD",
    "nodes_mondodisease": "MONDO",
    "nodes_nodetype": "NODETYPE",
    "nodes_ontologyclass": "REHABO",
    "nodes_ontologyindividual": "REHABO",
    "nodes_ontologyproperty": "REHABO",
    "nodes_ontolococoncept": "ONTOLOCO",
    "nodes_opeconcept": "OPE",
    "nodes_pmrconcept": "PMR",
    "nodes_uberonconcept": "UBERON",
    "nodes_copperconcept": "COPPER",
    "nodes_khmoconcept": "KHMO",
}

# node file stem -> relationship files whose endpoints point at that file's
# nodes (endpoints in other files' rel CSVs refer to other copies)
COLLISION_RELS = {
    "nodes_icfconcept": ["rel_subclass_of_icf.csv"],
    "nodes_mellodconcept": ["rel_subclass_of_mello_d.csv"],
    "nodes_mondodisease": ["rel_subclass_of_mondo.csv"],
    "nodes_nodetype": ["rel_from_node_type.csv", "rel_to_node_type.csv"],
    "nodes_ontologyclass": ["rel_subclass_of_rehabo.csv",
                            "rel_has_domain.csv", "rel_has_range.csv"],
    "nodes_ontolococoncept": ["rel_subclass_of_ontoloco.csv"],
    "nodes_opeconcept": ["rel_subclass_of_ope.csv"],
    "nodes_pmrconcept": ["rel_subclass_of_pmr.csv"],
    "nodes_uberonconcept": ["rel_subclass_of_uberon.csv"],
    "nodes_copperconcept": ["rel_subclass_of_copper.csv"],
    "nodes_khmoconcept": ["rel_subclass_of_khmo.csv"],
}


def resolve_id_collisions(nodes_dir=NODES_DIR, rels_dir=RELS_DIR):
    """Rename duplicate :IDs in later files (import order) and fix their rels.

    Returns the number of renamed node rows. Files without a COLLISION_PREFIX
    entry keep today's behaviour (their duplicate rows stay and are dropped at
    import)."""
    files = sorted(nodes_dir.glob("nodes_*.csv"))
    seen = {}        # :ID -> stem of first (winning) file
    renames = {}     # stem -> {old_id: new_id}
    for f in files:
        stem = f.stem
        own = renames.setdefault(stem, {})
        with open(f, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                nid = row.get(":ID")
                if not nid:
                    continue
                if nid not in seen:
                    seen[nid] = stem
                    continue
                prefix = COLLISION_PREFIX.get(stem)
                if prefix is None:
                    continue  # unknown file: keep as-is (dropped at import)
                new_id = f"{prefix}:{nid}"
                if new_id in seen:
                    raise AssertionError(
                        f"collision rename still collides: {new_id} ({f.name})")
                own[nid] = new_id
                seen[new_id] = stem

    renamed_rows = 0
    for stem, mapping in renames.items():
        if not mapping:
            continue
        node_file = nodes_dir / f"{stem}.csv"
        with open(node_file, encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            fieldnames = reader.fieldnames
            rows = list(reader)
        for row in rows:
            if row.get(":ID") in mapping:
                row[":ID"] = mapping[row[":ID"]]
                renamed_rows += 1
        with open(node_file, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        for rel_name in COLLISION_RELS.get(stem, []):
            rel_file = rels_dir / rel_name
            if not rel_file.exists():
                continue
            with open(rel_file, encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                fieldnames = reader.fieldnames
                rel_rows = list(reader)
            for row in rel_rows:
                if row.get(":START_ID") in mapping:
                    row[":START_ID"] = mapping[row[":START_ID"]]
                if row.get(":END_ID") in mapping:
                    row[":END_ID"] = mapping[row[":END_ID"]]
            with open(rel_file, "w", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rel_rows)

    if renamed_rows:
        by_file = {s: len(m) for s, m in renames.items() if m}
        print(f"  Resolved {renamed_rows} duplicate :IDs (renamed in later "
              f"files): {by_file}")
    return renamed_rows


def main():
    parser = argparse.ArgumentParser(description="Build CSVs from source files for bulk import")
    parser.add_argument("--step", choices=list(STEPS.keys()) + ["all"],
                        default="all", help="Which step to build")
    parser.add_argument("--validate", action="store_true",
                        help="Validate IDs after building")
    parser.add_argument("--clean", action="store_true",
                        help="Remove existing staged CSV files before building")
    args = parser.parse_args()

    ensure_dirs()
    if args.clean:
        for folder in (NODES_DIR, RELS_DIR):
            for path in folder.glob("*.csv"):
                path.unlink()

    if args.step == "all":
        for name, func in STEPS.items():
            func()
        resolve_id_collisions()
    else:
        STEPS[args.step]()
        if args.step in ("ontologies", "anatomy"):
            resolve_id_collisions()

    if args.validate:
        print("\nValidating IDs...")
        node_count, rel_count, errors = validate_ids()
        if errors:
            print(f"❌ {errors} files with missing IDs")
            sys.exit(1)
        else:
            print(f"✅ {node_count:,} nodes, {rel_count:,} relationships, all IDs valid")


if __name__ == "__main__":
    main()
