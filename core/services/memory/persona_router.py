from __future__ import annotations

"""Persona-aware memory routing utilities."""

from typing import Any, Dict, List, Optional

from .unified_memory import UnifiedMemoryService, SearchResult, MemoryLayer
from .meta_graph import MetaGraph


class PersonaMemoryRouter:
    """Route memory operations for a specific persona."""

    def __init__(
        self,
        persona: str,
        memory_service: UnifiedMemoryService,
        meta_graph: Optional[MetaGraph] = None,
    ) -> None:
        self.persona = persona
        self.memory = memory_service
        self.meta_graph = meta_graph

    async def query(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """Query all memory layers scoped to the active persona."""
        context = context or {}
        filters = {"metadata.persona": self.persona}
        results = await self.memory.search(query, filters=filters)

        if context.get("include_related") and self.meta_graph:
            related = self.meta_graph.get_related_personas(self.persona, context.get("relation", "default"))
            for other in related:
                extra = await self.memory.search(query, filters={"metadata.persona": other})
                results.extend(extra)

        return self._rank_results(results)

    def _rank_results(self, results: List[SearchResult]) -> List[SearchResult]:
        return sorted(results, key=lambda r: r.score, reverse=True)
