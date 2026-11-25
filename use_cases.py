#!/usr/bin/env python3
"""
RehabKG Use Cases - Runnable Python implementations.

Research prototype: curated edges are candidate associations. Most are
review_status='unreviewed' and are not clinical advice. Every use case here
returns provenance (review_status, confidence, method, source) so consumers
can see how much to trust each row.

Run: python use_cases.py
"""

from dotenv import load_dotenv

from db import get_driver

load_dotenv()


def print_results(results, title=""):
    """Pretty print query results."""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print('='*60)
    
    if not results:
        print("  No results found.")
        return
    
    # Print header
    keys = results[0].keys()
    widths = [max(len(str(r[k])) for r in results + [{k: k}]) for k in keys]
    
    header = " | ".join(f"{k:<{w}}" for k, w in zip(keys, widths))
    print(f"  {header}")
    print(f"  {'-'*len(header)}")
    
    # Print rows
    for r in results:
        row = " | ".join(f"{str(r[k]):<{w}}" for k, w in zip(keys, widths))
        print(f"  {row}")


# Stroke keyword predicate shared by the stroke-themed use cases. Excludes
# "heat stroke" the same way the curated keyword_group rows do.
STROKE_PRED = (
    "(toLower(c.name) CONTAINS 'stroke' OR toLower(c.name) CONTAINS 'hemipleg' "
    "OR toLower(c.name) CONTAINS 'hemipares') AND NOT toLower(c.name) CONTAINS 'heat stroke'"
)


def use_case_1_safety_aware_lookup(session, condition="Stroke"):
    """UC1: Exercises for a condition, returned together with safety edges and provenance.

    Many Condition nodes match a keyword (trial-derived names), so results are
    grouped per exercise to keep the output readable.
    """
    results = list(session.run("""
        MATCH (c:Condition)-[r:RECOMMENDS_EXERCISE|PRECAUTION|CONTRAINDICATION]->(e:Exercise)
        WHERE toLower(c.name) CONTAINS toLower($condition)
          AND NOT toLower(c.name) CONTAINS 'heat stroke'
        RETURN type(r) AS relation,
               e.name AS exercise,
               count(DISTINCT c) AS conditions,
               collect(DISTINCT r.review_status) AS review_status,
               collect(DISTINCT r.confidence) AS confidence,
               collect(DISTINCT c.name)[..2] AS example_conditions
        ORDER BY CASE relation WHEN 'CONTRAINDICATION' THEN 0
                               WHEN 'PRECAUTION' THEN 1 ELSE 2 END,
                 e.name
        LIMIT 40
    """, condition=condition))
    print_results(results, f"UC1: Safety-aware exercise lookup for '{condition}'")
    return results


def use_case_2_explain_path(session, start="Stroke", end="Walking Program (Progressive)"):
    """UC2: Explain-this-path: shortest path with provenance on every edge."""
    results = list(session.run("""
        MATCH (a {name: $start}), (b {name: $end})
        WITH a, b LIMIT 1
        MATCH p = shortestPath((a)-[*..4]-(b))
        UNWIND relationships(p) AS r
        RETURN startNode(r).name AS from_node,
               type(r) AS relation,
               endNode(r).name AS to_node,
               r.method AS method,
               r.match_type AS match_type,
               r.confidence AS confidence,
               r.review_status AS review_status
    """, start=start, end=end))
    print_results(results, f"UC2: Path {start} -> {end} (with provenance)")
    return results


def use_case_3_review_queue(session):
    """UC3: Review-queue triage: unreviewed clinical edges, lowest confidence first."""
    results = list(session.run("""
        MATCH ()-[r]->()
        WHERE type(r) IN ['RECOMMENDS_EXERCISE', 'PRECAUTION', 'CONTRAINDICATION']
        RETURN type(r) AS relation,
               coalesce(r.review_status, 'missing') AS review_status,
               coalesce(r.match_type, 'n/a') AS match_type,
               count(r) AS edges,
               round(avg(r.confidence), 2) AS avg_confidence
        ORDER BY review_status, relation, avg_confidence
    """))
    print_results(results, "UC3: Review queue by status and rule")
    return results


def use_case_4_gait_concept_resolver(session, term="gait"):
    """UC4: Resolve HPO gait terms to ICF concepts and show where links are missing.

    HPO->ICF links are the 9 curated explicit code pairs (RELATED_TO_ICF),
    not name matching, so most HPO terms have no ICF link. Unlinked terms are
    returned too: the gap is the finding.
    """
    results = list(session.run("""
        MATCH (h:HPOConcept)
        WHERE toLower(h.name) CONTAINS toLower($term)
        OPTIONAL MATCH (h)-[r:RELATED_TO_ICF]->(i:ICFConcept)
        OPTIONAL MATCH (a:AssessmentScale)-[:MEASURES]->(i)
        RETURN h.code AS hpo_code, h.name AS hpo_term,
               i.code AS icf_code, i.name AS icf_name,
               r.review_status AS review_status,
               collect(DISTINCT a.name) AS scales
        ORDER BY icf_code IS NULL, hpo_term
        LIMIT 15
    """, term=term))
    print_results(results, f"UC4: Concept resolver for '{term}' (curated code pairs only)")
    return results


