"""
Provides utilities for performing batch write operations (create, set, update, delete)
efficiently in Firestore.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, Union, Sequence
import asyncio  # Added for asyncio.Lock in FirestoreClientManager example, ensure it's here if needed for other async ops directly.

from google.cloud.firestore_v1.async_client import AsyncClient as FirestoreAsyncClient
from google.cloud.firestore_v1.async_batch import AsyncWriteBatch
from google.cloud.firestore_v1.async_document import AsyncDocumentReference
from google.api_core.exceptions import GoogleAPIError

# Assuming MemoryItem is defined. If not, use a placeholder or basic dict.
# TODO: Replace with actual MemoryItem import if operations become type-specific for data
# from packages.shared.src.models.base_models import MemoryItem

logger = logging.getLogger(__name__)


class FirestoreBatchProcessor:
    """
    Handles batch write operations to Firestore for memory items.
    """

    # Firestore batch limit (documents per batch)
    FIRESTORE_BATCH_LIMIT = 500

    def __init__(self, firestore_client: FirestoreAsyncClient, collection_name: str):
        """
        Initializes the FirestoreBatchProcessor.

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
        logger.info(f"FirestoreBatchProcessor initialized for collection: {self.collection_name}")

    async def _execute_batches(self, operations: List[Tuple[str, str, Optional[Dict[str, Any]]]]) -> Dict[str, int]:
        """
        Internal helper to execute operations in batches.

        Args:
            operations: A list of tuples, where each tuple is
                        (operation_type: str, item_id: str, data: Optional[Dict]).
                        operation_type can be "create", "set", "set_merge", "update", "delete".
                        data is None for "delete", a dict for others.

        Returns:
            Dictionary with counts of successful and failed operations.
        """
        num_operations = len(operations)
        successful_ops = 0
        failed_ops = 0

        for i in range(0, num_operations, self.FIRESTORE_BATCH_LIMIT):
            batch_operations = operations[i : i + self.FIRESTORE_BATCH_LIMIT]
            batch: AsyncWriteBatch = self.client.batch()

            actual_ops_in_this_batch = 0
            for op_type, item_id, data_or_updates in batch_operations:
                doc_ref: AsyncDocumentReference = self._collection_ref.document(item_id)
                if op_type == "create":
                    if data_or_updates is None:
                        continue  # Should not happen for create
                    batch.create(doc_ref, data_or_updates)
                elif op_type == "set":  # Create or overwrite
                    if data_or_updates is None:
                        continue  # Should not happen for set
                    batch.set(doc_ref, data_or_updates, merge=False)
                elif op_type == "set_merge":  # Create or merge/update
                    if data_or_updates is None:
                        continue  # Should not happen for set_merge
                    batch.set(doc_ref, data_or_updates, merge=True)
                elif op_type == "update":
                    if data_or_updates is None:
                        continue  # Should not happen for update
                    batch.update(doc_ref, data_or_updates)
                elif op_type == "delete":
                    batch.delete(doc_ref)
                else:
                    logger.warning(f"Unknown batch operation type '{op_type}' for item '{item_id}'. Skipping.")
                    continue
                actual_ops_in_this_batch += 1

            if actual_ops_in_this_batch == 0:
                continue  # No valid operations in this slice

            try:
                await batch.commit()
                successful_ops += actual_ops_in_this_batch
                logger.info(
                    f"Successfully committed batch of {actual_ops_in_this_batch} operations to '{self.collection_name}'."
                )
            except GoogleAPIError as e:
                failed_ops += actual_ops_in_this_batch
                logger.error(f"Error committing a batch to '{self.collection_name}': {e}", exc_info=True)
            except Exception as e:
                failed_ops += actual_ops_in_this_batch
                logger.error(f"Unexpected error committing a batch to '{self.collection_name}': {e}", exc_info=True)

        return {"successful": successful_ops, "failed": failed_ops, "total_attempted": num_operations}

    async def batch_create_items(self, items_data: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
        """
        Creates multiple new documents in Firestore using batch operations.
        Fails for an item if a document with the same item_id already exists (handled by batch.create behavior).

        Args:
            items_data: A dictionary where keys are item_ids (document IDs) and
                        values are dictionaries of the data to store.

        Returns:
            A dictionary with counts: {"successful": int, "failed": int, "total_attempted": int}.
        """
        if not isinstance(items_data, dict):
            raise ValueError("items_data must be a dictionary of item_id:data.")

        operations: List[Tuple[str, str, Optional[Dict[str, Any]]]] = []
        for item_id, data in items_data.items():
            if not isinstance(item_id, str) or not item_id:
                logger.warning(f"Invalid item_id found in batch_create_items: {item_id}. Skipping.")
                continue
            if not isinstance(data, dict):
                logger.warning(f"Invalid data for item_id '{item_id}' in batch_create_items. Skipping.")
                continue
            operations.append(("create", item_id, data))
        return await self._execute_batches(operations)

    async def batch_set_items(self, items_data: Dict[str, Dict[str, Any]], merge: bool = False) -> Dict[str, int]:
        """
        Creates or overwrites/merges multiple documents in Firestore using batch operations.

        Args:
            items_data: A dictionary where keys are item_ids (document IDs) and
                        values are dictionaries of the data to store.
            merge: If True, performs a merge (update or create if not exists, merging fields).
                   If False (default), performs an overwrite (set or create if not exists, replacing document).

        Returns:
            A dictionary with counts: {"successful": int, "failed": int, "total_attempted": int}.
        """
        if not isinstance(items_data, dict):
            raise ValueError("items_data must be a dictionary of item_id:data.")

        op_type = "set_merge" if merge else "set"
        operations: List[Tuple[str, str, Optional[Dict[str, Any]]]] = []
        for item_id, data in items_data.items():
            if not isinstance(item_id, str) or not item_id:
                logger.warning(f"Invalid item_id found in batch_set_items: {item_id}. Skipping.")
                continue
            if not isinstance(data, dict):
                logger.warning(f"Invalid data for item_id '{item_id}' in batch_set_items. Skipping.")
                continue
            operations.append((op_type, item_id, data))
        return await self._execute_batches(operations)

    async def batch_update_items(self, items_updates: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
        """
        Updates multiple existing documents in Firestore using batch operations.
        An update for a specific item_id will fail if the document does not exist (Firestore batch.update behavior).

        Args:
            items_updates: A dictionary where keys are item_ids (document IDs) and
                           values are dictionaries of the fields to update.

        Returns:
            A dictionary with counts: {"successful": int, "failed": int, "total_attempted": int}.
        """
        if not isinstance(items_updates, dict):
            raise ValueError("items_updates must be a dictionary of item_id:updates.")

        operations: List[Tuple[str, str, Optional[Dict[str, Any]]]] = []
        for item_id, updates in items_updates.items():
            if not isinstance(item_id, str) or not item_id:
                logger.warning(f"Invalid item_id found in batch_update_items: {item_id}. Skipping.")
                continue
            if not isinstance(updates, dict) or not updates:  # Updates cannot be empty
                logger.warning(f"Invalid or empty updates for item_id '{item_id}' in batch_update_items. Skipping.")
                continue
            operations.append(("update", item_id, updates))
        return await self._execute_batches(operations)

    async def batch_delete_items(self, item_ids: List[str]) -> Dict[str, int]:
        """
        Deletes multiple documents from Firestore using batch operations.
        Deletions are considered successful even if a document didn't exist.

        Args:
            item_ids: A list of item_ids (document IDs) to delete.

        Returns:
            A dictionary with counts: {"successful": int, "failed": int, "total_attempted": int}.
        """
        if not isinstance(item_ids, list) or not all(isinstance(item_id, str) and item_id for item_id in item_ids):
            raise ValueError("item_ids must be a list of non-empty strings.")

        operations: List[Tuple[str, str, Optional[Dict[str, Any]]]] = [
            ("delete", item_id, None) for item_id in item_ids
        ]
        return await self._execute_batches(operations)
