#!/usr/bin/env python3
"""
MCP Server for DragonflyDB Cache Management

This server enables Claude 4 to manage DragonflyDB caching operations
through the Model Context Protocol (MCP).

DragonflyDB is a Redis-compatible in-memory datastore that provides
high performance and modern architecture.
"""

import os
import logging
import json
import asyncio
from typing import Dict, Any, List, Optional, Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app for MCP server
app = FastAPI(
    title="DragonflyDB MCP Server", description="MCP server for managing DragonflyDB cache operations", version="1.0.0"
)

# Get configuration from environment
DRAGONFLY_HOST = os.getenv("DRAGONFLY_HOST", "localhost")
DRAGONFLY_PORT = int(os.getenv("DRAGONFLY_PORT", "6379"))
DRAGONFLY_PASSWORD = os.getenv("DRAGONFLY_PASSWORD")
DRAGONFLY_DB = int(os.getenv("DRAGONFLY_DB", "0"))
CONNECTION_POOL_SIZE = int(os.getenv("CONNECTION_POOL_SIZE", "10"))

# Global connection pool
connection_pool: Optional[ConnectionPool] = None
redis_client: Optional[redis.Redis] = None


class CacheSetRequest(BaseModel):
    """Request model for setting a cache value"""

    key: str = Field(..., description="Cache key")
    value: Any = Field(..., description="Value to cache (will be JSON serialized)")
    ttl: Optional[int] = Field(None, description="Time to live in seconds")
    nx: bool = Field(False, description="Only set if key doesn't exist")
    xx: bool = Field(False, description="Only set if key exists")


class CacheGetRequest(BaseModel):
    """Request model for getting a cache value"""

    key: str = Field(..., description="Cache key")


class CacheDeleteRequest(BaseModel):
    """Request model for deleting cache values"""

    keys: List[str] = Field(..., description="List of keys to delete")


class CacheExpireRequest(BaseModel):
    """Request model for setting key expiration"""

    key: str = Field(..., description="Cache key")
    ttl: int = Field(..., description="Time to live in seconds")


class ListOperationRequest(BaseModel):
    """Request model for list operations"""

    key: str = Field(..., description="List key")
    values: Optional[List[Any]] = Field(None, description="Values for push operations")
    start: Optional[int] = Field(0, description="Start index for range operations")
    stop: Optional[int] = Field(-1, description="Stop index for range operations")
    count: Optional[int] = Field(1, description="Count for pop operations")


class SetOperationRequest(BaseModel):
    """Request model for set operations"""

    key: str = Field(..., description="Set key")
    members: Optional[List[Any]] = Field(None, description="Members to add/remove")
    other_key: Optional[str] = Field(None, description="Other set key for operations")


class HashOperationRequest(BaseModel):
    """Request model for hash operations"""

    key: str = Field(..., description="Hash key")
    field: Optional[str] = Field(None, description="Hash field")
    fields: Optional[Dict[str, Any]] = Field(None, description="Multiple fields")
    value: Optional[Any] = Field(None, description="Field value")


class MCPToolDefinition(BaseModel):
    """MCP tool definition for Claude"""

    name: str
    description: str
    parameters: Dict[str, Any]


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client with connection pooling."""
    global connection_pool, redis_client

    if redis_client is None:
        # Create connection pool if not exists
        if connection_pool is None:
            connection_pool = redis.ConnectionPool(
                host=DRAGONFLY_HOST,
                port=DRAGONFLY_PORT,
                password=DRAGONFLY_PASSWORD,
                db=DRAGONFLY_DB,
                max_connections=CONNECTION_POOL_SIZE,
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
                retry_on_timeout=True,
                health_check_interval=30,
            )

        redis_client = redis.Redis(connection_pool=connection_pool)

        # Test connection
        try:
            await redis_client.ping()
            logger.info(f"Connected to DragonflyDB at {DRAGONFLY_HOST}:{DRAGONFLY_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to DragonflyDB: {e}")
            redis_client = None
            raise

    return redis_client


@app.on_event("startup")
async def startup_event():
    """Initialize connection on startup."""
    try:
        await get_redis_client()
    except Exception as e:
        logger.error(f"Failed to initialize DragonflyDB connection: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown."""
    global redis_client, connection_pool

    if redis_client:
        await redis_client.close()
        redis_client = None

    if connection_pool:
        await connection_pool.disconnect()
        connection_pool = None


