"""
Async FastAPI entrypoint for Orchestra API.
- High-performance, async-ready.
- Integrates with unified memory (DragonflyDB, Qdrant, Firestore).
- GCP-native: reads secrets from Secret Manager, supports Pub/Sub.
- Ready for Cloud Run deployment.
"""

from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Use centralized environment configuration
from core.env_config import settings
from orchestra_api.routers import agents, data_ingestion
from orchestrator.enrichment_orchestrator import EnrichmentOrchestrator
from packages.agents.company_enrichment_agent import CompanyEnrichmentAgent
from packages.agents.contact_enrichment_agent import ContactEnrichmentAgent
from packages.agents.property_enrichment_agent import PropertyEnrichmentAgent
from shared.memory.unified_memory import MemoryItem, UnifiedMemory

app = FastAPI(
    title="Orchestra API",
    description="Async, high-performance API for AI/data orchestration on GCP",
    version="0.1.0",
)

# Include routers
app.include_router(data_ingestion.router)
app.include_router(agents.router)

# Initialize unified memory (env-driven config)
memory = UnifiedMemory(
    use_dragonfly=True,
    use_qdrant=True,
    use_firestore=True,
    dragonfly_url=settings.dragonfly_url,
    qdrant_url=settings.qdrant_url,
    firestore_project=settings.gcp_project_id,
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


# --- Enrichment Orchestration Integration ---
# (imports moved to top of file)

# Instantiate agents and orchestrator (env-driven config)
property_agent = PropertyEnrichmentAgent(
    firestore_collection="properties",
    google_maps_api_key=settings.google_maps_api_key,
)
company_agent = CompanyEnrichmentAgent(
    firestore_collection="properties",
    serpapi_key=settings.serpapi_key,
    claude_max_webhook=settings.claude_max_webhook,
)
contact_agent = ContactEnrichmentAgent(
    firestore_collection="companies",
    apollo_api_key=settings.apollo_api_key,
    phantombuster_api_key=settings.phantombuster_api_key,
    browser_use_endpoint=settings.browser_use_endpoint,
    claude_max_webhook=settings.claude_max_webhook,
)
enrichment_orchestrator = EnrichmentOrchestrator(
    property_agent, company_agent, contact_agent
)


class EnrichmentRequest(BaseModel):
    properties: List[dict]


@app.post("/enrichment/batch", response_model=dict)
async def run_batch_enrichment(request: EnrichmentRequest):
    """
    Trigger full enrichment pipeline for a batch of properties.
    """
    enrichment_orchestrator.run_full_enrichment(request.properties)
    return {"status": "enrichment started", "count": len(request.properties)}


@app.post("/enrichment/property/{property_doc_id}", response_model=dict)
async def run_enrichment_for_property(property_doc_id: str):
    """
    Trigger company and contact enrichment for a single property.
    """
    enrichment_orchestrator.run_enrichment_for_property(property_doc_id)
    return {"status": "enrichment started", "property_doc_id": property_doc_id}
