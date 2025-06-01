"""Neo4j meta-memory integration."""

from typing import Any, Dict, List

try:
    from neo4j import GraphDatabase
except Exception:  # pragma: no cover - optional dependency
    GraphDatabase = None  # type: ignore


class MetaGraph:
    """Wrapper around a Neo4j driver for persona relationships."""

    def __init__(self, url: str, user: str | None = None, password: str | None = None) -> None:
        self.url = url
        self.user = user
        self.password = password
        if GraphDatabase:
            auth = (user, password) if user else None
            self.driver = GraphDatabase.driver(url, auth=auth)
        else:
            self.driver = None

    def get_related_personas(self, persona: str, context: str) -> List[str]:
        """Return personas related to the given persona for a context."""
        if not self.driver:
            return []
        query = (
            "MATCH (p:Persona {name:$name})-[r:RELATES {context:$ctx}]->(o:Persona) "
            "RETURN o.name as name"
        )
        with self.driver.session() as session:
            records = session.run(query, name=persona, ctx=context)
            return [rec["name"] for rec in records]
