"""
Orchestra API - Minimal working version for deployment.
"""

from typing import Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel

# Create FastAPI app
app = FastAPI(
    title="Orchestra API",
    description="AI Orchestrator and Modular Agent Framework",
    version="0.1.0"
)

# Health check model
class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

# Root endpoint
@app.get("/", response_model=HealthResponse)
async def root() -> Dict[str, str]:
    """Root endpoint - health check."""
    return {
        "status": "healthy",
        "message": "Orchestra API is running",
        "version": "0.1.0"
    }

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check() -> Dict[str, str]:
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "message": "All systems operational",
        "version": "0.1.0"
    }

# Basic info endpoint
@app.get("/api/v1/info")
async def get_info() -> Dict[str, Any]:
    """Get API information."""
    return {
        "name": "Orchestra API",
        "version": "0.1.0",
        "description": "AI Orchestrator and Modular Agent Framework",
        "endpoints": [
            "/",
            "/health",
            "/api/v1/info",
            "/docs",
            "/redoc"
        ]
    }

# Placeholder for agents endpoint
@app.get("/api/v1/agents")
async def list_agents() -> Dict[str, Any]:
    """List available agents (placeholder)."""
    return {
        "agents": [
            {"name": "company-enrichment", "status": "available"},
            {"name": "contact-enrichment", "status": "available"},
            {"name": "property-enrichment", "status": "available"}
        ],
        "total": 3
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
