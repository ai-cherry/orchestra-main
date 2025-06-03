"""
"""
    """Store and retrieve small JSON blobs in Weaviate."""
        self._adapter = WeaviateAdapter(class_name="Session")

    async def set_json(self, key: str, value: Dict[str, Any]) -> None:
        await self._adapter.batch_upsert(
            [
                {"id": key, "vector": [], "properties": {"data": value}},
            ]
        )

    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        results = await self._adapter.query(
            vector=[],
            top_k=1,
            filters={"path": ["id"], "operator": "Equal", "valueText": key},
        )
        if results:
            return results[0]["properties"].get("data")
        return None

cache = WeaviateSessionCache()
