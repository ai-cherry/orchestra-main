"""
Orchestra AI - Health Monitoring API
Real-time health monitoring for all services and APIs
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import asyncio
import time
import psutil
import requests
from datetime import datetime, timedelta
import json

# Import enhanced secret manager
from security.enhanced_secret_manager import secret_manager, validate_api_health

router = APIRouter(prefix="/api/health", tags=["health"])

class HealthMonitor:
    """Comprehensive health monitoring for Orchestra AI"""
    
    def __init__(self):
        self.last_check = None
        self.cached_results = {}
        self.cache_duration = 30  # seconds
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        
        # Check if we have recent cached results
        if (self.last_check and 
            time.time() - self.last_check < self.cache_duration and 
            self.cached_results):
            return self.cached_results
        
        health_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "services": {},
            "apis": {},
            "system": {},
            "secrets": {}
        }
        
        # Check system resources
        health_data["system"] = await self._check_system_resources()
        
        # Check API connections
        health_data["apis"] = await self._check_api_health()
        
        # Check services
        health_data["services"] = await self._check_services()
        
        # Check secrets availability
        health_data["secrets"] = await self._check_secrets()
        
        # Determine overall status
        health_data["overall_status"] = self._determine_overall_status(health_data)
        
        # Cache results
        self.cached_results = health_data
        self.last_check = time.time()
        
        return health_data
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy",
                "cpu": {
                    "usage_percent": cpu_percent,
                    "status": "healthy" if cpu_percent < 80 else "warning" if cpu_percent < 95 else "critical"
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "usage_percent": memory.percent,
                    "status": "healthy" if memory.percent < 80 else "warning" if memory.percent < 95 else "critical"
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "usage_percent": round((disk.used / disk.total) * 100, 2),
                    "status": "healthy" if (disk.used / disk.total) < 0.8 else "warning" if (disk.used / disk.total) < 0.95 else "critical"
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_api_health(self) -> Dict[str, Any]:
        """Check all API connections"""
        try:
            api_results = validate_api_health()
            
            # Add additional API checks
            api_results["orchestra_api"] = await self._check_orchestra_api()
            api_results["mcp_server"] = await self._check_mcp_server()
            
            return api_results
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    async def _check_orchestra_api(self) -> Dict[str, Any]:
        """Check Orchestra AI main API"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            return {
                "status": "healthy" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response_time": None
            }
    
    async def _check_mcp_server(self) -> Dict[str, Any]:
        """Check MCP server status"""
        try:
            response = requests.get("http://localhost:8003/health", timeout=5)
            return {
                "status": "healthy" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response_time": None
            }
    
    async def _check_services(self) -> Dict[str, Any]:
        """Check running services"""
        services = {
            "fastapi": self._check_process("uvicorn"),
            "mcp_server": self._check_process("main_mcp.py"),
            "redis": self._check_process("redis-server"),
            "postgresql": self._check_process("postgres")
        }
        
        return services
    
    def _check_process(self, process_name: str) -> Dict[str, Any]:
        """Check if a specific process is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if process_name.lower() in ' '.join(proc.info['cmdline'] or []).lower():
                    return {
                        "status": "running",
                        "pid": proc.info['pid'],
                        "name": proc.info['name']
                    }
            
            return {
                "status": "not_running",
                "pid": None,
                "name": process_name
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_secrets(self) -> Dict[str, Any]:
        """Check secrets availability"""
        try:
            validation_results = secret_manager.validate_all_secrets()
            secrets_for_ai = secret_manager.get_all_secrets_for_ai_agents()
            
            return {
                "validation": validation_results,
                "available_count": sum(1 for v in validation_results.values() if v),
                "total_count": len(validation_results),
                "ai_accessible": secrets_for_ai,
                "status": "healthy" if all(validation_results.values()) else "warning"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _determine_overall_status(self, health_data: Dict[str, Any]) -> str:
        """Determine overall system status"""
        statuses = []
        
        # Check system resources
        if health_data.get("system", {}).get("status") == "error":
            return "critical"
        
        # Check API health
        api_statuses = []
        for api_name, api_data in health_data.get("apis", {}).items():
            if isinstance(api_data, dict) and "status" in api_data:
                api_statuses.append(api_data["status"])
        
        if "error" in api_statuses:
            statuses.append("warning")
        
        # Check services
        service_statuses = []
        for service_name, service_data in health_data.get("services", {}).items():
            if isinstance(service_data, dict) and "status" in service_data:
                service_statuses.append(service_data["status"])
        
        if "error" in service_statuses or "not_running" in service_statuses:
            statuses.append("warning")
        
        # Check secrets
        secrets_status = health_data.get("secrets", {}).get("status", "healthy")
        if secrets_status == "error":
            statuses.append("critical")
        elif secrets_status == "warning":
            statuses.append("warning")
        
        # Determine final status
        if "critical" in statuses:
            return "critical"
        elif "warning" in statuses:
            return "warning"
        else:
            return "healthy"

# Global health monitor instance
health_monitor = HealthMonitor()

@router.get("/")
async def get_health():
    """Get comprehensive health status"""
    try:
        health_data = await health_monitor.get_system_health()
        return health_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quick")
async def get_quick_health():
    """Get quick health check (no caching)"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": time.time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/apis")
async def get_api_health():
    """Get API health status only"""
    try:
        api_health = validate_api_health()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "apis": api_health
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/secrets")
async def get_secrets_status():
    """Get secrets availability status"""
    try:
        validation_results = secret_manager.validate_all_secrets()
        secrets_for_ai = secret_manager.get_all_secrets_for_ai_agents()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "validation": validation_results,
            "available_count": sum(1 for v in validation_results.values() if v),
            "total_count": len(validation_results),
            "ai_accessible": secrets_for_ai
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system")
async def get_system_resources():
    """Get system resource usage"""
    try:
        health_data = await health_monitor._check_system_resources()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": health_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

