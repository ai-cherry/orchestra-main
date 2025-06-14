"""
AI Context Service - Active Context Provider
Continuously monitors and streams infrastructure context to AI agents
"""
import os
import json
import yaml
import asyncio
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import structlog
from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager
import redis.asyncio as redis
import aiofiles
import watchdog.observers
import watchdog.events

from context_loader import AIContextLoader

logger = structlog.get_logger()

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
UPDATE_INTERVAL = int(os.getenv("CONTEXT_UPDATE_INTERVAL", "30"))  # seconds
CONTEXT_CHANNEL = "ai:context:updates"

class FileChangeHandler(watchdog.events.FileSystemEventHandler):
    """Handles file system changes for context updates"""
    
    def __init__(self, context_service):
        self.context_service = context_service
    
    def on_modified(self, event):
        if not event.is_directory:
            asyncio.create_task(self.context_service.handle_file_change(event.src_path))

class AIContextService:
    """Active context service that monitors and streams updates"""
    
    def __init__(self):
        self.context_loader = AIContextLoader()
        self.redis_client = None
        self.websocket_clients: List[WebSocket] = []
        self.running = False
        self.current_context = {}
        self.file_observer = None
        
        # Monitored paths
        self.monitored_paths = [
            "Pulumi.yaml",
            "Pulumi.*.yaml",
            "docker-compose.yml",
            "requirements.txt",
            "package.json",
            "database/",
            "api/",
            "mcp_servers/"
        ]
    
    async def initialize(self):
        """Initialize the context service"""
        try:
            # Connect to Redis for pub/sub
            self.redis_client = await redis.from_url(REDIS_URL)
            await self.redis_client.ping()
            logger.info("Redis connection established for context service")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Running without pub/sub.")
        
        # Load initial context
        self.current_context = await self.load_complete_context()
        
        # Setup file monitoring
        self.setup_file_monitoring()
    
    def setup_file_monitoring(self):
        """Setup file system monitoring"""
        self.file_observer = watchdog.observers.Observer()
        handler = FileChangeHandler(self)
        
        # Monitor project root
        project_root = Path(__file__).parent.parent
        self.file_observer.schedule(handler, str(project_root), recursive=True)
        self.file_observer.start()
        logger.info("File monitoring started")
    
    async def load_complete_context(self) -> Dict[str, Any]:
        """Load complete context with real-time data"""
        base_context = self.context_loader.load_agent_context()
        
        # Add real-time infrastructure data
        base_context["real_time"] = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": await self._get_system_status(),
            "services": await self._get_service_status(),
            "lambda_labs": await self._get_lambda_status(),
            "pulumi_stack": await self._get_pulumi_stack_status(),
            "deployment": await self._get_vercel_status()
        }
        
        return base_context
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        try:
            network_connections = len(psutil.net_connections())
        except (psutil.AccessDenied, PermissionError):
            # Fallback for macOS permission issues
            network_connections = -1  # Indicate unable to determine
            
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
            "network_connections": network_connections
        }
    
    async def _get_service_status(self) -> Dict[str, Any]:
        """Check status of all services"""
        services = {}
        
        # Check API server
        services["api"] = await self._check_port(8000)
        
        # Check MCP servers
        services["mcp_memory"] = await self._check_port(8003)
        services["mcp_portkey"] = await self._check_port(8004)
        
        # Check frontend
        services["frontend"] = await self._check_port(3000)
        
        # Check databases
        services["postgresql"] = await self._check_port(5432)
        services["redis"] = await self._check_port(6379)
        
        return services
    
    async def _check_port(self, port: int) -> Dict[str, Any]:
        """Check if a service is running on a port"""
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        return {
            "port": port,
            "status": "running" if result == 0 else "stopped",
            "checked_at": datetime.utcnow().isoformat()
        }
    
    async def _get_lambda_status(self) -> Dict[str, Any]:
        """Get Lambda Labs GPU status"""
        # This would integrate with Lambda Labs API
        return {
            "gpu_available": True,
            "instance_type": "A10",
            "status": "active",
            "usage_hours": 42.5
        }
    
    async def _get_pulumi_stack_status(self) -> Dict[str, Any]:
        """Get current Pulumi stack status"""
        try:
            # Read Pulumi stack configuration
            stack_file = Path(".pulumi/stacks/development.json")
            if stack_file.exists():
                async with aiofiles.open(stack_file) as f:
                    stack_data = json.loads(await f.read())
                return {
                    "name": "development",
                    "last_update": stack_data.get("checkpoint", {}).get("latest", {}).get("time"),
                    "resources": len(stack_data.get("checkpoint", {}).get("latest", {}).get("resources", []))
                }
        except Exception as e:
            logger.error(f"Failed to read Pulumi stack: {e}")
        
        return {"status": "unknown"}
    
    async def _get_vercel_status(self) -> Dict[str, Any]:
        """Get Vercel deployment status"""
        # This would integrate with Vercel API
        return {
            "last_deployment": datetime.utcnow().isoformat(),
            "status": "ready",
            "url": "https://orchestra-ai.vercel.app"
        }
    
    async def handle_file_change(self, file_path: str):
        """Handle file system changes"""
        logger.info(f"File changed: {file_path}")
        
        # Check if it's a relevant file
        if any(pattern in file_path for pattern in self.monitored_paths):
            # Reload context
            self.current_context = await self.load_complete_context()
            
            # Broadcast update
            await self.broadcast_context_update({
                "type": "file_change",
                "file": file_path,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def broadcast_context_update(self, update: Dict[str, Any]):
        """Broadcast context update to all connected clients"""
        message = json.dumps({
            "type": "context_update",
            "data": update,
            "full_context": self.current_context
        })
        
        # Publish to Redis
        if self.redis_client:
            try:
                await self.redis_client.publish(CONTEXT_CHANNEL, message)
            except Exception as e:
                logger.error(f"Failed to publish to Redis: {e}")
        
        # Send to WebSocket clients
        disconnected = []
        for ws in self.websocket_clients:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)
        
        # Remove disconnected clients
        for ws in disconnected:
            self.websocket_clients.remove(ws)
    
    async def run_context_loop(self):
        """Main context update loop"""
        self.running = True
        logger.info("Starting context update loop")
        
        while self.running:
            try:
                # Reload context
                self.current_context = await self.load_complete_context()
                
                # Broadcast periodic update
                await self.broadcast_context_update({
                    "type": "periodic",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Export for static access
                await self.export_context()
                
            except Exception as e:
                logger.error(f"Context update error: {e}")
            
            await asyncio.sleep(UPDATE_INTERVAL)
    
    async def export_context(self):
        """Export context to file for static access"""
        cursor_dir = Path(".cursor")
        cursor_dir.mkdir(exist_ok=True)
        
        async with aiofiles.open(cursor_dir / "live_context.json", "w") as f:
            await f.write(json.dumps(self.current_context, indent=2))
    
    async def stop(self):
        """Stop the context service"""
        self.running = False
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
        if self.redis_client:
            await self.redis_client.close()

# FastAPI app for WebSocket connections
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    await context_service.initialize()
    asyncio.create_task(context_service.run_context_loop())
    yield
    await context_service.stop()

app = FastAPI(title="AI Context Service", lifespan=lifespan)
context_service = AIContextService()

@app.websocket("/ws/context")
async def websocket_context(websocket: WebSocket):
    """WebSocket endpoint for real-time context updates"""
    await websocket.accept()
    context_service.websocket_clients.append(websocket)
    
    # Send initial context
    await websocket.send_json({
        "type": "initial",
        "data": context_service.current_context
    })
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except Exception:
        context_service.websocket_clients.remove(websocket)

@app.get("/context")
async def get_context():
    """Get current context snapshot"""
    return context_service.current_context

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "running": context_service.running,
        "websocket_clients": len(context_service.websocket_clients),
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005) 