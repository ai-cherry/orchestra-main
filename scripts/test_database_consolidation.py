#!/usr/bin/env python3
"""
Test script for database consolidation.

Verifies that PostgreSQL and Weaviate clients are working correctly.
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database import UnifiedDatabase

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_postgresql_operations(db: UnifiedDatabase):
    """Test PostgreSQL operations."""
    logger.info("Testing PostgreSQL operations...")
    
    try:
        # Test health check
        if not db.postgres.health_check():
            logger.error("PostgreSQL health check failed")
            return False
        logger.info("✓ PostgreSQL health check passed")
        
        # Test agent creation
        agent = db.create_agent(
            name=f"test_agent_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            description="Test agent for database consolidation",
            capabilities={"test": True},
            autonomy_level=1,
            initial_memory="I am a test agent"
        )
        logger.info(f"✓ Created agent: {agent['name']} (ID: {agent['id']})")
        
        # Test agent retrieval
        retrieved = db.postgres.get_agent(agent['id'])
        if retrieved:
            logger.info(f"✓ Retrieved agent: {retrieved['name']}")
        else:
            logger.error("Failed to retrieve agent")
            return False
        
        # Test session creation
        session_id = f"test_session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        session = db.create_session(
            session_id=session_id,
            user_id="test_user",
            agent_id=str(agent['id']),
            ttl_hours=1
        )
        logger.info(f"✓ Created session: {session['id']}")
        
        # Test audit log
        audit = db.postgres.create_audit_log(
            event_type="test_event",
            actor="test_script",
            resource_type="test",
            resource_id="test_123",
            details={"test": True}
        )
        logger.info(f"✓ Created audit log: {audit['id']}")
        
        # Cleanup - delete test agent
        if db.postgres.delete_agent(agent['id']):
            logger.info(f"✓ Cleaned up test agent")
        
        return True
        
    except Exception as e:
        logger.error(f"PostgreSQL test failed: {e}")
        return False


def test_weaviate_operations(db: UnifiedDatabase):
    """Test Weaviate operations."""
    logger.info("\nTesting Weaviate operations...")
    
    try:
        # Test health check
        if not db.weaviate.health_check():
            logger.error("Weaviate health check failed")
            return False
        logger.info("✓ Weaviate health check passed")
        
        # Test memory storage
        agent_id = f"test_agent_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        memory_id = db.weaviate.store_memory(
            agent_id=agent_id,
            content="This is a test memory",
            memory_type="test",
            importance=0.5
        )
        logger.info(f"✓ Stored memory: {memory_id}")
        
        # Test memory search
        memories = db.weaviate.search_memories(
            agent_id=agent_id,
            query="test memory",
            limit=5
        )
        logger.info(f"✓ Found {len(memories)} memories")
        
        # Test knowledge storage
        knowledge_id = db.add_to_knowledge_base(
            title="Test Knowledge",
            content="This is test knowledge content",
            category="test",
            tags=["test", "consolidation"]
        )
        logger.info(f"✓ Stored knowledge: {knowledge_id}")
        
        # Test knowledge search
        knowledge = db.search_knowledge(
            query="test knowledge",
            category="test",
            limit=5
        )
        logger.info(f"✓ Found {len(knowledge)} knowledge items")
        
        # Test conversation storage
        session_id = f"test_session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        conv_id = db.weaviate.store_conversation(
            session_id=session_id,
            agent_id=agent_id,
            user_id="test_user",
            message="Test message",
            role="user"
        )
        logger.info(f"✓ Stored conversation: {conv_id}")
        
        # Get Weaviate stats
        stats = db.weaviate.get_stats()
        logger.info(f"✓ Weaviate stats: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"Weaviate test failed: {e}")
        return False


def test_unified_operations(db: UnifiedDatabase):
    """Test unified database operations."""
    logger.info("\nTesting unified operations...")
    
    try:
        # Test agent interaction storage
        agent_id = f"test_agent_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        session_id = f"test_session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        result = db.store_agent_interaction(
            agent_id=agent_id,
            user_input="Hello, test agent",
            agent_response="Hello! I'm a test response",
            session_id=session_id,
            user_id="test_user"
        )
        logger.info(f"✓ Stored interaction: Session {result['session_id']}, Memory {result['memory_id']}")
        
        # Test context search
        context = db.search_agent_context(
            agent_id=agent_id,
            query="test",
            include_conversations=True,
            include_memories=True
        )
        logger.info(f"✓ Found context: {len(context.get('memories', []))} memories, {len(context.get('conversations', []))} conversations")
        
        # Test system stats
        stats = db.get_system_stats()
        logger.info(f"✓ System stats: PostgreSQL={stats['postgresql']['health']}, Weaviate={stats['weaviate_health']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Unified operations test failed: {e}")
        return False


def main():
    """Run all database tests."""
    logger.info("Starting database consolidation tests...")
    
    # Initialize unified database
    try:
        db = UnifiedDatabase()
        logger.info("✓ Unified database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return 1
    
    # Run tests
    results = []
    
    # Test PostgreSQL
    results.append(("PostgreSQL", test_postgresql_operations(db)))
    
    # Test Weaviate
    results.append(("Weaviate", test_weaviate_operations(db)))
    
    # Test unified operations
    results.append(("Unified", test_unified_operations(db)))
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("Test Summary:")
    logger.info("="*50)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{name:15} {status}")
        if not passed:
            all_passed = False
    
    logger.info("="*50)
    
    if all_passed:
        logger.info("✅ All tests passed! Database consolidation is working correctly.")
        return 0
    else:
        logger.error("❌ Some tests failed. Please check the logs above.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 