"""Gold-question tests against a live RehabKG graph (CI-safe).

Skips entirely when the neo4j driver is not installed or the database is
unreachable, so the offline CI workflow is unaffected. When Neo4j is
available, every gold question must execute without error and satisfy
its expected result bounds.

Questions live in eval/gold_questions.jsonl; this module parametrizes one
test per question for precise failure reporting.
"""

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
GOLD = REPO / "eval" / "gold_questions.jsonl"


def _load_gold():
    with open(GOLD, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _get_driver():
    pytest.importorskip("neo4j", reason="neo4j driver not installed")
    try:
        from dotenv import load_dotenv
        load_dotenv(REPO / ".env")
        from db import get_driver
        driver = get_driver()
        with driver.session() as s:
            s.run("RETURN 1").single()
        return driver
    except Exception as exc:
        pytest.skip(f"Neo4j not reachable: {exc}")


@pytest.fixture(scope="module")
def driver():
    d = _get_driver()
    yield d
    d.close()


def _param_id(q):
    return q["id"]


GOLD_QUESTIONS = _load_gold()


@pytest.mark.parametrize("question", GOLD_QUESTIONS, ids=_param_id)
def test_gold_question(driver, question):
    from eval.run_gold import check_expected

    with driver.session() as s:
        record = s.run(question["cypher"]).single()
    assert record is not None, f"{question['id']}: query returned no record"
    ok, detail = check_expected(question["expected"], dict(record))
    assert ok, f"{question['id']}: {detail} — {question['question']}"


def test_gold_file_shape():
    """The gold file itself must stay well-formed (offline check)."""
    questions = _load_gold()
    assert len(questions) >= 20, "need at least 20 gold questions"
    ids = [q["id"] for q in questions]
    assert len(ids) == len(set(ids)), "duplicate question ids"
    categories = {q.get("category") for q in questions}
    assert categories <= {"core", "ontology", "provenance", "observation", "usecase"}
    for q in questions:
        assert q["cypher"].strip().upper().startswith("MATCH"), q["id"]
        assert "reviewer" in q and q["reviewer"], q["id"]
        assert "expected" in q and q["expected"], q["id"]
