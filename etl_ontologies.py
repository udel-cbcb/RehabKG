#!/usr/bin/env python3
"""
ELT for the rehabilitation ontologies into Neo4j.

Transforms the two local OWL files into a properly-modelled graph layer:

  rehabo.owl -> named OntologyClass/OntologyProperty/OntologyIndividual nodes
                (REHABO core + BFO/RO support terms referenced by it),
                with SUBCLASS_OF / HAS_DOMAIN / HAS_RANGE / INSTANCE_OF edges.
                FMA/KHMO terms are NOT loaded (no local source for their names).

  icf.owl    -> :ICFConcept nodes carrying ICF codes, names, definitions and
                chapters, plus domain labels per project schema:
                  b* -> :BodyFunction   s* -> :BodyStructure
                  d* -> :Activity       e* -> :EnvironmentalFactor
                with SUBCLASS_OF hierarchy (incl. grouping codes like d450-d469).

Also connects schema-documentation islands (RelType -> NodeType) and creates
curated Muscle/BodyPart -> ICF BodyStructure bridges.

Idempotent: all writes are MERGE-based. Run: python elt_ontologies.py
"""

import re
import xml.etree.ElementTree as ET
import os
from pathlib import Path

import rdflib
from rdflib import RDF, RDFS, OWL, URIRef
from dotenv import load_dotenv
from db import get_driver, get_session_config
from provenance import MUSCLE_TO_ICF

load_dotenv()

HERE = Path(__file__).parent
ONTO_DIR = Path(os.getenv("REHABKG_DATA_DIR", str(HERE / "data"))) / "ontologies"
REHABO_OWL = ONTO_DIR / "rehabo.owl"
ICF_OWL = ONTO_DIR / "icf.owl"
EXMO_OWL = ONTO_DIR / "exmo.owl"
PMR_OWL = ONTO_DIR / "pmr.owl"
MELLO_D_OWL = ONTO_DIR / "mello_d.owl"
COPPER_OWL = ONTO_DIR / "copper.owl"
KHMO_OWL = ONTO_DIR / "khmo.owl"
OPE_OWL = ONTO_DIR / "ope.owl"
PHY_OWL = ONTO_DIR / "phy.owl"
ONTOLOCO_OWL = ONTO_DIR / "ontoloco.owl"
PAIN_OWL = ONTO_DIR / "pain.owl"
# Tier-1 follow-up retained after source review (2026-10-17).
CBHA_OWL = ONTO_DIR / "cbha.owl"
CBHA_NS = "https://w3id.org/calendar-bench/human-activities/"

# Curated CBHA category -> ICF activity/participation code (2026-10-18).
# High-confidence only; the 1,210 Compendium activities reach ICF
# transitively via (CBHAActivity)-[:INSTANCE_OF]->(CBHAConcept).
# d925 (arts and culture) is absent from this icf.owl, so Dancing/Music
# fall back to d920 (recreation and leisure); d510 stands for the
# self-care chapter (d510-d599), which has no single umbrella code.
CBHA_TO_ICF = [
    ("SportsExerciseWorkoutWalking", "d450", "walking"),
    ("SportsExerciseWorkoutRunning", "d455", "moving around"),
    ("SportsExerciseWorkoutBicycling", "d470", "using transportation"),
    ("SportsExerciseWorkoutWaterActivities", "d455", "moving around"),
    ("SportsExerciseWorkoutWinterActivities", "d455", "moving around"),
    ("SportsExerciseWorkoutSports", "d920", "recreation and leisure"),
    ("SportsExerciseWorkoutDancing", "d920", "recreation and leisure"),
    ("LeisureEntertainmentTravelTransportation", "d470", "using transportation"),
    ("LeisureEntertainmentTravelMusicPlaying", "d920", "recreation and leisure"),
    ("LeisureEntertainmentTravelVideoGames", "d920", "recreation and leisure"),
    ("LeisureEntertainmentTravelFishingAndHunting", "d920", "recreation and leisure"),
    ("EverydayTasksHomeActivities", "d630", "housework activities"),
    ("EverydayTasksLawnAndGarden", "d630", "housework activities"),
    ("EverydayTasksSelfCare", "d510", "washing oneself (self-care chapter)"),
]

BATCH = 500
CODE_RE = re.compile(r"^([bsde])(\d{1,4})$")
ICF_NS = "http://who.int/icf#"
OBO = "http://purl.obolibrary.org/obo/"

DOMAIN_LABELS = {"b": "BodyFunction", "s": "BodyStructure",
                 "d": "Activity", "e": "EnvironmentalFactor"}

# Curated region-level mappings: muscle name (lowercase) -> ICF body-structure code
MUSCLE_TO_ICF_S = {
    "neck": "s710", "shoulders": "s720", "traps": "s720",
    "biceps": "s730", "triceps": "s730", "forearms": "s730",
    "glutes": "s740",
    "quadriceps": "s750", "hamstrings": "s750", "calves": "s750",
    "abductors": "s750", "adductors": "s750",
    "chest": "s760", "lats": "s760", "middle back": "s760",
    "lower back": "s760", "abdominals": "s760",
}

# Curated SKOS-style cross-ontology matches: REHABO uri suffix -> ICF code
# (grouping codes preferred for generic REHABO classes, exact codes otherwise)
# NOTE: codes follow THIS icf.owl file: b730 = "Muscle power functions"
# and b740 = "Muscle endurance functions". Re-check the source file before
# remapping these to printed/WHO labels.
REHABO_TO_ICF_MATCHES = [
    ("REHABO_0011005", "muscle function", ["b730-b749"]),
    ("REHABO_0011007", "power of a muscle", ["b730"]),
    ("REHABO_0011008", "strength of a muscle", ["b730"]),
    ("REHABO_0011006", "range of motion function of a joint", ["b710"]),
    ("REHABO_0011004", "joint function", ["b710-b729"]),
]


def first(g, subj, *preds):
    """First non-empty object of any predicate, as str."""
    for p in preds:
        for o in g.objects(subj, p):
            s = str(o).strip()
            if s:
                return s
    return None


def english_label(g, subj):
    """Preferred English label, else any label."""
    en = [str(o) for o in g.objects(subj, RDFS.label) if getattr(o, "language", None) == "en"]
    if en:
        return en[0]
    return first(g, subj, RDFS.label)


# ---------------------------------------------------------------- REHABO ----
def extract_rehabo():
    g = rdflib.Graph()
    g.parse(REHABO_OWL, format="xml")

    annotation_props = {str(s) for s in set(g.subjects(RDF.type, OWL.AnnotationProperty))
                        if isinstance(s, URIRef)}
    classes, props, individuals = {}, {}, {}
    for s in set(g.subjects(RDF.type, OWL.Class)):
        if not isinstance(s, URIRef) or str(s) in annotation_props:
            continue
        classes[str(s)] = {
            "uri": str(s),
            "name": english_label(g, s),
            "description": first(g, s, URIRef(OBO + "IAO_0000115"), RDFS.comment),
        }
    for t, bucket in ((OWL.ObjectProperty, props), (OWL.DatatypeProperty, props)):
        for s in set(g.subjects(RDF.type, t)):
            if not isinstance(s, URIRef):
                continue
            props[str(s)] = {
                "uri": str(s),
                "name": english_label(g, s),
                "description": first(g, s, URIRef(OBO + "IAO_0000115"), RDFS.comment),
            }
    for s in set(g.subjects(RDF.type, OWL.NamedIndividual)):
        if not isinstance(s, URIRef):
            continue
        types = [str(t) for t in g.objects(s, RDF.type)
                 if isinstance(t, URIRef) and t != OWL.NamedIndividual]
        individuals[str(s)] = {
            "uri": str(s), "name": english_label(g, s), "types": types,
        }

    subclass_of = [(str(s), str(o)) for s, _, o in g.triples((None, RDFS.subClassOf, None))
                   if isinstance(s, URIRef) and isinstance(o, URIRef)]
    domains = [(str(s), str(o)) for s, _, o in g.triples((None, RDFS.domain, None))
               if isinstance(s, URIRef) and isinstance(o, URIRef)]
    ranges = [(str(s), str(o)) for s, _, o in g.triples((None, RDFS.range, None))
              if isinstance(s, URIRef) and isinstance(o, URIRef)]

    # Support terms (BFO/RO parents etc.) referenced by edges but not defined
    # here: keep them only if this file carries a usable label.
    known = set(classes) | set(props)
    support = {}
    for a, b in subclass_of + domains + ranges:
        for uri in (a, b):
            if uri not in known and uri not in support and uri.startswith(OBO) \
                    and uri not in annotation_props:
                name = english_label(g, URIRef(uri))
                if name:
                    support[uri] = {"uri": uri, "name": name,
                                    "description": first(g, URIRef(uri), URIRef(OBO + "IAO_0000115"), RDFS.comment)}
    print(f"REHABO extract: {len(classes)} classes, {len(props)} properties, "
          f"{len(individuals)} individuals, {len(support)} support terms")
    return dict(classes=classes, props=props, individuals=individuals,
                support=support, subclass_of=subclass_of,
                domains=domains, ranges=ranges,
                annotation_props=sorted(annotation_props))


