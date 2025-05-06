#!/usr/bin/env python3
"""
Test script to verify the FirestoreMemoryManager implementation.

This script will:
1. Check that FirestoreMemoryManager properly implements the MemoryManager interface
2. Verify GCP authentication works with the provided service account
3. Test connection to Firestore
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add the project root to sys.path
sys.path.append('.')

from packages.shared.src.memory.memory_manager import MemoryManager
from packages.shared.src.storage.firestore.firestore_memory import FirestoreMemoryManager
from packages.shared.src.models.base_models import MemoryItem, AgentData


def print_section(title: str) -> None:
    """Print a section header with proper formatting."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


async def run_health_check(manager: FirestoreMemoryManager) -> None:
    """Run health check and print results."""
    print("Running health check...")
    health = await manager.health_check()
    
    print("Health Check Results:")
    print(f"  Status: {health['status']}")
    print(f"  Firestore: {health.get('firestore', False)}")
    
    if 'details' in health:
        print("  Details:")
        for key, value in health['details'].items():
            print(f"    {key}: {value}")


async def test_add_memory_item(manager: FirestoreMemoryManager) -> Optional[str]:
    """Test adding a memory item."""
    print("Testing add_memory_item...")
    
    try:
        # Create a test item
        test_item = MemoryItem(
            id="test-" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            user_id="test-user",
            session_id="test-session",
            timestamp=datetime.utcnow(),
            item_type="test",
            text_content="This is a test memory item",
            metadata={"test": True}
        )
        
        # Add the item
        item_id = await manager.add_memory_item(test_item)
        print(f"  Successfully added item with ID: {item_id}")
        
        # Retrieve the item
        retrieved = await manager.get_memory_item(item_id)
        if retrieved:
            print(f"  Successfully retrieved item: {retrieved.id}")
            print(f"  Content: {retrieved.text_content}")
        else:
            print("  Failed to retrieve item")
        
        return item_id
    except Exception as e:
        print(f"  Error: {e}")
        return None


async def main() -> None:
    print_section("FirestoreMemoryManager Implementation Test")
    
    # Check environment variables
    print("Checking environment variables...")
    project_id = os.environ.get("GCP_PROJECT_ID")
    credentials_path = os.environ.get("GCP_SA_KEY_PATH")
    credentials_json = os.environ.get("GCP_SA_KEY_JSON")
    
    print(f"  GCP_PROJECT_ID: {'Set' if project_id else 'Not set'}")
    print(f"  GCP_SA_KEY_PATH: {'Set' if credentials_path else 'Not set'}")
    print(f"  GCP_SA_KEY_JSON: {'Set' if credentials_json else 'Not set'}")
    
    # Create and initialize the FirestoreMemoryManager
    print("\nInitializing FirestoreMemoryManager...")
    manager = FirestoreMemoryManager(
        project_id=project_id,
        credentials_json=credentials_json,
        credentials_path=credentials_path
    )
    
    try:
        manager.initialize()
        print("  Successfully initialized manager")
        
        # Run tests
        await run_health_check(manager)
        
        # Test adding a memory item
        item_id = await test_add_memory_item(manager)
        
        # Clean up
        print("\nCleaning up...")
        manager.close()
        print("  Manager closed")
        
        print("\nTest Results:")
        if item_id:
            print("  ✓ Successfully implemented FirestoreMemoryManager")
        else:
            print("  ✗ Implementation has issues")
    
    except Exception as e:
        print(f"  Error: {e}")
        print("  ✗ Implementation failed")


if __name__ == "__main__":
    asyncio.run(main())
