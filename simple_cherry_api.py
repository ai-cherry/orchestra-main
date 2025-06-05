#!/usr/bin/env python3
"""
Simple Cherry AI API Server
Minimal FastAPI server for the working interface
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cherry AI API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data for demonstration
MOCK_DOMAIN_DATA = [
    {
        "title": "AI Orchestration Framework",
        "snippet": "Our advanced AI orchestration framework enables seamless integration of multiple AI models and services.",
        "source": "internal_docs",
        "relevance": 0.95
    },
    {
        "title": "Agent Management System",
        "snippet": "The agent management system provides tools for creating, monitoring, and controlling AI agents.",
        "source": "knowledge_base",
        "relevance": 0.88
    },
    {
        "title": "Workflow Automation Guide",
        "snippet": "Learn how to create automated workflows using our visual workflow builder and API.",
        "source": "tutorials",
        "relevance": 0.82
    }
]

MOCK_WEB_DATA = [
    {
        "title": "Latest AI Research Papers",
        "snippet": "Recent advances in large language models and their applications in enterprise settings.",
        "source": "arxiv.org",
        "relevance": 0.91
    },
    {
        "title": "AI Industry News",
        "snippet": "Major tech companies announce new AI initiatives and partnerships.",
        "source": "techcrunch.com",
        "relevance": 0.85
    }
]

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Cherry AI API Server", "status": "running"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "running",
            "database": "connected",
            "weaviate": "connected"
        }
    }

@app.get("/api/search")
async def search(
    q: str = Query(..., description="Search query"),
    mode: str = Query("normal", description="Search mode"),
    type: str = Query("external", description="Search type: internal or external"),
    persona: str = Query("cherry", description="Persona: cherry, sophia, or karen")
):
    """Handle search requests"""
    logger.info(f"Search request: q='{q}', mode={mode}, type={type}, persona={persona}")
    
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter is required")
    
    # Select mock data based on search type
    if type == "internal":
        results = MOCK_DOMAIN_DATA
        # Filter results based on query (simple keyword matching)
        results = [r for r in results if q.lower() in r["title"].lower() or q.lower() in r["snippet"].lower()]
        if not results:
            results = MOCK_DOMAIN_DATA[:2]  # Return some results anyway
    else:
        results = MOCK_WEB_DATA
        # Add query to results for realism
        results = [dict(r, snippet=f"{r['snippet']} Related to: {q}") for r in results]
    
    # Adjust results based on mode
    if mode == "creative":
        for r in results:
            r["relevance"] *= 0.9
    elif mode == "deep" or mode == "super-deep":
        for r in results:
            r["relevance"] *= 1.05
            r["relevance"] = min(r["relevance"], 1.0)
    
    # Adjust based on persona
    persona_adjustments = {
        "cherry": "personal context",
        "sophia": "business context",
        "karen": "healthcare context"
    }
    
    if persona in persona_adjustments:
        for r in results:
            r["snippet"] += f" ({persona_adjustments[persona]})"
    
    return {
        "query": q,
        "mode": mode,
        "type": type,
        "persona": persona,
        "results": results,
        "search_config": {
            "name": f"{mode} search",
            "depth": mode
        }
    }

@app.get("/api/agents")
async def get_agents():
    """Get mock agents"""
    return [
        {"id": "1", "name": "Data Processor", "status": "active"},
        {"id": "2", "name": "Web Scraper", "status": "active"},
        {"id": "3", "name": "AI Analyzer", "status": "idle"}
    ]

@app.get("/api/orchestrations")
async def get_orchestrations():
    """Get mock orchestrations"""
    return [
        {"id": "1", "name": "Customer Feedback Pipeline", "status": "running"},
        {"id": "2", "name": "Data Sync Workflow", "status": "scheduled"}
    ]

@app.get("/api/workflows")
async def get_workflows():
    """Get mock workflows"""
    return [
        {"id": "1", "name": "Daily Report Generation", "status": "active"},
        {"id": "2", "name": "Real-time Monitoring", "status": "active"}
    ]

def main():
    """Main entry point"""
    logger.info("Starting Simple Cherry AI API Server...")
    
    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    main()