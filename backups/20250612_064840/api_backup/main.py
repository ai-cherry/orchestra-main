#!/usr/bin/env python3
"""Main API entry point for Cherry AI"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from src.search_engine.search_router import SearchRouter
from src.file_ingestion.ingestion_controller import IngestionController

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Cherry AI API...")
    yield
    logger.info("Shutting down Cherry AI API...")

app = FastAPI(
    title="Cherry AI API",
    description="Advanced AI coordination system",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
search_router = SearchRouter()
ingestion_controller = IngestionController()

@app.get("/")
    """t endpoint"""
    return {
        "name": "Cherry AI",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "cherry_ai-ai"
    }

@app.post("/search")
async def search(query: str, mode: str = "normal", options: dict = None):
    """Execute search with specified mode"""
    try:
        result = await search_router.route(query, mode, options or {})
        return result
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
async def ingest_file(file_path: str, metadata: dict = None):
    """Ingest a file into the system"""
    try:
        result = await ingestion_controller.ingest_file(file_path, metadata)
        return result
    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
