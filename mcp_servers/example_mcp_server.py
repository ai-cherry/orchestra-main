"""
Example MCP Server Implementation
Shows how to use the base MCP server template
"""

import asyncio
from typing import Dict, List, Any
from datetime import datetime

import psycopg2
import weaviate
from fastapi import HTTPException
import uvicorn

from base_mcp_server import BaseMCPServer, MCP_PORT_ALLOCATION


class ExampleMCPServer(BaseMCPServer):
    """
    Example implementation of an MCP server
    This server demonstrates database connections and custom endpoints
    """
    
    def __init__(self):
        super().__init__(
            port=MCP_PORT_ALLOCATION.get("example", 8020),
            name="example",
            capabilities=[
                "data_processing",
                "analytics",
                "reporting"
            ],
            environment="development"
        )
        
        # Custom connections
        self.postgres_conn = None
        self.weaviate_client = None
        
    def _setup_custom_routes(self):
        """Setup server-specific routes"""
        
        @self.app.post("/process")
        async def process_data(data: dict) -> dict:
            """Process incoming data"""
            try:
                # Example processing logic
                result = await self._process_data(data)
                return {"status": "success", "result": result}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/analytics/{metric}")
        async def get_analytics(metric: str) -> dict:
            """Get analytics for a specific metric"""
            try:
                analytics = await self._calculate_analytics(metric)
                return {"metric": metric, "analytics": analytics}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/report/{report_type}")
        async def generate_report(report_type: str) -> dict:
            """Generate a report"""
            try:
                report = await self._generate_report(report_type)
                return {"report_type": report_type, "report": report}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _custom_startup(self) -> None:
        """Custom startup logic for specific server"""
        # Initialize PostgreSQL connection
        try:
            self.postgres_conn = psycopg2.connect(
                host="45.77.87.106",
                port=5432,
                database="orchestra_db",
                user="postgres",
                password="your_password"  # Should come from environment
            )
            logger.info("PostgreSQL connection established")
        except Exception as e:
            logger.warning(f"PostgreSQL connection failed: {e}")
        
        # Initialize Weaviate client
        try:
            self.weaviate_client = weaviate.Client(
                url="http://localhost:8080",
                timeout_config=(5, 30)
            )
            logger.info("Weaviate client initialized")
        except Exception as e:
            logger.warning(f"Weaviate connection failed: {e}")
    
    async def _custom_shutdown(self) -> None:
        """Custom shutdown logic for specific server"""
        if self.postgres_conn:
            self.postgres_conn.close()
            logger.info("PostgreSQL connection closed")
        
        if self.weaviate_client:
            # Weaviate client doesn't need explicit closing
            logger.info("Weaviate client shutdown")
    
    async def _check_custom_connections(self) -> Dict[str, bool]:
        """Check custom connections specific to server"""
        connections = {}
        
        # Check PostgreSQL
        if self.postgres_conn:
            try:
                cursor = self.postgres_conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                connections["postgres"] = True
            except:
                connections["postgres"] = False
        else:
            connections["postgres"] = False
        
        # Check Weaviate
        if self.weaviate_client:
            try:
                self.weaviate_client.schema.get()
                connections["weaviate"] = True
            except:
                connections["weaviate"] = False
        else:
            connections["weaviate"] = False
        
        return connections
    
    async def _get_health_metrics(self) -> Dict[str, Any]:
        """Get custom health metrics for server"""
        metrics = {
            "processed_items": 1234,  # Example metric
            "average_processing_time_ms": 45.6,
            "error_rate": 0.02,
            "last_processed": datetime.now().isoformat()
        }
        
        # Add database metrics if connected
        if self.postgres_conn:
            try:
                cursor = self.postgres_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM pg_stat_activity")
                metrics["postgres_connections"] = cursor.fetchone()[0]
                cursor.close()
            except:
                pass
        
        return metrics
    
    async def _process_data(self, data: dict) -> dict:
        """Example data processing logic"""
        # Simulate processing
        await asyncio.sleep(0.1)
        
        # Store in database if connected
        if self.postgres_conn:
            try:
                cursor = self.postgres_conn.cursor()
                # Example: Store processed data
                cursor.execute(
                    "INSERT INTO processed_data (data, timestamp) VALUES (%s, %s)",
                    (str(data), datetime.now())
                )
                self.postgres_conn.commit()
                cursor.close()
            except Exception as e:
                logger.error(f"Failed to store data: {e}")
        
        # Index in Weaviate if connected
        if self.weaviate_client:
            try:
                self.weaviate_client.data_object.create(
                    data_object=data,
                    class_name="ProcessedData"
                )
            except Exception as e:
                logger.error(f"Failed to index in Weaviate: {e}")
        
        return {
            "processed": True,
            "timestamp": datetime.now().isoformat(),
            "item_count": len(data)
        }
    
    async def _calculate_analytics(self, metric: str) -> dict:
        """Example analytics calculation"""
        # Simulate analytics calculation
        analytics = {
            "metric": metric,
            "value": 42.0,
            "trend": "increasing",
            "period": "last_24h"
        }
        
        if self.postgres_conn and metric == "user_activity":
            try:
                cursor = self.postgres_conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM user_activities WHERE created_at > NOW() - INTERVAL '24 hours'"
                )
                analytics["value"] = cursor.fetchone()[0]
                cursor.close()
            except:
                pass
        
        return analytics
    
    async def _generate_report(self, report_type: str) -> dict:
        """Example report generation"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "type": report_type,
            "sections": []
        }
        
        if report_type == "daily":
            report["sections"] = [
                {
                    "title": "Daily Summary",
                    "content": "System processed 1,234 items today"
                },
                {
                    "title": "Performance",
                    "content": "Average processing time: 45.6ms"
                }
            ]
        elif report_type == "weekly":
            report["sections"] = [
                {
                    "title": "Weekly Overview",
                    "content": "System uptime: 99.9%"
                }
            ]
        
        return report


if __name__ == "__main__":
    # Create and run the server
    server = ExampleMCPServer()
    
    # Configure logging
    import structlog
    logger = structlog.get_logger(__name__)
    
    # Run the server
    uvicorn.run(
        server.app,
        host="0.0.0.0",
        port=server.port,
        log_level="info"
    ) 