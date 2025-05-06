#!/usr/bin/env python3
"""
Memory Data Migration Tool for AI Orchestra.

This script migrates memory data from Firestore V1 to Firestore V2 format.
It reads data from the V1 implementation and writes it to the V2 implementation,
performing any necessary transformations along the way.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.shared.src.memory.memory_manager import MemoryManager
from packages.shared.src.models.base_models import MemoryItem, AgentData
from packages.shared.src.storage.firestore.constants import (
    MEMORY_ITEMS_COLLECTION, 
    AGENT_DATA_COLLECTION
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("memory_migration.log")]
)
logger = logging.getLogger("memory_migration")

class MigrationStats:
    """Statistics for the migration process."""
    
    def __init__(self):
        self.total_items = 0
        self.migrated_items = 0
        self.failed_items = 0
        self.skipped_items = 0
        self.start_time = datetime.now()
        self.end_time = None
    
    def record_success(self):
        """Record a successful migration."""
        self.migrated_items += 1
        self.total_items += 1
    
    def record_failure(self):
        """Record a failed migration."""
        self.failed_items += 1
        self.total_items += 1
    
    def record_skip(self):
        """Record a skipped item."""
        self.skipped_items += 1
        self.total_items += 1
    
    def complete(self):
        """Mark the migration as complete."""
        self.end_time = datetime.now()
    
    def get_duration(self) -> float:
        """Get the duration of the migration in seconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    def __str__(self) -> str:
        """Return a string representation of the migration statistics."""
        return (
            f"Migration Statistics:\n"
            f"  Total items processed: {self.total_items}\n"
            f"  Successfully migrated: {self.migrated_items}\n"
            f"  Failed to migrate: {self.failed_items}\n"
            f"  Skipped items: {self.skipped_items}\n"
            f"  Duration: {self.get_duration():.2f} seconds"
        )

async def migrate_memory_items(
    source_manager: MemoryManager,
    target_manager: MemoryManager,
    batch_size: int = 100,
    dry_run: bool = False,
    stats: Optional[MigrationStats] = None
) -> MigrationStats:
    """
    Migrate memory items from source to target manager.
    
    Args:
        source_manager: Source memory manager (V1)
        target_manager: Target memory manager (V2)
        batch_size: Number of items to process in each batch
        dry_run: If True, don't actually write to the target
        stats: Optional statistics object to update
        
    Returns:
        Migration statistics
    """
    if stats is None:
        stats = MigrationStats()
    
    logger.info("Starting memory items migration")
    
    # Get all user IDs from the source
    # This is a simplified approach - in a real implementation, you would
    # need to paginate through all users if there are many
    
    # For demonstration purposes, we'll use a direct Firestore query
    # In a real implementation, you would use the memory manager's API
    source_firestore = source_manager._backend._firestore_memory._firestore_client
    users_collection = source_firestore.collection("users")
    users = await users_collection.get()
    
    for user in users:
        user_id = user.id
        logger.info(f"Processing user: {user_id}")
        
        # Get memory items for this user
        cursor = None
        while True:
            # Get a batch of items
            items = await source_manager.get_conversation_history(
                user_id=user_id,
                limit=batch_size,
                # Use cursor for pagination if available
                # This is a simplified approach
            )
            
            if not items:
                break
                
            # Process each item
            for item in items:
                try:
                    # Check if item already exists in target
                    exists = await target_manager.check_duplicate(item)
                    
                    if exists:
                        logger.debug(f"Item already exists in target: {item.id}")
                        stats.record_skip()
                        continue
                    
                    # Migrate the item
                    if not dry_run:
                        await target_manager.add_memory_item(item)
                        logger.debug(f"Migrated item: {item.id}")
                        stats.record_success()
                    else:
                        logger.debug(f"Would migrate item: {item.id} (dry run)")
                        stats.record_success()
                        
                except Exception as e:
                    logger.error(f"Failed to migrate item {item.id}: {e}")
                    stats.record_failure()
            
            # Update cursor for next batch
            if items:
                cursor = items[-1]
            else:
                break
    
    return stats

async def migrate_agent_data(
    source_manager: MemoryManager,
    target_manager: MemoryManager,
    batch_size: int = 100,
    dry_run: bool = False,
    stats: Optional[MigrationStats] = None
) -> MigrationStats:
    """
    Migrate agent data from source to target manager.
    
    Args:
        source_manager: Source memory manager (V1)
        target_manager: Target memory manager (V2)
        batch_size: Number of items to process in each batch
        dry_run: If True, don't actually write to the target
        stats: Optional statistics object to update
        
    Returns:
        Migration statistics
    """
    if stats is None:
        stats = MigrationStats()
    
    logger.info("Starting agent data migration")
    
    # For demonstration purposes, we'll use a direct Firestore query
    # In a real implementation, you would use the memory manager's API
    source_firestore = source_manager._backend._firestore_memory._firestore_client
    agent_collection = source_firestore.collection(AGENT_DATA_COLLECTION)
    
    # Get all agent data
    agent_data_docs = await agent_collection.limit(batch_size).get()
    
    for doc in agent_data_docs:
        try:
            # Convert to AgentData
            data_dict = doc.to_dict()
            agent_data = AgentData(
                agent_id=data_dict.get("agent_id", ""),
                data_type=data_dict.get("data_type", ""),
                content=data_dict.get("content", {}),
                metadata=data_dict.get("metadata", {}),
                timestamp=data_dict.get("timestamp", datetime.now().isoformat()),
            )
            
            # Migrate the data
            if not dry_run:
                await target_manager.add_raw_agent_data(agent_data)
                logger.debug(f"Migrated agent data: {doc.id}")
                stats.record_success()
            else:
                logger.debug(f"Would migrate agent data: {doc.id} (dry run)")
                stats.record_success()
                
        except Exception as e:
            logger.error(f"Failed to migrate agent data {doc.id}: {e}")
            stats.record_failure()
    
    return stats

