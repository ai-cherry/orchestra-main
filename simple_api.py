# Simple Orchestra AI Backend for Testing
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
import psutil
from datetime import datetime

app = FastAPI(
    title="Orchestra AI Simple Backend",
    description="Simplified backend for testing containerized deployment",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

start_time = time.time()

@app.get("/")
async def root():
    return {
        "message": "Orchestra AI Simple Backend", 
        "status": "operational", 
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "orchestra-simple-api",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/system/status")
async def get_system_status():
    """Get basic system metrics"""
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    uptime = (time.time() - start_time) / 3600  # hours
    
    return {
        "active_agents": 3,
        "api_requests_per_minute": 45,
        "memory_usage_percent": memory.percent,
        "cpu_usage_percent": cpu_percent,
        "success_rate": 98.5,
        "uptime_hours": uptime,
        "disk_usage_percent": 45.2,
        "network_io": {
            "bytes_sent": 1024000.0,
            "bytes_recv": 2048000.0
        },
        "database_status": "healthy",
        "vector_store_status": "healthy",
        "file_processing_queue": 0,
        "total_files_processed": 42
    }

@app.get("/api/agents")
async def get_agents():
    """Get agent status"""
    return [
        {
            "id": "agent-001",
            "name": "Customer Support Agent",
            "status": "active",
            "requests_count": 247,
            "success_rate": 98.5,
            "avg_response_time": 1.2,
            "last_activity": datetime.now().isoformat(),
            "memory_usage": 45.2,
            "cpu_usage": 12.3
        },
        {
            "id": "agent-002", 
            "name": "Data Analysis Agent",
            "status": "active",
            "requests_count": 89,
            "success_rate": 94.1,
            "avg_response_time": 3.7,
            "last_activity": datetime.now().isoformat(),
            "memory_usage": 67.8,
            "cpu_usage": 23.1
        },
        {
            "id": "agent-003",
            "name": "Content Generator",
            "status": "idle", 
            "requests_count": 12,
            "success_rate": 100.0,
            "avg_response_time": 5.1,
            "last_activity": datetime.now().isoformat(),
            "memory_usage": 23.4,
            "cpu_usage": 2.1
        }
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