def load_rehabo(session, ext):
    session.run(
        """
        UNWIND $rows AS row
        MERGE (n:OntologyClass {uri: row.uri})
        SET n.name = row.name, n.description = row.description,
            n.source = 'rehabo.owl'
        WITH n, row WHERE row.uri STARTS WITH $obo + 'REHABO_'
        SET n:REHABOConcept, n.concept_id = row.uri
        """,
        rows=list(ext["classes"].values()) + list(ext["support"].values()),
        obo=OBO,
    ).consume()
    session.run(
        """
        UNWIND $rows AS row
        MERGE (n:OntologyProperty {uri: row.uri})
        SET n.name = row.name, n.description = row.description,
            n.source = 'rehabo.owl'
        """,
        rows=list(ext["props"].values()),
    ).consume()
    # Repair any node previously mis-filed as a class but actually an
    # OWL AnnotationProperty (e.g. IAO term-tracker metadata).
    session.run(
        """
        UNWIND $uris AS uri
        MATCH (n:OntologyClass {uri: uri})
        REMOVE n:OntologyClass, n:REHABOConcept
        SET n:OntologyProperty
        """,
        uris=ext["annotation_props"],
    ).consume()
    session.run(
        """
        UNWIND $rows AS row
        MERGE (n:OntologyIndividual {uri: row.uri})
        SET n.name = row.name, n.source = 'rehabo.owl'
        """,
        rows=[{k: v for k, v in r.items() if k != "types"}
              for r in ext["individuals"].values()],
    ).consume()

    known_classes = set(ext["classes"]) | set(ext["support"])
    subrels = [(a, b) for a, b in ext["subclass_of"] if b in known_classes]
    for i in range(0, len(subrels), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MATCH (a:OntologyClass {uri: row.a}), (b:OntologyClass {uri: row.b})
            MERGE (a)-[:SUBCLASS_OF]->(b)
            """,
            rows=[{"a": a, "b": b} for a, b in subrels[i:i + BATCH]],
        ).consume()

    for rel_type, pairs in (("HAS_DOMAIN", ext["domains"]), ("HAS_RANGE", ext["ranges"])):
        typed = [(a, b) for a, b in pairs if b in known_classes]
        for i in range(0, len(typed), BATCH):
            session.run(
                f"""
                UNWIND $rows AS row
                MATCH (a:OntologyProperty {{uri: row.a}}), (c:OntologyClass {{uri: row.b}})
                MERGE (a)-[:{rel_type}]->(c)
                """,
                rows=[{"a": a, "b": b} for a, b in typed[i:i + BATCH]],
            ).consume()

    inst = [(ind["uri"], t) for ind in ext["individuals"].values() for t in ind["types"]
            if t in known_classes]
    for i in range(0, len(inst), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MATCH (n:OntologyIndividual {uri: row.a}), (c:OntologyClass {uri: row.b})
            MERGE (n)-[:INSTANCE_OF]->(c)
            """,
            rows=[{"a": a, "b": b} for a, b in inst[i:i + BATCH]],
        ).consume()

    print(f"  REHABO load: {len(subrels)} SUBCLASS_OF, "
          f"{len(ext['domains'])}/{len(ext['ranges'])} domain/range kept, {len(inst)} INSTANCE_OF")


# ------------------------------------------------------------------- ICF ----
def extract_icf():
    g = rdflib.Graph()
    g.parse(ICF_OWL, format="xml")
    defn = URIRef(ICF_NS + "definition")

    concepts, skipped = {}, 0
    for s in set(g.subjects(RDF.type, OWL.Class)):
        if not isinstance(s, URIRef) or not str(s).startswith("http://who.int/icf#"):
            continue
        frag = str(s)[len(ICF_NS):]
        label = english_label(g, s)
        if not label:
            skipped += 1
            continue
        m = CODE_RE.match(frag)
        name = None
        if m:
            name = first(g, s, URIRef(ICF_NS + "altLabel")) or \
                re.sub(r"^%s\.\s*" % re.escape(frag), "", label).strip() or label
        desc = None
        def_obj = g.value(s, defn)
        if def_obj is not None:
            desc = str(def_obj) if isinstance(def_obj, rdflib.Literal) \
                else english_label(g, def_obj)

        concepts[str(s)] = {
            "uri": str(s),
            "code": frag,
            "name": name or label,
            "description": desc,
            "chapter": m.group(2)[0] if m else None,
            "domain": DOMAIN_LABELS.get(m.group(1)) if m else None,
        }

    subclass_of = []
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef) \
                and str(s) in concepts and str(o) in concepts:
            subclass_of.append((str(s), str(o)))
    print(f"ICF extract: {len(concepts)} concepts ({skipped} unlabeled skipped), "
          f"{len(subclass_of)} hierarchy edges")
    return concepts, subclass_of


def load_icf(session, concepts, subclass_of):
    rows = list(concepts.values())
    for i in range(0, len(rows), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MERGE (n:ICFConcept {code: row.code})
            SET n.uri = row.uri, n.name = row.name,
                n.description = row.description, n.chapter = row.chapter,
                n.source = 'icf.owl'
            WITH n, row CALL apoc.create.addLabels(n,
                CASE WHEN row.domain IS NULL THEN [] ELSE [row.domain] END
            ) YIELD node RETURN count(node)
            """,
            rows=rows[i:i + BATCH],
        ).consume()
    for i in range(0, len(subclass_of), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MATCH (a:ICFConcept {code: row.a_code}), (b:ICFConcept {code: row.b_code})
            MERGE (a)-[:SUBCLASS_OF]->(b)
            """,
            rows=[{"a_code": a.split("#")[-1], "b_code": b.split("#")[-1]}
                  for a, b in subclass_of[i:i + BATCH]],
        ).consume()


# --------------------------------------------------------------- EXMO ----
def extract_exmo():
    """Extract Exercise Medicine Ontology (EXMO) - OBO Foundry, CC BY 4.0.
    Focus: Exercise medicine for healthy people, chronic conditions, and disability."""
    g = rdflib.Graph()
    g.parse(EXMO_OWL, format="xml")
    
    concepts, skipped = {}, 0
    for s in set(g.subjects(RDF.type, OWL.Class)):
        if not isinstance(s, URIRef):
            continue
        uri_str = str(s)
        if not uri_str.startswith("http://purl.obolibrary.org/obo/EXMO_"):
            continue
        frag = uri_str.split("_")[-1]
        label = english_label(g, s)
        if not label:
            skipped += 1
            continue
        
        concepts[uri_str] = {
            "uri": uri_str,
            "code": f"EXMO_{frag}",
            "name": label,
            "description": first(g, s, URIRef(OBO + "IAO_0000115"), RDFS.comment),
        }
    
    subclass_of = []
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef) \
                and str(s) in concepts and str(o) in concepts:
            subclass_of.append((str(s), str(o)))
    print(f"EXMO extract: {len(concepts)} concepts ({skipped} unlabeled skipped), "
          f"{len(subclass_of)} hierarchy edges")
    return concepts, subclass_of


