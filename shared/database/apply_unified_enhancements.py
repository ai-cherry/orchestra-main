"""
Apply unified PostgreSQL enhancements to fix all missing methods.

This script updates the existing code to use the enhanced versions that include
all missing methods through mixins, providing a seamless fix without breaking changes.
"""

import os
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_imports_in_file(file_path: Path, replacements: dict) -> bool:
    """
    Update imports in a Python file.

    Args:
        file_path: Path to the file
        replacements: Dictionary of old import -> new import

    Returns:
        True if file was modified, False otherwise
    """
    try:
        content = file_path.read_text()
        original_content = content

        for old_import, new_import in replacements.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                logger.info(f"Updated import in {file_path}: {old_import} -> {new_import}")

        if content != original_content:
            file_path.write_text(content)
            return True

        return False

    except Exception as e:
        logger.error(f"Error updating {file_path}: {e}")
        return False


def create_compatibility_wrapper():
    """
    Create a compatibility wrapper that redirects old imports to enhanced versions.
    """
    wrapper_content = '''"""
Compatibility wrapper for unified PostgreSQL architecture.

This module redirects imports to the enhanced versions that include all missing methods.
"""

# Import enhanced versions
from .connection_manager_enhanced import (
    PostgreSQLConnectionManagerEnhanced as PostgreSQLConnectionManager,
    get_connection_manager_enhanced as get_connection_manager,
    close_connection_manager_enhanced as close_connection_manager
)

from .unified_postgresql_enhanced import (
    UnifiedPostgreSQLEnhanced as UnifiedPostgreSQL,
    get_unified_postgresql_enhanced as get_unified_postgresql,
    close_unified_postgresql_enhanced as close_unified_postgresql
)

# Re-export for compatibility
__all__ = [
    'PostgreSQLConnectionManager',
    'get_connection_manager',
    'close_connection_manager',
    'UnifiedPostgreSQL',
    'get_unified_postgresql',
    'close_unified_postgresql'
]
'''

    wrapper_path = Path("shared/database/unified_compat.py")
    wrapper_path.write_text(wrapper_content)
    logger.info(f"Created compatibility wrapper at {wrapper_path}")


def update_unified_db_v2():
    """
    Update unified_db_v2.py to fix method signature issues.
    """
    file_path = Path("shared/database/unified_db_v2.py")

    try:
        content = file_path.read_text()

        # Fix agent_create method call
        content = content.replace(
            "agent = await self._postgres.agent_create(**agent_data)",
            "agent = await self._postgres.agent_create(agent_data)",
        )

        # Fix workflow_create method call
        content = content.replace("workflow = await self._postgres.workflow_create({", "workflow_data = {")
        content = content.replace("})", "}\n        workflow = await self._postgres.workflow_create(workflow_data)")

        file_path.write_text(content)
        logger.info("Updated unified_db_v2.py with method signature fixes")

    except Exception as e:
        logger.error(f"Error updating unified_db_v2.py: {e}")


def create_initialization_script():
    """
    Create a script to initialize the enhanced system.
    """
    init_content = '''#!/usr/bin/env python3
"""
Initialize the enhanced unified PostgreSQL system.

This script ensures all components are properly initialized with the enhanced versions.
"""

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
        cache_items = await postgres.cache_get_by_tags(['test'])
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
'''

    init_path = Path("scripts/initialize_enhanced_system.py")
    init_path.write_text(init_content)
    os.chmod(init_path, 0o755)
    logger.info(f"Created initialization script at {init_path}")


