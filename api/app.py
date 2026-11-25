"""RehabKG read-only API.

Minimal FastAPI service over the live Neo4j graph, designed as the
shared substrate for the dashboard "explain" panel, GraphRAG citation,
and gold-question evaluation.

Design rules:
  - READ sessions only (default_access_mode=READ_ACCESS); no write route
    exists. Bind to localhost unless you add auth at a reverse proxy.
  - Every response carries edge provenance (method/match_type/confidence/
    source/review_status) so consumers can cite and filter mechanically.
  - Recommendation responses also return PRECAUTION/CONTRAINDICATION
    edges for the same condition — safety must never be opt-in.

Run:
    pip install -r requirements-api.txt
    uvicorn api.app:app --host 127.0.0.1 --port 8000

Docs: http://127.0.0.1:8000/docs
"""

from fastapi import Depends, FastAPI, HTTPException, Query
from neo4j import READ_ACCESS

from db import get_driver, get_session_config
from provenance import CSV_IMPORT_RELS

# Hard caps so a typo'd query cannot scan the whole graph.
MAX_DEPTH = 3
MAX_PATHS = 25
MAX_LIST = 100


def create_app(driver_factory=None):
    """Build the FastAPI app. driver_factory is injectable for tests."""
    app = FastAPI(
        title="RehabKG API",
        description=(
            "Read-only query service for the RehabKG rehabilitation "
            "knowledge graph. Every edge payload carries provenance; "
            "recommendation responses include safety edges. "
            "NOT a clinical decision-support device."
        ),
        version="0.1.0",
    )
    app.state.driver_factory = driver_factory or get_driver

    def get_session():
        driver = app.state.driver_factory()
        if driver is None:
            # Test stubs may inject a null driver; request validation can
            # fail (422) during dependency solving, so never assume a
            # live driver here.
            yield None
            return
        try:
            with driver.session(default_access_mode=READ_ACCESS,
                                 **get_session_config()) as s:
                yield s
        finally:
            driver.close()

    session_dep = Depends(get_session)

    # ── Routes ─────────────────────────────────────────────────────────

    @app.get("/health")
    def health():
        """Liveness check; touches no database."""
        return {"status": "ok"}

    @app.get("/stats")
    def stats(session=session_dep):
        """Node/relationship counts plus provenance coverage per clinical type."""
        nodes = session.run("""
            MATCH (n) UNWIND labels(n) AS label
            RETURN label, count(*) AS count
            ORDER BY count DESC
        """).data()
        rels = session.run("""
            MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS count
            ORDER BY count DESC
        """).data()
        provenance = []
        for rel_type in CSV_IMPORT_RELS:
            r = session.run(f"""
                MATCH ()-[r:{rel_type}]->()
                RETURN count(r) AS total,
                       sum(CASE WHEN r.method IS NOT NULL THEN 1 ELSE 0 END)
                           AS with_method,
                       sum(CASE WHEN r.review_status IS NOT NULL THEN 1 ELSE 0 END)
                           AS with_review_status
            """).single()
            if r["total"]:
                provenance.append({
                    "type": rel_type,
                    "total": r["total"],
                    "with_method": r["with_method"],
                    "with_review_status": r["with_review_status"],
                })
        return {"nodes": nodes, "relationships": rels,
                "clinical_edge_provenance": provenance}

    @app.get("/conditions")
    def search_conditions(
        q: str = Query(..., min_length=2, description="Name substring"),
        limit: int = Query(20, le=MAX_LIST),
        session=session_dep,
    ):
        """Search Condition nodes by name substring (case-insensitive)."""
        rows = session.run("""
            MATCH (c:Condition)
            WHERE toLower(c.name) CONTAINS toLower($q)
            RETURN c.code AS code, c.name AS name,
                   c.icd10_code AS icd10_code
            ORDER BY c.name
            LIMIT $limit
        """, q=q, limit=limit).data()
        return {"conditions": rows}

    @app.get("/conditions/{ref}/recommendations")
    def condition_recommendations(
        ref: str,
        limit: int = Query(50, le=MAX_LIST),
        session=session_dep,
    ):
        """Exercises recommended for a condition, WITH safety edges.

        ref matches Condition.code or exact name. The response always
        includes precautions and contraindications for the same
        condition — consumers must not have to ask twice for safety.
        Edges carry the full provenance contract; unreviewed rows are
        candidates for clinician review, not clinical advice.
        """
        cond = session.run("""
            MATCH (c:Condition)
            WHERE c.code = $ref OR toLower(c.name) = toLower($ref)
            RETURN c.code AS code, c.name AS name, c.icd10_code AS icd10_code
            LIMIT 1
        """, ref=ref).single()
        if cond is None:
            raise HTTPException(404, f"No Condition matching {ref!r}")

        recs = session.run("""
            MATCH (c:Condition)-[r:RECOMMENDS_EXERCISE]->(e:Exercise)
            WHERE c.code = $code OR toLower(c.name) = toLower($name)
            RETURN e.exercise_id AS exercise_id, e.name AS name,
                   e.category AS category, properties(r) AS edge
            ORDER BY e.name
            LIMIT $limit
        """, code=cond["code"], name=cond["name"], limit=limit).data()

        def safety_rows(rel_type):
            return session.run(f"""
                MATCH (c:Condition)-[r:{rel_type}]->(e:Exercise)
                WHERE c.code = $code OR toLower(c.name) = toLower($name)
                RETURN e.exercise_id AS exercise_id, e.name AS name,
                       properties(r) AS edge
                ORDER BY e.name
                LIMIT $limit
            """, code=cond["code"], name=cond["name"], limit=limit).data()

        return {
            "condition": cond,
            "disclaimer": (
                "Candidate recommendations with review_status on every "
                "edge; not clinical advice."
            ),
            "recommendations": recs,
            "precautions": safety_rows("PRECAUTION"),
            "contraindications": safety_rows("CONTRAINDICATION"),
        }

    @app.get("/paths")
    def find_paths(
        start_name: str = Query(..., description="Exact node name to start from"),
        end_name: str = Query(..., description="Exact node name to end at"),
        max_depth: int = Query(2, ge=1, le=MAX_DEPTH),
        limit: int = Query(10, le=MAX_PATHS),
        session=session_dep,
    ):
        """Shortest paths between two named nodes with per-edge provenance.

        Bounded depth/limit; undirected traversal over all relationship
        types. Each relationship payload includes the provenance
        contract so callers can cite every hop.
        """
        # Neo4j 5 does not allow parameterized variable-length hops inside
        # shortestPath; interpolate a bounds-checked integer instead.
        # Literal Cypher braces are doubled for the f-string.
        depth = max(1, min(int(max_depth), MAX_DEPTH))
        rows = session.run(f"""
            MATCH path = shortestPath(
                (a {{name: $start_name}})-[*1..{depth}]-(b {{name: $end_name}})
            )
            WHERE a <> b
            RETURN [n IN nodes(path) | {{
                id: elementId(n), labels: labels(n), name: n.name
            }}] AS nodes,
                   [r IN relationships(path) | {{
                       type: type(r),
                       id: elementId(r),
                       props: properties(r)
                   }}] AS relationships,
                   length(path) AS length
            LIMIT $limit
        """, start_name=start_name, end_name=end_name, limit=limit).data()
        return {
            "start_name": start_name,
            "end_name": end_name,
            "paths": rows,
            "count": len(rows),
        }

    return app


# Uvicorn entry point: `uvicorn api.app:app --port 8000`
app = create_app()