def load_exmo(session, concepts, subclass_of):
    rows = list(concepts.values())
    for i in range(0, len(rows), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MERGE (n:EXMOConcept {code: row.code})
            SET n.uri = row.uri, n.name = row.name,
                n.description = row.description, n.source = 'exmo.owl'
            """,
            rows=rows[i:i + BATCH],
        ).consume()
    for i in range(0, len(subclass_of), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MATCH (a:EXMOConcept {code: row.a_code}), (b:EXMOConcept {code: row.b_code})
            MERGE (a)-[:SUBCLASS_OF]->(b)
            """,
            rows=[{"a_code": a.split("_")[-1], "b_code": b.split("_")[-1]}
                  for a, b in subclass_of[i:i + BATCH]],
        ).consume()


# --------------------------------------------------------------- PMR ----
def extract_pmr():
    """Extract Physical Medicine and Rehabilitation Ontology (PMR).
    Focus: Clinical decision support in rehabilitation, integrates ICD-11, ICF, SNOMED CT."""
    g = rdflib.Graph()
    g.parse(PMR_OWL, format="xml")
    
    PMR_NS = "http://purl.bioontology.org/ontology/PMR.owl#"
    name_prop = URIRef(PMR_NS + "name")
    
    concepts, skipped = {}, 0
    for s in set(g.subjects(RDF.type, OWL.Class)):
        if not isinstance(s, URIRef):
            continue
        uri_str = str(s)
        # PMR uses http://purl.bioontology.org/ontology/ConceptName (no #)
        if not uri_str.startswith("http://purl.bioontology.org/ontology/"):
            continue
        frag = uri_str.split("/")[-1]
        
        # Try rdfs:label first, then custom PMR name property
        label = english_label(g, s)
        if not label:
            for o in g.objects(s, name_prop):
                label = str(o).strip()
                if label:
                    break
        
        if not label:
            # Use the URI fragment as fallback
            label = frag.replace("_", " ").title()
        
        concepts[uri_str] = {
            "uri": uri_str,
            "code": frag,
            "name": label,
            "description": first(g, s, RDFS.comment),
        }
    
    subclass_of = []
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef) \
                and str(s) in concepts and str(o) in concepts:
            subclass_of.append((str(s), str(o)))
    print(f"PMR extract: {len(concepts)} concepts ({skipped} unlabeled skipped), "
          f"{len(subclass_of)} hierarchy edges")
    return concepts, subclass_of


def load_pmr(session, concepts, subclass_of):
    rows = list(concepts.values())
    for i in range(0, len(rows), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MERGE (n:PMRConcept {code: row.code})
            SET n.uri = row.uri, n.name = row.name,
                n.description = row.description, n.source = 'pmr.owl'
            """,
            rows=rows[i:i + BATCH],
        ).consume()
    for i in range(0, len(subclass_of), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MATCH (a:PMRConcept {code: row.a_code}), (b:PMRConcept {code: row.b_code})
            MERGE (a)-[:SUBCLASS_OF]->(b)
            """,
            rows=[{"a_code": a.split("#")[-1], "b_code": b.split("#")[-1]}
                  for a, b in subclass_of[i:i + BATCH]],
        ).consume()


# -------------------------------------------------------------- MELLO-D ----
def extract_mello_d():
    """Extract Medical LifeLog Ontology for people with Disability (MELLO-D).
    Focus: LifeLog data for people with disability, exercise, sports, body regions."""
    g = rdflib.Graph()
    g.parse(MELLO_D_OWL, format="xml")
    
    concepts, skipped = {}, 0
    for s in set(g.subjects(RDF.type, OWL.Class)):
        if not isinstance(s, URIRef):
            continue
        uri_str = str(s)
        label = english_label(g, s)
        if not label:
            skipped += 1
            continue
        
        # Use URI fragment or generate code
        if "#" in uri_str:
            code = uri_str.split("#")[-1]
        else:
            code = uri_str.split("/")[-1]
        
        concepts[uri_str] = {
            "uri": uri_str,
            "code": code,
            "name": label,
            "description": first(g, s, RDFS.comment),
        }
    
    subclass_of = []
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef) \
                and str(s) in concepts and str(o) in concepts:
            subclass_of.append((str(s), str(o)))
    print(f"MELLO-D extract: {len(concepts)} concepts ({skipped} unlabeled skipped), "
          f"{len(subclass_of)} hierarchy edges")
    return concepts, subclass_of


def load_mello_d(session, concepts, subclass_of):
    rows = list(concepts.values())
    for i in range(0, len(rows), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MERGE (n:MELLODConcept {code: row.code})
            SET n.uri = row.uri, n.name = row.name,
                n.description = row.description, n.source = 'mello_d.owl'
            """,
            rows=rows[i:i + BATCH],
        ).consume()
    for i in range(0, len(subclass_of), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MATCH (a:MELLODConcept {code: row.a_code}), (b:MELLODConcept {code: row.b_code})
            MERGE (a)-[:SUBCLASS_OF]->(b)
            """,
            rows=[{"a_code": a.split("#")[-1] if "#" in a else a.split("/")[-1],
                   "b_code": b.split("#")[-1] if "#" in b else b.split("/")[-1]}
                  for a, b in subclass_of[i:i + BATCH]],
        ).consume()


# ------------------------------------------------------------- COPPER ----
def extract_copper():
    """Extract COPPER Ontology - Physical Activity Exercise Recommendations.
    Focus: Physical activity action and coping plans, OBO Foundry, CC BY 4.0."""
    g = rdflib.Graph()
    g.parse(COPPER_OWL, format="xml")
    
    concepts, skipped = {}, 0
    # COPPER uses multiple URI patterns including ADDICTO, BFO, etc.
    for s in set(g.subjects(RDF.type, OWL.Class)):
        if not isinstance(s, URIRef):
            continue
        uri_str = str(s)
        # Include any class that has a label
        label = english_label(g, s)
        if not label:
            skipped += 1
            continue
        
        # Generate code from URI
        if "#" in uri_str:
            code = uri_str.split("#")[-1]
        else:
            code = uri_str.split("/")[-1]
        
        concepts[uri_str] = {
            "uri": uri_str,
            "code": code,
            "name": label,
            "description": first(g, s, URIRef(OBO + "IAO_0000115"), RDFS.comment),
        }
    
    subclass_of = []
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef) \
                and str(s) in concepts and str(o) in concepts:
            subclass_of.append((str(s), str(o)))
    print(f"COPPER extract: {len(concepts)} concepts ({skipped} unlabeled skipped), "
          f"{len(subclass_of)} hierarchy edges")
    return concepts, subclass_of


def load_copper(session, concepts, subclass_of):
    rows = list(concepts.values())
    for i in range(0, len(rows), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MERGE (n:COPPERConcept {code: row.code})
            SET n.uri = row.uri, n.name = row.name,
                n.description = row.description, n.source = 'copper.owl'
            """,
            rows=rows[i:i + BATCH],
        ).consume()
    for i in range(0, len(subclass_of), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MATCH (a:COPPERConcept {code: row.a_code}), (b:COPPERConcept {code: row.b_code})
            MERGE (a)-[:SUBCLASS_OF]->(b)
            """,
            rows=[{"a_code": a.split("_")[-1], "b_code": b.split("_")[-1]}
                  for a, b in subclass_of[i:i + BATCH]],
        ).consume()