def use_case_5_coverage_gaps(session):
    """UC5: Stroke-condition coverage: conditions with no recommendation or safety edge."""
    results = list(session.run(f"""
        MATCH (c:Condition)
        WHERE {STROKE_PRED}
        OPTIONAL MATCH (c)-[rec:RECOMMENDS_EXERCISE]->()
        OPTIONAL MATCH (c)-[saf:PRECAUTION|CONTRAINDICATION]->()
        WITH c, count(DISTINCT rec) AS recommendations, count(DISTINCT saf) AS safety_edges
        RETURN CASE WHEN recommendations = 0 AND safety_edges = 0 THEN 'no clinical edges'
                    WHEN safety_edges = 0 THEN 'recommendations only'
                    ELSE 'has safety edges' END AS coverage,
               count(c) AS conditions,
               collect(c.name)[..3] AS examples
        ORDER BY conditions DESC
    """))
    print_results(results, "UC5: Stroke condition coverage audit")
    return results


def use_case_6_contradiction_check(session):
    """UC6: Exercises that one condition recommends and another contraindicates."""
    results = list(session.run("""
        MATCH (c1:Condition)-[r1:RECOMMENDS_EXERCISE]->(e:Exercise)
              <-[r2:CONTRAINDICATION]-(c2:Condition)
        WHERE c1 <> c2
        RETURN e.name AS exercise,
               count(DISTINCT c1) AS recommending_conditions,
               collect(DISTINCT c1.name)[..2] AS recommended_for_examples,
               collect(DISTINCT c2.name)[..2] AS contraindicated_for,
               collect(DISTINCT r1.review_status + '/' + r2.review_status) AS rec_contra_status
        ORDER BY recommending_conditions DESC, e.name
        LIMIT 25
    """))
    print_results(results, "UC6: Recommendation vs. contraindication conflicts")
    return results


def use_case_7_assessment_selection(session, domain="balance"):
    """UC7: Find assessment scales for a domain, with ICF links and LOINC where curated."""
    results = list(session.run("""
        MATCH (a:AssessmentScale)
        WHERE a.domain = $domain
        OPTIONAL MATCH (a)-[:MEASURES]->(i:ICFConcept)
        RETURN a.name AS scale,
               a.domain AS domain,
               a.scoring_range AS range,
               a.loinc_code AS loinc,
               collect(i.code) AS icf_codes
        ORDER BY a.name
    """, domain=domain))
    print_results(results, f"UC7: Assessment scales ({domain})")
    return results


def use_case_8_trial_landscape(session, condition_name="Stroke"):
    """UC8: Trial landscape for a condition (name-based match; not eligibility matching)."""
    results = list(session.run("""
        MATCH (t:ClinicalTrial)-[:STUDIES_CONDITION]->(c:Condition)
        WHERE toLower(c.name) CONTAINS toLower($condition)
          AND t.status IN ['RECRUITING', 'NOT_YET_RECRUITING', 'ENROLLING_BY_INVITATION']
        RETURN t.nct_id AS nct_id,
               substring(t.title, 0, 60) AS title,
               t.enrollment AS enrollment,
               t.start_date AS start_date,
               c.name AS condition
        ORDER BY t.enrollment DESC
        LIMIT 10
    """, condition=condition_name))
    print_results(results, f"UC8: Recruiting-trial landscape for '{condition_name}'")
    return results


def use_case_9_condition_muscle_map(session, condition="stroke"):
    """UC9: Condition -> candidate exercise -> targeted muscle (merged old UC4 + UC8).

    Grouped per exercise; muscles are empty for exercises (e.g. walking
    programs) that carry no TARGETS_PRIMARY link.
    """
    results = list(session.run("""
        MATCH (c:Condition)-[r:RECOMMENDS_EXERCISE]->(e:Exercise)
        WHERE toLower(c.name) CONTAINS toLower($condition)
        OPTIONAL MATCH (e)-[:TARGETS_PRIMARY]->(m:Muscle)
        RETURN e.name AS exercise,
               collect(DISTINCT m.name) AS muscles,
               count(DISTINCT c) AS conditions,
               collect(DISTINCT r.review_status) AS review_status
        ORDER BY conditions DESC, e.name
        LIMIT 25
    """, condition=condition))
    print_results(results, f"UC9: Condition-exercise-muscle map for '{condition}'")
    return results


def use_case_10_measure_context(session, patient_id="SYNTHETIC-GAIT-001"):
    """UC10: Synthetic gait observations: the starting point for a measure resolver.

    Observation->ICF links are deliberately absent (the bulk import deletes
    them until restored and provenance-validated), so this returns the raw
    measures only. Adding a MeasureDefinition layer that carries unit, range,
    ICF code and LOINC is the proposed next step. Data are fully synthetic.
    """
    results = list(session.run("""
        MATCH (:Patient {patient_id: $pid})-[:HAS_OBSERVATION]->(o:Observation)
        RETURN o.feature AS feature, o.value AS value, o.unit AS unit,
               o.observed_at AS observed_at, o.source AS source
        ORDER BY o.feature, o.observed_at
    """, pid=patient_id))
    print_results(results, f"UC10: Observations for {patient_id} (synthetic, no ICF link yet)")
    return results


