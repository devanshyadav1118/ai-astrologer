"""Neo4j connection helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(slots=True)
class Neo4jSettings:
    """Runtime settings for Neo4j access."""

    uri: str
    user: str
    password: str


def load_neo4j_settings() -> Neo4jSettings:
    """Load Neo4j settings from `.env`."""
    load_dotenv()
    uri = os.getenv("NEO4J_URI", "").strip()
    user = os.getenv("NEO4J_USER", "").strip()
    password = os.getenv("NEO4J_PASSWORD", "").strip()
    if not uri or not user or not password:
        raise RuntimeError("Neo4j settings are incomplete")
    return Neo4jSettings(uri=uri, user=user, password=password)
