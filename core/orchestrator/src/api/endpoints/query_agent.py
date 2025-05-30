"""Endpoint to forward queries to Weaviate Agent runtime."""

import httpx
from fastapi import APIRouter, HTTPException
from core.orchestrator.src.config.settings import get_settings

router = APIRouter()

@router.post("/query", tags=["query"])
async def query_agent(payload: dict) -> dict:
    settings = get_settings()
    url = f"{settings.WEAVIATE_URL}/agent/query"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            return r.json()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
