#!/usr/bin/env python3
"""
Service Management Consolidation Script

This script consolidates service management logic from various parts of the codebase
into a unified service management framework. It aims to standardize service
registration, discovery, and lifecycle management.

Key improvements:
- Centralized service registry (PostgreSQL + Weaviate)
- Standardized service health checks
- Unified configuration management
- Simplified service discovery mechanism
- Improved error handling and resilience
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

# Add parent directory to path for imports
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from shared.database import initialize_database, UnifiedDatabase
from core.config import ServiceConfig, get_service_config

logger = logging.getLogger(__name__)

# --- Constants ---
SERVICE_REGISTRY_TABLE = "orchestra_services"
SERVICE_HEALTH_COLLECTION = "service_health_checks"
DEFAULT_SERVICE_TTL_SECONDS = 300  # 5 minutes

# --- Enums ---
class ServiceStatus(str, Enum):
    """Represents the operational status of a service."""
    UNKNOWN = "UNKNOWN"
    STARTING = "STARTING"
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"
    DEGRADED = "DEGRADED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"

class ServiceLifecycleEvent(str, Enum):
    """Represents events in a service's lifecycle."""
    REGISTERED = "REGISTERED"
    HEALTH_CHECK_PASSED = "HEALTH_CHECK_PASSED"
    HEALTH_CHECK_FAILED = "HEALTH_CHECK_FAILED"
    UPDATED = "UPDATED"
    DEREGISTERED = "DEREGISTERED"
    HEARTBEAT_RECEIVED = "HEARTBEAT_RECEIVED"

# --- Data Models ---
class ServiceInstance(BaseModel):
    """Represents a registered service instance."""
    service_id: str = Field(default_factory=lambda: str(uuid4()))
    service_name: str
    service_type: str # e.g., "mcp_server", "ai_tool", "database"
    version: str
    endpoint: str
    status: ServiceStatus = ServiceStatus.UNKNOWN
    metadata: Dict[str, Any] = Field(default_factory=dict)
    last_heartbeat_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_seconds: int = DEFAULT_SERVICE_TTL_SECONDS

class ServiceHealthCheck(BaseModel):
    """Represents a health check result for a service."""
    check_id: str = Field(default_factory=lambda: str(uuid4()))
    service_id: str
    service_name: str
    status: ServiceStatus
    details: Dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# --- Service Management Class ---
