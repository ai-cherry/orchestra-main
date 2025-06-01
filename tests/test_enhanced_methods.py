#!/usr/bin/env python3
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
    
    print("\nTesting Enhanced PostgreSQL Cache Methods:")
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
    
    print("\nTesting Enhanced PostgreSQL Session Methods:")
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
    
    print("\nTesting Enhanced PostgreSQL Memory Methods:")
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
    
    print("\n✅ All enhanced methods tested successfully!")


if __name__ == "__main__":
    asyncio.run(test_enhanced_methods())
