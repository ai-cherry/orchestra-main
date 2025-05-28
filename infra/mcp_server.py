"""
MCP Server implementation for DragonflyDB integration.
Provides natural language interface to database operations.
"""

import logging
import os
from typing import Any, Dict

import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DatabaseCommand(BaseModel):
    """Request model for MCP commands."""

    command: str
    args: Dict[str, Any] = {}
    options: Dict[str, Any] = {}


class MCPRedisServer:
    def __init__(self, config: Dict[str, str]):
        """
        Initialize MCP server with DragonflyDB connection.

        Args:
            config: Dictionary containing connection parameters
        """
        self.config = config
        self.redis = redis.StrictRedis(
            host=config.get("host", "localhost"),
            port=config.get("port", 6379),
            db=config.get("db", 0),
            decode_responses=True,
        )
        self._verify_connection()

    def _verify_connection(self) -> None:
        """Test database connection on startup."""
        try:
            if not self.redis.ping():
                raise ConnectionError("Failed to connect to DragonflyDB")
            logger.info("Connected to DragonflyDB successfully")
        except Exception as e:
            logger.error("DragonflyDB connection failed: %s", str(e))
            raise

    def execute_command(self, db_command: DatabaseCommand) -> Any:
        """
        Execute Redis command through MCP interface.

        Args:
            db_command: Parsed command object

        Returns:
            Result of Redis operation

        Raises:
            HTTPException: For invalid commands or database errors
        """
        try:
            # Convert natural language to Redis command
            command = db_command.command.lower()

            if command == "get":
                return self.redis.get(db_command.args["key"])
            elif command == "set":
                return self.redis.set(
                    db_command.args["key"],
                    db_command.args["value"],
                    **db_command.options,
                )
            elif command == "search":
                # Example vector search integration
                return self._handle_vector_search(db_command.args)
            else:
                raise ValueError(f"Unsupported command: {command}")

        except Exception as e:
            logger.error("Command failed: %s", str(e))
            raise HTTPException(status_code=400, detail=f"Command execution error: {str(e)}")

    def _handle_vector_search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vector search operations."""
        # Placeholder for vector search integration
        return {
            "status": "success",
            "message": "Vector search not yet implemented",
            "args": args,
        }


def get_redis_config() -> Dict[str, Any]:
    """Get Redis/DragonflyDB configuration based on environment."""
    if os.getenv("PAPERSPACE_ENV") == "true":
        # Paperspace local configuration
        return {
            "host": "localhost",
            "port": int(os.getenv("MCP_REDIS_SERVER_PORT", "6379")),
            "password": os.getenv("PAPERSPACE_DRAGONFLYDB_PASSWORD"),
        }
    else:
        # DigitalOcean production configuration
        return {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", 6379)),
        }


# FastAPI application setup
app = FastAPI(title="DragonflyDB MCP Server")
server = MCPRedisServer(get_redis_config())


@app.post("/execute")
async def execute_command(command: DatabaseCommand):
    """API endpoint for command execution."""
    return server.execute_command(command)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