def create_test_enhanced_methods():
    """
    Create a test script to verify all enhanced methods work.
    """
    test_content = '''#!/usr/bin/env python3
"""
Test all enhanced methods to ensure they work correctly.
"""

import asyncio
import uuid
from datetime import datetime
from shared.database.connection_manager_enhanced import get_connection_manager_enhanced
from shared.database.unified_postgresql_enhanced import get_unified_postgresql_enhanced


async def test_enhanced_methods():
    """Test all methods added by mixins."""
    
    # Get enhanced instances
    manager = await get_connection_manager_enhanced()
    postgres = await get_unified_postgresql_enhanced()
    
    print("Testing Enhanced Connection Manager Methods:")
    print("-" * 50)
    
    # Test get_pool_stats
    pool_stats = await manager.get_pool_stats()
    print(f"✓ get_pool_stats: {pool_stats}")
    
    # Test get_extended_pool_stats
    extended_stats = await manager.get_extended_pool_stats()
    print(f"✓ get_extended_pool_stats: Pool utilization: {extended_stats['derived_metrics']['pool_utilization']:.2%}")
    
    # Test get_pool_recommendations
    recommendations = await manager.get_pool_recommendations()
    print(f"✓ get_pool_recommendations: {len(recommendations['recommendations'])} recommendations")
    
    print("\\nTesting Enhanced PostgreSQL Cache Methods:")
    print("-" * 50)
    
    # Test cache_set and cache_get_by_tags
    test_key = f"test_{uuid.uuid4()}"
    await postgres.cache_set(test_key, {"test": "data"}, ttl=3600, tags=["test", "enhanced"])
    
    tagged_items = await postgres.cache_get_by_tags(["test"])
    print(f"✓ cache_get_by_tags: Found {len(tagged_items)} items with 'test' tag")
    
    # Test cache_get_many
    keys = [test_key, "nonexistent_key"]
    values = await postgres.cache_get_many(keys)
    print(f"✓ cache_get_many: Retrieved {sum(1 for v in values.values() if v)} of {len(keys)} keys")
    
    # Test cache_info
    cache_info = await postgres.cache_info()
    print(f"✓ cache_info: {cache_info['statistics'].get('total_entries', 0)} total entries")
    
    print("\\nTesting Enhanced PostgreSQL Session Methods:")
    print("-" * 50)
    
    # Test session_create and session_list
    session_id = await postgres.session_create(
        user_id="test_user",
        agent_id="test_agent",
        data={"test": "session"},
        ttl=3600
    )
    
    sessions = await postgres.session_list(user_id="test_user")
    print(f"✓ session_list: Found {len(sessions)} sessions for test_user")
    
    # Test session_analytics
    analytics = await postgres.session_analytics(time_range_hours=24)
    print(f"✓ session_analytics: {analytics['statistics'].get('active_sessions', 0)} active sessions")
    
    print("\\nTesting Enhanced PostgreSQL Memory Methods:")
    print("-" * 50)
    
    # Test memory_snapshot_create and memory_snapshot_list
    snapshot_id = await postgres.memory_snapshot_create(
        agent_id="test_agent",
        user_id="test_user",
        snapshot_data={"memory": "test snapshot"},
        metadata={"test": True}
    )
    print(f"✓ memory_snapshot_create: Created snapshot {snapshot_id}")
    
    snapshots = await postgres.memory_snapshot_list(agent_id="test_agent")
    print(f"✓ memory_snapshot_list: Found {len(snapshots)} snapshots")
    
    # Test memory_snapshot_get
    snapshot = await postgres.memory_snapshot_get(snapshot_id)
    print(f"✓ memory_snapshot_get: Retrieved snapshot created at {snapshot['created_at']}")
    
    # Cleanup
    await postgres.cache_delete(test_key)
    await postgres.session_delete(session_id)
    await postgres.memory_snapshot_delete(snapshot_id)
    
    print("\\n✅ All enhanced methods tested successfully!")


if __name__ == "__main__":
    asyncio.run(test_enhanced_methods())
'''

    test_path = Path("tests/test_enhanced_methods.py")
    test_path.write_text(test_content)
    os.chmod(test_path, 0o755)
    logger.info(f"Created test script at {test_path}")


def main():
    """
    Main function to apply all enhancements.
    """
    logger.info("Applying unified PostgreSQL enhancements...")

    # Create compatibility wrapper
    create_compatibility_wrapper()

    # Update unified_db_v2.py
    update_unified_db_v2()

    # Create initialization script
    create_initialization_script()

    # Create test script
    create_test_enhanced_methods()

    # Update imports in key files
    replacements = {
        "from shared.database.connection_manager import get_connection_manager": "from shared.database.connection_manager_enhanced import get_connection_manager_enhanced as get_connection_manager",
        "from shared.database.unified_postgresql import get_unified_postgresql": "from shared.database.unified_postgresql_enhanced import get_unified_postgresql_enhanced as get_unified_postgresql",
    }

    # Find Python files that need updating
    python_files = []
    for pattern in ["agent/**/*.py", "tests/*.py", "scripts/*.py"]:
        python_files.extend(Path(".").glob(pattern))

    updated_count = 0
    for file_path in python_files:
        if update_imports_in_file(file_path, replacements):
            updated_count += 1

    logger.info(f"Updated {updated_count} files with enhanced imports")

    print("\n" + "=" * 60)
    print("UNIFIED POSTGRESQL ENHANCEMENTS APPLIED")
    print("=" * 60)
    print("\nAll missing methods have been added through mixins:")
    print("✓ Connection Manager: get_pool_stats() and related methods")
    print("✓ Cache: cache_get_by_tags(), cache_get_many(), cache_info()")
    print("✓ Sessions: session_list(), session_analytics(), etc.")
    print("✓ Memory: memory_snapshot_create(), memory_snapshot_get(), etc.")
    print("\nNext steps:")
    print("1. Run the initialization script:")
    print("   python scripts/initialize_enhanced_system.py")
    print("2. Test the enhanced methods:")
    print("   python tests/test_enhanced_methods.py")
    print("3. Run the migration if upgrading:")
    print("   python scripts/migrate_to_unified_postgresql.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
