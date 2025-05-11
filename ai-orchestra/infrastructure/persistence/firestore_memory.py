"""
Firestore implementation of the memory provider interface.

This module provides a Firestore-based implementation of the memory provider.
"""

import json
import time
from typing import Any, Dict, List, Optional, Union
import asyncio

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from ai_orchestra.core.interfaces.memory import MemoryProvider
from ai_orchestra.core.errors import MemoryError
from ai_orchestra.core.config import settings
from ai_orchestra.utils.logging import log_event, log_start, log_end, log_error

import logging
logger = logging.getLogger("ai_orchestra.infrastructure.persistence.firestore_memory")


class FirestoreMemoryProvider:
    """Firestore implementation of the memory provider interface."""
    
    def __init__(
        self,
        collection_name: str = "memory",
        client: Optional[firestore.Client] = None,
    ):
        """
        Initialize the Firestore memory provider.
        
        Args:
            collection_name: The Firestore collection name
            client: Optional Firestore client
        """
        self.collection_name = collection_name
        
        # Use provided client or create a new one
        if client:
            self.client = client
        else:
            # Use emulator if configured
            if settings.database.use_firestore_emulator and settings.database.firestore_emulator_host:
                import os
                os.environ["FIRESTORE_EMULATOR_HOST"] = settings.database.firestore_emulator_host
            
            self.client = firestore.Client(project=settings.gcp.project_id)
        
        log_event(logger, "firestore_memory_provider", "initialized", {
            "collection_name": collection_name,
            "project_id": settings.gcp.project_id,
        })
    
    async def store(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store a value with an optional TTL.
        
        Args:
            key: The key to store the value under
            value: The value to store
            ttl: Optional time-to-live in seconds
            
        Returns:
            True if the value was stored successfully, False otherwise
            
        Raises:
            MemoryError: If there was an error storing the value
        """
        start_time = log_start(logger, "store", {"key": key})
        
        try:
            # Serialize the value to JSON
            if not isinstance(value, (str, int, float, bool, dict, list, type(None))):
                value = json.dumps({"serialized": str(value)})
            
            # Calculate expiry time if TTL is provided
            expiry = int(time.time() + ttl) if ttl else None
            
            # Create document data
            doc_data = {
                "key": key,
                "value": value,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
            
            if expiry:
                doc_data["expiry"] = expiry
            
            # Store the document
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.collection(self.collection_name).document(key).set(doc_data)
            )
            
            log_end(logger, "store", start_time, {"key": key, "success": True})
            return True
            
        except Exception as e:
            log_error(logger, "store", e, {"key": key})
            raise MemoryError(f"Failed to store value for key '{key}'", cause=e)
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve a value by key.
        
        Args:
            key: The key to retrieve the value for
            
        Returns:
            The stored value, or None if not found
            
        Raises:
            MemoryError: If there was an error retrieving the value
        """
        start_time = log_start(logger, "retrieve", {"key": key})
        
        try:
            # Get the document
            doc_ref = self.client.collection(self.collection_name).document(key)
            doc = await asyncio.get_event_loop().run_in_executor(None, doc_ref.get)
            
            # Check if document exists
            if not doc.exists:
                log_end(logger, "retrieve", start_time, {"key": key, "exists": False})
                return None
            
            # Get document data
            data = doc.to_dict()
            
            # Check if document has expired
            if "expiry" in data and data["expiry"] < time.time():
                # Document has expired, delete it
                await asyncio.get_event_loop().run_in_executor(None, doc_ref.delete)
                log_end(logger, "retrieve", start_time, {"key": key, "expired": True})
                return None
            
            # Return the value
            log_end(logger, "retrieve", start_time, {"key": key, "exists": True})
            return data["value"]
            
        except Exception as e:
            log_error(logger, "retrieve", e, {"key": key})
            raise MemoryError(f"Failed to retrieve value for key '{key}'", cause=e)
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value by key.
        
        Args:
            key: The key to delete
            
        Returns:
            True if the value was deleted successfully, False otherwise
            
        Raises:
            MemoryError: If there was an error deleting the value
        """
        start_time = log_start(logger, "delete", {"key": key})
        
        try:
            # Delete the document
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.collection(self.collection_name).document(key).delete()
            )
            
            log_end(logger, "delete", start_time, {"key": key, "success": True})
            return True
            
        except Exception as e:
            log_error(logger, "delete", e, {"key": key})
            raise MemoryError(f"Failed to delete value for key '{key}'", cause=e)
    
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
            
        Raises:
            MemoryError: If there was an error checking if the key exists
        """
        start_time = log_start(logger, "exists", {"key": key})
        
        try:
            # Get the document
            doc_ref = self.client.collection(self.collection_name).document(key)
            doc = await asyncio.get_event_loop().run_in_executor(None, doc_ref.get)
            
            # Check if document exists
            exists = doc.exists
            
            # If document exists, check if it has expired
            if exists and "expiry" in doc.to_dict() and doc.to_dict()["expiry"] < time.time():
                # Document has expired, delete it
                await asyncio.get_event_loop().run_in_executor(None, doc_ref.delete)
                exists = False
            
            log_end(logger, "exists", start_time, {"key": key, "exists": exists})
            return exists
            
        except Exception as e:
            log_error(logger, "exists", e, {"key": key})
            raise MemoryError(f"Failed to check if key '{key}' exists", cause=e)
    
    async def list_keys(self, pattern: str = "*") -> List[str]:
        """
        List keys matching a pattern.
        
        Args:
            pattern: The pattern to match keys against
            
        Returns:
            A list of matching keys
            
        Raises:
            MemoryError: If there was an error listing keys
        """
        start_time = log_start(logger, "list_keys", {"pattern": pattern})
        
        try:
            # Firestore doesn't support glob patterns directly, so we need to handle this differently
            # For now, we'll just list all keys and filter them in Python
            # In a real implementation, you might want to use a more efficient approach
            
            # Get all documents
            collection_ref = self.client.collection(self.collection_name)
            docs = await asyncio.get_event_loop().run_in_executor(None, collection_ref.stream)
            
            # Convert pattern to regex
            import re
            pattern_regex = re.compile(pattern.replace("*", ".*"))
            
            # Filter keys by pattern and check expiry
            current_time = time.time()
            keys = []
            
            for doc in docs:
                data = doc.to_dict()
                key = data.get("key")
                
                # Skip if key doesn't match pattern
                if not key or not pattern_regex.match(key):
                    continue
                
                # Skip if document has expired
                if "expiry" in data and data["expiry"] < current_time:
                    continue
                
                keys.append(key)
            
            log_end(logger, "list_keys", start_time, {"pattern": pattern, "count": len(keys)})
            return keys
            
        except Exception as e:
            log_error(logger, "list_keys", e, {"pattern": pattern})
            raise MemoryError(f"Failed to list keys matching pattern '{pattern}'", cause=e)