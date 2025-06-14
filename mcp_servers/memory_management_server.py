"""
MCP Memory Management Server
Provides memory storage and retrieval for AI agents
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from fastapi import HTTPException
from pydantic import BaseModel
import uvicorn

from base_mcp_server import BaseMCPServer, MCP_PORT_ALLOCATION


class MemoryEntry(BaseModel):
    """Memory entry model"""
    key: str
    value: Any
    metadata: Optional[Dict[str, Any]] = {}
    timestamp: Optional[str] = None
    ttl: Optional[int] = None  # Time to live in seconds


class MemoryQuery(BaseModel):
    """Memory query model"""
    keys: Optional[List[str]] = None
    pattern: Optional[str] = None
    metadata_filter: Optional[Dict[str, Any]] = None


class MemoryManagementServer(BaseMCPServer):
    """
    MCP Server for managing AI agent memory
    """
    
    def __init__(self):
        super().__init__(
            port=MCP_PORT_ALLOCATION.get("memory", 8003),
            name="memory",
            capabilities=[
                "memory_storage",
                "memory_retrieval", 
                "memory_search",
                "memory_analytics"
            ],
            environment="development"
        )
        self.memory_store: Dict[str, MemoryEntry] = {}
        self.access_log: List[Dict[str, Any]] = []
    
    async def initialize_resources(self):
        """Initialize memory management resources"""
        self.logger.info("Initializing memory management server")
        
        # Load persistent memory if exists
        try:
            with open("memory_store.json", "r") as f:
                stored_memories = json.load(f)
                for key, data in stored_memories.items():
                    self.memory_store[key] = MemoryEntry(**data)
                self.logger.info(f"Loaded {len(self.memory_store)} memories")
        except FileNotFoundError:
            self.logger.info("No persistent memory found, starting fresh")
        except Exception as e:
            self.logger.error(f"Failed to load memory: {e}")
    
    def get_custom_endpoints(self):
        """Define memory management endpoints"""
        
        @self.app.post("/memory/store")
        async def store_memory(entry: MemoryEntry):
            """Store a memory entry"""
            try:
                # Add timestamp if not provided
                if not entry.timestamp:
                    entry.timestamp = datetime.utcnow().isoformat()
                
                # Store in memory
                self.memory_store[entry.key] = entry
                
                # Log access
                self.access_log.append({
                    "action": "store",
                    "key": entry.key,
                    "timestamp": entry.timestamp
                })
                
                # Increment metrics
                self.request_count.labels(
                    method="POST",
                    endpoint="/memory/store",
                    status="success"
                ).inc()
                
                return {
                    "status": "success",
                    "key": entry.key,
                    "timestamp": entry.timestamp
                }
            except Exception as e:
                self.logger.error(f"Memory store error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/memory/retrieve")
        async def retrieve_memory(query: MemoryQuery):
            """Retrieve memory entries"""
            try:
                results = []
                
                # Filter by keys if provided
                if query.keys:
                    for key in query.keys:
                        if key in self.memory_store:
                            results.append(self.memory_store[key].dict())
                
                # Filter by pattern if provided
                elif query.pattern:
                    import re
                    pattern = re.compile(query.pattern)
                    for key, entry in self.memory_store.items():
                        if pattern.match(key):
                            results.append(entry.dict())
                
                # Return all if no filters
                else:
                    results = [entry.dict() for entry in self.memory_store.values()]
                
                # Apply metadata filter if provided
                if query.metadata_filter and results:
                    filtered = []
                    for result in results:
                        match = all(
                            result.get("metadata", {}).get(k) == v
                            for k, v in query.metadata_filter.items()
                        )
                        if match:
                            filtered.append(result)
                    results = filtered
                
                # Log access
                self.access_log.append({
                    "action": "retrieve",
                    "query": query.dict(),
                    "results": len(results),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "status": "success",
                    "count": len(results),
                    "memories": results
                }
            except Exception as e:
                self.logger.error(f"Memory retrieve error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/memory/clear")
        async def clear_memory(keys: Optional[List[str]] = None):
            """Clear memory entries"""
            try:
                if keys:
                    # Clear specific keys
                    cleared = []
                    for key in keys:
                        if key in self.memory_store:
                            del self.memory_store[key]
                            cleared.append(key)
                    message = f"Cleared {len(cleared)} entries"
                else:
                    # Clear all
                    count = len(self.memory_store)
                    self.memory_store.clear()
                    message = f"Cleared all {count} entries"
                
                # Log action
                self.access_log.append({
                    "action": "clear",
                    "keys": keys,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return {
                    "status": "success",
                    "message": message
                }
            except Exception as e:
                self.logger.error(f"Memory clear error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/memory/stats")
        async def memory_stats():
            """Get memory statistics"""
            try:
                # Calculate stats
                total_entries = len(self.memory_store)
                total_size = sum(
                    len(json.dumps(entry.dict()))
                    for entry in self.memory_store.values()
                )
                
                # Get access patterns
                recent_accesses = self.access_log[-10:]
                
                return {
                    "total_entries": total_entries,
                    "total_size_bytes": total_size,
                    "recent_accesses": recent_accesses,
                    "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds()
                }
            except Exception as e:
                self.logger.error(f"Memory stats error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/memory/persist")
        async def persist_memory():
            """Persist memory to disk"""
            try:
                # Convert to serializable format
                serializable = {
                    key: entry.dict()
                    for key, entry in self.memory_store.items()
                }
                
                # Save to file
                with open("memory_store.json", "w") as f:
                    json.dump(serializable, f, indent=2)
                
                return {
                    "status": "success",
                    "message": f"Persisted {len(self.memory_store)} entries"
                }
            except Exception as e:
                self.logger.error(f"Memory persist error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def cleanup_resources(self):
        """Cleanup and persist memory on shutdown"""
        self.logger.info("Shutting down memory management server")
        
        # Persist memory
        try:
            serializable = {
                key: entry.dict()
                for key, entry in self.memory_store.items()
            }
            with open("memory_store.json", "w") as f:
                json.dump(serializable, f, indent=2)
            self.logger.info(f"Persisted {len(self.memory_store)} memories")
        except Exception as e:
            self.logger.error(f"Failed to persist memory: {e}")
    
    async def _custom_startup(self):
        """Custom startup logic"""
        pass
    
    async def _custom_shutdown(self):
        """Custom shutdown logic"""
        pass
    
    def _setup_custom_routes(self):
        """Setup custom routes - implemented via get_custom_endpoints"""
        pass
    
    async def _check_custom_connections(self) -> Dict[str, bool]:
        """Check custom service connections"""
        return {}
    
    def _get_health_metrics(self) -> Dict[str, Any]:
        """Get custom health metrics"""
        return {
            "memory_entries": len(self.memory_store),
            "access_log_size": len(self.access_log)
        }


if __name__ == "__main__":
    server = MemoryManagementServer()
    asyncio.run(server.start_server()) 