#!/usr/bin/env python3
"""Coverage audit for RehabKG: conditions, scales, exercises, cohort limits.

Prints a markdown-style report against the live graph:
  - Condition coverage: ICD-10 links, recommendation edges, safety edges
  - Outcome scale coverage: which instruments appear, admission/discharge pairs
  - Outcome value backfill: value vs value_numeric coverage
  - Exercise coverage: recommendation fan-in, evidence columns present
  - MOTU cohort limits: birth-year range, sex distribution, patient counts
  - Known gaps: condition rows without ICD mapping, curated override rows
    awaiting review, synthetic-data caveats

Usage:
    python scripts/audit_coverage.py            # full report
    python scripts/audit_coverage.py --json out.json
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))  # allow `python scripts/audit_coverage.py` from anywhere


def q1(session, cypher, **params):
    rec = session.run(cypher, **params).single()
    return dict(rec) if rec else {}


def audit(driver_factory=None):
    if driver_factory is None:
        from dotenv import load_dotenv
        load_dotenv(REPO / ".env")
        from db import get_driver as driver_factory  # noqa: N813

    report = {}
    driver = driver_factory()
    try:
        with driver.session() as s:
            report["conditions"] = q1(s, """
                MATCH (c:Condition)
                RETURN count(c) AS total,
                       count(c.icd10_code) AS with_icd10
            """)
            report["conditions"]["with_recommendations"] = q1(s, """
                MATCH (c:Condition)-[:RECOMMENDS_EXERCISE]->(:Exercise)
                RETURN count(DISTINCT c) AS n
            """)["n"]
            report["conditions"]["with_precaution"] = q1(s, """
                MATCH (c:Condition)-[:PRECAUTION]->(:Exercise)
                RETURN count(DISTINCT c) AS n
            """)["n"]
            report["conditions"]["with_contraindication"] = q1(s, """
                MATCH (c:Condition)-[:CONTRAINDICATION]->(:Exercise)
                RETURN count(DISTINCT c) AS n
            """)["n"]

            report["outcomes"] = q1(s, """
                MATCH (o:Outcome)
                RETURN count(o) AS total,
                       count(o.value_numeric) AS with_value_numeric
            """)
            scales = s.run("""
                MATCH (o:Outcome)-[:MEASURED_BY]->(a:AssessmentScale)
                RETURN a.name AS scale, count(o) AS n
                ORDER BY n DESC LIMIT 15
            """).data()
            report["outcomes"]["top_scales"] = scales
            report["outcomes"]["admission"] = q1(s, """
                MATCH (o:Outcome) WHERE o.outcome_id CONTAINS '-ADM'
                RETURN count(o) AS n
            """)["n"]
            report["outcomes"]["discharge"] = q1(s, """
                MATCH (o:Outcome) WHERE o.outcome_id CONTAINS '-DC'
                RETURN count(o) AS n
            """)["n"]

            report["exercises"] = q1(s, """
                MATCH (e:Exercise) RETURN count(e) AS total
            """)
            report["exercises"]["recommended_at_least_once"] = q1(s, """
                MATCH (:Condition)-[:RECOMMENDS_EXERCISE]->(e:Exercise)
                RETURN count(DISTINCT e) AS n
            """)["n"]

            report["cohort"] = q1(s, """
                MATCH (p:Patient) WHERE p.source = 'MOTU'
                RETURN count(p) AS patients,
                       min(toInteger(p.birth_year)) AS min_birth_year,
                       max(toInteger(p.birth_year)) AS max_birth_year
            """)
            report["cohort"]["by_sex"] = s.run("""
                MATCH (p:Patient) WHERE p.source = 'MOTU'
                RETURN p.sex AS sex, count(p) AS n ORDER BY n DESC
            """).data()

            report["provenance"] = q1(s, """
                MATCH ()-[r:RECOMMENDS_EXERCISE]->()
                RETURN count(r) AS recommends,
                       count(r.source) AS recommends_with_source,
                       count(r.review_status) AS recommends_with_review_status
            """)
            report["provenance"]["safety"] = q1(s, """
                MATCH ()-[r:PRECAUTION|CONTRAINDICATION]->()
                RETURN count(r) AS safety_edges,
                       count(r.source) AS safety_with_source,
                       count(r.review_status) AS safety_with_review_status
            """)

            report["observations"] = q1(s, """
                MATCH (o:Observation) RETURN count(o) AS total
            """)
    finally:
        driver.close()
    return report


def print_report(r):
    c = r["conditions"]
    print("## Condition coverage")
    total = c["total"]
    print(f"  Conditions: {total:,}")
    print(f"  with ICD-10 link:     {c['with_icd10']:,}"
          f" ({c['with_icd10']/total:.1%})" if total else "  (none)")
    print(f"  with recommendations: {c['with_recommendations']:,}")
    print(f"  with precaution:      {c['with_precaution']:,}")
    print(f"  with contraindication:{c['with_contraindication']:,}")

    o = r["outcomes"]
    print("\n## Outcome scale coverage")
    print(f"  Outcomes: {o['total']:,}"
          f" (value_numeric backfill: {o['with_value_numeric']:,})")
    print(f"  admission: {o['admission']:,} / discharge: {o['discharge']:,}")
    for row in o["top_scales"][:8]:
        print(f"    {row['scale']}: {row['n']:,}")

    e = r["exercises"]
    print("\n## Exercise coverage")
    print(f"  Exercises: {e['total']:,}")
    print(f"  recommended at least once: {e['recommended_at_least_once']:,}")

    cohort = r["cohort"]
    print("\n## MOTU cohort limits (synthetic demo data)")
    print(f"  Patients: {cohort['patients']:,}")
    if cohort.get("min_birth_year") is not None:
        print(f"  Birth years: {cohort['min_birth_year']}–{cohort['max_birth_year']}")
    for row in cohort["by_sex"]:
        print(f"    sex={row['sex']}: {row['n']:,}")

    p = r["provenance"]
    print("\n## Provenance coverage")
    print(f"  RECOMMENDS with source/review_status:"
          f" {p['recommends_with_source']:,}/{p['recommends_with_review_status']:,}"
          f" of {p['recommends']:,}")
    ps = p["safety"]
    print(f"  Safety with source/review_status:"
          f" {ps['safety_with_source']:,}/{ps['safety_with_review_status']:,}"
          f" of {ps['safety_edges']:,}")

    print(f"\n## Observations\n  Observation nodes: {r['observations']['total']:,}")

    print("\n## Known gaps")
    print("  - Condition.icd10_code is populated only by exact-name Mondo")
    print("    propagation and curated/condition_icd10_overrides.csv (Gate 0")
    print("    policy); both are unreviewed candidates — see")
    print("    docs/notes/phase0_findings.md and curated/README.md.")
    print("  - MOTU data is synthetic/labeled demo data — not for clinical use.")
    print("  - Unreviewed curated edges are research candidates, not advice.")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", metavar="PATH",
                        help="Also write the audit as JSON")
    args = parser.parse_args()

    report = audit()
    print_report(report)
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nJSON written to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