# -------------------------------------------------------------- KHMO ----
def extract_khmo():
    """Extract Kinetic Human Movement Ontology (KHMO).
    Focus: Human movement, anatomical and physiological entities, CC BY 4.0."""
    g = rdflib.Graph()
    g.parse(KHMO_OWL, format="xml")
    
    concepts, skipped = {}, 0
    # KHMO uses multiple URI patterns including OBO, FMA, etc.
    for s in set(g.subjects(RDF.type, OWL.Class)):
        if not isinstance(s, URIRef):
            continue
        uri_str = str(s)
        # Include any class that has a label
        label = english_label(g, s)
        if not label:
            skipped += 1
            continue
        
        # Generate code from URI
        if "#" in uri_str:
            code = uri_str.split("#")[-1]
        else:
            code = uri_str.split("/")[-1]
        
        concepts[uri_str] = {
            "uri": uri_str,
            "code": code,
            "name": label,
            "description": first(g, s, RDFS.comment),
        }
    
    subclass_of = []
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef) \
                and str(s) in concepts and str(o) in concepts:
            subclass_of.append((str(s), str(o)))
    print(f"KHMO extract: {len(concepts)} concepts ({skipped} unlabeled skipped), "
          f"{len(subclass_of)} hierarchy edges")
    return concepts, subclass_of


def load_khmo(session, concepts, subclass_of):
    rows = list(concepts.values())
    for i in range(0, len(rows), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MERGE (n:KHMOConcept {code: row.code})
            SET n.uri = row.uri, n.name = row.name,
                n.description = row.description, n.source = 'khmo.owl'
            """,
            rows=rows[i:i + BATCH],
        ).consume()
    for i in range(0, len(subclass_of), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MATCH (a:KHMOConcept {code: row.a_code}), (b:KHMOConcept {code: row.b_code})
            MERGE (a)-[:SUBCLASS_OF]->(b)
            """,
            rows=[{"a_code": a.split("/")[-1], "b_code": b.split("/")[-1]}
                  for a, b in subclass_of[i:i + BATCH]],
        ).consume()


# --------------------------------------------------------------- OPE ----
def extract_ope():
    """Extract Ontology of Physical Exercises (OPE).
    Focus: Exercises, movements, muscles, equipment, health outcomes."""
    g = rdflib.Graph()
    try:
        g.parse(OPE_OWL, format="xml")
    except Exception as e:
        print(f"OPE parse error (xml), trying turtle: {e}")
        try:
            g.parse(OPE_OWL, format="turtle")
        except Exception as e2:
            print(f"OPE parse failed completely: {e2}")
            return {}, []
    
    concepts, skipped = {}, 0
    for s in set(g.subjects(RDF.type, OWL.Class)):
        if not isinstance(s, URIRef):
            continue
        uri_str = str(s)
        label = english_label(g, s)
        if not label:
            skipped += 1
            continue
        
        if "#" in uri_str:
            code = uri_str.split("#")[-1]
        else:
            code = uri_str.split("/")[-1]
        
        concepts[uri_str] = {
            "uri": uri_str,
            "code": code,
            "name": label,
            "description": first(g, s, RDFS.comment),
        }
    
    subclass_of = []
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef) \
                and str(s) in concepts and str(o) in concepts:
            subclass_of.append((str(s), str(o)))
    print(f"OPE extract: {len(concepts)} concepts ({skipped} unlabeled skipped), "
          f"{len(subclass_of)} hierarchy edges")
    return concepts, subclass_of


def load_ope(session, concepts, subclass_of):
    rows = list(concepts.values())
    for i in range(0, len(rows), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MERGE (n:OPEConcept {code: row.code})
            SET n.uri = row.uri, n.name = row.name,
                n.description = row.description, n.source = 'ope.owl'
            """,
            rows=rows[i:i + BATCH],
        ).consume()
    for i in range(0, len(subclass_of), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MATCH (a:OPEConcept {code: row.a_code}), (b:OPEConcept {code: row.b_code})
            MERGE (a)-[:SUBCLASS_OF]->(b)
            """,
            rows=[{"a_code": a.split("#")[-1] if "#" in a else a.split("/")[-1],
                   "b_code": b.split("#")[-1] if "#" in b else b.split("/")[-1]}
                  for a, b in subclass_of[i:i + BATCH]],
        ).consume()


# --------------------------------------------------------------- PHY ----
def extract_phy():
    """Extract Physiotherapy Ontology (PHY).
    Focus: Physiotherapy exercises for lower limb rehabilitation."""
    g = rdflib.Graph()
    try:
        g.parse(PHY_OWL, format="xml")
    except Exception as e:
        print(f"PHY parse error: {e}")
        return {}, []
    
    concepts, skipped = {}, 0
    # PHY uses rdfs:Class instead of owl:Class
    for s in set(g.subjects(RDF.type, OWL.Class)):
        if not isinstance(s, URIRef):
            continue
        uri_str = str(s)
        label = english_label(g, s)
        if not label:
            skipped += 1
            continue
        
        if "#" in uri_str:
            code = uri_str.split("#")[-1]
        else:
            code = uri_str.split("/")[-1]
        
        concepts[uri_str] = {
            "uri": uri_str,
            "code": code,
            "name": label,
            "description": first(g, s, RDFS.comment),
        }
    
    # Also try rdfs:Class
    for s in set(g.subjects(RDF.type, RDFS.Class)):
        if not isinstance(s, URIRef) or str(s) in concepts:
            continue
        uri_str = str(s)
        label = english_label(g, s)
        if not label:
            skipped += 1
            continue
        
        if "#" in uri_str:
            code = uri_str.split("#")[-1]
        else:
            code = uri_str.split("/")[-1]
        
        concepts[uri_str] = {
            "uri": uri_str,
            "code": code,
            "name": label,
            "description": first(g, s, RDFS.comment),
        }
    
    subclass_of = []
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef) \
                and str(s) in concepts and str(o) in concepts:
            subclass_of.append((str(s), str(o)))
    print(f"PHY extract: {len(concepts)} concepts ({skipped} unlabeled skipped), "
          f"{len(subclass_of)} hierarchy edges")
    return concepts, subclass_of


def load_phy(session, concepts, subclass_of):
    rows = list(concepts.values())
    for i in range(0, len(rows), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MERGE (n:PHYConcept {code: row.code})
            SET n.uri = row.uri, n.name = row.name,
                n.description = row.description, n.source = 'phy.owl'
            """,
            rows=rows[i:i + BATCH],
        ).consume()
    for i in range(0, len(subclass_of), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MATCH (a:PHYConcept {code: row.a_code}), (b:PHYConcept {code: row.b_code})
            MERGE (a)-[:SUBCLASS_OF]->(b)
            """,
            rows=[{"a_code": a.split("#")[-1] if "#" in a else a.split("/")[-1],
                   "b_code": b.split("#")[-1] if "#" in b else b.split("/")[-1]}
                  for a, b in subclass_of[i:i + BATCH]],
        ).consume()


# ----------------------------------------------------------- ONTOLOCO ----
def extract_ontoloco():
    """Extract ONTOLOCO - VR Locomotion Rehabilitation for Stroke.
    Focus: Virtual reality-based locomotion rehabilitation for stroke injuries."""
    g = rdflib.Graph()
    try:
        g.parse(ONTOLOCO_OWL, format="xml")
    except Exception as e:
        print(f"ONTOLOCO parse error (xml), trying turtle: {e}")
        try:
            g.parse(ONTOLOCO_OWL, format="turtle")
        except Exception as e2:
            print(f"ONTOLOCO parse failed completely: {e2}")
            return {}, []
    
    concepts, skipped = {}, 0
    for s in set(g.subjects(RDF.type, OWL.Class)):
        if not isinstance(s, URIRef):
            continue
        uri_str = str(s)
        label = english_label(g, s)
        if not label:
            skipped += 1
            continue
        
        if "#" in uri_str:
            code = uri_str.split("#")[-1]
        else:
            code = uri_str.split("/")[-1]
        
        concepts[uri_str] = {
            "uri": uri_str,
            "code": code,
            "name": label,
            "description": first(g, s, RDFS.comment),
        }
    
    subclass_of = []
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef) \
                and str(s) in concepts and str(o) in concepts:
            subclass_of.append((str(s), str(o)))
    print(f"ONTOLOCO extract: {len(concepts)} concepts ({skipped} unlabeled skipped), "
          f"{len(subclass_of)} hierarchy edges")
    return concepts, subclass_of


