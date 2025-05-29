#!/usr/bin/env python3
"""
Validate Paperspace environment configuration.
Checks connectivity to all required services.
"""

import logging
import os
import sys

import redis
import weaviate
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def check_weaviate() -> bool:
    """Test Weaviate connection."""
    try:
        client = weaviate.connect_to_local(
            host="localhost",
            port=int(os.getenv("PAPERSPACE_MCP_WEAVIATE_PORT", "8081")),
            auth=weaviate.AuthApiKey(os.getenv("PAPERSPACE_WEAVIATE_API_KEY")),
        )
        ready = client.is_ready()
        client.close()
        return ready
    except Exception as e:
        logger.error(f"Weaviate check failed: {str(e)}")
        return False


def check_redis() -> bool:
    """Test Redis/DragonflyDB connection."""
    try:
        r = redis.StrictRedis(
            host="localhost",
            port=int(os.getenv("PAPERSPACE_MCP_REDIS_PORT", "6379")),
            password=os.getenv("PAPERSPACE_DRAGONFLYDB_PASSWORD"),
            decode_responses=True,
        )
        return r.ping()
    except Exception as e:
        logger.error(f"Redis check failed: {str(e)}")
        return False


def check_mongodb() -> bool:
    """Test MongoDB connection."""
    try:
        client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
        return client.admin.command("ping").get("ok") == 1.0
    except Exception as e:
        logger.error(f"MongoDB check failed: {str(e)}")
        return False


def main() -> int:
    """Run all validation checks."""
    if not os.getenv("PAPERSPACE_ENV"):
        logger.error("Not running in Paperspace environment")
        return 1

    checks = [("Weaviate", check_weaviate), ("Redis/DragonflyDB", check_redis), ("MongoDB", check_mongodb)]

    failures = 0
    for name, check_fn in checks:
        logger.info(f"Checking {name}...")
        if check_fn():
            logger.info(f"{name} connection successful")
        else:
            logger.error(f"{name} connection failed")
            failures += 1

    if failures > 0:
        logger.error(f"Validation failed with {failures} errors")
        return 1

    logger.info("All services validated successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
