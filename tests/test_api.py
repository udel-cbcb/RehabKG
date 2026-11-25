"""Smoke tests for the read-only API (no Neo4j required).

fastapi is an optional dependency (requirements-api.txt); these tests
skip cleanly when it is not installed (e.g. in CI, which only installs
requirements.txt). Route registration and /health are checked without a
database; live-graph checks live in test_graph.py instead.
"""
import os
import sys

import pytest

fastapi = pytest.importorskip("fastapi")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.app import create_app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


class TestAppFactory:
    def test_health_does_not_touch_database(self):
        # driver_factory that explodes proves /health never calls it.
        def exploding_factory():
            raise AssertionError("driver_factory must not be called on /health")

        app = create_app(driver_factory=exploding_factory)
        client = TestClient(app)
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_expected_routes_registered(self):
        app = create_app(driver_factory=lambda: None)
        paths = {getattr(route, "path", None) for route in app.routes}
        for expected in (
            "/health",
            "/stats",
            "/conditions",
            "/conditions/{ref}/recommendations",
            "/paths",
        ):
            assert expected in paths, f"missing route {expected}"

    def test_openapi_marks_api_read_only(self):
        app = create_app(driver_factory=lambda: None)
        client = TestClient(app)
        spec = client.get("/openapi.json").json()
        # No write-method paths may ever be registered.
        for path, methods in spec["paths"].items():
            for method in methods:
                assert method.upper() not in ("POST", "PUT", "PATCH", "DELETE"), (
                    f"{method} {path} would make the API non-read-only"
                )

    def test_search_conditions_requires_min_length(self):
        app = create_app(driver_factory=lambda: None)
        client = TestClient(app)
        r = client.get("/conditions", params={"q": "a"})  # below min_length=2
        assert r.status_code == 422