def load_ontoloco(session, concepts, subclass_of):
    rows = list(concepts.values())
    for i in range(0, len(rows), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MERGE (n:ONTOLOCOConcept {code: row.code})
            SET n.uri = row.uri, n.name = row.name,
                n.description = row.description, n.source = 'ontoloco.owl'
            """,
            rows=rows[i:i + BATCH],
        ).consume()
    for i in range(0, len(subclass_of), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MATCH (a:ONTOLOCOConcept {code: row.a_code}), (b:ONTOLOCOConcept {code: row.b_code})
            MERGE (a)-[:SUBCLASS_OF]->(b)
            """,
            rows=[{"a_code": a.split("#")[-1] if "#" in a else a.split("/")[-1],
                   "b_code": b.split("#")[-1] if "#" in b else b.split("/")[-1]}
                  for a, b in subclass_of[i:i + BATCH]],
        ).consume()


# --------------------------------------------------------------- bridges ----
def connect_schema_islands(session):
    session.run(
        """
        MATCH (r:RelType) WHERE r.from_type IS NOT NULL
        MATCH (from:NodeType {name: r.from_type})
        MERGE (r)-[:FROM_NODE_TYPE]->(from)
        """
    ).consume()
    session.run(
        """
        MATCH (r:RelType) WHERE r.to_type IS NOT NULL
        MATCH (to:NodeType {name: r.to_type})
        MERGE (r)-[:TO_NODE_TYPE]->(to)
        """
    ).consume()
    n = session.run(
        "MATCH (:RelType)-[:FROM_NODE_TYPE|TO_NODE_TYPE]->() RETURN count(*) AS c"
    ).single()["c"]
    print(f"Schema islands: {n} RelType->NodeType links")


def bridge_muscles_to_icf(session):
    available = {r["code"] for r in session.run(
        "MATCH (i:ICFConcept) WHERE i.code IN $codes RETURN i.code AS code",
        codes=list(set(MUSCLE_TO_ICF_S.values())),
    )}
    mapped, unmapped = [], []
    for muscle, code in MUSCLE_TO_ICF_S.items():
        if code in available:
            mapped.append({"muscle": muscle, "code": code})
        else:
            unmapped.append((muscle, code))
    session.run(
        """
        UNWIND $rows AS row
        MATCH (m:Muscle) WHERE toLower(m.name) = row.muscle
        MATCH (i:ICFConcept {code: row.code})
        MERGE (m)-[r:MAPS_TO_ICF]->(i)
        SET r += $props, r.granularity = 'region'
        WITH m, i MATCH (bp:BodyPart {part_id: m.muscle_id})
        MERGE (bp)-[r2:MAPS_TO_ICF]->(i)
        SET r2 += $props, r2.granularity = 'region'
        """,
        rows=mapped,
        props=MUSCLE_TO_ICF,
    ).consume()
    n = session.run(
        "MATCH (:Muscle)-[:MAPS_TO_ICF]->(:ICFConcept) RETURN count(*) AS c"
    ).single()["c"]
    print(f"Muscle->ICF bridge: {n} MAPS_TO_ICF edges "
          f"({len(unmapped)} targets missing: {unmapped or 'none'})")


# ------------------------------------------------------------ dedup check ---
def bridge_rehabo_to_icf(session):
    """Curated SKOS-style closeMatch links between REHABO classes and ICF
    concepts. Rebuilds all curated edges each run so mapping updates take
    effect; only creates an edge when both endpoints exist."""
    session.run(
        "MATCH ()-[m:CLOSE_MATCH {source: 'curated'}]->() DELETE m"
    ).consume()
    landed, missed = [], []
    for suffix, name, candidates in REHABO_TO_ICF_MATCHES:
        target = next((c for c in candidates if session.run(
            "MATCH (i:ICFConcept {code: $c}) RETURN 1 LIMIT 1", c=c).peek()), None)
        if target is None:
            missed.append((name, candidates))
            continue
        session.run(
            """
            MATCH (r:REHABOConcept {uri: $obo + $suffix})
            MATCH (i:ICFConcept {code: $code})
            MERGE (r)-[m:CLOSE_MATCH]->(i)
            SET m.source = 'curated', m.standard = 'SKOS'
            """,
            obo=OBO, suffix=suffix, code=target,
        ).consume()
        landed.append((name, target))
    print(f"REHABO->ICF closeMatch: {len(landed)} edges "
          f"({', '.join(n + '->' + c for n, c in landed)})")
    if missed:
        print(f"  skipped (no matching ICF code): {[n for n, _ in missed]}")


def document_maps_to_icf(session):
    """Add a RelType documentation node for the MAPS_TO_ICF relationship we
    introduced, so the meta-layer stays complete."""
    session.run(
        """
        MERGE (r:RelType {name: 'MAPS_TO_ICF'})
        SET r.description = 'Muscle/body part maps to an ICF concept',
            r.from_type = 'BodyPart', r.to_type = 'ICFConcept'
        WITH r MATCH (from:NodeType {name: r.from_type})
        MERGE (r)-[:FROM_NODE_TYPE]->(from)
        WITH DISTINCT r MATCH (to:NodeType {name: r.to_type})
        MERGE (r)-[:TO_NODE_TYPE]->(to)
        """
    ).consume()
    print("Schema docs: MAPS_TO_ICF RelType documented")