@app.get("/mcp/dragonfly/tools")
async def get_tools() -> List[MCPToolDefinition]:
    """Return available tools for Claude to use"""
    return [
        # String operations
        MCPToolDefinition(
            name="cache_set",
            description="Set a value in the cache with optional TTL",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Cache key"},
                    "value": {"description": "Value to cache"},
                    "ttl": {"type": "integer", "description": "Time to live in seconds"},
                    "nx": {"type": "boolean", "description": "Only set if key doesn't exist"},
                    "xx": {"type": "boolean", "description": "Only set if key exists"},
                },
                "required": ["key", "value"],
            },
        ),
        MCPToolDefinition(
            name="cache_get",
            description="Get a value from the cache",
            parameters={
                "type": "object",
                "properties": {"key": {"type": "string", "description": "Cache key"}},
                "required": ["key"],
            },
        ),
        MCPToolDefinition(
            name="cache_delete",
            description="Delete one or more keys from the cache",
            parameters={
                "type": "object",
                "properties": {"keys": {"type": "array", "items": {"type": "string"}, "description": "Keys to delete"}},
                "required": ["keys"],
            },
        ),
        MCPToolDefinition(
            name="cache_expire",
            description="Set expiration time for a key",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Cache key"},
                    "ttl": {"type": "integer", "description": "Time to live in seconds"},
                },
                "required": ["key", "ttl"],
            },
        ),
        # List operations
        MCPToolDefinition(
            name="list_push",
            description="Push values to a list",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "List key"},
                    "values": {"type": "array", "description": "Values to push"},
                    "left": {"type": "boolean", "description": "Push to left (head) of list"},
                },
                "required": ["key", "values"],
            },
        ),
        MCPToolDefinition(
            name="list_pop",
            description="Pop values from a list",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "List key"},
                    "count": {"type": "integer", "description": "Number of values to pop"},
                    "left": {"type": "boolean", "description": "Pop from left (head) of list"},
                },
                "required": ["key"],
            },
        ),
        MCPToolDefinition(
            name="list_range",
            description="Get a range of values from a list",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "List key"},
                    "start": {"type": "integer", "description": "Start index"},
                    "stop": {"type": "integer", "description": "Stop index"},
                },
                "required": ["key"],
            },
        ),
        # Set operations
        MCPToolDefinition(
            name="set_add",
            description="Add members to a set",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Set key"},
                    "members": {"type": "array", "description": "Members to add"},
                },
                "required": ["key", "members"],
            },
        ),
        MCPToolDefinition(
            name="set_remove",
            description="Remove members from a set",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Set key"},
                    "members": {"type": "array", "description": "Members to remove"},
                },
                "required": ["key", "members"],
            },
        ),
        MCPToolDefinition(
            name="set_members",
            description="Get all members of a set",
            parameters={
                "type": "object",
                "properties": {"key": {"type": "string", "description": "Set key"}},
                "required": ["key"],
            },
        ),
        # Hash operations
        MCPToolDefinition(
            name="hash_set",
            description="Set field(s) in a hash",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Hash key"},
                    "field": {"type": "string", "description": "Field name (for single field)"},
                    "value": {"description": "Field value (for single field)"},
                    "fields": {"type": "object", "description": "Multiple fields and values"},
                },
                "required": ["key"],
            },
        ),
        MCPToolDefinition(
            name="hash_get",
            description="Get field(s) from a hash",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Hash key"},
                    "field": {"type": "string", "description": "Field name (for single field)"},
                },
                "required": ["key"],
            },
        ),
        MCPToolDefinition(
            name="hash_delete",
            description="Delete field(s) from a hash",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Hash key"},
                    "fields": {"type": "array", "items": {"type": "string"}, "description": "Fields to delete"},
                },
                "required": ["key", "fields"],
            },
        ),
    ]