class UnifiedServiceManager:
    """
    Manages service registration, discovery, and health monitoring.
    Leverages UnifiedDatabase for persistence.
    """

    def __init__(self, db: UnifiedDatabase):
        self.db = db
        self.service_cache: Dict[str, ServiceInstance] = {}
        self.last_cache_refresh: Optional[datetime] = None
        self.cache_ttl_seconds = 60  # Cache services for 60 seconds

    async def initialize(self):
        """Initialize the service manager and database schema."""
        await self._setup_service_registry_schema()
        await self._refresh_service_cache()
        logger.info("Unified Service Manager initialized.")

    async def _setup_service_registry_schema(self):
        """Create necessary database tables and collections if they don't exist."""
        # PostgreSQL schema for service registry
        await self.db.execute_query(f"""
            CREATE TABLE IF NOT EXISTS {SERVICE_REGISTRY_TABLE} (
                service_id VARCHAR(36) PRIMARY KEY,
                service_name VARCHAR(255) NOT NULL,
                service_type VARCHAR(100) NOT NULL,
                version VARCHAR(50),
                endpoint VARCHAR(512) NOT NULL,
                status VARCHAR(50) NOT NULL,
                metadata JSONB,
                last_heartbeat_at TIMESTAMPTZ NOT NULL,
                registered_at TIMESTAMPTZ NOT NULL,
                ttl_seconds INTEGER NOT NULL,
                expires_at TIMESTAMPTZ GENERATED ALWAYS AS (last_heartbeat_at + (ttl_seconds * INTERVAL '1 second')) STORED
            );
        """, fetch=False)
        await self.db.execute_query(f"CREATE INDEX IF NOT EXISTS idx_service_name ON {SERVICE_REGISTRY_TABLE}(service_name);", fetch=False)
        await self.db.execute_query(f"CREATE INDEX IF NOT EXISTS idx_service_type ON {SERVICE_REGISTRY_TABLE}(service_type);", fetch=False)
        await self.db.execute_query(f"CREATE INDEX IF NOT EXISTS idx_service_status ON {SERVICE_REGISTRY_TABLE}(status);", fetch=False)
        await self.db.execute_query(f"CREATE INDEX IF NOT EXISTS idx_service_expires_at ON {SERVICE_REGISTRY_TABLE}(expires_at);", fetch=False)

        # Weaviate schema for health checks (optional, can also store in PostgreSQL)
        # For this example, we'll assume Weaviate is used for more complex log/event analysis
        client = self.db.get_weaviate_client()
        if client:
            class_obj = {
                "class": SERVICE_HEALTH_COLLECTION,
                "description": "Stores service health check records.",
                "properties": [
                    {"name": "check_id", "dataType": ["string"]},
                    {"name": "service_id", "dataType": ["string"]},
                    {"name": "service_name", "dataType": ["string"]},
                    {"name": "status", "dataType": ["string"]},
                    {"name": "details_json", "dataType": ["text"]}, # Store details as JSON string
                    {"name": "checked_at_unix", "dataType": ["int"]}
                ]
            }
            try:
                if not client.schema.exists(SERVICE_HEALTH_COLLECTION):
                    client.schema.create_class(class_obj)
                    logger.info(f"Weaviate class '{SERVICE_HEALTH_COLLECTION}' created.")
            except Exception as e:
                logger.warning(f"Could not create Weaviate class '{SERVICE_HEALTH_COLLECTION}': {e}")

    async def _refresh_service_cache(self, force_refresh: bool = False):
        """Refresh the local service cache from the database."""
        now = datetime.now(timezone.utc)
        if not force_refresh and self.last_cache_refresh and \
           (now - self.last_cache_refresh).total_seconds() < self.cache_ttl_seconds:
            return

        logger.debug("Refreshing service cache...")
        rows = await self.db.execute_query(f"""
            SELECT service_id, service_name, service_type, version, endpoint, status, metadata, last_heartbeat_at, registered_at, ttl_seconds
            FROM {SERVICE_REGISTRY_TABLE} WHERE expires_at > NOW()
        """)
        self.service_cache = {}
        for row in rows:
            self.service_cache[row['service_id']] = ServiceInstance(**row)
        self.last_cache_refresh = now
        logger.debug(f"Service cache refreshed with {len(self.service_cache)} active services.")

    async def register_service(self, service_instance: ServiceInstance) -> ServiceInstance:
        """Register a new service instance or update an existing one."""
        await self.db.execute_query(f"""
            INSERT INTO {SERVICE_REGISTRY_TABLE} 
            (service_id, service_name, service_type, version, endpoint, status, metadata, last_heartbeat_at, registered_at, ttl_seconds)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (service_id) DO UPDATE SET
                service_name = EXCLUDED.service_name,
                service_type = EXCLUDED.service_type,
                version = EXCLUDED.version,
                endpoint = EXCLUDED.endpoint,
                status = EXCLUDED.status,
                metadata = EXCLUDED.metadata,
                last_heartbeat_at = EXCLUDED.last_heartbeat_at,
                ttl_seconds = EXCLUDED.ttl_seconds
        """, params=[
            service_instance.service_id,
            service_instance.service_name,
            service_instance.service_type,
            service_instance.version,
            service_instance.endpoint,
            service_instance.status.value,
            json.dumps(service_instance.metadata),
            service_instance.last_heartbeat_at,
            service_instance.registered_at,
            service_instance.ttl_seconds
        ], fetch=False)
        await self._refresh_service_cache(force_refresh=True)
        logger.info(f"Service '{service_instance.service_name}' (ID: {service_instance.service_id}) registered/updated.")
        await self._log_lifecycle_event(service_instance.service_id, ServiceLifecycleEvent.REGISTERED, {"endpoint": service_instance.endpoint})
        return service_instance

    async def deregister_service(self, service_id: str) -> bool:
        """Deregister a service instance."""
        await self.db.execute_query(f"DELETE FROM {SERVICE_REGISTRY_TABLE} WHERE service_id = $1", params=[service_id], fetch=False)
        if service_id in self.service_cache:
            del self.service_cache[service_id]
        logger.info(f"Service (ID: {service_id}) deregistered.")
        await self._log_lifecycle_event(service_id, ServiceLifecycleEvent.DEREGISTERED)
        return True

    async def send_heartbeat(self, service_id: str, status: ServiceStatus = ServiceStatus.HEALTHY, metadata_update: Optional[Dict] = None) -> bool:
        """Update a service's heartbeat and status."""
        params = [
            datetime.now(timezone.utc),
            status.value,
            service_id
        ]
        query = f"UPDATE {SERVICE_REGISTRY_TABLE} SET last_heartbeat_at = $1, status = $2"
        if metadata_update:
            query += ", metadata = metadata || $4"
            params.append(json.dumps(metadata_update))
        query += " WHERE service_id = $3 RETURNING service_id;"
        
        result = await self.db.execute_query(query, params=params, fetch=True)
        if result and result[0]['service_id'] == service_id:
            if service_id in self.service_cache:
                self.service_cache[service_id].last_heartbeat_at = params[0]
                self.service_cache[service_id].status = status
                if metadata_update:
                    self.service_cache[service_id].metadata.update(metadata_update)
            logger.debug(f"Heartbeat received for service ID: {service_id}, status: {status.value}")
            await self._log_lifecycle_event(service_id, ServiceLifecycleEvent.HEARTBEAT_RECEIVED, {"status": status.value})
            return True
        logger.warning(f"Failed to update heartbeat for service ID: {service_id}")
        return False

    async def find_service(self, service_name: Optional[str] = None, service_type: Optional[str] = None, status: ServiceStatus = ServiceStatus.HEALTHY) -> Optional[ServiceInstance]:
        """Find a single healthy instance of a service. Implements basic round-robin."""
        instances = await self.find_services(service_name, service_type, status)
        if not instances:
            return None
        # Basic round-robin for now, could be enhanced with smarter load balancing
        return instances[0]

    async def find_services(self, service_name: Optional[str] = None, service_type: Optional[str] = None, status: Optional[ServiceStatus] = ServiceStatus.HEALTHY) -> List[ServiceInstance]:
        """Find all instances of a service matching criteria."""
        await self._refresh_service_cache()
        
        filtered_services = list(self.service_cache.values())

        if service_name:
            filtered_services = [s for s in filtered_services if s.service_name == service_name]
        if service_type:
            filtered_services = [s for s in filtered_services if s.service_type == service_type]
        if status:
            filtered_services = [s for s in filtered_services if s.status == status]
        
        # Ensure they haven't expired according to their TTL (even if DB query includes this)
        now = datetime.now(timezone.utc)
        valid_services = [s for s in filtered_services if (s.last_heartbeat_at + timedelta(seconds=s.ttl_seconds)) > now]
        
        return sorted(valid_services, key=lambda s: s.registered_at) # Return oldest first for round-robin

    async def record_health_check(self, health_check_data: ServiceHealthCheck):
        """Record a health check result."""
        # Update service status based on health check
        await self.send_heartbeat(health_check_data.service_id, health_check_data.status, health_check_data.details)

        # Store detailed health check in Weaviate
        client = self.db.get_weaviate_client()
        if client:
            properties = {
                "check_id": health_check_data.check_id,
                "service_id": health_check_data.service_id,
                "service_name": health_check_data.service_name,
                "status": health_check_data.status.value,
                "details_json": json.dumps(health_check_data.details),
                "checked_at_unix": int(health_check_data.checked_at.timestamp())
            }
            try:
                client.data_object.create(
                    data_object=properties,
                    class_name=SERVICE_HEALTH_COLLECTION,
                    uuid=health_check_data.check_id
                )
                logger.debug(f"Health check {health_check_data.check_id} for {health_check_data.service_name} stored in Weaviate.")
            except Exception as e:
                logger.error(f"Failed to store health check in Weaviate: {e}")
        else:
            logger.warning("Weaviate client not available. Health check details not stored in vector store.")
        
        event = ServiceLifecycleEvent.HEALTH_CHECK_PASSED if health_check_data.status == ServiceStatus.HEALTHY else ServiceLifecycleEvent.HEALTH_CHECK_FAILED
        await self._log_lifecycle_event(health_check_data.service_id, event, health_check_data.details)

    async def get_service_health_history(self, service_id: str, limit: int = 10) -> List[ServiceHealthCheck]:
        """Get recent health check history for a service (from Weaviate)."""
        client = self.db.get_weaviate_client()
        if not client:
            logger.warning("Weaviate client not available for health history.")
            return []
        
        try:
            result = (
                client.query
                .get(SERVICE_HEALTH_COLLECTION, ["check_id", "service_id", "service_name", "status", "details_json", "checked_at_unix"])
                .with_where({
                    "path": ["service_id"],
                    "operator": "Equal",
                    "valueString": service_id
                })
                .with_sort([{"path": ["checked_at_unix"], "order": "desc"}])
                .with_limit(limit)
                .do()
            )
            
            history = []
            if result and "data" in result and "Get" in result["data"] and SERVICE_HEALTH_COLLECTION in result["data"]["Get"]:
                for obj in result["data"]["Get"][SERVICE_HEALTH_COLLECTION]:
                    history.append(ServiceHealthCheck(
                        check_id=obj["check_id"],
                        service_id=obj["service_id"],
                        service_name=obj["service_name"],
                        status=ServiceStatus(obj["status"]),
                        details=json.loads(obj["details_json"]),
                        checked_at=datetime.fromtimestamp(obj["checked_at_unix"], timezone.utc)
                    ))
            return history
        except Exception as e:
            logger.error(f"Failed to get service health history for {service_id}: {e}")
            return []

    async def cleanup_expired_services(self) -> int:
        """Remove services whose TTL has expired."""
        query = f"DELETE FROM {SERVICE_REGISTRY_TABLE} WHERE expires_at <= NOW() RETURNING service_id"
        expired_services = await self.db.execute_query(query, fetch=True)
        count = len(expired_services)
        if count > 0:
            expired_ids = [row['service_id'] for row in expired_services]
            logger.info(f"Cleaned up {count} expired services: {expired_ids}")
            for service_id in expired_ids:
                if service_id in self.service_cache:
                    del self.service_cache[service_id]
                await self._log_lifecycle_event(service_id, ServiceLifecycleEvent.DEREGISTERED, {"reason": "TTL expired"})
        return count

    async def _log_lifecycle_event(self, service_id: str, event: ServiceLifecycleEvent, data: Optional[Dict] = None):
        """Log a service lifecycle event (e.g., to an audit log or event stream)."""
        # This is a placeholder for actual event logging. 
        # Could write to a dedicated log, a message queue, or another table.
        log_message = f"ServiceLifecycleEvent: service_id={service_id}, event={event.value}, data={data or {}}"
        logger.info(log_message)
        # Example: await self.db.execute_query("INSERT INTO service_lifecycle_logs ...")

