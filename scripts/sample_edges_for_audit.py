#!/usr/bin/env python3
"""Sample edges from the graph, stratified by relationship type, for review.

Writes a CSV in the same shape as the review-loop decisions template plus
graph-side columns (endpoints, provenance props). Feed the sample to a
reviewer; their decisions come back through curated/apply_decisions.py
(for curated rows) or a future model-edge review path.

Usage:
    python scripts/sample_edges_for_audit.py                     # 10 per type
    python scripts/sample_edges_for_audit.py --per-type 25 \
        --out audit_sample.csv
"""

import argparse
import csv
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))  # allow `python scripts/sample_edges_for_audit.py` from anywhere

# Types worth reviewing: curated clinical edges first, then bridge edges.
DEFAULT_TYPES = [
    "RECOMMENDS_EXERCISE",
    "PRECAUTION",
    "CONTRAINDICATION",
    "MAPS_TO_ICF",
    "MAPS_TO_MONDO",
    "STUDIES_CONDITION",
    "HAS_ICD10",
]

FIELDNAMES = [
    "rel_type", "start_label", "start_name", "end_label", "end_name",
    "method", "match_type", "confidence", "source", "review_status",
    "rationale", "random_seed_row",
]


def sample(driver_factory, rel_types, per_type, seed=42):
    rng = random.Random(seed)
    rows = []
    driver = driver_factory()
    try:
        for rel_type in rel_types:
            with driver.session() as s:
                candidates = s.run(f"""
                    MATCH (a)-[r:`{rel_type}`]->(b)
                    RETURN labels(a)[0] AS start_label, a.name AS start_name,
                           labels(b)[0] AS end_label, b.name AS end_name,
                           r.method AS method, r.match_type AS match_type,
                           r.confidence AS confidence, r.source AS source,
                           r.review_status AS review_status,
                           r.rationale AS rationale
                """).data()
            if not candidates:
                print(f"  {rel_type}: no edges", file=sys.stderr)
                continue
            chosen = rng.sample(candidates, min(per_type, len(candidates)))
            for row in chosen:
                row["rel_type"] = rel_type
                row["random_seed_row"] = seed
            rows.extend(chosen)
            print(f"  {rel_type}: sampled {len(chosen)} of {len(candidates)}")
    finally:
        driver.close()
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--per-type", type=int, default=10)
    parser.add_argument("--types", nargs="*", default=DEFAULT_TYPES)
    parser.add_argument("--out", default="audit_sample.csv")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv(REPO / ".env")
    from db import get_driver

    rows = sample(get_driver, args.types, args.per_type, seed=args.seed)
    out = Path(args.out)
    with open(out, "w", newline="\n", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"\n{len(rows)} edges written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
