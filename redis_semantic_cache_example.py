#!/usr/bin/env python3
"""
Redis Semantic Caching Example for Orchestra

This script demonstrates how to use Redis for semantic caching in Orchestra
using both the redisvl SemanticCacher and LangChain RedisSemanticCache
for efficient vector similarity search and memory retrieval.
"""

import asyncio
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Import necessary libraries
try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings as GeminiEmbeddings
    from langchain_redis.cache import RedisSemanticCache
    from redisvl import SemanticCacher

    from packages.shared.src.memory.redis_semantic_cacher import RedisSemanticCacheProvider
    from packages.shared.src.models.base_models import MemoryItem
except ImportError as e:
    logger.error(f"Failed to import required libraries: {e}")
    logger.error("Please install required packages: pip install redisvl langchain-redis langchain-google-genai")
    sys.exit(1)

async def main():
    """
    Main function to demonstrate Redis semantic caching functionality.
    """
    logger.info("Starting Redis semantic caching example")

    # Check for environment variables
    redis_url = os.environ.get("REDIS_URL", "redis://vertex-agent@cherry-ai-project")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")

    if not gemini_api_key:
        try:
            with open("gemini.key", "r") as f:
                gemini_api_key = f.read().strip()
        except FileNotFoundError as e:
            logger.error(
                f"Gemini API key file 'gemini.key' not found: {e}. Set GEMINI_API_KEY environment variable or create the file."
            )
            sys.exit(1)

    # 1. Set up redisvl SemanticCacher for direct use
    logger.info("Setting up redisvl SemanticCacher")
    try:
        SemanticCacher(
            threshold=0.85,  # Similarity threshold
            ttl=3600,  # TTL in seconds (1 hour)
            index_schema="agent_memory.yaml",
            redis_url=redis_url,
        )
        logger.info("Successfully initialized SemanticCacher")
    except Exception as e:
        logger.error(f"Failed to initialize SemanticCacher: {e}")
        sys.exit(1)

    # 2. Set up LangChain integration
    logger.info("Setting up LangChain RedisSemanticCache")
    try:
        langchain_cache = RedisSemanticCache(
            embeddings=GeminiEmbeddings(api_key=gemini_api_key),
            redis_url=redis_url,
            name="agent_semantic_cache",
        )
        logger.info("Successfully initialized LangChain RedisSemanticCache")
    except Exception as e:
        logger.error(f"Failed to initialize LangChain RedisSemanticCache: {e}")
        sys.exit(1)

    # 3. Set up Orchestra's RedisSemanticCacheProvider
    logger.info("Setting up Orchestra's RedisSemanticCacheProvider")
    try:
        # Configure Orchestra's provider
        provider_config = {
            "threshold": 0.85,
            "ttl": 3600,
            "index_schema": "agent_memory.yaml",
            "redis_url": redis_url,
            "enable_vector_index": True,
        }

        provider = RedisSemanticCacheProvider(config=provider_config)
        await provider.initialize()
        logger.info("Successfully initialized RedisSemanticCacheProvider")
    except Exception as e:
        logger.error(f"Failed to initialize RedisSemanticCacheProvider: {e}")
        sys.exit(1)

    # 4. Demonstrate adding memory items
    logger.info("Demonstrating memory operations")

    # Create a test memory item
    memory_item = MemoryItem(
        user_id="test_user",
        session_id="test_session",
        item_type="conversation",
        text_content="This is a test memory about AI orchestration and semantic caching",
        metadata={"source": "user", "importance": "high"},
    )

    # Add to Orchestra's provider
    try:
        memory_id = await provider.add_memory(memory_item)
        logger.info(f"Added memory item to Redis with ID: {memory_id}")
    except Exception as e:
        logger.error(f"Failed to add memory item: {e}")

    # 5. Demonstrate retrieval
    try:
        # Retrieve using semantic search
        memories = await provider.get_memories(
            user_id="test_user",
            session_id="test_session",
            query="Tell me about orchestration",
            limit=5,
        )
        logger.info(f"Retrieved {len(memories)} memories")
        for i, mem in enumerate(memories):
            logger.info(f"Memory {i+1}: {mem.text_content}")
    except Exception as e:
        logger.error(f"Failed to retrieve memories: {e}")

    logger.info("Redis semantic caching example completed")

if __name__ == "__main__":
    asyncio.run(main())
