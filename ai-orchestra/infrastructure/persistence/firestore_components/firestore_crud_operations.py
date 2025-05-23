"""
Handles basic Create, Read, Update, Delete (CRUD) operations for memory items
in Firestore. This class directly interacts with the Firestore client for
document manipulation.
"""
# import asyncio # Not used in current outline
import logging
from typing import Dict, Any, Optional # Removed List as it might not be used yet

# from google.cloud import firestore # Potentially unused direct import
from google.cloud.firestore_v1.async_client import AsyncClient as FirestoreAsyncClient
from google.cloud.firestore_v1.async_document import AsyncDocumentReference
# from google.cloud.firestore_v1.base_query import AsyncBaseQuery # Not used in this CRUD file

# Assuming a shared logger or get one
# from core.logging_config import get_logger
# logger = get_logger(__name__)
# For now, using a standard logger
logger = logging.getLogger(__name__)

class FirestoreCrudOperations:
    """
    Provides basic CRUD operations for Firestore documents representing memory items.
    """

    def __init__(self, firestore_client: FirestoreAsyncClient, collection_name: str):
        """
        Initializes the FirestoreCrudOperations.

        Args:
            firestore_client: An initialized instance of Firestore AsyncClient.
            collection_name: The name of the Firestore collection to operate on.
        """
        if not isinstance(firestore_client, FirestoreAsyncClient):
            raise TypeError("firestore_client must be an instance of FirestoreAsyncClient.")
        if not collection_name or not isinstance(collection_name, str):
            raise ValueError("collection_name must be a non-empty string.")
            
        self.client: FirestoreAsyncClient = firestore_client
        self.collection_name: str = collection_name
        self._collection_ref = self.client.collection(self.collection_name)
        logger.info(f"FirestoreCrudOperations initialized for collection: {self.collection_name}")

    async def create_item(self, item_id: str, data: Dict[str, Any]) -> bool:
        """
        Creates a new document in Firestore with the given item_id and data.
        This method will fail if a document with the same item_id already exists.

        Args:
            item_id: The unique ID for the new memory item (document ID).
            data: A dictionary containing the data to store. 
                  Should be Firestore-compatible (e.g., primitive types, lists, dicts).

        Returns:
            True if the item was created successfully, False otherwise (e.g., if item already exists).
        
        Raises:
            ValueError: If item_id or data is invalid.
            Exception: For underlying Firestore errors.
        """
        if not item_id or not isinstance(item_id, str):
            raise ValueError("item_id must be a non-empty string.")
        if not isinstance(data, dict):
            raise ValueError("data must be a dictionary.")
        
        logger.debug(f"Attempting to create item '{item_id}' in '{self.collection_name}'")
        doc_ref: AsyncDocumentReference = self._collection_ref.document(item_id)
        try:
            # Use create() to ensure the document doesn't already exist.
            await doc_ref.create(document_data=data)
            logger.info(f"Successfully created item '{item_id}' in '{self.collection_name}'.")
            return True
        except Exception as e: # Replace with more specific google.cloud.exceptions.Conflict if needed
            logger.error(f"Error creating item '{item_id}' in '{self.collection_name}': {e}", exc_info=True)
            # Could be a google.cloud.exceptions.Conflict if item_id already exists
            # Or other Firestore errors.
            return False # Or re-raise a custom domain error

    async def create_or_update_item(self, item_id: str, data: Dict[str, Any]) -> bool:
        """
        Creates a new document or overwrites an existing document in Firestore
        with the given item_id and data. Uses Firestore's set() method.

        Args:
            item_id: The unique ID for the memory item (document ID).
            data: A dictionary containing the data to store.

        Returns:
            True if the operation was successful.
            
        Raises:
            ValueError: If item_id or data is invalid.
            Exception: For underlying Firestore errors.
        """
        if not item_id or not isinstance(item_id, str):
            raise ValueError("item_id must be a non-empty string.")
        if not isinstance(data, dict):
            raise ValueError("data must be a dictionary.")

        logger.debug(f"Attempting to set (create/update) item '{item_id}' in '{self.collection_name}'")
        doc_ref: AsyncDocumentReference = self._collection_ref.document(item_id)
        try:
            # Using set() with merge=False will overwrite the document if it exists,
            # or create it if it doesn't.
            await doc_ref.set(document_data=data, merge=False) 
            logger.info(f"Successfully set item '{item_id}' in '{self.collection_name}'.")
            return True
        except Exception as e:
            logger.error(f"Error setting item '{item_id}' in '{self.collection_name}': {e}", exc_info=True)
            return False # Or re-raise

    async def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a document from Firestore by its ID.

        Args:
            item_id: The ID of the memory item to retrieve.

        Returns:
            A dictionary containing the document data if found, otherwise None.
            
        Raises:
            ValueError: If item_id is invalid.
            Exception: For underlying Firestore errors.
        """
        if not item_id or not isinstance(item_id, str):
            raise ValueError("item_id must be a non-empty string.")

        logger.debug(f"Attempting to get item '{item_id}' from '{self.collection_name}'")
        doc_ref: AsyncDocumentReference = self._collection_ref.document(item_id)
        try:
            doc_snapshot = await doc_ref.get()
            if doc_snapshot.exists:
                logger.info(f"Successfully retrieved item '{item_id}'.")
                return doc_snapshot.to_dict()
            else:
                logger.info(f"Item '{item_id}' not found in '{self.collection_name}'.")
                return None
        except Exception as e:
            logger.error(f"Error getting item '{item_id}': {e}", exc_info=True)
            return None # Or re-raise

    async def update_item(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        Updates an existing document in Firestore with the provided data.
        This method will fail if the document does not already exist.
        Uses Firestore's update() method, which supports field_paths for nested updates.

        Args:
            item_id: The ID of the memory item to update.
            updates: A dictionary containing the fields and new values to update.
                     Supports dot notation for nested fields (e.g., "metadata.source": "new_source").

        Returns:
            True if the update was successful, False if the document was not found or an error occurred.
            
        Raises:
            ValueError: If item_id or updates is invalid.
            Exception: For underlying Firestore errors.
        """
        if not item_id or not isinstance(item_id, str):
            raise ValueError("item_id must be a non-empty string.")
        if not isinstance(updates, dict) or not updates:
            raise ValueError("updates must be a non-empty dictionary.")

        logger.debug(f"Attempting to update item '{item_id}' in '{self.collection_name}' with: {updates}")
        doc_ref: AsyncDocumentReference = self._collection_ref.document(item_id)
        try:
            # First, check if the document exists before attempting an update.
            # Firestore's update() will fail if the document doesn't exist.
            doc_snapshot = await doc_ref.get()
            if not doc_snapshot.exists:
                logger.warning(f"Cannot update item '{item_id}': document not found.")
                return False
            
            await doc_ref.update(updates)
            logger.info(f"Successfully updated item '{item_id}'.")
            return True
        except Exception as e: # Replace with more specific google.cloud.exceptions.NotFound if needed for update
            logger.error(f"Error updating item '{item_id}': {e}", exc_info=True)
            return False # Or re-raise

    async def delete_item(self, item_id: str) -> bool:
        """
        Deletes a document from Firestore by its ID.

        Args:
            item_id: The ID of the memory item to delete.

        Returns:
            True if the deletion was successful or if the document didn't exist.
            False if an error occurred during deletion.
            
        Raises:
            ValueError: If item_id is invalid.
            Exception: For underlying Firestore errors.
        """
        if not item_id or not isinstance(item_id, str):
            raise ValueError("item_id must be a non-empty string.")

        logger.debug(f"Attempting to delete item '{item_id}' from '{self.collection_name}'")
        doc_ref: AsyncDocumentReference = self._collection_ref.document(item_id)
        try:
            await doc_ref.delete()
            # Firestore's delete() does not raise an error if the document doesn't exist.
            # It's considered a successful deletion in that case.
            logger.info(f"Successfully deleted item '{item_id}' (or it did not exist).")
            return True
        except Exception as e:
            logger.error(f"Error deleting item '{item_id}': {e}", exc_info=True)
            return False # Or re-raise

    async def item_exists(self, item_id: str) -> bool:
        """
        Checks if a document with the given ID exists in Firestore.

        Args:
            item_id: The ID of the memory item to check.

        Returns:
            True if the document exists, False otherwise.

        Raises:
            ValueError: If item_id is invalid.
            Exception: For underlying Firestore errors.
        """
        if not item_id or not isinstance(item_id, str):
            raise ValueError("item_id must be a non-empty string.")

        logger.debug(f"Checking existence of item '{item_id}' in '{self.collection_name}'")
        doc_ref: AsyncDocumentReference = self._collection_ref.document(item_id)
        try:
            doc_snapshot = await doc_ref.get()
            exists = doc_snapshot.exists
            logger.debug(f"Item '{item_id}' exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking existence of item '{item_id}': {e}", exc_info=True)
            return False # Or re-raise, or return False indicating not findable due to error 