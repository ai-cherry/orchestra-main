"""
Tiered memory storage system for the AI Orchestration System.

This module provides a tiered storage implementation that automatically
moves data between hot, warm, and cold tiers based on access patterns,
optimizing for both performance and cost.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from google.cloud import firestore
from google.cloud import storage
from google.oauth2 import service_account

from packages.shared.src.models.base_models import MemoryItem, AgentData, PersonaConfig
from packages.shared.src.memory.memory_interface import MemoryInterface
from packages.shared.src.memory.cache_manager import (
    get_cache_manager, 
    CacheManager, 
    EvictionPolicy
)
from packages.shared.src.storage.exceptions import StorageError, ConnectionError, OperationError
from core.orchestrator.src.exceptions import MemoryError, MemoryConnectionError, MemoryOperationError

# Set up logger
logger = logging.getLogger(__name__)


class StorageTier(Enum):
    """Storage tier enumeration."""
    
    HOT = "hot"      # Frequently accessed, fastest retrieval
    WARM = "warm"    # Occasionally accessed, standard retrieval
    COLD = "cold"    # Rarely accessed, slower retrieval, compressed


class TieredStorageManager(MemoryInterface):
    """
    Tiered storage manager for memory items.
    
    This class implements a tiered storage system that automatically
    categorizes and migrates memory items between hot, warm, and cold
    storage tiers based on access patterns.
    """
    
    def __init__(
        self,
        base_memory_manager: MemoryInterface,
        project_id: str,
        redis_host: Optional[str] = None,
        redis_port: int = 6379,
        redis_password: Optional[str] = None,
        credentials_path: Optional[str] = None,
        hot_tier_max_age_days: int = 7,      # Items older than this move to warm
        warm_tier_max_age_days: int = 30,    # Items older than this move to cold
        min_access_count_hot: int = 5,       # Min access count to stay in hot
        min_access_count_warm: int = 2,      # Min access count to stay in warm
        enable_compression: bool = True,     # Compress cold tier items
        tier_migration_interval: int = 3600, # Run tier migration every hour
    ):
        """
        Initialize the tiered storage manager.
        
        Args:
            base_memory_manager: The underlying memory manager
            project_id: Google Cloud project ID
            redis_host: Optional Redis host for hot tier (if None, use Firestore for hot tier)
            redis_port: Redis port
            redis_password: Optional Redis password
            credentials_path: Optional path to service account credentials
            hot_tier_max_age_days: Maximum age in days for items in hot tier
            warm_tier_max_age_days: Maximum age in days for items in warm tier
            min_access_count_hot: Minimum access count to remain in hot tier
            min_access_count_warm: Minimum access count to remain in warm tier
            enable_compression: Whether to compress cold tier items
            tier_migration_interval: Interval in seconds for tier migration
        """
        self._base_memory = base_memory_manager
        self._project_id = project_id
        self._redis_host = redis_host
        self._redis_port = redis_port
        self._redis_password = redis_password
        self._credentials_path = credentials_path
        
        # Tier configuration
        self._hot_tier_max_age = timedelta(days=hot_tier_max_age_days)
        self._warm_tier_max_age = timedelta(days=warm_tier_max_age_days)
        self._min_access_count_hot = min_access_count_hot
        self._min_access_count_warm = min_access_count_warm
        self._enable_compression = enable_compression
        self._tier_migration_interval = tier_migration_interval
        
        # Initialize Firestore and Storage clients
        self._firestore_client = None
        self._storage_client = None
        self._redis_client = None
        self._initialize_clients()
        
        # Track last tier migration time
        self._last_tier_migration = time.time()
        
        # Cache manager for hot tier items (properly bounded with eviction)
        self._hot_cache_manager = get_cache_manager(
            name=f"tiered_storage_hot_tier_{project_id}",
            max_size=int(os.environ.get("HOT_TIER_MAX_SIZE", "10000")),
            eviction_policy=EvictionPolicy.LRU,
            default_ttl_seconds=int(os.environ.get("HOT_TIER_TTL", str(60 * 60 * 24))),  # 24 hours default
            cleanup_interval=300  # Clean up every 5 minutes
        )
        
        # Access count tracking (in-memory, will be persisted periodically)
        self._access_counts = {}
        self._last_access_time = {}
        
        logger.info(
            f"Initialized tiered storage with hot cache max size: {self._hot_cache_manager.max_size}, "
            f"eviction policy: {self._hot_cache_manager.eviction_policy.value}"
        )
        
    def _initialize_clients(self) -> None:
        """
        Initialize Firestore, Cloud Storage, and Redis clients.
        """
        try:
            # Set up credentials if provided
            credentials = None
            if self._credentials_path:
                credentials = service_account.Credentials.from_service_account_file(
                    self._credentials_path
                )
            
            # Initialize Firestore client
            if credentials:
                self._firestore_client = firestore.Client(
                    project=self._project_id,
                    credentials=credentials
                )
            else:
                self._firestore_client = firestore.Client(project=self._project_id)
                
            # Initialize Cloud Storage client (for cold tier)
            if credentials:
                self._storage_client = storage.Client(
                    project=self._project_id,
                    credentials=credentials
                )
            else:
                self._storage_client = storage.Client(project=self._project_id)
                
            # Initialize Redis client if host provided (for hot tier)
            if self._redis_host:
                import redis
                self._redis_client = redis.Redis(
                    host=self._redis_host,
                    port=self._redis_port,
                    password=self._redis_password,
                    decode_responses=True,
                )
                # Test connection
                self._redis_client.ping()
                
            logger.info(f"Successfully initialized tiered storage clients for project {self._project_id}")
                
        except Exception as e:
            logger.error(f"Failed to initialize storage clients: {e}")
            raise ConnectionError(f"Failed to initialize storage clients: {e}", e)
    
    async def initialize(self) -> None:
        """Initialize the base memory manager and tiered storage."""
        # Initialize the base memory manager
        await self._base_memory.initialize()
        
        # Load access counts from Firestore
        await self._load_access_tracking()
    
    async def close(self) -> None:
        """Close all connections."""
        # Close the base memory manager
        await self._base_memory.close()
        
        # Save access tracking data
        await self._save_access_tracking()
        
        # Close Redis connection if present
        if self._redis_client:
            try:
                self._redis_client.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
    
    async def add_memory_item(self, item: MemoryItem) -> str:
        """
        Add a memory item to storage.
        
        New items are initially stored in the warm tier, then promoted
        or demoted based on access patterns.
        
        Args:
            item: The memory item to add
            
        Returns:
            The ID of the added item
        """
        # Add to base storage first (ensures persistence)
        item_id = await self._base_memory.add_memory_item(item)
        
        try:
            # Store in warm tier by default (new items)
            await self._store_in_tier(item_id, item, StorageTier.WARM)
            
            # Initialize access tracking
            self._access_counts[item_id] = 1
            self._last_access_time[item_id] = datetime.now()
            
            # Check if tier migration is needed
            await self._check_tier_migration()
                
        except Exception as e:
            logger.error(f"Error storing item in tiered storage: {e}")
            # Still return the ID since it was stored in base storage
            
        return item_id
    
    async def get_memory_item(self, item_id: str) -> Optional[MemoryItem]:
        """
        Retrieve a memory item from the appropriate tier.
        
        This method attempts to retrieve the item from the hot tier first,
        then warm, then cold, updating access counts along the way.
        
        Args:
            item_id: The ID of the item to retrieve
            
        Returns:
            The memory item, or None if not found
        """
        item = None
        
        try:
            # Try hot tier first (using cache manager)
            item_dict = self._hot_cache_manager.get(item_id)
            if item_dict is not None:
                try:
                    item = MemoryItem(**item_dict)
                    logger.debug(f"Hot tier cache hit for item {item_id}")
                except Exception as e:
                    logger.warning(f"Error deserializing hot tier item {item_id}: {e}")
                    # Remove from hot cache if we can't deserialize
                    self._hot_cache_manager.remove(item_id)
            
            # Try Redis hot tier if available
            if not item and self._redis_client:
                try:
                    redis_key = f"hot_tier:{item_id}"
                    item_json = self._redis_client.get(redis_key)
                    if item_json:
                        item_dict = json.loads(item_json)
                        item = MemoryItem(**item_dict)
                        # Also update cache manager
                        self._hot_cache_manager.put(item_id, item_dict)
                        logger.debug(f"Redis hot tier hit for item {item_id}")
                except Exception as e:
                    logger.warning(f"Error retrieving from Redis hot tier: {e}")
            
            # Try warm tier (Firestore)
            if not item:
                warm_doc_ref = self._firestore_client.collection("warm_tier").document(item_id)
                warm_doc = warm_doc_ref.get()
                if warm_doc.exists:
                    item_dict = warm_doc.to_dict()
                    item = MemoryItem(**item_dict)
                    # Promote to hot tier
                    await self._store_in_tier(item_id, item, StorageTier.HOT)
                    logger.debug(f"Warm tier hit for item {item_id}")
            
            # Try cold tier (Firestore with compression)
            if not item:
                cold_doc_ref = self._firestore_client.collection("cold_tier").document(item_id)
                cold_doc = cold_doc_ref.get()
                if cold_doc.exists:
                    item_dict = cold_doc.to_dict()
                    
                    # Check if item is compressed
                    if item_dict.get("compressed", False):
                        # Decompress the content
                        import zlib, base64
                        compressed_content = item_dict.get("compressed_content")
                        if compressed_content:
                            try:
                                decoded = base64.b64decode(compressed_content)
                                decompressed = zlib.decompress(decoded).decode("utf-8")
                                item_dict["content"] = decompressed
                                # Remove compressed fields for MemoryItem construction
                                item_dict.pop("compressed", None)
                                item_dict.pop("compressed_content", None)
                            except Exception as e:
                                logger.error(f"Error decompressing cold tier item: {e}")
                                # If decompression fails, try base storage
                                return await self._base_memory.get_memory_item(item_id)
                    
                    item = MemoryItem(**item_dict)
                    # Promote to warm tier (items retrieved from cold are elevated)
                    await self._store_in_tier(item_id, item, StorageTier.WARM)
                    logger.debug(f"Cold tier hit for item {item_id}")
            
            # If not found in any tier, try base storage
            if not item:
                item = await self._base_memory.get_memory_item(item_id)
                if item:
                    # Store in warm tier
                    await self._store_in_tier(item_id, item, StorageTier.WARM)
                    logger.debug(f"Base storage hit for item {item_id}")
            
            # Update access tracking if item was found
            if item:
                self._access_counts[item_id] = self._access_counts.get(item_id, 0) + 1
                self._last_access_time[item_id] = datetime.now()
                
            # Check if tier migration is needed
            await self._check_tier_migration()
                
        except Exception as e:
            logger.error(f"Error retrieving item from tiered storage: {e}")
            # Fall back to base storage
            item = await self._base_memory.get_memory_item(item_id)
            
        return item
    
    async def get_conversation_history(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem]:
        """
        Retrieve conversation history across tiers.
        
        This method attempts to optimize retrieval by checking tiers in order
        and consolidating results.
        
        Args:
            user_id: User ID to retrieve history for
            session_id: Optional session ID to filter by
            limit: Maximum number of items to return
            filters: Optional additional filters
            
        Returns:
            List of memory items in the conversation history
        """
        # Start with items from base memory
        history = await self._base_memory.get_conversation_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit,
            filters=filters,
        )
        
        # Update access tracking for all retrieved items
        for item in history:
            if item.id:
                self._access_counts[item.id] = self._access_counts.get(item.id, 0) + 1
                self._last_access_time[item.id] = datetime.now()
        
        # Check if tier migration is needed
        await self._check_tier_migration()
        
        return history
    
    async def semantic_search(
        self,
        user_id: str,
        query_embedding: List[float],
        persona_context: Optional[PersonaConfig] = None,
        top_k: int = 5,
    ) -> List[MemoryItem]:
        """
        Perform semantic search across tiers.
        
        This delegates to the base memory manager for semantic search
        but updates access tracking for retrieved items.
        
        Args:
            user_id: User ID to search within
            query_embedding: Vector embedding for the query
            persona_context: Optional persona context to filter by
            top_k: Maximum number of results to return
            
        Returns:
            List of memory items matching the semantic search
        """
        # Delegate to base memory
        results = await self._base_memory.semantic_search(
            user_id=user_id,
            query_embedding=query_embedding,
            persona_context=persona_context,
            top_k=top_k,
        )
        
        # Update access tracking for all retrieved items
        for item in results:
            if item.id:
                self._access_counts[item.id] = self._access_counts.get(item.id, 0) + 1
                self._last_access_time[item.id] = datetime.now()
                
                # Ensure items are in appropriate tier
                await self._ensure_item_in_tier(item.id, item)
        
        # Check if tier migration is needed
        await self._check_tier_migration()
        
        return results
    
    async def add_raw_agent_data(self, data: AgentData) -> str:
        """
        Store raw agent data.
        
        Agent data is stored in the warm tier by default.
        
        Args:
            data: The agent data to store
            
        Returns:
            The ID of the stored data
        """
        # Add to base storage first
        data_id = await self._base_memory.add_raw_agent_data(data)
        
        try:
            # Store in Firestore warm tier
            data_dict = data.dict()
            warm_doc_ref = self._firestore_client.collection("warm_tier_agent_data").document(data_id)
            warm_doc_ref.set(data_dict)
            
            # Initialize access tracking
            self._access_counts[f"agent:{data_id}"] = 1
            self._last_access_time[f"agent:{data_id}"] = datetime.now()
            
        except Exception as e:
            logger.error(f"Error storing agent data in tiered storage: {e}")
            
        return data_id
    
    async def check_duplicate(self, item: MemoryItem) -> bool:
        """
        Check if a memory item already exists.
        
        This delegates to the base memory manager for duplicate checking.
        
        Args:
            item: The memory item to check
            
        Returns:
            True if a duplicate exists, False otherwise
        """
        # Delegate to base memory
        return await self._base_memory.check_duplicate(item)
    
    async def cleanup_expired_items(self) -> int:
        """
        Remove expired items from all tiers.
        
        Returns:
            Number of items removed
        """
        # First run base memory cleanup
        removed_count = await self._base_memory.cleanup_expired_items()
        
        # Run tier migration to ensure items are in correct tiers
        await self._run_tier_migration(force=True)
        
        return removed_count
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of tiered storage.
        
        Returns:
            Health check information
        """
        # Get base storage health
        base_health = await self._base_memory.health_check()
        
        # Get cache manager stats
        cache_stats = self._hot_cache_manager.get_stats()
        
        # Check tier health
        tier_health = {
            "status": "healthy",
            "details": {
                "hot_tier_items": cache_stats["size"],
                "hot_tier_max_size": cache_stats["max_size"],
                "hot_tier_hit_rate": cache_stats["hit_rate"],
                "hot_tier_evictions": cache_stats["evictions"],
                "last_migration": datetime.fromtimestamp(self._last_tier_migration).isoformat(),
                "tracked_items": len(self._access_counts),
            }
        }
        
        try:
            # Check Firestore connection
            test_doc = self._firestore_client.collection("health_check").document("test")
            test_doc.set({"timestamp": firestore.SERVER_TIMESTAMP})
            test_doc.delete()
            
            # Check Redis if used
            if self._redis_client:
                self._redis_client.ping()
                tier_health["details"]["redis_connected"] = True
                
        except Exception as e:
            tier_health["status"] = "unhealthy"
            tier_health["details"]["error"] = str(e)
            
        # Combine health information
        return {
            "base_storage": base_health,
            "tiered_storage": tier_health,
        }
    
    async def _store_in_tier(
        self,
        item_id: str,
        item: MemoryItem,
        tier: StorageTier
    ) -> None:
        """
        Store a memory item in the specified tier.

        Args:
            item_id: The ID of the item
            item: The memory item to store
            tier: The storage tier to use
            
        Raises:
            MemoryOperationError: If there's an error storing the item
        """
        item_dict = item.dict()

        if tier == StorageTier.HOT:
            # Store in cache manager with appropriate TTL
            self._hot_cache_manager.put(item_id, item_dict)

            # Also store in Redis if available
            if self._redis_client:
                try:
                    redis_key = f"hot_tier:{item_id}"
                    self._redis_client.setex(
                        redis_key,
                        60 * 60 * 24,  # 24 hour TTL
                        json.dumps(item_dict)
                    )
                except Exception as e:
                    logger.warning(f"Error storing item in Redis hot tier: {e}")

        elif tier == StorageTier.WARM:
            # Store in Firestore warm tier
            try:
                warm_doc_ref = self._firestore_client.collection("warm_tier").document(item_id)
                warm_doc_ref.set(item_dict)
            except Exception as e:
                logger.error(f"Error storing item in warm tier: {e}")
                raise MemoryOperationError(f"Failed to store item in warm tier: {e}", e)

        elif tier == StorageTier.COLD:
            # Store in Firestore cold tier, possibly with compression
            try:
                if self._enable_compression and len(item.content) > 500:
                    try:
                        # Compress the content
                        import zlib, base64
                        compressed = zlib.compress(item.content.encode("utf-8"))
                        b64_compressed = base64.b64encode(compressed).decode("utf-8")

                        # Create a modified dict with compressed content
                        cold_item_dict = item_dict.copy()
                        cold_item_dict.pop("content", None)  # Remove content
                        cold_item_dict["compressed"] = True
                        cold_item_dict["compressed_content"] = b64_compressed

                        # Store compressed version
                        cold_doc_ref = self._firestore_client.collection("cold_tier").document(item_id)
                        cold_doc_ref.set(cold_item_dict)

                    except Exception as e:
                        logger.error(f"Error compressing item for cold tier: {e}")
                        # Fall back to uncompressed storage
                        cold_doc_ref = self._firestore_client.collection("cold_tier").document(item_id)
                        cold_doc_ref.set(item_dict)
                else:
                    # Store uncompressed
                    cold_doc_ref = self._firestore_client.collection("cold_tier").document(item_id)
                    cold_doc_ref.set(item_dict)
            except Exception as e:
                logger.error(f"Error storing item in cold tier: {e}")
                raise MemoryOperationError(f"Failed to store item in cold tier: {e}", e)

    async def _remove_from_tier(
        self,
        item_id: str,
        tier: StorageTier
    ) -> None:
        """
        Remove a memory item from the specified tier.
        
        Args:
            item_id: The ID of the item to remove
            tier: The storage tier to remove from
            
        Raises:
            MemoryOperationError: If there's an error removing the item
        """
        try:
            if tier == StorageTier.HOT:
                # Remove from cache manager
                self._hot_cache_manager.remove(item_id)
                
                # Remove from Redis if available
                if self._redis_client:
                    try:
                        redis_key = f"hot_tier:{item_id}"
                        self._redis_client.delete(redis_key)
                    except Exception as e:
                        logger.warning(f"Error removing item from Redis hot tier: {e}")
                        
            elif tier == StorageTier.WARM:
                # Remove from Firestore warm tier
                warm_doc_ref = self._firestore_client.collection("warm_tier").document(item_id)
                warm_doc_ref.delete()
                
            elif tier == StorageTier.COLD:
                # Remove from Firestore cold tier
                cold_doc_ref = self._firestore_client.collection("cold_tier").document(item_id)
                cold_doc_ref.delete()
                
        except Exception as e:
            logger.error(f"Error removing item from {tier.value} tier: {e}")
            raise MemoryOperationError(f"Failed to remove item from {tier.value} tier: {e}", e)
    
    async def _migrate_item(
        self,
        item_id: str,
        from_tier: StorageTier,
        to_tier: StorageTier
    ) -> None:
        """
        Migrate an item from one tier to another.
        
        Args:
            item_id: The ID of the item to migrate
            from_tier: The source tier
            to_tier: The destination tier
        """
        logger.debug(f"Migrating item {item_id} from {from_tier.value} to {to_tier.value}")
        
        # Get the item from the source tier
        item = None
        
        if from_tier == StorageTier.HOT:
            # Check cache manager
            item_dict = self._hot_cache_manager.get(item_id)
            if item_dict:
                try:
                    item = MemoryItem(**item_dict)
                except Exception as e:
                    logger.warning(f"Error deserializing hot tier item {item_id}: {e}")
            
            # Check Redis if not in cache manager
            if not item and self._redis_client:
                try:
                    redis_key = f"hot_tier:{item_id}"
                    item_json = self._redis_client.get(redis_key)
                    if item_json:
                        item_dict = json.loads(item_json)
                        item = MemoryItem(**item_dict)
                except Exception as e:
                    logger.warning(f"Error retrieving from Redis hot tier: {e}")
                    
        elif from_tier == StorageTier.WARM:
            # Get from Firestore warm tier
            warm_doc_ref = self._firestore_client.collection("warm_tier").document(item_id)
            warm_doc = warm_doc_ref.get()
            if warm_doc.exists:
                item_dict = warm_doc.to_dict()
                item = MemoryItem(**item_dict)
                
        elif from_tier == StorageTier.COLD:
            # Get from Firestore cold tier
            cold_doc_ref = self._firestore_client.collection("cold_tier").document(item_id)
            cold_doc = cold_doc_ref.get()
            if cold_doc.exists:
                item_dict = cold_doc.to_dict()
                
                # Check if item is compressed
                if item_dict.get("compressed", False):
                    # Decompress the content
                    import zlib, base64
                    compressed_content = item_dict.get("compressed_content")
                    if compressed_content:
                        try:
                            decoded = base64.b64decode(compressed_content)
                            decompressed = zlib.decompress(decoded).decode("utf-8")
                            item_dict["content"] = decompressed
                            # Remove compressed fields for MemoryItem construction
                            item_dict.pop("compressed", None)
                            item_dict.pop("compressed_content", None)
                        except Exception as e:
                            logger.error(f"Error decompressing cold tier item: {e}")
                            # If decompression fails, fall back to base storage
                            item = await self._base_memory.get_memory_item(item_id)
                            if not item:
                                return
                
                if not item:  # Only create if not already created in decompression error handling
                    item = MemoryItem(**item_dict)
                    
        # If item not found in tier, try base storage
        if not item:
            item = await self._base_memory.get_memory_item(item_id)
            if not item:
                logger.warning(f"Item {item_id} not found in {from_tier.value} tier or base storage")
                return
                
        # Remove from source tier
        await self._remove_from_tier(item_id, from_tier)
        
        # Store in destination tier
        await self._store_in_tier(item_id, item, to_tier)
    
    async def _ensure_item_in_tier(self, item_id: str, item: MemoryItem) -> None:
        """
        Ensure an item is in the appropriate tier based on access patterns.
        
        Args:
            item_id: The ID of the item
            item: The memory item
        """
        access_count = self._access_counts.get(item_id, 0)
        last_access = self._last_access_time.get(item_id, datetime.now())
        current_time = datetime.now()
        
        # Determine the appropriate tier
        if access_count >= self._min_access_count_hot and (current_time - last_access) <= self._hot_tier_max_age:
            # Item should be in hot tier
            if not self._hot_cache_manager.contains(item_id) and (self._redis_client is None or 
                                                           not self._redis_client.exists(f"hot_tier:{item_id}")):
                await self._store_in_tier(item_id, item, StorageTier.HOT)
                
        elif access_count >= self._min_access_count_warm and (current_time - last_access) <= self._warm_tier_max_age:
            # Item should be in warm tier
            warm_doc_ref = self._firestore_client.collection("warm_tier").document(item_id)
            if not warm_doc_ref.get().exists:
                await self._store_in_tier(item_id, item, StorageTier.WARM)
    
    async def _check_tier_migration(self) -> None:
        """
        Check if tier migration should be run and execute if needed.
        """
        now = time.time()
        if now - self._last_tier_migration > self._tier_migration_interval:
            await self._run_tier_migration()
    
    async def _run_tier_migration(self, force: bool = False) -> None:
        """
        Run the tier migration process.

        This process moves items between tiers based on access patterns.

        Args:
            force: Whether to force migration regardless of timing
        """
        now = time.time()
        self._last_tier_migration = now
        current_time = datetime.now()

        # Save access tracking first
        await self._save_access_tracking()

        logger.info("Starting tiered storage migration process")

        # Get all items in hot tier from cache manager
        hot_tier_items = self._hot_cache_manager.get_keys()
        
        # Also get hot tier items from Redis if available
        if self._redis_client:
            try:
                # Get all hot tier keys from Redis
                redis_keys = self._redis_client.keys("hot_tier:*")
                redis_ids = [key.split(":", 1)[1] for key in redis_keys]
                # Combine with cache manager keys
                hot_tier_items = list(set(hot_tier_items + redis_ids))
            except Exception as e:
                logger.warning(f"Error getting hot tier keys from Redis: {e}")

        # Process items in hot tier
        for item_id in hot_tier_items:
            # Check if item should be demoted to warm tier
            last_access = self._last_access_time.get(item_id, datetime.fromtimestamp(0))
            access_count = self._access_counts.get(item_id, 0)

            # Demote if old or infrequently accessed
            if (current_time - last_access > self._hot_tier_max_age or 
                access_count < self._min_access_count_hot):
                try:
                    # Get the item data
                    item_dict = self._hot_cache_manager.get(item_id)
                    if item_dict:
                        item = MemoryItem(**item_dict)
                        await self._migrate_item(item_id, StorageTier.HOT, StorageTier.WARM)
                    else:
                        # If not in cache manager but in Redis, try Redis
                        if self._redis_client:
                            redis_key = f"hot_tier:{item_id}"
                            item_json = self._redis_client.get(redis_key)
                            if item_json:
                                item_dict = json.loads(item_json)
                                item = MemoryItem(**item_dict)
                                await self._migrate_item(item_id, StorageTier.HOT, StorageTier.WARM)
                except Exception as e:
                    logger.warning(f"Error migrating hot tier item {item_id}: {e}")

        # Process items in warm tier (batch processing)
        try:
            warm_query = self._firestore_client.collection("warm_tier").limit(100)
            warm_docs = warm_query.stream()
            
            tasks = []
            for doc in warm_docs:
                item_id = doc.id
                
                # Check if item should be promoted to hot tier or demoted to cold
                last_access = self._last_access_time.get(item_id, datetime.fromtimestamp(0))
                access_count = self._access_counts.get(item_id, 0)
                
                if access_count >= self._min_access_count_hot:
                    # Promote to hot tier if frequently accessed
                    item_dict = doc.to_dict()
                    try:
                        item = MemoryItem(**item_dict)
                        tasks.append(self._migrate_item(item_id, StorageTier.WARM, StorageTier.HOT))
                    except Exception as e:
                        logger.warning(f"Error promoting item {item_id} to hot tier: {e}")
                elif current_time - last_access > self._warm_tier_max_age or access_count < self._min_access_count_warm:
                    # Demote to cold tier if old or infrequently accessed
                    item_dict = doc.to_dict()
                    try:
                        item = MemoryItem(**item_dict)
                        tasks.append(self._migrate_item(item_id, StorageTier.WARM, StorageTier.COLD))
                    except Exception as e:
                        logger.warning(f"Error demoting item {item_id} to cold tier: {e}")
            
            # Run migrations concurrently
            if tasks:
                await asyncio.gather(*tasks)
                
        except Exception as e:
            logger.error(f"Error processing warm tier items: {e}")
        
        logger.info("Tiered storage migration process completed")
    
    async def _load_access_tracking(self) -> None:
        """
        Load access tracking data from Firestore.
        
        This method loads access counts and last access times from Firestore
        to maintain access tracking across restarts.
        """
        try:
            # Load access counts
            access_counts_doc = self._firestore_client.collection("tiered_storage_meta").document("access_counts")
            if access_counts_doc.get().exists:
                self._access_counts = access_counts_doc.get().to_dict() or {}
                
            # Load last access times
            access_times_doc = self._firestore_client.collection("tiered_storage_meta").document("access_times")
            if access_times_doc.get().exists:
                # Convert ISO timestamp strings back to datetime objects
                access_times_dict = access_times_doc.get().to_dict() or {}
                for item_id, timestamp_str in access_times_dict.items():
                    try:
                        self._last_access_time[item_id] = datetime.fromisoformat(timestamp_str)
                    except (ValueError, TypeError):
                        # If we can't parse the timestamp, use current time
                        self._last_access_time[item_id] = datetime.now()
                        
            logger.info(f"Loaded access tracking data for {len(self._access_counts)} items")
            
        except Exception as e:
            logger.warning(f"Failed to load access tracking data: {e}")
            # Initialize empty tracking data
            self._access_counts = {}
            self._last_access_time = {}
    
    async def _save_access_tracking(self) -> None:
        """
        Save access tracking data to Firestore.
        
        This method saves access counts and last access times to Firestore
        to maintain access tracking across restarts.
        """
        try:
            # Save access counts
            access_counts_doc = self._firestore_client.collection("tiered_storage_meta").document("access_counts")
            access_counts_doc.set(self._access_counts)
            
            # Save last access times (convert datetime to ISO strings)
            access_times_dict = {}
            for item_id, dt in self._last_access_time.items():
                try:
                    access_times_dict[item_id] = dt.isoformat()
                except (AttributeError, TypeError):
                    # If it's not a valid datetime, skip it
                    continue
            
            access_times_doc = self._firestore_client.collection("tiered_storage_meta").document("access_times")
            access_times_doc.set(access_times_dict)
            
            logger.debug(f"Saved access tracking data for {len(self._access_counts)} items")
            
        except Exception as e:
            logger.warning(f"Failed to save access tracking data: {e}")
