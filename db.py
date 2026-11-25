"""Shared Neo4j connection helpers.

Every script that talks to the database should use these instead of
rolling its own os.getenv(..., "password") fallback — a missing password
must fail fast with a clear message, never silently connect with a
default credential.

Environment variables (see .env.example):
  NEO4J_URI      default bolt://localhost:7687
  NEO4J_USER     default neo4j
  NEO4J_PASSWORD required — no default
"""
import os


def get_uri():
    return os.getenv("NEO4J_URI", "bolt://localhost:7687")


def get_user():
    return os.getenv("NEO4J_USER", "neo4j")


def get_password():
    pw = os.getenv("NEO4J_PASSWORD")
    if not pw:
        raise RuntimeError(
            "NEO4J_PASSWORD is not set. Copy .env.example to .env and fill "
            "it in (never commit the real password)."
        )
    return pw


def get_driver(**kwargs):
    """Return a Neo4j driver using the shared env-var settings."""
    from neo4j import GraphDatabase
    return GraphDatabase.driver(
        get_uri(), auth=(get_user(), get_password()), **kwargs
    )


def get_database():
    """Optional Neo4j database name for isolated integration tests/deployments."""
    return os.getenv("NEO4J_DATABASE") or None


def get_session_config():
    """Return database-aware Session kwargs when NEO4J_DATABASE is configured."""
    database = get_database()
    return {"database": database} if database else {}