def appendix_amputation_cohort(session):
    """Appendix: MOTU amputation cohort. NOT a stroke cohort; descriptive only.

    Shows the Patient/Session/Outcome layer. It is a single-center
    synthetic/de-identified demo cohort and supports no prediction claims.
    """
    results = list(session.run("""
        MATCH (p:Patient)-[:HAS_STAY]->(s:Session)-[:HAS_OUTCOME]->(o:Outcome)
        WHERE o.outcome_id CONTAINS 'BARTEL'
        WITH p, s,
             max(CASE WHEN o.outcome_id CONTAINS 'ADM' THEN toFloat(coalesce(o.value_numeric, o.value)) END) AS admission,
             max(CASE WHEN o.outcome_id CONTAINS 'DC' THEN toFloat(coalesce(o.value_numeric, o.value)) END) AS discharge
        WHERE admission IS NOT NULL AND discharge IS NOT NULL
        RETURN s.amputation_cause AS cause,
               count(DISTINCT p) AS patients,
               round(avg(admission), 1) AS avg_admission_barthel,
               round(avg(discharge), 1) AS avg_discharge_barthel
        ORDER BY patients DESC
    """))
    print_results(results, "Appendix: Barthel change by amputation cause (descriptive)")
    return results


def demo_full_journey(session, patient_id="MOTU-1"):
    """Demo: Full patient journey analysis."""
    print(f"\n{'='*60}")
    print(f"  DEMO: Patient Journey for {patient_id}")
    print('='*60)
    
    # Patient info
    result = session.run("""
        MATCH (p:Patient {patient_id: $pid})
        RETURN p.sex AS sex, p.birth_year AS birth_year, p.source AS source
    """, pid=patient_id).single()
    
    if result:
        print("\n  Demographics:")
        print(f"    Sex: {result['sex']}")
        print(f"    Birth Year: {result['birth_year']}")
        print(f"    Source: {result['source']}")
    
    # Hospital stays
    stays = list(session.run("""
        MATCH (p:Patient {patient_id: $pid})-[:HAS_STAY]->(s:Session)
        OPTIONAL MATCH (s)-[:HAS_OUTCOME]->(o:Outcome)
        RETURN s.session_id AS stay_id,
               s.admission_date AS admission,
               s.discharge_date AS discharge,
               s.length_of_stay AS los,
               s.amputation_side AS side,
               s.amputation_cause AS cause,
               collect({
                   outcome_id: o.outcome_id,
                   phase: o.phase,
                   value: o.value
               }) AS outcomes
        ORDER BY s.admission_date
    """, pid=patient_id))
    
    print(f"\n  Hospital Stays: {len(stays)}")
    for stay in stays:
        print(f"\n    Stay: {stay['stay_id']}")
        print(f"    Dates: {stay['admission']} to {stay['discharge']}")
        print(f"    LOS: {stay['los']} days")
        print(f"    Amputation: {stay['side']} ({stay['cause']})")
        
        if stay['outcomes']:
            print("    Outcomes:")
            for o in stay['outcomes']:
                if o['value'] is not None:
                    # Extract assessment name from outcome_id (e.g., MOTU-STAY-1-BARTEL-ADM)
                    parts = o['outcome_id'].split('-')
                    assessment = '-'.join(parts[2:-1]) if len(parts) > 3 else o['outcome_id']
                    print(f"      - {assessment} ({o['phase']}): {o['value']}")
    
    # Adverse events (linked via patient_id pattern in event_id)
    events = list(session.run("""
        MATCH (e:AdverseEvent)
        WHERE e.event_id STARTS WITH $pid
        RETURN e.type AS type, e.date AS date, e.event_id AS event_id
    """, pid=patient_id))
    
    if events:
        print(f"\n  Adverse Events: {len(events)}")
        for e in events:
            print(f"    - {e['type']} on {e['date']} ({e['event_id']})")


def main():
    print("RehabKG Use Cases - Interactive Demo")
    print("=" * 60)

    driver = get_driver()

    try:
        with driver.session() as session:
            result = session.run("RETURN 1 as test").single()
            print(f"\nConnected to Neo4j: {result['test'] == 1}")

            use_case_1_safety_aware_lookup(session)
            use_case_2_explain_path(session)
            use_case_3_review_queue(session)
            use_case_4_gait_concept_resolver(session)
            use_case_5_coverage_gaps(session)
            use_case_6_contradiction_check(session)
            use_case_7_assessment_selection(session)
            use_case_8_trial_landscape(session)
            use_case_9_condition_muscle_map(session)
            use_case_10_measure_context(session)
            appendix_amputation_cohort(session)

            demo_full_journey(session)

    finally:
        driver.close()

    print("\n" + "=" * 60)
    print("  Use cases complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
