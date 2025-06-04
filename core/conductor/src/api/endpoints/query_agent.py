"""Endpoint to forward queries to Weaviate Agent runtime."""
@router.post("/query", tags=["query"])
async def query_agent(payload: dict) -> dict:
    settings = get_settings()
    url = f"{settings.WEAVIATE_URL}/agent/query"
    try:

        pass
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            return r.json()
    except Exception:

        pass
        raise HTTPException(status_code=500, detail=str(exc))
