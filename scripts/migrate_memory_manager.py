#!/usr/bin/env python3
"""
Migration script for the memory management system.

This script demonstrates how to migrate from the old memory manager
implementation to the new FirestoreMemoryManagerV2 implementation.

Usage:
    python migrate_memory_manager.py [--dry-run]
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("memory_migration")

# Import settings
try:
    from core.orchestrator.src.config.settings import get_settings
    settings = get_settings()
except ImportError:
    logger.warning("Could not import settings, using environment variables")
    settings = None

# Import memory manager implementations
from packages.shared.src.memory.memory_manager import MemoryManager
try:
    from packages.shared.src.memory.firestore_adapter import FirestoreMemoryAdapter
    OLD_FIRESTORE_AVAILABLE = True
except ImportError:
    logger.warning("Old FirestoreMemoryAdapter not available")
    OLD_FIRESTORE_AVAILABLE = False

# Import new implementation
try:
    from packages.shared.src.storage.firestore.v2 import FirestoreMemoryManagerV2
    NEW_FIRESTORE_AVAILABLE = True
except ImportError:
    logger.warning("New FirestoreMemoryManagerV2 not available")
    NEW_FIRESTORE_AVAILABLE = False


async def get_old_memory_manager() -> Optional[MemoryManager]:
    """
    Get an instance of the old memory manager.
    
    Returns:
        The old memory manager instance, or None if not available
    """
    if not OLD_FIRESTORE_AVAILABLE:
        return None
        
    # Get project ID from settings or environment
    project_id = None
    if settings:
        project_id = settings.get_gcp_project_id()
    else:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        
    # Get credentials path from settings or environment
    credentials_path = None
    if settings:
        credentials_path = settings.get_gcp_credentials_path()
    else:
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        
    # Create instance
    old_manager = FirestoreMemoryAdapter(
        project_id=project_id,
        credentials_path=credentials_path,
        namespace="production"
    )
    
    # Initialize
    await old_manager.initialize()
    logger.info("Initialized old memory manager")
    
    return old_manager


async def get_new_memory_manager() -> Optional[MemoryManager]:
    """
    Get an instance of the new memory manager.
    
    Returns:
        The new memory manager instance, or None if not available
    """
    if not NEW_FIRESTORE_AVAILABLE:
        return None
        
    # Get project ID from settings or environment
    project_id = None
    if settings:
        project_id = settings.get_gcp_project_id()
    else:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        
    # Get credentials path from settings or environment
    credentials_path = None
    if settings:
        credentials_path = settings.get_gcp_credentials_path()
    else:
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        
    # Create instance
    new_manager = FirestoreMemoryManagerV2(
        project_id=project_id,
        credentials_path=credentials_path,
        namespace="production-v2"
    )
    
    # Initialize
    await new_manager.initialize()
    logger.info("Initialized new memory manager")
    
    return new_manager


async def migrate_user_data(
    old_manager: MemoryManager,
    new_manager: MemoryManager,
    user_id: str,
    dry_run: bool = False
) -> int:
    """
    Migrate data for a specific user.
    
    Args:
        old_manager: The old memory manager
        new_manager: The new memory manager
        user_id: The user ID to migrate
        dry_run: If True, don't actually write data
        
    Returns:
        The number of items migrated
    """
    logger.info(f"Migrating data for user {user_id}")
    
    # Get conversation history from old manager
    history = await old_manager.get_conversation_history(
        user_id=user_id,
        limit=1000  # Use a large limit to get all items
    )
    
    logger.info(f"Found {len(history)} items for user {user_id}")
    
    # Skip if no items
    if not history:
        return 0
        
    # Migrate items
    migrated = 0
    for item in history:
        # Skip if already migrated
        if dry_run:
            logger.info(f"[DRY RUN] Would migrate item {item.id}")
            migrated += 1
            continue
            
        try:
            # Check if item already exists in new storage
            if item.id:
                existing = await new_manager.get_memory_item(item.id)
                if existing:
                    logger.debug(f"Item {item.id} already exists in new storage")
                    migrated += 1
                    continue
                    
            # Add item to new storage
            item_id = await new_manager.add_memory_item(item)
            logger.debug(f"Migrated item {item_id}")
            migrated += 1
            
        except Exception as e:
            logger.error(f"Error migrating item {item.id}: {e}")
            
    logger.info(f"Migrated {migrated} items for user {user_id}")
    return migrated


async def get_user_ids(manager: MemoryManager) -> List[str]:
    """
    Get all user IDs from the memory manager.
    
    Args:
        manager: The memory manager
        
    Returns:
        List of user IDs
    """
    # This is just a placeholder - in a real implementation, you would
    # need to query the database to get all user IDs
    return ["test_user_1", "test_user_2"]


async def migrate_all_users(
    old_manager: MemoryManager,
    new_manager: MemoryManager,
    dry_run: bool = False
) -> Dict[str, int]:
    """
    Migrate data for all users.
    
    Args:
        old_manager: The old memory manager
        new_manager: The new memory manager
        dry_run: If True, don't actually write data
        
    Returns:
        Dictionary mapping user IDs to number of items migrated
    """
    # Get all user IDs
    user_ids = await get_user_ids(old_manager)
    logger.info(f"Found {len(user_ids)} users to migrate")
    
    # Migrate each user
    results = {}
    for user_id in user_ids:
        try:
            count = await migrate_user_data(old_manager, new_manager, user_id, dry_run)
            results[user_id] = count
        except Exception as e:
            logger.error(f"Error migrating user {user_id}: {e}")
            results[user_id] = 0
            
    return results


async def main(dry_run: bool = False):
    """
    Main function.
    
    Args:
        dry_run: If True, don't actually write data
    """
    # Get memory managers
    old_manager = await get_old_memory_manager()
    if not old_manager:
        logger.error("Could not create old memory manager")
        return
        
    new_manager = await get_new_memory_manager()
    if not new_manager:
        logger.error("Could not create new memory manager")
        await old_manager.close()
        return
        
    try:
        # Check health of both managers
        old_health = await old_manager.health_check()
        logger.info(f"Old memory manager health: {old_health['status']}")
        
        new_health = await new_manager.health_check()
        logger.info(f"New memory manager health: {new_health['status']}")
        
        # Migrate data
        if old_health["status"] == "healthy" and new_health["status"] == "healthy":
            logger.info("Starting migration")
            if dry_run:
                logger.info("DRY RUN MODE - No data will be written")
                
            results = await migrate_all_users(old_manager, new_manager, dry_run)
            
            # Print summary
            total = sum(results.values())
            logger.info(f"Migration complete. Migrated {total} items for {len(results)} users.")
            
            for user_id, count in results.items():
                logger.info(f"User {user_id}: {count} items")
        else:
            logger.error("One or both memory managers are not healthy, aborting migration")
            
    finally:
        # Close managers
        await old_manager.close()
        await new_manager.close()


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Migrate memory manager data")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually write data")
    args = parser.parse_args()
    
    # Run the migration
    asyncio.run(main(dry_run=args.dry_run))