def bridge_ontologies(session):
    """Create cross-ontology bridge relationships between different ontology layers.
    Links EXMO, PMR, COPPER, KHMO, OPE, PHY, ONTOLOCO concepts to ICF where
    semantic overlap exists."""
    
    # Bridge EXMO -> ICF (exercise medicine concepts often map to body functions/activities)
    exmo_icf_bridges = [
        ("exercise", "d450", "Walking - exercise prescription"),
        ("physical_activity", "d450", "Physical activity as walking"),
        ("strength_training", "b730", "Strength training relates to muscle power"),
        ("flexibility", "b710", "Flexibility relates to joint mobility"),
        ("balance", "b235", "Balance training relates to vestibular functions"),
        ("endurance", "b455", "Endurance relates to exercise tolerance"),
    ]
    
    landed = []
    for exmo_frag, icf_code, description in exmo_icf_bridges:
        exmo_exists = session.run(
            "MATCH (e:EXMOConcept) WHERE e.code CONTAINS $frag RETURN 1 LIMIT 1",
            frag=exmo_frag
        ).peek()
        icf_exists = session.run(
            "MATCH (i:ICFConcept {code: $code}) RETURN 1 LIMIT 1",
            code=icf_code
        ).peek()
        if exmo_exists and icf_exists:
            session.run(
                """
                MATCH (e:EXMOConcept) WHERE e.code CONTAINS $frag
                MATCH (i:ICFConcept {code: $code})
                MERGE (e)-[r:MAPS_TO_ICF]->(i)
                SET r.source = 'curated', r.description = $desc
                """,
                frag=exmo_frag, code=icf_code, desc=description
            ).consume()
            landed.append(f"EXMO:{exmo_frag}->ICF:{icf_code}")
    
    print(f"EXMO->ICF bridges: {len(landed)} edges")
    
    # Bridge PMR -> ICF (PMR integrates ICD-11, ICF, SNOMED CT)
    pmr_icf_bridges = [
        ("Joint_movement", "b710", "Joint movement maps to joint mobility"),
        ("Muscle_strength", "b730", "Muscle strength maps to muscle power"),
        ("Gait", "d450", "Gait maps to walking activity"),
        ("Balance", "b235", "Balance maps to vestibular functions"),
        ("Range_of_motion", "b710", "Range of motion maps to joint mobility"),
    ]
    
    landed = []
    for pmr_frag, icf_code, description in pmr_icf_bridges:
        pmr_exists = session.run(
            "MATCH (p:PMRConcept) WHERE p.code CONTAINS $frag RETURN 1 LIMIT 1",
            frag=pmr_frag
        ).peek()
        icf_exists = session.run(
            "MATCH (i:ICFConcept {code: $code}) RETURN 1 LIMIT 1",
            code=icf_code
        ).peek()
        if pmr_exists and icf_exists:
            session.run(
                """
                MATCH (p:PMRConcept) WHERE p.code CONTAINS $frag
                MATCH (i:ICFConcept {code: $code})
                MERGE (p)-[r:MAPS_TO_ICF]->(i)
                SET r.source = 'curated', r.description = $desc
                """,
                frag=pmr_frag, code=icf_code, desc=description
            ).consume()
            landed.append(f"PMR:{pmr_frag}->ICF:{icf_code}")
    
    print(f"PMR->ICF bridges: {len(landed)} edges")
    
    # Bridge KHMO -> ICF (kinetic human movement to body functions/activities)
    khmo_icf_bridges = [
        ("walking", "d450", "Walking movement"),
        ("running", "d450", "Running movement"),
        ("squatting", "d430", "Squatting movement"),
        ("lifting", "d430", "Lifting movement"),
        ("reaching", "d440", "Reaching movement"),
    ]
    
    landed = []
    for khmo_frag, icf_code, description in khmo_icf_bridges:
        khmo_exists = session.run(
            "MATCH (k:KHMOConcept) WHERE k.code CONTAINS $frag RETURN 1 LIMIT 1",
            frag=khmo_frag
        ).peek()
        icf_exists = session.run(
            "MATCH (i:ICFConcept {code: $code}) RETURN 1 LIMIT 1",
            code=icf_code
        ).peek()
        if khmo_exists and icf_exists:
            session.run(
                """
                MATCH (k:KHMOConcept) WHERE k.code CONTAINS $frag
                MATCH (i:ICFConcept {code: $code})
                MERGE (k)-[r:MAPS_TO_ICF]->(i)
                SET r.source = 'curated', r.description = $desc
                """,
                frag=khmo_frag, code=icf_code, desc=description
            ).consume()
            landed.append(f"KHMO:{khmo_frag}->ICF:{icf_code}")
    
    print(f"KHMO->ICF bridges: {len(landed)} edges")
    
    # Bridge COPPER -> ICF (physical activity recommendations to activities)
    copper_icf_bridges = [
        ("walking", "d450", "Walking activity recommendation"),
        ("cycling", "d450", "Cycling activity recommendation"),
        ("swimming", "d450", "Swimming activity recommendation"),
    ]
    
    landed = []
    for copper_frag, icf_code, description in copper_icf_bridges:
        copper_exists = session.run(
            "MATCH (c:COPPERConcept) WHERE c.code CONTAINS $frag RETURN 1 LIMIT 1",
            frag=copper_frag
        ).peek()
        icf_exists = session.run(
            "MATCH (i:ICFConcept {code: $code}) RETURN 1 LIMIT 1",
            code=icf_code
        ).peek()
        if copper_exists and icf_exists:
            session.run(
                """
                MATCH (c:COPPERConcept) WHERE c.code CONTAINS $frag
                MATCH (i:ICFConcept {code: $code})
                MERGE (c)-[r:MAPS_TO_ICF]->(i)
                SET r.source = 'curated', r.description = $desc
                """,
                frag=copper_frag, code=icf_code, desc=description
            ).consume()
            landed.append(f"COPPER:{copper_frag}->ICF:{icf_code}")
    
    print(f"COPPER->ICF bridges: {len(landed)} edges")
    
    # Document new RelTypes in schema
    for rel_name, from_type, to_type in [
        ("MAPS_TO_EXMO", "Exercise", "EXMOConcept"),
        ("MAPS_TO_KHMO", "Exercise", "KHMOConcept"),
        ("MAPS_TO_COPPER", "Exercise", "COPPERConcept"),
    ]:
        session.run(
            """
            MERGE (r:RelType {name: $name})
            SET r.description = 'Maps to ' + $to_type + ' concept',
                r.from_type = $from_type, r.to_type = $to_type
            """,
            name=rel_name, from_type=from_type, to_type=to_type
        ).consume()
    
    print("Schema docs: New RelTypes documented")


def dedup_check(session):
    print("\n=== Deduplication check ===")
    issues = 0
    for label, key in (("OntologyClass", "uri"), ("OntologyProperty", "uri"),
                       ("OntologyIndividual", "uri"), ("ICFConcept", "code"),
                       ("EXMOConcept", "code"), ("PMRConcept", "code"),
                       ("MELLODConcept", "code"), ("COPPERConcept", "code"),
                       ("KHMOConcept", "code"), ("OPEConcept", "code"),
                       ("PHYConcept", "code"), ("ONTOLOCOConcept", "code"),
                       ("Exercise", "exercise_id")):
        dups = session.run(
            f"""
            MATCH (n:{label}) WHERE n.{key} IS NOT NULL
            WITH n.{key} AS k, count(*) AS c WHERE c > 1
            RETURN collect(k)[..5] AS examples, count(k) AS dup_keys
            """
        ).single()
        status = f"{dups['dup_keys']} duplicate keys" if dups["dup_keys"] else "clean"
        print(f"  :{label} by {key}: {status}"
              + (f" e.g. {dups['examples']}" if dups["dup_keys"] else ""))
        issues += dups["dup_keys"]

    name_dups = session.run(
        """
        MATCH (n) WHERE n.name IS NOT NULL AND (n:OntologyClass OR n:ICFConcept
              OR n:Exercise OR n:Muscle OR n:Equipment)
        WITH labels(n)[0] AS lbl, toLower(trim(n.name)) AS nm, count(*) AS c
        WHERE c > 1 RETURN count(*) AS dup_groups, collect(lbl + ':' + nm)[..8] AS ex
        """
    ).single()
    print(f"  shared-name groups across ontology/exercise layer: "
          f"{name_dups['dup_groups']}" + (f" e.g. {name_dups['ex']}" if name_dups["dup_groups"] else ""))
    if issues or name_dups["dup_groups"]:
        print("  -> merging duplicates with apoc.refactor.mergeNodes ...")
        for label, key in (("OntologyClass", "uri"), ("OntologyProperty", "uri"),
                           ("OntologyIndividual", "uri"), ("ICFConcept", "code")):
            session.run(
                f"""
                MATCH (n:{label}) WHERE n.{key} IS NOT NULL
                WITH n.{key} AS k, collect(n) AS ns WHERE size(ns) > 1
                CALL apoc.refactor.mergeNodes(ns, {{properties:'discard'}}) YIELD node
                RETURN count(node) AS merged
                """
            ).consume()
        print("  done.")
    return issues


