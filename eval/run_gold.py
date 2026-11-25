#!/usr/bin/env python3
"""Run the stroke-gait gold questions against a live RehabKG graph.

Each line of eval/gold_questions.jsonl is one question with expected
result bounds (min/max on the first returned integer, or ratio_fields/
ratio_min for coverage checks). The runner executes every Cypher query,
checks the expectation, and prints a PASS/FAIL report.

Exit code = number of failed questions (0 = all pass).

Usage:
    python eval/run_gold.py                    # all questions
    python eval/run_gold.py --category core    # one category
    python eval/run_gold.py --json report.json # machine-readable report
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GOLD = Path(__file__).resolve().parent / "gold_questions.jsonl"
sys.path.insert(0, str(REPO))  # allow `python eval/run_gold.py` from anywhere


def load_questions(category=None):
    questions = []
    with open(GOLD, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            q = json.loads(line)
            if category and q.get("category") != category:
                continue
            questions.append(q)
    return questions


def check_expected(expected, record):
    """Return (ok, detail) for one query result record."""
    if "ratio_fields" in expected:
        num_field, den_field = expected["ratio_fields"][0]
        num, den = record[num_field], record[den_field]
        ratio = (num / den) if den else 0.0
        ok = ratio >= expected.get("ratio_min", 1.0)
        return ok, f"{num}/{den} = {ratio:.2%} (min {expected['ratio_min']:.0%})"

    # Single integer field: first integer value in the record
    value = None
    for v in record.values():
        if isinstance(v, int) and not isinstance(v, bool):
            value = v
            break
    if value is None:
        return False, f"no integer field in result {dict(record)}"
    ok = True
    parts = []
    if "min" in expected:
        ok = ok and value >= expected["min"]
        parts.append(f">= {expected['min']}")
    if "max" in expected:
        ok = ok and value <= expected["max"]
        parts.append(f"<= {expected['max']}")
    return ok, f"{value} ({' and '.join(parts)})"


def run(questions, driver_factory=None):
    """Run questions; returns list of result dicts."""
    if driver_factory is None:
        from dotenv import load_dotenv
        load_dotenv(REPO / ".env")
        from db import get_driver as driver_factory  # noqa: N813

    results = []
    driver = driver_factory()
    try:
        for q in questions:
            entry = {"id": q["id"], "category": q["category"],
                     "question": q["question"]}
            try:
                with driver.session() as s:
                    record = s.run(q["cypher"]).single()
                if record is None:
                    entry.update(ok=False, detail="query returned no record")
                else:
                    ok, detail = check_expected(q["expected"], dict(record))
                    entry.update(ok=ok, detail=detail)
            except Exception as exc:  # Cypher/syntax/connection errors
                entry.update(ok=False, detail=f"error: {exc}")
            results.append(entry)
    finally:
        driver.close()
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--category", choices=[
        "core", "ontology", "provenance", "observation", "usecase"], default=None)
    parser.add_argument("--json", metavar="PATH",
                        help="Also write a JSON report to PATH")
    args = parser.parse_args()

    questions = load_questions(args.category)
    if not questions:
        print("No questions loaded (bad category or empty file).")
        return 1

    results = run(questions)
    failed = 0
    for r in results:
        status = "PASS" if r["ok"] else "FAIL"
        if not r["ok"]:
            failed += 1
        print(f"  {status}  [{r['category']}] {r['id']}: {r['detail']}")
        if not r["ok"]:
            print(f"        Q: {r['question']}")

    total = len(results)
    print(f"\n{total - failed}/{total} passed"
          + (f", {failed} FAILED" if failed else ""))

    if args.json:
        Path(args.json).write_text(
            json.dumps({"total": total, "failed": failed,
                        "results": results}, indent=2),
            encoding="utf-8")
        print(f"Report written to {args.json}")
    return failed


if __name__ == "__main__":
    sys.exit(main())
