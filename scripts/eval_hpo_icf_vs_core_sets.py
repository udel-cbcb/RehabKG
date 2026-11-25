#!/usr/bin/env python3
"""Report HPO→ICF reachability against the curated ICF Core Sets register.

This is a read-only evaluation: it does not change HPO→ICF edges or load
categories into Neo4j. An empty register is valid until category lists and
redistribution terms are supplied by a human reviewer.
"""
import argparse
import csv
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import get_driver

REGISTER = ROOT / "curated" / "icf_core_sets.csv"
DEFAULT_OUTPUT = ROOT / "eval" / "hpo_icf_core_sets_report.md"
REQUIRED_COLUMNS = {
    "core_set", "condition_key", "icf_code", "component", "source_url",
    "review_status", "reviewed_by", "reviewed_on",
}


def load_register(path=REGISTER):
    """Load non-empty curated category rows, validating the template schema."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError("{} missing columns: {}".format(path, sorted(missing)))
        rows = []
        for row in reader:
            if not any((value or "").strip() for value in row.values()):
                continue
            if not all((row.get(key) or "").strip() for key in
                       ("core_set", "condition_key", "icf_code", "component",
                        "source_url", "review_status")):
                raise ValueError("incomplete ICF Core Set row: {}".format(row))
            rows.append(row)
    return rows


def collect_graph_metrics(session, rows):
    """Read-only graph metrics keyed by ICF code."""
    core_codes = sorted({row["icf_code"].strip() for row in rows})
    query = session.run("""
        MATCH (h:HPOConcept)-[r:MAPS_TO_ICF]->(i:ICFConcept)
        RETURN i.code AS icf_code, count(DISTINCT h) AS hpo_count,
               count(r) AS edge_count
    """).data()
    per_code = {row["icf_code"]: row for row in query}
    reachable = {code for code in core_codes if per_code.get(code, {}).get("hpo_count", 0) > 0}
    covered_codes = set(core_codes)
    outside = sum(1 for code in per_code if code not in covered_codes)
    return {
        "core_codes": core_codes,
        "reachable_codes": reachable,
        "hpo_icf_target_codes": set(per_code),
        "uncovered_target_codes": outside,
        "per_code": per_code,
    }


def render_report(rows, metrics):
    """Render a dated Markdown report using only computed graph metrics."""
    lines = [
        "# HPO→ICF reachability vs ICF Core Sets",
        "",
        "Read-only evaluation; this report does not alter graph edges.",
        "",
    ]
    if not rows:
        lines += [
            "The curated register `curated/icf_core_sets.csv` is empty. No ICF",
            "Core Set category lists were supplied, so per-core-set recall cannot",
            "yet be evaluated. Add source-backed categories only after confirming",
            "their redistribution terms.",
            "",
        ]
    else:
        by_set = defaultdict(set)
        for row in rows:
            by_set[row["core_set"].strip()].add(row["icf_code"].strip())
        lines += [
            "| Core set | Categories | Reachable via HPO→ICF | Unreachable |",
            "|---|---:|---:|---:|",
        ]
        for core_set, codes in sorted(by_set.items()):
            reachable = codes & metrics["reachable_codes"]
            lines.append("| {} | {} | {} | {} |".format(
                core_set, len(codes), len(reachable), len(codes - reachable)))
        lines.append("")
    lines += [
        "## HPO→ICF edges outside supplied Core Sets",
        "",
        "- Distinct ICF target codes with HPO→ICF edges: {}".format(
            len(metrics["hpo_icf_target_codes"])),
        "- Distinct target codes not present in the supplied Core Set register: {}".format(
            metrics["uncovered_target_codes"]),
        "",
        "All counts are direct graph counts; no matcher behavior was changed.",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT),
                        help="Markdown output path")
    args = parser.parse_args()
    rows = load_register()
    if not os.getenv("NEO4J_PASSWORD"):
        if rows:
            raise RuntimeError(
                "NEO4J_PASSWORD is required to evaluate supplied Core Set rows")
        metrics = {
            "core_codes": [], "reachable_codes": set(),
            "hpo_icf_target_codes": set(), "uncovered_target_codes": 0,
            "per_code": {},
        }
        connection_note = (
            "Live graph metrics were not collected because NEO4J_PASSWORD is "
            "not configured in this environment."
        )
    else:
        with get_driver() as driver:
            with driver.session() as session:
                metrics = collect_graph_metrics(session, rows)
        connection_note = "Live read-only graph metrics collected."
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(rows, metrics) + "\n" + connection_note + "\n",
                       encoding="utf-8")
    print("Wrote {}".format(output))


if __name__ == "__main__":
    main()