# ------------------------------------------------------------- components ---
def component_report(session):
    nodes = {r["id"]: r["labels"] for r in
             session.run("MATCH (n) RETURN elementId(n) AS id, labels(n) AS labels")}
    edges = [(r["a"], r["b"]) for r in
             session.run("MATCH (a)--(b) RETURN elementId(a) AS a, elementId(b) AS b")]
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    comps = {}
    for n in nodes:
        comps.setdefault(find(n), []).append(n)
    ordered = sorted(comps.values(), key=len, reverse=True)
    print(f"\n=== Connected components: {len(ordered)} ===")
    for i, comp in enumerate(ordered[:6]):
        kinds = {}
        for n in comp:
            lbl = next(l for l in nodes[n] if l != "_placeholder_")
            kinds[lbl] = kinds.get(lbl, 0) + 1
        desc = ", ".join(f"{k}:{v}" for k, v in sorted(kinds.items(), key=lambda kv: -kv[1])[:4])
        print(f"  #{i+1}: {len(comp)} nodes ({desc})")
    singletons = sum(1 for c in ordered if len(c) == 1)
    print(f"  singletons: {singletons}")
    return len(ordered)




def parse_owl_xml(owl_path):
    """Parse OWL/XML file using xml.etree.ElementTree (fallback for malformed OWL).

    Returns (classes_dict, subclass_pairs) where:
    - classes_dict: {iri: {"iri": iri, "code": code, "name": name}}
    - subclass_pairs: [(child_iri, parent_iri), ...]
    Relative IRIs (e.g. "#Term") are resolved against the root xml:base so
    fallback URIs stay globally unique (MSO declares IRI="#Term" with
    xml:base="http://scai.fraunhofer.de/MSOntology").
    """
    tree = ET.parse(owl_path)
    root = tree.getroot()

    OWL_NS = 'http://www.w3.org/2002/07/owl#'

    def _resolve(iri):
        if not iri:
            return iri
        if iri.startswith('#'):
            base = root.get('{http://www.w3.org/XML/1998/namespace}base', '')
            return (base + iri) if base else iri
        return iri

    # Extract classes from Declaration elements
    classes = {}
    for decl in root.findall(f'{{{OWL_NS}}}Declaration'):
        cls = decl.find(f'{{{OWL_NS}}}Class')
        if cls is not None:
            iri = _resolve(cls.get('IRI') or cls.get('abbreviatedIRI'))
            if iri:
                # Create code from IRI
                if '#' in iri:
                    code = iri.split('#')[-1]
                else:
                    code = iri.split('/')[-1]
                name = code.replace('_', ' ')
                classes[iri] = {
                    "iri": iri,
                    "code": code,
                    "name": name,
                }

    # Extract SubClassOf relationships
    subclasses = []
    for sc in root.findall(f'{{{OWL_NS}}}SubClassOf'):
        class_elems = sc.findall(f'{{{OWL_NS}}}Class')
        if len(class_elems) == 2:
            child_iri = _resolve(class_elems[0].get('IRI') or class_elems[0].get('abbreviatedIRI'))
            parent_iri = _resolve(class_elems[1].get('IRI') or class_elems[1].get('abbreviatedIRI'))
            if child_iri and parent_iri:
                subclasses.append((child_iri, parent_iri))

    return classes, subclasses



# All are simple class-hierarchy ontologies, so they share one generic
# extractor/loader; thin wrappers keep per-ontology entry points.

def parse_obo_text(owl_path):
    """Minimal OBO 1.2 stanza parser (id / name / def / is_a only).

    BioPortal serves some ontologies (e.g. TRAK) as OBO text rather than
    RDF/XML. Returns (concepts, subclass_of) keyed by OBO id ("TRAK:0000001").
    """
    concepts, subclass_of = {}, []
    cur, is_as = None, []

    def flush():
        nonlocal cur, is_as
        if cur and cur.get("id") and cur.get("name"):
            concepts[cur["id"]] = {
                "uri": cur["id"], "code": cur["id"],
                "name": cur["name"], "description": cur.get("def"),
            }
            subclass_of.extend((cur["id"], p) for p in is_as)
        cur, is_as = None, []

    with open(owl_path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("!"):
                continue
            if line.startswith("["):
                flush()
                cur, is_as = ({}, []) if line == "[Term]" else (None, [])
                continue
            if cur is None or ":" not in line:
                continue
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip()
            if key == "id":
                cur["id"] = val
            elif key == "name":
                cur["name"] = val
            elif key == "def":
                cur["def"] = val.split('" [')[0].strip().strip('"')
            elif key == "is_a":
                is_as.append(val.split("!")[0].strip())
    flush()
    # keep edges whose child was loaded; parents without names are dropped
    # at load time by the both-endpoints-in-concepts filter
    subclass_of = [(c, p) for c, p in subclass_of if c in concepts]
    return concepts, subclass_of


def _name_from_uri(uri_str):
    """Derive a human-readable name from a URI fragment (e.g. PACO has no
    rdfs:label; names live in fragments like '#Scrubbing_floor')."""
    frag = uri_str.split("#")[-1] if "#" in uri_str else uri_str.rstrip("/").split("/")[-1]
    frag = re.sub(r"[_\-]+", " ", frag).strip()
    if not frag or not re.search(r"[A-Za-z]", frag):
        return None
    return frag


def extract_simple_ontology(owl_path, name, try_obo=False):
    """Generic extractor for class-hierarchy OWL ontologies.

    Tries rdflib XML, then turtle; for OBO-text sources (try_obo=True) falls
    back to parse_obo_text, then to xml.etree. Classes without rdfs:label get
    a name derived from their URI fragment instead of being skipped.
    """
    g = rdflib.Graph()
    try:
        g.parse(owl_path, format="xml")
    except Exception as e:
        print(f"{name} parse error (xml), trying turtle: {e}")
        try:
            g.parse(owl_path, format="turtle")
        except Exception as e2:
            if try_obo:
                try:
                    concepts, subclass_of = parse_obo_text(owl_path)
                    print(f"{name} extract (obo text): {len(concepts)} concepts, "
                          f"{len(subclass_of)} hierarchy edges")
                    return concepts, subclass_of
                except Exception as e3:
                    print(f"{name} obo parse failed: {e3}")
            print(f"{name} rdflib failed, trying xml.etree fallback: {e2}")
            try:
                classes, subclass_pairs = parse_owl_xml(owl_path)
                concepts = {iri: {"uri": iri, "code": info["code"],
                                  "name": info["name"], "description": None}
                            for iri, info in classes.items()}
                subclass_of = [(a, b) for a, b in subclass_pairs
                               if a in concepts and b in concepts]
                print(f"{name} extract (xml.etree): {len(concepts)} concepts, "
                      f"{len(subclass_of)} hierarchy edges")
                return concepts, subclass_of
            except Exception as e4:
                print(f"{name} all parsers failed: {e4}")
                return {}, []

    concepts, skipped = {}, 0
    for s in set(g.subjects(RDF.type, OWL.Class)):
        if not isinstance(s, URIRef):
            continue
        uri_str = str(s)
        label = english_label(g, s) or _name_from_uri(uri_str)
        if not label:
            skipped += 1
            continue
        code = uri_str.split("#")[-1] if "#" in uri_str else uri_str.split("/")[-1]
        concepts[uri_str] = {
            "uri": uri_str,
            "code": code,
            "name": label,
            "description": first(g, s, RDFS.comment),
        }

    subclass_of = []
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef) \
                and str(s) in concepts and str(o) in concepts:
            subclass_of.append((str(s), str(o)))
    print(f"{name} extract: {len(concepts)} concepts ({skipped} unlabeled skipped), "
          f"{len(subclass_of)} hierarchy edges")
    return concepts, subclass_of


def extract_pain():
    """PAIN - The Pain Ontology (IASP-based)."""
    return extract_simple_ontology(PAIN_OWL, "PAIN")