# String operations
@app.post("/mcp/dragonfly/set")
async def cache_set(request: CacheSetRequest) -> Dict[str, Any]:
    """Set a value in the cache."""
    try:
        client = await get_redis_client()

        # Serialize non-string values to JSON
        value = request.value
        if not isinstance(value, str):
            value = json.dumps(value)

        # Build set options
        set_kwargs = {}
        if request.ttl:
            set_kwargs["ex"] = request.ttl
        if request.nx:
            set_kwargs["nx"] = True
        if request.xx:
            set_kwargs["xx"] = True

        result = await client.set(request.key, value, **set_kwargs)

        return {"status": "success" if result else "failed", "key": request.key, "ttl": request.ttl}
    except Exception as e:
        logger.error(f"Failed to set cache value: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/dragonfly/get")
async def cache_get(request: CacheGetRequest) -> Dict[str, Any]:
    """Get a value from the cache."""
    try:
        client = await get_redis_client()
        value = await client.get(request.key)

        if value is None:
            return {"status": "not_found", "key": request.key, "value": None}

        # Try to deserialize JSON values
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            pass  # Keep as string if not JSON

        # Get TTL
        ttl = await client.ttl(request.key)

        return {"status": "success", "key": request.key, "value": value, "ttl": ttl if ttl > 0 else None}
    except Exception as e:
        logger.error(f"Failed to get cache value: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/dragonfly/delete")
async def cache_delete(request: CacheDeleteRequest) -> Dict[str, Any]:
    """Delete keys from the cache."""
    try:
        client = await get_redis_client()
        deleted_count = await client.delete(*request.keys)

        return {"status": "success", "deleted_count": deleted_count, "keys": request.keys}
    except Exception as e:
        logger.error(f"Failed to delete cache keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/dragonfly/expire")