async def validate_migration(
    source_manager: MemoryManager,
    target_manager: MemoryManager,
    sample_size: int = 10
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate the migration by comparing samples from source and target.
    
    Args:
        source_manager: Source memory manager (V1)
        target_manager: Target memory manager (V2)
        sample_size: Number of items to sample for validation
        
    Returns:
        Tuple of (success, validation_results)
    """
    logger.info("Validating migration")
    
    # For demonstration purposes, we'll use a direct Firestore query
    # In a real implementation, you would use the memory manager's API
    source_firestore = source_manager._backend._firestore_memory._firestore_client
    memory_collection = source_firestore.collection(MEMORY_ITEMS_COLLECTION)
    
    # Get a sample of items from the source
    sample_docs = await memory_collection.limit(sample_size).get()
    
    validation_results = {
        "total_samples": len(sample_docs),
        "matched": 0,
        "mismatched": 0,
        "missing": 0,
        "details": []
    }
    
    for doc in sample_docs:
        item_id = doc.id
        source_data = doc.to_dict()
        
        # Get the same item from the target
        target_item = await target_manager.get_memory_item(item_id)
        
        if target_item is None:
            logger.warning(f"Item {item_id} not found in target")
            validation_results["missing"] += 1
            validation_results["details"].append({
                "item_id": item_id,
                "status": "missing",
                "source_data": source_data
            })
            continue
        
        # Compare the items
        # This is a simplified comparison - in a real implementation,
        # you would need to compare all relevant fields
        if (
            target_item.user_id == source_data.get("user_id") and
            target_item.text_content == source_data.get("text_content")
        ):
            validation_results["matched"] += 1
            validation_results["details"].append({
                "item_id": item_id,
                "status": "matched"
            })
        else:
            validation_results["mismatched"] += 1
            validation_results["details"].append({
                "item_id": item_id,
                "status": "mismatched",
                "source_data": source_data,
                "target_data": target_item.dict()
            })
    
    success = (
        validation_results["mismatched"] == 0 and
        validation_results["missing"] == 0
    )
    
    return success, validation_results

async def run_migration(
    project_id: str,
    credentials_path: Optional[str] = None,
    batch_size: int = 100,
    dry_run: bool = False,
    validate: bool = True,
    sample_size: int = 10
) -> Tuple[MigrationStats, Dict[str, Any]]:
    """
    Run the full migration process.
    
    Args:
        project_id: Google Cloud project ID
        credentials_path: Path to service account credentials file
        batch_size: Number of items to process in each batch
        dry_run: If True, don't actually write to the target
        validate: Whether to validate the migration
        sample_size: Number of items to sample for validation
        
    Returns:
        Tuple of (migration_stats, validation_results)
    """
    logger.info(f"Starting migration for project {project_id}")
    logger.info(f"Dry run: {dry_run}")
    
    # Initialize source manager (V1)
    source_manager = MemoryManager(
        memory_backend_type="firestore_v1",
        project_id=project_id,
        credentials_path=credentials_path
    )
    await source_manager.initialize()
    
    # Initialize target manager (V2)
    target_manager = MemoryManager(
        memory_backend_type="firestore_v2",
        project_id=project_id,
        credentials_path=credentials_path
    )
    await target_manager.initialize()
    
    try:
        # Migrate memory items
        stats = MigrationStats()
        await migrate_memory_items(
            source_manager=source_manager,
            target_manager=target_manager,
            batch_size=batch_size,
            dry_run=dry_run,
            stats=stats
        )
        
        # Migrate agent data
        await migrate_agent_data(
            source_manager=source_manager,
            target_manager=target_manager,
            batch_size=batch_size,
            dry_run=dry_run,
            stats=stats
        )
        
        stats.complete()
        logger.info(str(stats))
        
        # Validate the migration
        validation_results = {}
        if validate and not dry_run:
            success, validation_results = await validate_migration(
                source_manager=source_manager,
                target_manager=target_manager,
                sample_size=sample_size
            )
            
            if success:
                logger.info("Validation successful")
            else:
                logger.warning("Validation failed")
                
        return stats, validation_results
        
    finally:
        # Clean up
        await source_manager.close()
        await target_manager.close()

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Migrate memory data from V1 to V2")
    parser.add_argument("--project-id", required=True, help="Google Cloud project ID")
    parser.add_argument("--credentials-path", help="Path to service account credentials file")
    parser.add_argument("--batch-size", type=int, default=100, help="Number of items to process in each batch")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually write to the target")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation")
    parser.add_argument("--sample-size", type=int, default=10, help="Number of items to sample for validation")
    parser.add_argument("--output", help="Path to write validation results to")
    
    args = parser.parse_args()
    
    # Run the migration
    stats, validation_results = asyncio.run(run_migration(
        project_id=args.project_id,
        credentials_path=args.credentials_path,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        validate=not args.no_validate,
        sample_size=args.sample_size
    ))
    
    # Write validation results to file if requested
    if args.output and validation_results:
        with open(args.output, "w") as f:
            json.dump(validation_results, f, indent=2)
            logger.info(f"Validation results written to {args.output}")
    
    # Exit with appropriate status code
    if stats.failed_items > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()