def extract_cbha():
    """CBHA - CalendarBench Human Activities (Compendium of Physical Activities).

    Turtle ontology: 37 rdfs:subClassOf category classes under
    HumanActivity, plus 1,210 activity individuals (URI .../activity/<slug>)
    each typed with their category class and carrying Compendium
    ha:activityCode + ha:metValue annotations. Activities are NOT declared
    owl:NamedIndividual — they are detected via the activityCode subjects.
    """
    g = rdflib.Graph()
    try:
        g.parse(CBHA_OWL, format="turtle")
    except Exception as e:
        print(f"CBHA parse error (turtle), trying xml: {e}")
        g.parse(CBHA_OWL, format="xml")

    code_prop = URIRef(CBHA_NS + "activityCode")
    met_prop = URIRef(CBHA_NS + "metValue")

    classes = {}
    for s in set(g.subjects(RDF.type, OWL.Class)):
        if not isinstance(s, URIRef):
            continue
        uri_str = str(s)
        label = english_label(g, s) or _name_from_uri(uri_str)
        if not label:
            continue
        code = uri_str.split("#")[-1] if "#" in uri_str else uri_str.split("/")[-1]
        classes[uri_str] = {
            "uri": uri_str,
            "code": code,
            "name": label,
            "description": first(g, s, RDFS.comment),
        }

    activities = {}
    for s in set(g.subjects(code_prop, None)):
        if not isinstance(s, URIRef):
            continue
        uri_str = str(s)
        types = [str(t) for t in g.objects(s, RDF.type)
                 if isinstance(t, URIRef) and str(t) in classes]
        try:
            met = float(first(g, s, met_prop) or "")
        except (TypeError, ValueError):
            met = None
        activities[uri_str] = {
            "uri": uri_str,
            "name": english_label(g, s) or _name_from_uri(uri_str) or uri_str,
            "activity_code": first(g, s, code_prop) or "",
            "met": met,
            "types": types,
        }

    subclass_of = []
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        if isinstance(s, URIRef) and isinstance(o, URIRef) \
                and str(s) in classes and str(o) in classes:
            subclass_of.append((str(s), str(o)))

    typed = sum(1 for a in activities.values() if a["types"])
    print(f"CBHA extract: {len(classes)} category classes, "
          f"{len(activities)} activities ({typed} typed), "
          f"{len(subclass_of)} hierarchy edges")
    return dict(classes=classes, activities=activities, subclass_of=subclass_of)


def load_simple_ontology(session, concepts, subclass_of, label, source):
    """Load concepts + SUBCLASS_OF hierarchy under any concept label."""
    rows = list(concepts.values())
    for i in range(0, len(rows), BATCH):
        session.run(
            f"""
            UNWIND $rows AS row
            MERGE (n:{label} {{code: row.code}})
            SET n.uri = row.uri, n.name = row.name,
                n.description = row.description, n.source = $source
            """,
            rows=rows[i:i + BATCH], source=source,
        ).consume()
    for i in range(0, len(subclass_of), BATCH):
        session.run(
            f"""
            UNWIND $rows AS row
            MATCH (a:{label} {{code: row.a_code}}), (b:{label} {{code: row.b_code}})
            MERGE (a)-[:SUBCLASS_OF]->(b)
            """,
            rows=[{"a_code": a.split("#")[-1] if "#" in a else a.split("/")[-1],
                   "b_code": b.split("#")[-1] if "#" in b else b.split("/")[-1]}
                  for a, b in subclass_of[i:i + BATCH]],
        ).consume()


def load_pain(session, concepts, subclass_of):
    load_simple_ontology(session, concepts, subclass_of, "PAINConcept", "pain.owl")


def load_cbha(session, ext):
    """Load CBHA categories (CBHAConcept) + Compendium activities (CBHAActivity)."""
    rows = list(ext["classes"].values())
    for i in range(0, len(rows), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MERGE (n:CBHAConcept {code: row.code})
            SET n.uri = row.uri, n.name = row.name,
                n.description = row.description, n.source = 'cbha.owl'
            """,
            rows=rows[i:i + BATCH],
        ).consume()

    act_rows = [{k: v for k, v in a.items() if k != "types"}
                for a in ext["activities"].values()]
    for i in range(0, len(act_rows), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MERGE (n:CBHAActivity {uri: row.uri})
            SET n.name = row.name, n.activity_code = row.activity_code,
                n.met = row.met, n.source = 'cbha.owl'
            """,
            rows=act_rows[i:i + BATCH],
        ).consume()

    for i in range(0, len(ext["subclass_of"]), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MATCH (a:CBHAConcept {uri: row.a}), (b:CBHAConcept {uri: row.b})
            MERGE (a)-[:SUBCLASS_OF]->(b)
            """,
            rows=[{"a": a, "b": b} for a, b in ext["subclass_of"][i:i + BATCH]],
        ).consume()

    inst = [(uri, t) for uri, a in ext["activities"].items() for t in a["types"]]
    for i in range(0, len(inst), BATCH):
        session.run(
            """
            UNWIND $rows AS row
            MATCH (n:CBHAActivity {uri: row.a}), (c:CBHAConcept {uri: row.b})
            MERGE (n)-[:INSTANCE_OF]->(c)
            """,
            rows=[{"a": a, "b": b} for a, b in inst[i:i + BATCH]],
        ).consume()

    print(f"  CBHA load: {len(rows)} categories, {len(act_rows)} activities, "
          f"{len(ext['subclass_of'])} SUBCLASS_OF, {len(inst)} INSTANCE_OF")



def bridge_activity_ontologies_to_icf(session):
    """Curated MAPS_TO_ICF links from CBHA categories and MSO clinical scales.

    Rebuilds only curated-sourced edges each run (muscle MAPS_TO_ICF edges
    from add_additional_data are untouched). Compendium activities inherit
    ICF context transitively via INSTANCE_OF into the CBHA category tree.
    Only creates an edge when both endpoints exist."""
    session.run(
        "MATCH ()-[m:MAPS_TO_ICF {source: 'curated'}]->() DELETE m"
    ).consume()
    landed, missed = [], []
    for label, rows in (("CBHAConcept", CBHA_TO_ICF),):
        for code, target, note in rows:
            ok = session.run(
                f"""
                MATCH (c:{label} {{code: $code}}), (i:ICFConcept {{code: $target}})
                MERGE (c)-[m:MAPS_TO_ICF]->(i)
                SET m.source = 'curated', m.note = $note
                RETURN 1
                """,
                code=code, target=target, note=note,
            ).peek()
            if ok:
                landed.append(f"{label}:{code}->{target}")
            else:
                missed.append(f"{label}:{code}->{target}")
    print(f"CBHA/MSO->ICF curated: {len(landed)} edges ({', '.join(landed)})")
    if missed:
        print(f"  skipped (missing endpoint): {missed}")


def main():
    """Load only the focused default ontology source set.

    Experimental/restricted-source extractors remain available as functions,
    but are deliberately not called by the default pipeline.
    """
    driver = get_driver()
    try:
        with driver.session(**get_session_config()) as session:
            session.run("RETURN 1").consume()
            print("Connected.\n")

            print("=== ELT: REHABO ===")
            load_rehabo(session, extract_rehabo())

            print("\n=== ELT: ICF ===")
            concepts, subclass_of = extract_icf()
            load_icf(session, concepts, subclass_of)

            print("\n=== ELT: EXMO (Exercise Medicine Ontology) ===")
            exmo_concepts, exmo_subclass = extract_exmo()
            load_exmo(session, exmo_concepts, exmo_subclass)

            print("\n=== ELT: PAIN (The Pain Ontology) ===")
            pain_concepts, pain_subclass = extract_pain()
            load_pain(session, pain_concepts, pain_subclass)

            print("\n=== Bridges ===")
            connect_schema_islands(session)
            bridge_muscles_to_icf(session)
            bridge_rehabo_to_icf(session)
            document_maps_to_icf(session)
            # Default source set deliberately excludes COPPER/KHMO/CBHA and
            # other unreviewed families; avoid legacy broad bridge routines.
            from bridges import bridge_default_sources
            bridge_default_sources(session)

            dedup_check(session)
            component_report(session)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