async def cache_expire(request: CacheExpireRequest) -> Dict[str, Any]:
    """Set expiration for a key."""
    try:
        client = await get_redis_client()
        result = await client.expire(request.key, request.ttl)

        return {"status": "success" if result else "key_not_found", "key": request.key, "ttl": request.ttl}
    except Exception as e:
        logger.error(f"Failed to set expiration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# List operations
@app.post("/mcp/dragonfly/list/push")
async def list_push(request: ListOperationRequest) -> Dict[str, Any]:
    """Push values to a list."""
    try:
        client = await get_redis_client()

        # Serialize values
        values = [json.dumps(v) if not isinstance(v, str) else v for v in request.values]

        # Push left or right
        left = request.__dict__.get("left", False)
        if left:
            length = await client.lpush(request.key, *values)
        else:
            length = await client.rpush(request.key, *values)

        return {"status": "success", "key": request.key, "length": length, "pushed": len(values)}
    except Exception as e:
        logger.error(f"Failed to push to list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/dragonfly/list/pop")
async def list_pop(request: ListOperationRequest) -> Dict[str, Any]:
    """Pop values from a list."""
    try:
        client = await get_redis_client()

        count = request.count or 1
        left = request.__dict__.get("left", False)
        values = []

        for _ in range(count):
            if left:
                value = await client.lpop(request.key)
            else:
                value = await client.rpop(request.key)

            if value is None:
                break

            # Try to deserialize
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                pass

            values.append(value)

        return {"status": "success", "key": request.key, "values": values, "popped": len(values)}
    except Exception as e:
        logger.error(f"Failed to pop from list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/dragonfly/list/range")
async def list_range(request: ListOperationRequest) -> Dict[str, Any]:
    """Get a range of values from a list."""
    try:
        client = await get_redis_client()

        start = request.start or 0
        stop = request.stop if request.stop is not None else -1

        values = await client.lrange(request.key, start, stop)

        # Try to deserialize values
        deserialized_values = []
        for value in values:
            try:
                deserialized_values.append(json.loads(value))
            except (json.JSONDecodeError, TypeError):
                deserialized_values.append(value)

        return {
            "status": "success",
            "key": request.key,
            "values": deserialized_values,
            "count": len(deserialized_values),
        }
    except Exception as e:
        logger.error(f"Failed to get list range: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Set operations
@app.post("/mcp/dragonfly/set/add")
async def set_add(request: SetOperationRequest) -> Dict[str, Any]:
    """Add members to a set."""
    try:
        client = await get_redis_client()

        # Serialize members
        members = [json.dumps(m) if not isinstance(m, str) else m for m in request.members]

        added = await client.sadd(request.key, *members)

        return {
            "status": "success",
            "key": request.key,
            "added": added,
            "total_members": await client.scard(request.key),
        }
    except Exception as e:
        logger.error(f"Failed to add to set: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/dragonfly/set/remove")
async def set_remove(request: SetOperationRequest) -> Dict[str, Any]:
    """Remove members from a set."""
    try:
        client = await get_redis_client()

        # Serialize members
        members = [json.dumps(m) if not isinstance(m, str) else m for m in request.members]

        removed = await client.srem(request.key, *members)

        return {
            "status": "success",
            "key": request.key,
            "removed": removed,
            "total_members": await client.scard(request.key),
        }
    except Exception as e:
        logger.error(f"Failed to remove from set: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/dragonfly/set/members")
async def set_members(request: SetOperationRequest) -> Dict[str, Any]:
    """Get all members of a set."""
    try:
        client = await get_redis_client()
        members = await client.smembers(request.key)

        # Try to deserialize members
        deserialized_members = []
        for member in members:
            try:
                deserialized_members.append(json.loads(member))
            except (json.JSONDecodeError, TypeError):
                deserialized_members.append(member)

        return {
            "status": "success",
            "key": request.key,
            "members": deserialized_members,
            "count": len(deserialized_members),
        }
    except Exception as e:
        logger.error(f"Failed to get set members: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Hash operations
@app.post("/mcp/dragonfly/hash/set")
async def hash_set(request: HashOperationRequest) -> Dict[str, Any]:
    """Set field(s) in a hash."""
    try:
        client = await get_redis_client()

        if request.fields:
            # Multiple fields
            mapping = {}
            for field, value in request.fields.items():
                if not isinstance(value, str):
                    value = json.dumps(value)
                mapping[field] = value

            await client.hset(request.key, mapping=mapping)
            fields_set = len(mapping)
        else:
            # Single field
            value = request.value
            if not isinstance(value, str):
                value = json.dumps(value)

            await client.hset(request.key, request.field, value)
            fields_set = 1

        return {"status": "success", "key": request.key, "fields_set": fields_set}
    except Exception as e:
        logger.error(f"Failed to set hash fields: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/dragonfly/hash/get")
async def hash_get(request: HashOperationRequest) -> Dict[str, Any]:
    """Get field(s) from a hash."""
    try:
        client = await get_redis_client()

        if request.field:
            # Single field
            value = await client.hget(request.key, request.field)
            if value is not None:
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    pass

            return {"status": "success", "key": request.key, "field": request.field, "value": value}
        else:
            # All fields
            fields = await client.hgetall(request.key)

            # Try to deserialize values
            for field, value in fields.items():
                try:
                    fields[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    pass

            return {"status": "success", "key": request.key, "fields": fields, "count": len(fields)}
    except Exception as e:
        logger.error(f"Failed to get hash fields: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp/dragonfly/hash/delete")
async def hash_delete(request: HashOperationRequest) -> Dict[str, Any]:
    """Delete field(s) from a hash."""
    try:
        client = await get_redis_client()

        fields = request.fields if isinstance(request.fields, list) else list(request.fields.keys())
        deleted = await client.hdel(request.key, *fields)

        return {"status": "success", "key": request.key, "deleted": deleted, "fields": fields}
    except Exception as e:
        logger.error(f"Failed to delete hash fields: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/dragonfly/info")
async def get_info() -> Dict[str, Any]:
    """Get DragonflyDB server information."""
    try:
        client = await get_redis_client()
        info = await client.info()

        return {
            "status": "connected",
            "server": {
                "version": info.get("redis_version", "unknown"),
                "mode": info.get("redis_mode", "standalone"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
            },
            "memory": {
                "used_memory_human": info.get("used_memory_human", "0B"),
                "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
                "total_system_memory_human": info.get("total_system_memory_human", "0B"),
            },
            "stats": {
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
            },
        }
    except Exception as e:
        logger.error(f"Failed to get server info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        client = await get_redis_client()
        await client.ping()
        return {"status": "healthy", "service": "dragonfly-mcp", "host": f"{DRAGONFLY_HOST}:{DRAGONFLY_PORT}"}
    except Exception as e:
        return {"status": "unhealthy", "service": "dragonfly-mcp", "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8004)