# --- Helper Functions and Main Execution ---
async def run_service_cleanup_job(service_manager: UnifiedServiceManager):
    """Periodically run service cleanup tasks."""
    while True:
        try:
            logger.info("Running periodic service cleanup...")
            cleaned_count = await service_manager.cleanup_expired_services()
            logger.info(f"Service cleanup job: {cleaned_count} services removed.")
        except Exception as e:
            logger.error(f"Error in service cleanup job: {e}")
        await asyncio.sleep(3600) # Run every hour

async def main():
    """Demonstrate usage of the UnifiedServiceManager."""
    # Setup basic logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    
    # Ensure environment variables are set (POSTGRES_URL, etc.)
    # Example: os.environ["POSTGRES_URL"] = "postgresql://user:pass@host:port/db"
    
    if not os.getenv("POSTGRES_URL"):
        logger.error("POSTGRES_URL environment variable not set. Exiting.")
        return

    db = await initialize_database(postgres_url=os.environ["POSTGRES_URL"]) 
    service_manager = UnifiedServiceManager(db)
    
    try:
        await service_manager.initialize()

        # Start cleanup job in background
        asyncio.create_task(run_service_cleanup_job(service_manager))

        # Example: Register a service
        test_service = ServiceInstance(
            service_name="test_mcp_server",
            service_type="mcp_server",
            version="1.0.0",
            endpoint="http://localhost:8001",
            status=ServiceStatus.HEALTHY,
            metadata={"region": "us-west-1", "environment": "dev"}
        )
        await service_manager.register_service(test_service)

        # Example: Find the service
        found_service = await service_manager.find_service(service_name="test_mcp_server")
        if found_service:
            logger.info(f"Found service: {found_service.service_name} at {found_service.endpoint}")

        # Example: Send heartbeat
        await service_manager.send_heartbeat(test_service.service_id)

        # Example: Record health check
        health_data = ServiceHealthCheck(
            service_id=test_service.service_id,
            service_name=test_service.service_name,
            status=ServiceStatus.DEGRADED,
            details={"cpu_load": 0.85, "reason": "High CPU usage"}
        )
        await service_manager.record_health_check(health_data)
        
        health_history = await service_manager.get_service_health_history(test_service.service_id)
        logger.info(f"Health history for {test_service.service_name}: {health_history}")

        # Simulate waiting for a while to let cleanup run if there were expired services
        # In a real app, this would be part of a long-running process or scheduled task
        # await asyncio.sleep(3605) 

    except Exception as e:
        logger.error(f"Error in main demonstration: {e}")
    finally:
        # Clean up
        if hasattr(service_manager, 'db') and service_manager.db._initialized:
            await service_manager.deregister_service(test_service.service_id) # Clean up test service
            await service_manager.db.close()
        logger.info("Demonstration finished.")

if __name__ == "__main__":
    # This main function is for demonstration; real service management would be part of the application lifecycle.
    asyncio.run(main())
