#!/usr/bin/env python3
"""Apply clinician review decisions back to the curated CSVs.

The dashboard's "Evidence & Review" page exports a decisions template
(one row per curated CSV row). A reviewer fills decision
(approved/rejected), reviewed_by, reviewed_on, and optionally citation/
comment. This script merges those decisions into the curated CSVs —
Git stays the system of record; clinicians never touch Git.

Rules:
  - decision must be 'approved' or 'rejected'; blank/unreviewed skips.
  - 'approved' REQUIRES a citation or citation_doi (curated CSV rows
    without a citation must stay unreviewed — enforced by tests).
  - Unknown keys (file/match_type/condition_key/exercise_name[/rel_type])
    are refused with a per-row error, never silently skipped.
  - --update-graph re-runs the idempotent curated loaders against the
    live database so changes reflect immediately.

Usage:
    python curated/apply_decisions.py review_decisions.csv
    python curated/apply_decisions.py review_decisions.csv --update-graph
    python curated/apply_decisions.py review_decisions.csv --dry-run
"""

import argparse
import csv
import sys
from pathlib import Path

CURATED = Path(__file__).resolve().parent
CONDITION_CSV = CURATED / "condition_exercise.csv"
SAFETY_CSV = CURATED / "safety_contraindications.csv"
ALLOWED_FILES = {CONDITION_CSV.name, SAFETY_CSV.name}
DECISIONS = {"approved", "rejected"}

REQUIRED_COLUMNS = {
    "file", "match_type", "condition_key", "exercise_name",
    "decision", "reviewed_by", "reviewed_on",
}


def _row_key(row):
    """Natural key for matching a decision to a curated CSV row."""
    return (
        row["match_type"].strip(),
        row["condition_key"].strip(),
        row["exercise_name"].strip(),
        row.get("rel_type", "").strip(),
    )


def load_decisions(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - header
        if missing:
            raise SystemExit(f"decisions CSV missing columns: {sorted(missing)}")
        return [r for r in reader if (r.get("decision") or "").strip().lower()]


def apply_to_csv(csv_path, decisions, dry_run=False):
    """Merge decisions into one curated CSV. Returns (applied, errors)."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys())

    # Index curated rows by natural key
    index = {}
    for i, row in enumerate(rows):
        index[_row_key(row)] = i

    matched_keys = set()
    applied, errors = [], []
    for dec in decisions:
        if dec["file"].strip() != csv_path.name:
            continue
        decision = dec["decision"].strip().lower()
        if decision not in DECISIONS:
            errors.append(f"invalid decision {decision!r} for {dec}")
            continue
        if not dec.get("reviewed_by", "").strip():
            errors.append(
                f"reviewed_by required for {dec['exercise_name']!r}")
            continue
        if (decision == "approved"
                and not dec.get("citation", "").strip()):
            errors.append(
                f"approval of {dec['exercise_name']!r} requires a citation")
            continue
        key = (
            dec["match_type"].strip(),
            dec["condition_key"].strip(),
            dec["exercise_name"].strip(),
            dec.get("rel_type", "").strip(),
        )
        if key not in index:
            errors.append(
                f"unknown row refused: file={dec['file']!r} "
                f"match_type={key[0]!r} condition_key={key[1]!r} "
                f"exercise_name={key[2]!r} rel_type={key[3]!r}")
            continue
        row = rows[index[key]]
        row["status"] = decision
        row["reviewed_by"] = dec["reviewed_by"].strip()
        row["reviewed_on"] = dec["reviewed_on"].strip()
        citation = dec.get("citation", "").strip()
        if citation:
            row["citation"] = citation
        matched_keys.add(key)
        applied.append(f"{csv_path.name}: {key[1]!r} × {key[2]!r} -> {decision}")

    if applied and not dry_run:
        with open(csv_path, "w", newline="\n", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    return applied, errors


def update_graph():
    """Re-run the idempotent curated loaders against the live database."""
    sys.path.insert(0, str(CURATED.parent))
    from dotenv import load_dotenv
    load_dotenv(CURATED.parent / ".env")
    from db import get_driver
    from bridges import (
        link_conditions_to_exercises,
        link_safety_edges,
    )
    driver = get_driver()
    try:
        with driver.session() as s:
            link_conditions_to_exercises(s)
            link_safety_edges(s)
    finally:
        driver.close()


def main():
    parser = argparse.ArgumentParser(
        description="Apply review decisions to curated CSVs")
    parser.add_argument("decisions", help="Decisions CSV from the dashboard")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without writing")
    parser.add_argument("--update-graph", action="store_true",
                        help="Re-run curated loaders against live Neo4j")
    args = parser.parse_args()

    decisions = load_decisions(args.decisions)
    if not decisions:
        print("No decision rows to apply (all blank/unreviewed).")
        return

    all_applied, all_errors = [], []
    for csv_path in (CONDITION_CSV, SAFETY_CSV):
        applied, errors = apply_to_csv(csv_path, decisions, dry_run=args.dry_run)
        all_applied.extend(applied)
        all_errors.extend(errors)

    for line in all_applied:
        print(f"  ✓ {line}")
    for line in all_errors:
        print(f"  ✗ {line}", file=sys.stderr)
    print(f"\n{len(all_applied)} applied, {len(all_errors)} refused"
          + (" (dry run)" if args.dry_run else ""))

    if all_errors:
        sys.exit(1)
    if all_applied and args.update_graph and not args.dry_run:
        print("\nUpdating live graph from curated CSVs...")
        update_graph()
        print("  ✅ Graph updated")


if __name__ == "__main__":
    main()
