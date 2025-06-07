"""
"""
    """
    """
        """
        """
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
        """
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
        except Exception:

            pass
            logger.exception(f"Exception during store operation for key {key} in layer {layer}: {e}")
            return False
        finally:
            duration = time.perf_counter() - start_time
            logger.info(f"store(key={key}, layer={layer}) took {duration:.4f}s")

    async def retrieve(
        self, key: str, layers: Optional[List[str]] = None, migrate: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        """
            logger.exception(f"Exception during retrieve operation for key {key}: {e}")
            return None
        finally:
            duration = time.perf_counter() - start_time
            logger.info(f"retrieve(key={key}) took {duration:.4f}s")

    async def delete(self, key: str, layers: Optional[List[str]] = None) -> bool:
        """
        """
                    logger.error(f"Failed to delete item with key {key} from layer {layer}")

        return success

    async def exists(self, key: str, layers: Optional[List[str]] = None) -> bool:
        """
        """
        operator: str = "==",
        limit: int = 10,
        layers: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        """
            # If field is "semantic", use semantic search
            if field == "semantic" and "semantic" in self.layers:
                return await self.layers["semantic"].search("semantic", value, operator, limit)

            # If no layers specified, use all layers in hierarchy order
            if layers is None:
                search_layers = self.layer_hierarchy.copy()

                # Add any layers not in the hierarchy
                # TODO: Consider using list comprehension for better performance

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
        except Exception:

            pass
            logger.exception(f"Exception during search operation for field {field}: {e}")
            return []
        finally:
            duration = time.perf_counter() - start_time
            logger.info(f"search(field={field}) took {duration:.4f}s")

    async def update(self, key: str, updates: Dict[str, Any], layers: Optional[List[str]] = None) -> bool:
        """
        """
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
        """
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
        """
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
        """
        """
        This method always prioritizes the "semantic" layer (e.g., Weaviate or other vector DB) if available,
        offloading heavy computation to the vector DB for optimal scalability and performance.
        If the "semantic" layer is not present, falls back to text search in other layers.

        Parameters
        ----------
        query : str
            The query text.
        limit : int
            Maximum number of results to return.
        layers : Optional[List[str]]
            The layers to search in (default: semantic layer).

        Returns
        -------
        List[Dict[str, Any]]
            List of matching items.
        """
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
        """
                if hasattr(layer_backend, "get_stats") and callable(getattr(layer_backend, "get_stats")):
                    layer_stats = await layer_backend.get_stats()
                    stats[layer_name] = layer_stats
                else:
                    stats[layer_name] = {"error": "get_stats not implemented"}
            except Exception:

                pass
                logger.error(f"Error getting stats from layer {layer_name}: {e}")
                stats[layer_name] = {"error": str(e)}

        return stats

    async def ttl(self, key: str, ttl: int, layers: Optional[List[str]] = None) -> bool:
        """
        """
                logger.warning(f"Layer {layer_name} not found in memory layers")
                continue

            if hasattr(self.layers[layer_name], "ttl") and callable(getattr(self.layers[layer_name], "ttl")):
                result = await self.layers[layer_name].ttl(key, ttl)
                success = success or result
            else:
                logger.warning(f"Layer {layer_name} does not support TTL")

        return success
