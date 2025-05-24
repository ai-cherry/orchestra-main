"""
Async FastAPI entrypoint for Orchestra API.
- High-performance, async-ready.
- Integrates with unified memory (DragonflyDB, Qdrant, Firestore).
- GCP-native: reads secrets from Secret Manager, supports Pub/Sub.
- Ready for Cloud Run deployment.
"""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from shared.memory.unified_memory import UnifiedMemory, MemoryItem
from orchestra_api.routers import data_ingestion

app = FastAPI(
    title="Orchestra API",
    description="Async, high-performance API for AI/data orchestration on GCP",
    version="0.1.0",
)

# Include routers
app.include_router(data_ingestion.router)

# Initialize unified memory (env-driven config)
memory = UnifiedMemory(
    use_dragonfly=True,
    use_qdrant=True,
    use_firestore=True,
    dragonfly_url=os.getenv("DRAGONFLY_URL"),
    qdrant_url=os.getenv("QDRANT_URL"),
    firestore_project=os.getenv("GCP_PROJECT"),
)

class MemoryCreateRequest(BaseModel):
    id: str
    content: str
    source: str
    timestamp: str
    metadata: Optional[dict] = None
    priority: Optional[float] = 0.5
    embedding: Optional[List[float]] = None

@app.post("/memory/", response_model=dict)
async def create_memory(item: MemoryCreateRequest):
    """Store a memory item in all enabled backends."""
    memory_id = memory.store(MemoryItem(**item.dict()))
    return {"id": memory_id}

@app.get("/memory/{memory_id}", response_model=MemoryCreateRequest)
async def get_memory(memory_id: str):
    """Retrieve a memory item by ID."""
    item = memory.retrieve(memory_id)
    if not item:
        raise HTTPException(status_code=404, detail="Memory item not found")
    return item

@app.get("/memory/search/", response_model=List[MemoryCreateRequest])
async def search_memory(query: str, limit: int = 10):
    """Search memory items by text or vector (comma-separated floats)."""
    try:
        # Try to parse as vector
        if "," in query:
            vector = [float(x) for x in query.split(",")]
            results = memory.search(vector, limit=limit)
        else:
            results = memory.search(query, limit=limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Search error: {e}")

@app.delete("/memory/{memory_id}", response_model=dict)
async def delete_memory(memory_id: str):
    """Delete a memory item from all backends."""
    deleted = memory.delete(memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory item not found")
    return {"deleted": True}

@app.get("/health", response_model=dict)
async def health_check():
    """Health check for all backends."""
    return memory.health()