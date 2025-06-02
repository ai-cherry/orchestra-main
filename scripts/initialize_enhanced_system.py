#!/usr/bin/env python3
"""
Initialize the enhanced unified PostgreSQL system.

This script ensures all components are properly initialized with the enhanced versions.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from shared.database.connection_manager_enhanced import get_connection_manager_enhanced
from shared.database.unified_postgresql_enhanced import get_unified_postgresql_enhanced
from shared.database.unified_db_v2 import get_unified_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def initialize_enhanced_system():
    """Initialize all enhanced components."""
    try:
        # Initialize enhanced connection manager
        logger.info("Initializing enhanced connection manager...")
        manager = await get_connection_manager_enhanced()

        # Verify pool stats method works
        pool_stats = await manager.get_pool_stats()
        logger.info(f"Pool stats: {pool_stats}")

        # Initialize enhanced PostgreSQL client
        logger.info("Initializing enhanced PostgreSQL client...")
        postgres = await get_unified_postgresql_enhanced()

        # Verify missing methods are available
        logger.info("Verifying cache_get_by_tags method...")
        cache_items = await postgres.cache_get_by_tags(["test"])
        logger.info(f"Cache items by tags: {len(cache_items)}")

        logger.info("Verifying session_list method...")
        sessions = await postgres.session_list(limit=10)
        logger.info(f"Sessions: {len(sessions)}")

        logger.info("Verifying memory_snapshot_list method...")
        snapshots = await postgres.memory_snapshot_list(agent_id="test-agent")
        logger.info(f"Memory snapshots: {len(snapshots)}")

        # Initialize unified database
        logger.info("Initializing unified database...")
        db = await get_unified_database()

        # Perform health check
        health = await db.health_check()
        logger.info(f"System health: {health['status']}")

        logger.info("Enhanced system initialized successfully!")

    except Exception as e:
        logger.error(f"Failed to initialize enhanced system: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(initialize_enhanced_system())
