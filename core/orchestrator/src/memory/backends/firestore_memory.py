"""
Firestore memory backend for AI Orchestra.

This module provides a Firestore-based memory implementation for mid/long-term storage.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from google.cloud import firestore

from core.orchestrator.src.memory.interface import MemoryInterface

logger = logging.getLogger(__name__)

class FirestoreMemory(MemoryInterface):
    """Firestore-based memory implementation for mid/long-term storage."""
    
    def __init__(
        self,
        collection_name: str = "orchestra_memory",
        ttl: Optional[int] = None,
        client = None
    ):
        """
        Initialize Firestore memory.
        
        Args:
            collection_name: Name of the Firestore collection to use
            ttl: Time-to-live in seconds (optional)
            client: Firestore client (optional, will create one if not provided)
        """
        self.client = client or firestore.Client()
        self.collection = self.client.collection(collection_name)
        self.ttl = ttl
        logger.info(f"FirestoreMemory initialized with collection={collection_name}")
    
    async def store(self, key: str, value: Dict[str, Any], **kwargs) -> bool:
        """
        Store an item in Firestore.
        
        Args:
            key: Unique identifier for the item
            value: Data to store
            **kwargs: Additional parameters (ignored)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add timestamp and TTL info if needed
            if self.ttl:
                value["_timestamp"] = time.time()
                value["_expiry"] = time.time() + self.ttl
            
            # Store in Firestore
            self.collection.document(key).set(value)
            logger.debug(f"Stored item with key {key} in Firestore")
            return True
        except Exception as e:
            logger.error(f"Error storing item in Firestore: {e}")
            return False
    
    async def retrieve(self, key: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Retrieve an item from Firestore.
        
        Args:
            key: Unique identifier for the item
            **kwargs: Additional parameters (ignored)
            
        Returns:
            The stored data, or None if not found
        """
        try:
            doc = self.collection.document(key).get()
            if not doc.exists:
                logger.debug(f"Item with key {key} not found in Firestore")
                return None
            
            data = doc.to_dict()
            
            # Check if item has expired
            if self.ttl and "_expiry" in data:
                if data["_expiry"] < time.time():
                    # Item has expired, delete it
                    await self.delete(key)
                    logger.debug(f"Item with key {key} has expired")
                    return None
            
            logger.debug(f"Retrieved item with key {key} from Firestore")
            return data
        except Exception as e:
            logger.error(f"Error retrieving item from Firestore: {e}")
            return None
    
    async def delete(self, key: str, **kwargs) -> bool:
        """
        Delete an item from Firestore.
        
        Args:
            key: Unique identifier for the item
            **kwargs: Additional parameters (ignored)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.document(key).delete()
            logger.debug(f"Deleted item with key {key} from Firestore")
            return True
        except Exception as e:
            logger.error(f"Error deleting item from Firestore: {e}")
            return False
    
    async def get_all_keys(self, **kwargs) -> List[str]:
        """
        Get all document IDs in the collection.
        
        Args:
            **kwargs: Additional parameters (ignored)
            
        Returns:
            List of keys
        """
        try:
            docs = self.collection.stream()
            return [doc.id for doc in docs]
        except Exception as e:
            logger.error(f"Error getting keys from Firestore: {e}")
            return []
    
    async def clear(self, **kwargs) -> bool:
        """
        Clear all documents in the collection.
        
        Args:
            **kwargs: Additional parameters (ignored)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            batch_size = 500
            docs = self.collection.limit(batch_size).stream()
            deleted = 0
            
            # Delete in batches
            for doc in docs:
                doc.reference.delete()
                deleted += 1
            
            logger.info(f"Cleared {deleted} items from Firestore collection")
            return True
        except Exception as e:
            logger.error(f"Error clearing Firestore: {e}")
            return False
    
    async def batch_store(self, items: Dict[str, Dict[str, Any]], **kwargs) -> bool:
        """
        Store multiple items in Firestore using batched writes.
        
        Args:
            items: Dictionary mapping keys to values
            **kwargs: Additional parameters (ignored)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Firestore batches are limited to 500 operations
            batch_size = 500
            keys = list(items.keys())
            
            for i in range(0, len(keys), batch_size):
                batch = self.client.batch()
                batch_keys = keys[i:i+batch_size]
                
                for key in batch_keys:
                    value = items[key]
                    
                    # Add timestamp and TTL info if needed
                    if self.ttl:
                        value["_timestamp"] = time.time()
                        value["_expiry"] = time.time() + self.ttl
                    
                    # Add to batch
                    batch.set(self.collection.document(key), value)
                
                # Commit batch
                batch.commit()
            
            logger.debug(f"Batch stored {len(keys)} items in Firestore")
            return True
        except Exception as e:
            logger.error(f"Error batch storing items in Firestore: {e}")
            return False
    
    async def batch_retrieve(self, keys: List[str], **kwargs) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Retrieve multiple items from Firestore.
        
        Args:
            keys: List of keys to retrieve
            **kwargs: Additional parameters (ignored)
            
        Returns:
            Dictionary mapping keys to values (or None if not found)
        """
        try:
            results = {}
            
            # Firestore get() can retrieve up to 10 documents at once
            batch_size = 10
            
            for i in range(0, len(keys), batch_size):
                batch_keys = keys[i:i+batch_size]
                docs = [self.collection.document(key) for key in batch_keys]
                snapshots = self.client.get_all(docs)
                
                for key, snapshot in zip(batch_keys, snapshots):
                    if snapshot.exists:
                        data = snapshot.to_dict()
                        
                        # Check if item has expired
                        if self.ttl and "_expiry" in data:
                            if data["_expiry"] < time.time():
                                # Item has expired, delete it
                                await self.delete(key)
                                results[key] = None
                                continue
                        
                        results[key] = data
                    else:
                        results[key] = None
            
            logger.debug(f"Batch retrieved {len(keys)} items from Firestore")
            return results
        except Exception as e:
            logger.error(f"Error batch retrieving items from Firestore: {e}")
            return {key: None for key in keys}
    
    async def batch_delete(self, keys: List[str], **kwargs) -> bool:
        """
        Delete multiple items from Firestore using batched writes.
        
        Args:
            keys: List of keys to delete
            **kwargs: Additional parameters (ignored)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Firestore batches are limited to 500 operations
            batch_size = 500
            
            for i in range(0, len(keys), batch_size):
                batch = self.client.batch()
                batch_keys = keys[i:i+batch_size]
                
                for key in batch_keys:
                    batch.delete(self.collection.document(key))
                
                # Commit batch
                batch.commit()
            
            logger.debug(f"Batch deleted {len(keys)} items from Firestore")
            return True
        except Exception as e:
            logger.error(f"Error batch deleting items from Firestore: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Firestore collection.
        
        Returns:
            Dictionary of statistics
        """
        try:
            # Count documents
            query = self.collection.limit(1000000)  # Firestore limit
            docs = query.stream()
            count = sum(1 for _ in docs)
            
            # Get size estimate (rough approximation)
            size_bytes = 0
            sample_size = min(100, count)
            if sample_size > 0:
                sample_docs = self.collection.limit(sample_size).stream()
                for doc in sample_docs:
                    # Rough estimate: 1 byte per character in JSON representation
                    size_bytes += len(str(doc.to_dict()))
                
                # Extrapolate to full collection
                if sample_size < count:
                    size_bytes = int(size_bytes * (count / sample_size))
            
            return {
                "count": count,
                "size_bytes": size_bytes,
                "size_mb": round(size_bytes / (1024 * 1024), 2),
                "collection": self.collection.id
            }
        except Exception as e:
            logger.error(f"Error getting stats from Firestore: {e}")
            return {"error": str(e)}
    
    async def exists(self, key: str, **kwargs) -> bool:
        """
        Check if a key exists in Firestore.
        
        Args:
            key: Unique identifier for the item
            **kwargs: Additional parameters (ignored)
            
        Returns:
            True if the key exists, False otherwise
        """
        try:
            doc = self.collection.document(key).get()
            exists = doc.exists
            
            # Check if item has expired
            if exists and self.ttl:
                data = doc.to_dict()
                if "_expiry" in data and data["_expiry"] < time.time():
                    # Item has expired
                    exists = False
                    # Delete expired item
                    await self.delete(key)
            
            return exists
        except Exception as e:
            logger.error(f"Error checking if key exists in Firestore: {e}")
            return False
    
    async def ttl(self, key: str, ttl: int, **kwargs) -> bool:
        """
        Set the time-to-live for a key.
        
        Args:
            key: Unique identifier for the item
            ttl: Time-to-live in seconds
            **kwargs: Additional parameters (ignored)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the document
            doc = self.collection.document(key).get()
            if not doc.exists:
                logger.debug(f"Item with key {key} not found in Firestore")
                return False
            
            # Update the expiry
            data = doc.to_dict()
            data["_timestamp"] = time.time()
            data["_expiry"] = time.time() + ttl
            
            # Update the document
            self.collection.document(key).set(data)
            logger.debug(f"Updated TTL for key {key} in Firestore")
            return True
        except Exception as e:
            logger.error(f"Error updating TTL in Firestore: {e}")
            return False