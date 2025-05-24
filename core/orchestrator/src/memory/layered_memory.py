"""
Layered memory implementation for AI Orchestra.

This module provides a unified memory system with short-term, mid-term, and long-term memory capabilities.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from core.orchestrator.src.memory.interface import MemoryInterface

logger = logging.getLogger(__name__)


class LayeredMemory:
    """
    Layered memory implementation for AI Orchestra.

    This class provides a unified memory system with multiple layers:
    - Short-term memory: Fast, ephemeral storage (Redis)
    - Mid-term memory: Structured storage (Firestore)
    - Long-term memory: Persistent storage (Firestore)
    - Semantic memory: Vector-based storage (Vertex AI)
    """

    def __init__(
        self,
        layers: Dict[str, MemoryInterface],
        auto_promote: bool = True,
        auto_demote: bool = False,
    ):
        """
        Initialize layered memory.

        Args:
            layers: Dictionary mapping layer names to memory backends
            auto_promote: Whether to automatically promote items to higher memory layers
            auto_demote: Whether to automatically demote items to lower memory layers
        """
        self.layers = layers
        self.auto_promote = auto_promote
        self.auto_demote = auto_demote

        # Define layer hierarchy for promotion/demotion
        self.layer_hierarchy = ["short_term", "mid_term", "long_term"]

        logger.info(f"LayeredMemory initialized with layers: {list(layers.keys())}")

    async def store(
        self,
        key: str,
        value: Dict[str, Any],
        layer: str = "short_term",
        ttl: Optional[int] = None,
        cascade: bool = False,
    ) -> bool:
        """
        Store an item in memory.

        Args:
            key: The key to store the value under
            value: The value to store
            layer: The layer to store in
            ttl: Time-to-live in seconds (optional)
            cascade: Whether to cascade storage to lower layers

        Returns:
            True if successful, False otherwise
        """
        # Check if the specified layer exists
        if layer not in self.layers:
            logger.error(f"Layer '{layer}' not found")
            return False

        # Add metadata
        document = value.copy()
        document["stored_at"] = int(time.time())
        document["memory_key"] = key
        document["memory_layer"] = layer

        # Store in the specified layer
        success = await self.layers[layer].store(key, document, ttl)

        if not success:
            logger.error(f"Failed to store item with key {key} in layer {layer}")
            return False

        # If cascade is enabled, store in lower layers
        if cascade and layer in self.layer_hierarchy:
            layer_index = self.layer_hierarchy.index(layer)

            # Store in all layers below the specified layer
            for lower_layer in self.layer_hierarchy[:layer_index]:
                if lower_layer in self.layers:
                    await self.layers[lower_layer].store(key, document, ttl)

        return True

    async def retrieve(
        self, key: str, layers: Optional[List[str]] = None, migrate: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an item from memory.

        Args:
            key: The key to retrieve
            layers: The layers to search in (default: all layers in hierarchy order)
            migrate: Whether to migrate items between layers

        Returns:
            The stored value, or None if not found
        """
        result = None
        found_layer = None

        # If no layers specified, use all layers in hierarchy order
        if layers is None:
            search_layers = self.layer_hierarchy.copy()

            # Add any layers not in the hierarchy
            for layer in self.layers:
                if layer not in search_layers:
                    search_layers.append(layer)
        else:
            search_layers = layers

        # Search in each layer
        for layer in search_layers:
            if layer in self.layers:
                result = await self.layers[layer].retrieve(key)

                if result is not None:
                    found_layer = layer
                    break

        # If item was found and migration is enabled, handle promotion
        if result is not None and migrate and found_layer in self.layer_hierarchy and self.auto_promote:
            layer_index = self.layer_hierarchy.index(found_layer)

            # Promote to all layers above the found layer
            for higher_layer in self.layer_hierarchy[layer_index + 1 :]:
                if higher_layer in self.layers:
                    await self.layers[higher_layer].store(key, result)

        return result

    async def delete(self, key: str, layers: Optional[List[str]] = None) -> bool:
        """
        Delete an item from memory.

        Args:
            key: The key to delete
            layers: The layers to delete from (default: all layers)

        Returns:
            True if successful, False otherwise
        """
        success = True

        # If no layers specified, use all layers
        if layers is None:
            delete_layers = list(self.layers.keys())
        else:
            delete_layers = layers

        # Delete from each layer
        for layer in delete_layers:
            if layer in self.layers:
                if not await self.layers[layer].delete(key):
                    success = False
                    logger.error(f"Failed to delete item with key {key} from layer {layer}")

        return success

    async def exists(self, key: str, layers: Optional[List[str]] = None) -> bool:
        """
        Check if an item exists in memory.

        Args:
            key: The key to check
            layers: The layers to check in (default: all layers)

        Returns:
            True if the item exists, False otherwise
        """
        # If no layers specified, use all layers
        if layers is None:
            check_layers = list(self.layers.keys())
        else:
            check_layers = layers

        # Check each layer
        for layer in check_layers:
            if layer in self.layers and await self.layers[layer].exists(key):
                return True

        return False

    async def search(
        self,
        field: str,
        value: Any,
        operator: str = "==",
        limit: int = 10,
        layers: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for items in memory.

        Args:
            field: The field to search on
            value: The value to search for
            operator: The comparison operator to use
            limit: Maximum number of results to return
            layers: The layers to search in (default: all layers in hierarchy order)

        Returns:
            List of matching items
        """
        results = []

        # If field is "semantic", use semantic search
        if field == "semantic" and "semantic" in self.layers:
            return await self.layers["semantic"].search("semantic", value, operator, limit)

        # If no layers specified, use all layers in hierarchy order
        if layers is None:
            search_layers = self.layer_hierarchy.copy()

            # Add any layers not in the hierarchy
            for layer in self.layers:
                if layer not in search_layers:
                    search_layers.append(layer)
        else:
            search_layers = layers

        # Search in each layer
        for layer in search_layers:
            if layer in self.layers:
                # Skip if we already have enough results
                if len(results) >= limit:
                    break

                # Search in this layer
                layer_results = await self.layers[layer].search(field, value, operator, limit - len(results))

                # Add unique results
                existing_keys = {item.get("id", item.get("memory_key", "")) for item in results}
                for item in layer_results:
                    item_key = item.get("id", item.get("memory_key", ""))
                    if item_key not in existing_keys:
                        results.append(item)
                        existing_keys.add(item_key)

        return results

    async def update(self, key: str, updates: Dict[str, Any], layers: Optional[List[str]] = None) -> bool:
        """
        Update an item in memory.

        Args:
            key: The key of the item to update
            updates: The fields to update
            layers: The layers to update in (default: all layers)

        Returns:
            True if successful, False otherwise
        """
        success = True

        # Add metadata
        document = updates.copy()
        document["updated_at"] = int(time.time())

        # If no layers specified, use all layers
        if layers is None:
            update_layers = list(self.layers.keys())
        else:
            update_layers = layers

        # Update in each layer
        for layer in update_layers:
            if layer in self.layers:
                if not await self.layers[layer].update(key, document):
                    success = False
                    logger.error(f"Failed to update item with key {key} in layer {layer}")

        return success

    async def clear(self, layers: Optional[List[str]] = None) -> bool:
        """
        Clear all items from memory.

        Args:
            layers: The layers to clear (default: all layers)

        Returns:
            True if successful, False otherwise
        """
        success = True

        # If no layers specified, use all layers
        if layers is None:
            clear_layers = list(self.layers.keys())
        else:
            clear_layers = layers

        # Clear each layer
        for layer in clear_layers:
            if layer in self.layers:
                if hasattr(self.layers[layer], "clear_all") and callable(getattr(self.layers[layer], "clear_all")):
                    if not await self.layers[layer].clear_all():
                        success = False
                        logger.error(f"Failed to clear layer {layer}")
                elif hasattr(self.layers[layer], "clear") and callable(getattr(self.layers[layer], "clear")):
                    if not await self.layers[layer].clear():
                        success = False
                        logger.error(f"Failed to clear layer {layer}")
                else:
                    logger.warning(f"Layer {layer} does not support clearing")

        return success

    async def promote(self, key: str, from_layer: str, to_layer: str) -> bool:
        """
        Promote an item from one layer to another.

        Args:
            key: The key of the item to promote
            from_layer: The source layer
            to_layer: The target layer

        Returns:
            True if successful, False otherwise
        """
        # Check if the layers exist
        if from_layer not in self.layers:
            logger.error(f"Layer '{from_layer}' not found")
            return False

        if to_layer not in self.layers:
            logger.error(f"Layer '{to_layer}' not found")
            return False

        # Retrieve the item from the source layer
        item = await self.layers[from_layer].retrieve(key)
        if item is None:
            logger.error(f"Item with key {key} not found in layer {from_layer}")
            return False

        # Store the item in the target layer
        if not await self.layers[to_layer].store(key, item):
            logger.error(f"Failed to store item with key {key} in layer {to_layer}")
            return False

        return True

    async def demote(self, key: str, from_layer: str, to_layer: str) -> bool:
        """
        Demote an item from one layer to another.

        Args:
            key: The key of the item to demote
            from_layer: The source layer
            to_layer: The target layer

        Returns:
            True if successful, False otherwise
        """
        # This is essentially the same as promote, but with different semantics
        return await self.promote(key, from_layer, to_layer)

    async def semantic_search(
        self, query: str, limit: int = 10, layers: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search.

        Args:
            query: The query text
            limit: Maximum number of results to return
            layers: The layers to search in (default: semantic layer)

        Returns:
            List of matching items
        """
        # If no layers specified, use semantic layer if available
        if layers is None:
            if "semantic" in self.layers:
                return await self.layers["semantic"].search("semantic", query, "==", limit)
            else:
                search_layers = self.layer_hierarchy.copy()
        else:
            search_layers = layers

        results = []

        # Search in each layer
        for layer in search_layers:
            if layer in self.layers:
                # Skip if we already have enough results
                if len(results) >= limit:
                    break

                # For semantic layer, use semantic search
                if layer == "semantic":
                    layer_results = await self.layers[layer].search("semantic", query, "==", limit - len(results))
                # For other layers, use text search
                else:
                    # Try content field first
                    content_results = await self.layers[layer].search(
                        "content", query, "contains", limit - len(results)
                    )

                    # If no results, try text field
                    if not content_results:
                        layer_results = await self.layers[layer].search("text", query, "contains", limit - len(results))
                    else:
                        layer_results = content_results

                # Add unique results
                existing_keys = {item.get("id", item.get("memory_key", "")) for item in results}
                for item in layer_results:
                    item_key = item.get("id", item.get("memory_key", ""))
                    if item_key not in existing_keys:
                        results.append(item)
                        existing_keys.add(item_key)

        return results

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about all memory layers.

        Returns:
            Dictionary of statistics by layer
        """
        stats = {}

        for layer_name, layer_backend in self.layers.items():
            try:
                if hasattr(layer_backend, "get_stats") and callable(getattr(layer_backend, "get_stats")):
                    layer_stats = await layer_backend.get_stats()
                    stats[layer_name] = layer_stats
                else:
                    stats[layer_name] = {"error": "get_stats not implemented"}
            except Exception as e:
                logger.error(f"Error getting stats from layer {layer_name}: {e}")
                stats[layer_name] = {"error": str(e)}

        return stats

    async def ttl(self, key: str, ttl: int, layers: Optional[List[str]] = None) -> bool:
        """
        Set the time-to-live for a key in the specified layers.

        Args:
            key: The key to set TTL for
            ttl: Time-to-live in seconds
            layers: List of layers to set TTL in (defaults to all layers)

        Returns:
            True if successful in at least one layer, False otherwise
        """
        # Default to all layers
        if layers is None:
            ttl_layers = list(self.layers.keys())
        else:
            ttl_layers = layers

        success = False

        # Set TTL in each layer
        for layer_name in ttl_layers:
            if layer_name not in self.layers:
                logger.warning(f"Layer {layer_name} not found in memory layers")
                continue

            if hasattr(self.layers[layer_name], "ttl") and callable(getattr(self.layers[layer_name], "ttl")):
                result = await self.layers[layer_name].ttl(key, ttl)
                success = success or result
            else:
                logger.warning(f"Layer {layer_name} does not support TTL")

        return success
