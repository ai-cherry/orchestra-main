#!/usr/bin/env python3
"""
Orchestra AI API - Simplified Version
This version bypasses database initialization for basic testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Orchestra AI Admin API - Simplified",
    description="Simplified version for testing basic functionality",
    version="2.0.0-simple"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Orchestra AI Admin API - Simplified Version",
        "version": "2.0.0-simple",
        "status": "running"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Orchestra AI API is running",
        "version": "2.0.0-simple"
    }

@app.get("/api/status")
async def get_status():
    """Basic status endpoint"""
    import psutil
    
    return {
        "status": "operational",
        "cpu_usage": psutil.cpu_percent(),
        "memory_usage": psutil.virtual_memory().percent,
        "message": "Simplified version - database features disabled"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 