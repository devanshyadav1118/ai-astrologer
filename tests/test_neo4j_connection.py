"""Phase 0 Neo4j connectivity check."""

from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv


def test_neo4j_connection() -> None:
    neo4j = pytest.importorskip("neo4j")
    load_dotenv()
    uri = os.getenv("NEO4J_URI", "").strip()
    user = os.getenv("NEO4J_USER", "").strip()
    password = os.getenv("NEO4J_PASSWORD", "").strip()
    if not uri or not user or not password or password == "your_neo4j_password_here":
        pytest.skip("Neo4j credentials are not configured")
    driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run("RETURN 'Neo4j connected' AS msg")
        assert result.single()["msg"] == "Neo4j connected"
    driver.close()
