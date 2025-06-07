"""
Resource management and limits for AI agents
Prevents resource exhaustion and handles overflow
"""

import asyncio
import psutil
import os
from typing import Dict, Optional, Any
from datetime import datetime
import logging
from collections import deque
import resource

logger = logging.getLogger(__name__)

class ResourceManager:
    """Manages resource allocation and limits for AI agents"""
    
    def __init__(self):
        self.max_concurrent_agents = int(os.getenv("MAX_CONCURRENT_AGENTS", "50"))
        self.agent_memory_limit_mb = int(os.getenv("AGENT_MEMORY_LIMIT_MB", "512"))
        self.active_agents = {}
        self.agent_queue = asyncio.Queue(maxsize=200)  # Overflow queue
        self.metrics = {
            "total_agents_created": 0,
            "agents_rejected": 0,
            "memory_limit_hits": 0,
            "queue_overflows": 0
        }
        
    async def acquire_agent_slot(self, agent_id: str) -> bool:
        """Try to acquire a slot for a new agent"""
        if len(self.active_agents) >= self.max_concurrent_agents:
            # Try to queue the agent
            try:
                await asyncio.wait_for(
                    self.agent_queue.put(agent_id),
                    timeout=5.0
                )
                logger.warning(f"Agent {agent_id} queued due to concurrency limit")
                self.metrics["queue_overflows"] += 1
                return False
            except asyncio.TimeoutError:
                logger.error(f"Agent {agent_id} rejected - queue full")
                self.metrics["agents_rejected"] += 1
                raise RuntimeError("Agent queue full - system overloaded")
                
        self.active_agents[agent_id] = {
            "start_time": datetime.now(),
            "memory_usage": 0
        }
        self.metrics["total_agents_created"] += 1
        return True
        
    def release_agent_slot(self, agent_id: str):
        """Release an agent slot"""
        if agent_id in self.active_agents:
            del self.active_agents[agent_id]
            
        # Check if any queued agents can now run
        if not self.agent_queue.empty():
            asyncio.create_task(self._process_queue())
            
    async def _process_queue(self):
        """Process queued agents"""
        while not self.agent_queue.empty() and len(self.active_agents) < self.max_concurrent_agents:
            try:
                agent_id = await self.agent_queue.get()
                await self.acquire_agent_slot(agent_id)
            except Exception as e:
                logger.error(f"Error processing agent queue: {e}")
                
    def check_memory_limit(self, agent_id: str) -> bool:
        """Check if agent is within memory limits"""
        try:
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if agent_id in self.active_agents:
                self.active_agents[agent_id]["memory_usage"] = memory_mb
                
            if memory_mb > self.agent_memory_limit_mb:
                logger.error(f"Agent {agent_id} exceeded memory limit: {memory_mb}MB")
                self.metrics["memory_limit_hits"] += 1
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking memory limit: {e}")
            return True
            
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        return {
            "active_agents": len(self.active_agents),
            "queued_agents": self.agent_queue.qsize(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "metrics": self.metrics,
            "health_status": self._calculate_health_status(cpu_percent, memory.percent)
        }
        
    def _calculate_health_status(self, cpu: float, memory: float) -> str:
        """Calculate overall system health"""
        if cpu > 90 or memory > 90:
            return "CRITICAL"
        elif cpu > 70 or memory > 70:
            return "WARNING"
        else:
            return "HEALTHY"

# Global resource manager instance
resource_manager = ResourceManager()

class ResourceLimitedAgent:
    """Base class for resource-limited agents"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.resource_manager = resource_manager
        
    async def __aenter__(self):
        """Acquire resources on entry"""
        success = await self.resource_manager.acquire_agent_slot(self.agent_id)
        if not success:
            raise RuntimeError("Unable to acquire agent slot")
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release resources on exit"""
        self.resource_manager.release_agent_slot(self.agent_id)
        
    async def execute_with_limits(self, func, *args, **kwargs):
        """Execute function with resource limits"""
        # Check memory before execution
        if not self.resource_manager.check_memory_limit(self.agent_id):
            raise MemoryError("Agent memory limit exceeded")
            
        # Set process limits
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, 
                         (self.resource_manager.agent_memory_limit_mb * 1024 * 1024, hard))
        
        try:
            return await func(*args, **kwargs)
        finally:
            # Reset limits
            resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
