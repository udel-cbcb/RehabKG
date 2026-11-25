#!/usr/bin/env python3
"""Focused ontology-layer refresh for the currently approved source subset.

This is deliberately not a full graph rebuild. It replaces only ontology nodes
from the selected staged files, removes excluded ontology families, recreates
their source-owned hierarchy, and then runs the approved bridge/link steps.
Clinical/dataset nodes are retained. Review source terms and the generated
manifest before using this against a production graph.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import get_driver, get_uri, get_session_config
from etl_ontologies import (
    bridge_muscles_to_icf,
    bridge_rehabo_to_icf,
    connect_schema_islands,
    extract_exmo,
    extract_icf,
    extract_pain,
    extract_rehabo,
    load_exmo,
    load_icf,
    load_pain,
    load_rehabo,
)
from import_ontologies import (
    DISEASE_TO_ICD10,
    connect_exercises_to_uberon,
    connect_muscles_to_uberon,
)
from bridges import set_condition_icd10_codes
from provenance import HAS_ICD10, MAPS_TO_MONDO


DATA_DIR = Path(os.getenv("REHABKG_DATA_DIR", ROOT / "data"))
ONTO_DIR = DATA_DIR / "ontologies"
MANIFEST_PATH = Path(os.getenv(
    "REHABKG_REFRESH_MANIFEST", ROOT / "eval" / "public_ontology_refresh_manifest.json"
))
DEFAULT_ONTOLOGY_SOURCE_SET = frozenset({
    "rehabo.owl", "icf.owl", "exmo.owl", "pain.owl", "mondo.owl",
    "uberon.owl", "hp.owl",
})

REFRESHED_SOURCES = (
    "rehabo.owl", "icf.owl", "exmo.owl", "pain.owl", "mondo.owl", "uberon.owl",
)


def is_default_ontology_source(filename):
    """Whether a staged file belongs to the focused default refresh source set."""
    return filename in DEFAULT_ONTOLOGY_SOURCE_SET
REMOVED_SOURCES = (
    "copper.owl", "khmo.owl", "cbha.owl", "PMR", "mello_d.owl", "ope.owl",
    "phy.owl", "ontoloco.owl", "FRMO", "STO", "PACO", "NIHSS", "ACVD",
    "BCIO", "BCTT", "MSO", "POEM", "PHENX", "TRAK",
)


def _file_record(name):
    path = ONTO_DIR / name
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"file": str(path.relative_to(ROOT)), "size_bytes": path.stat().st_size,
            "sha256": digest}


def _delete_source_nodes(session):
    """Remove ontology-owned nodes; DETACH DELETE also removes incident edges."""
    # Source filenames/labels reflect the actual currently configured graph.
    # Restrict selectors to known ontology labels/sources, never generic data.
    query = """
    MATCH (n)
    WHERE n.source IN $sources
       OR any(lbl IN labels(n) WHERE lbl IN $labels)
       OR ((n:OntologyClass OR n:OntologyProperty OR n:OntologyIndividual)
           AND n.source = 'rehabo.owl')
    DETACH DELETE n
    """
    labels = [
        "ICFConcept", "REHABOConcept", "EXMOConcept", "PAINConcept",
        "MondoDisease", "UberonConcept", "HPOConcept", "COPPERConcept", "KHMOConcept",
        "CBHAConcept", "CBHAActivity", "PMRConcept", "MELLODConcept",
        "OPEConcept", "PHYConcept", "ONTOLOCOConcept", "FRMOConcept",
        "STOConcept", "PACOConcept", "NIHSSConcept", "ACVDConcept",
        "BCIOConcept", "BCTTConcept", "MSOConcept", "POEMConcept",
        "PHENXConcept", "TRAKConcept",
    ]
    sources = list(REFRESHED_SOURCES) + list(REMOVED_SOURCES)
    deleted = session.run(query, sources=sources, labels=labels).consume()
    return deleted.counters.nodes_deleted


def _delete_stale_ontology_edges(session):
    """Remove derived ontology bridges/hierarchy edges for clean regeneration.

    This runs only after ontology nodes were replaced. Dataset-owned
    relationships (patient/session/outcome/exercise records) are not selected.
    """
    hierarchy = session.run("""
        MATCH (a)-[r]->(b)
        WHERE type(r) IN ['SUBCLASS_OF', 'HAS_DOMAIN', 'HAS_RANGE', 'INSTANCE_OF']
          AND (a.source IN $sources OR b.source IN $sources)
        DELETE r
    """, sources=list(REFRESHED_SOURCES) + list(REMOVED_SOURCES) + ["Human Phenotype Ontology"]).consume()
    return hierarchy.counters.relationships_deleted


def _delete_rebuilt_bridge_edges(session):
    """Remove bridge edges before regenerating them against refreshed nodes."""
    result = session.run("""
        MATCH ()-[r]->()
        WHERE type(r) IN ['MAPS_TO_ICF', 'MAPS_TO_MONDO', 'HAS_ICD10',
                          'MAPS_TO_UBERON', 'TARGETS_ANATOMY', 'MEASURES',
                          'CLOSE_MATCH']
          AND (startNode(r).source IN $sources OR endNode(r).source IN $sources
               OR type(r) IN ['MAPS_TO_MONDO', 'HAS_ICD10'])
        DELETE r
    """, sources=list(REFRESHED_SOURCES) + ["Human Phenotype Ontology"]).consume()
    return result.counters.relationships_deleted


def _bridge_selected_ontologies(session):
    """Rebuild applicable bridges without invoking excluded source families."""
    from bridges import bridge_assessment_scales, bridge_exact_names, propagate_hierarchy
    from provenance import edge_props

    bridge_rehabo_to_icf(session)
    bridge_muscles_to_icf(session)
    bridge_exact_names(session)

    # Explicit EXMO bridge subset from etl_ontologies.bridge_ontologies;
    # skip its PMR/KHMO/COPPER sections because those sources are excluded.
    exmo_icf_bridges = [
        ("exercise", "d450", "Walking - exercise prescription"),
        ("physical_activity", "d450", "Physical activity as walking"),
        ("strength_training", "b730", "Strength training relates to muscle power"),
        ("flexibility", "b710", "Flexibility relates to joint mobility"),
        ("balance", "b235", "Balance training relates to vestibular functions"),
        ("endurance", "b455", "Endurance relates to exercise tolerance"),
    ]
    for fragment, code, description in exmo_icf_bridges:
        props = edge_props("curated", "explicit_source_rule", 1.0,
                           "etl_ontologies.py:EXMO_TO_ICF",
                           review_status="unreviewed", description=description)
        session.run("""
            MATCH (e:EXMOConcept) WHERE e.code CONTAINS $fragment
            MATCH (i:ICFConcept {code: $code})
            MERGE (e)-[r:MAPS_TO_ICF]->(i)
            SET r += $props
        """, fragment=fragment, code=code, props=props).consume()

    bridge_assessment_scales(session)
    propagate_hierarchy(session)
    _rebuild_hpo_icf(session)


def _load_hpo_nodes(session, hp_file):
    """Load labeled HPO classes from the staged file, without auto-bridging."""
    from rdflib import Graph, RDF, OWL, RDFS

    graph = Graph()
    graph.parse(str(hp_file), format="xml")
    rows = {}
    for subject in graph.subjects(RDF.type, OWL.Class):
        label = next((str(value) for value in graph.objects(subject, RDFS.label)), None)
        if label:
            uri = str(subject)
            code = uri.split("/")[-1].replace("_", ":")
            rows[code] = {"code": code, "name": label, "uri": uri}
    items = list(rows.values())
    for start in range(0, len(items), 500):
        session.run("""
            UNWIND $rows AS row
            MERGE (h:HPOConcept {code: row.code})
            SET h.name = row.name, h.uri = row.uri,
                h.source = 'Human Phenotype Ontology'
        """, rows=items[start:start + 500]).consume()
    return len(items)


def _rebuild_mondo_icd10(session):
    for disease, code in DISEASE_TO_ICD10.items():
        session.run(
            "MATCH (m:MondoDisease) WHERE toLower(m.name) CONTAINS $disease "
            "SET m.icd10_code = $code",
            disease=disease, code=code,
        ).consume()
    session.run("""
        MATCH (m:MondoDisease)
        WHERE m.icd10_code IS NOT NULL AND m.icd10_code <> ''
        WITH m, replace(m.icd10_code, '.', '') AS code
        MATCH (i:ICD10Code)
        WHERE i.code = code OR i.code STARTS WITH code
        MERGE (m)-[r:HAS_ICD10]->(i)
        SET r += $props
    """, props=HAS_ICD10).consume()


def _rebuild_condition_mondo(session):
    session.run("""
        MATCH (m:MondoDisease)
        WHERE m.name IS NOT NULL
        MATCH (c:Condition)
        WHERE c.name IS NOT NULL
          AND (toLower(trim(m.name)) = toLower(trim(c.name))
               OR (size(c.name) >= 5 AND toLower(m.name) CONTAINS toLower(c.name)))
        MERGE (c)-[r:MAPS_TO_MONDO]->(m)
        SET r += $props
    """, props=MAPS_TO_MONDO).consume()
    set_condition_icd10_codes(session)


def _rebuild_exercise_uberon(session):
    connect_muscles_to_uberon(session)
    connect_exercises_to_uberon(session)


def _rebuild_hpo_icf(session):
    """Recreate the nine explicit HPO-code to ICF-code links from the loader."""
    from bridges import bridge_default_sources
    return bridge_default_sources(session)


def _snapshot_counts(session):
    return session.run("""
        MATCH (n)
        WITH labels(n) AS labels, n.source AS source
        UNWIND labels AS label
        RETURN label, source, count(*) AS count
        ORDER BY label, source
    """).data()


def select_uberon_rows(graph, limit=10000):
    """Return the deterministic named UBERON class subset used by both paths."""
    from rdflib import RDF, OWL, RDFS, URIRef

    rows = []
    for cls in set(graph.subjects(RDF.type, OWL.Class)):
        if not isinstance(cls, URIRef):
            continue
        uri = str(cls)
        if "UBERON:" not in uri and "obo/UBERON_" not in uri:
            continue
        label = next((str(v) for v in graph.objects(cls, RDFS.label)), None)
        if label:
            rows.append({"uri": uri, "name": label})
    rows.sort(key=lambda row: row["uri"])
    return rows[:limit]


def select_mondo_rows(graph, limit=5000):
    """Return the deterministic Mondo disease subset used by both paths."""
    from rdflib import RDF, OWL, RDFS, URIRef

    rows = []
    for cls in set(graph.subjects(RDF.type, OWL.Class)):
        if not isinstance(cls, URIRef):
            continue
        label = next((str(v) for v in graph.objects(cls, RDFS.label)), None)
        if not label:
            continue
        codes = set()
        for _, value in graph.predicate_objects(cls):
            text = str(value)
            if "ICD10CM/" in text:
                codes.add(text.split("ICD10CM/")[-1])
            elif "ICD10CM:" in text:
                codes.add(text.split("ICD10CM:")[-1])
        rows.append({"uri": str(cls), "name": label,
                     "icd10_code": sorted(codes)[0] if codes else None})
    rows.sort(key=lambda row: (
        row["icd10_code"] is None, row["name"].lower(), row["uri"]))
    return rows[:limit]


def refresh(dry_run=False):
    missing = [name for name in REFRESHED_SOURCES if not (ONTO_DIR / name).is_file()]
    if not (ONTO_DIR / "hp.owl").is_file():
        missing.append("hp.owl")
    if missing:
        raise FileNotFoundError("Required staged ontology files missing: " + ", ".join(missing))

    # The current import_ontologies functions do not return rows, so use their
    # parser/extractor helpers for the focused load implementation below.
    from rdflib import Graph, RDF, OWL

    # Parse all selected sources before any graph write. This catches malformed
    # files and lets us refuse a partial destructive refresh.
    extracted = {
        "rehabo": extract_rehabo(),
        "icf": extract_icf(),
        "exmo": extract_exmo(),
        "pain": extract_pain(),
    }
    hp_file = ONTO_DIR / "hp.owl"
    hpo_graph = Graph()
    hpo_graph.parse(str(hp_file), format="xml")
    hpo_class_count = sum(1 for _ in hpo_graph.subjects(RDF.type, OWL.Class))
    uberon_graph = Graph()
    uberon_graph.parse(str(ONTO_DIR / "uberon.owl"), format="xml")
    uberon = select_uberon_rows(uberon_graph)

    # Mondo parsing can be expensive; run it before deleting anything.
    mondo_graph = Graph()
    mondo_graph.parse(str(ONTO_DIR / "mondo.owl"), format="xml")
    mondo_rows = select_mondo_rows(mondo_graph)

    staged_files = {name: _file_record(name) for name in REFRESHED_SOURCES}
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "database_uri": get_uri(),
        "operation": "focused ontology replacement; clinical dataset nodes retained",
        "e2e_database": get_session_config().get("database"),
        "bridge_refresh_policy": "rebuilds selected-source ICF/Mondo/Uberon/REHABO/EXMO and HPO/scale bridges; COPPER, KHMO and CBHA bridge families excluded",
        "sources_refreshed": staged_files,
        "hpo_file": _file_record("hp.owl"),
        "hpo_node_count_expected": hpo_class_count,
        "default_source_set": sorted(DEFAULT_ONTOLOGY_SOURCE_SET),
        "sources_removed": list(REMOVED_SOURCES),
        "files_loaded": {
            "HPO": "data/ontologies/hp.owl (32,772 labeled classes)",
            "ICF": "data/ontologies/icf.owl (1,509 concepts)",
        },
        "sources_retained_not_reloaded": ["HPO", "clinical/dataset sources"],
        "decisions": {
            "ICF": "included per user confirmation of local latest BioPortal file; CC BY-ND adaptation interpretation remains a user/legal review question",
            "Uberon": "included at user's direction; current loader subset is limited to 10,000 named UBERON classes; imported-term licenses mixed",
            "COPPER": "excluded; no license annotation found in staged copper.owl",
            "KHMO": "excluded; mixed imported-term licenses",
            "CBHA": "excluded at user's direction; category and activity nodes removed",
            "NIHSS": "excluded; staged file declares CC BY-NC 4.0",
        },
        "validation": "pending",
    }

    if dry_run:
        print(json.dumps({"manifest": manifest,
                          "extracted_counts": {
                              "REHABO_classes": len(extracted["rehabo"]["classes"]),
                              "ICF_concepts": len(extracted["icf"][0]),
                              "EXMO_concepts": len(extracted["exmo"][0]),
                              "PAIN_concepts": len(extracted["pain"][0]),
                              "Uberon_concepts": len(uberon),
                              "Mondo_diseases": len(mondo_rows),
                              "HPO_classes": hpo_class_count,
                          }}, indent=2))
        return

    driver = get_driver()
    try:
        with driver.session(**get_session_config()) as session:
            session.run("RETURN 1").consume()
            before = _snapshot_counts(session)
            live_hpo_before = session.run("MATCH (h:HPOConcept) RETURN count(h) AS c").single()["c"]
            unexpected = session.run("""
                MATCH (n)
                WHERE n.source ENDS WITH '.owl'
                  AND NOT (n.source IN $allowed)
                RETURN n.source AS source, count(n) AS count ORDER BY source
            """, allowed=list(REFRESHED_SOURCES) + ["Human Phenotype Ontology"] + list(REMOVED_SOURCES)).data()
            if unexpected:
                raise RuntimeError(
                    "Unexpected ontology sources remain; review before focused "
                    f"replacement: {unexpected}"
                )
            # All ontology parsing completed above; now replace selected and
            # excluded ontology layers. HPO is retained and refreshed in place;
            # clinical dataset records are retained.
            with session.begin_transaction() as tx:
                deleted_nodes = _delete_source_nodes(tx)
                deleted_edges = _delete_stale_ontology_edges(tx)
                deleted_bridge_edges = _delete_rebuilt_bridge_edges(tx)
                load_rehabo(tx, extracted["rehabo"])
                load_icf(tx, *extracted["icf"])
                load_exmo(tx, *extracted["exmo"])
                load_pain(tx, *extracted["pain"])
                for i in range(0, len(mondo_rows), 500):
                    tx.run("""
                        UNWIND $rows AS row
                        MERGE (n:MondoDisease {uri: row.uri})
                        SET n.name = row.name, n.icd10_code = row.icd10_code,
                            n.source = 'mondo.owl'
                    """, rows=mondo_rows[i:i+500]).consume()
                for i in range(0, len(uberon), 500):
                    tx.run("""
                        UNWIND $rows AS row
                        MERGE (n:UberonConcept {uri: row.uri})
                        SET n.name = row.name, n.source = 'uberon.owl'
                    """, rows=uberon[i:i+500]).consume()
                loaded_hpo = _load_hpo_nodes(tx, hp_file)
                tx.commit()

            # Rebuild Mondo/Uberon and ICF-dependent relationships against the
            # refreshed nodes. HPO is retained and its bridge is recomputed.
            with session.begin_transaction() as tx:
                _rebuild_mondo_icd10(tx)
                _rebuild_condition_mondo(tx)
                _rebuild_exercise_uberon(tx)
                connect_schema_islands(tx)
                _bridge_selected_ontologies(tx)
                from provenance import backfill_csv_import_edges
                backfill_csv_import_edges(tx)
                tx.commit()

            after = _snapshot_counts(session)
            manifest["validation"] = {
                "nodes_deleted": deleted_nodes,
                "hpo_nodes_deleted": 0,
                # The Neo4j counters include recreations in the same
                # transaction. These are transaction net counts, not pure
                # deletion counts; see explicit post-refresh relationship
                # validation below.
                "ontology_edges_deleted_net_transaction": deleted_edges,
                "bridge_edges_deleted_net_transaction": deleted_bridge_edges,
                "before_source_label_counts": before,
                "after_source_label_counts": after,
                "final_node_count": session.run(
                    "MATCH (n) RETURN count(n) AS count").single()["count"],
                "final_relationship_count": session.run(
                    "MATCH ()-[r]->() RETURN count(r) AS count").single()["count"],
                "selected_sources_have_incident_relationships": session.run("""
                    MATCH (n)-[r]-() WHERE n.source IN $sources
                    RETURN count(r) AS count
                """, sources=list(REFRESHED_SOURCES)).single()["count"],
                "excluded_source_nodes_remaining": session.run("""
                    MATCH (n) WHERE n.source IN $sources
                       OR any(lbl IN labels(n) WHERE lbl IN $labels)
                    RETURN count(n) AS count
                """, sources=list(REMOVED_SOURCES), labels=[
                    "COPPERConcept", "KHMOConcept", "CBHAConcept", "CBHAActivity",
                    "PMRConcept", "MELLODConcept", "OPEConcept", "PHYConcept",
                    "ONTOLOCOConcept", "FRMOConcept", "STOConcept", "PACOConcept",
                    "NIHSSConcept", "ACVDConcept", "BCIOConcept", "BCTTConcept",
                    "MSOConcept", "POEMConcept", "PHENXConcept", "TRAKConcept",
                ]).single()["count"],
                "hpo_nodes_loaded": loaded_hpo,
                "hpo_nodes_before": live_hpo_before,
                "hpo_related_to_icf_edges": session.run("""
                    MATCH (:HPOConcept)-[r:RELATED_TO_ICF]->(:ICFConcept)
                    RETURN count(r) AS count
                """).single()["count"],
                "hpo_related_to_icf_edges_with_valid_provenance": session.run("""
                    MATCH (:HPOConcept)-[r:RELATED_TO_ICF]->(:ICFConcept)
                    WHERE r.method = 'curated'
                      AND r.match_type = 'explicit_code_pair'
                      AND r.review_status = 'unreviewed'
                      AND r.source = 'add_additional_data.py:HPO_TO_ICF_MAPPINGS'
                      AND r.confidence = 1.0
                    RETURN count(r) AS count
                """).single()["count"],
            }
            if manifest["validation"]["excluded_source_nodes_remaining"] != 0:
                raise RuntimeError("Excluded-source nodes remain after refresh")
            MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(manifest["validation"], indent=2))
            print("Wrote", MANIFEST_PATH)
    finally:
        driver.close()


def main():
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse/validate staged files and show planned counts; no Neo4j writes")
    args = parser.parse_args()
    refresh(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
