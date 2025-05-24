#!/usr/bin/env python3
"""
memory_compression_engine.py - Optimized Memory Compression Engine

This module provides an optimized memory compression engine for compressing and
decompressing memory entries. It supports multiple compression levels and content
types, using efficient algorithms for each scenario.
"""

import zlib
import pickle
import json
import logging
import copy
from typing import Any, Dict, List, Optional, Union, Tuple

# Import from relative paths
from ..models.memory import MemoryEntry, CompressionLevel

logger = logging.getLogger(__name__)


class MemoryCompressionEngine:
    """Optimized memory compression engine with support for multiple content types."""

    @staticmethod
    def compress(entry: MemoryEntry) -> MemoryEntry:
        """Compress a memory entry based on its compression level and content type.

        Args:
            entry: The memory entry to compress

        Returns:
            MemoryEntry: The compressed memory entry
        """
        if entry.compression_level == CompressionLevel.NONE:
            return entry

        # Create a copy to avoid modifying the original
        compressed_entry = copy.deepcopy(entry)

        # Apply different compression strategies based on content type
        if isinstance(entry.content, str):
            compressed_entry.content = MemoryCompressionEngine._compress_string(entry.content, entry.compression_level)
        elif isinstance(entry.content, dict):
            compressed_entry.content = MemoryCompressionEngine._compress_dict(entry.content, entry.compression_level)
        elif isinstance(entry.content, list):
            compressed_entry.content = MemoryCompressionEngine._compress_list(entry.content, entry.compression_level)
        else:
            # For other types, try to convert to string and compress
            try:
                content_str = str(entry.content)
                compressed_entry.content = MemoryCompressionEngine._compress_string(
                    content_str, entry.compression_level
                )
            except Exception as e:
                logger.warning(f"Failed to compress content of type {type(entry.content)}: {e}")

        return compressed_entry

    @staticmethod
    def _compress_string(content: str, level: CompressionLevel) -> Any:
        """Compress string content based on compression level.

        Args:
            content: The string content to compress
            level: The compression level to apply

        Returns:
            Any: The compressed content
        """
        content_len = len(content)

        if level == CompressionLevel.LIGHT:
            # Basic compression: truncate long strings with ellipsis
            if content_len > 1000:
                return content[:900] + "... [compressed]"

        elif level == CompressionLevel.MEDIUM:
            # Medium compression: extract key sentences
            if content_len > 500:
                sentences = content.split(". ")
                if len(sentences) > 5:
                    important_sentences = sentences[:2] + ["..."] + sentences[-2:]
                    return ". ".join(important_sentences)

        elif level == CompressionLevel.HIGH:
            # High compression: binary compression for long strings
            if content_len > 300:
                compressed = zlib.compress(content.encode(), level=6)
                return {
                    "_compressed_data": compressed.hex(),
                    "_compression_type": "zlib",
                    "_original_type": "str",
                    "_original_length": content_len,
                }

        elif level == CompressionLevel.EXTREME:
            # Extreme compression: keep only first paragraph or binary compression
            if content_len > 100:
                if content_len > 1000:
                    # Use binary compression for very long strings
                    compressed = zlib.compress(content.encode(), level=9)
                    return {
                        "_compressed_data": compressed.hex(),
                        "_compression_type": "zlib",
                        "_original_type": "str",
                        "_original_length": content_len,
                    }
                else:
                    # Keep only first paragraph for shorter strings
                    paragraphs = content.split("\n\n")
                    return paragraphs[0] + " ... [extremely compressed]"

        elif level == CompressionLevel.REFERENCE_ONLY:
            # Reference only: keep only a reference
            return {
                "_reference": True,
                "_content_type": "str",
                "_content_length": content_len,
                "_content_preview": content[:50] + "..." if content_len > 50 else content,
            }

        return content

    @staticmethod
    def _compress_dict(content: Dict, level: CompressionLevel) -> Any:
        """Compress dictionary content based on compression level.

        Args:
            content: The dictionary content to compress
            level: The compression level to apply

        Returns:
            Any: The compressed content
        """
        # Get dictionary size metrics
        key_count = len(content)
        try:
            content_size = len(json.dumps(content))
        except (TypeError, ValueError):
            # Fallback for non-serializable content
            content_size = sum(len(str(k)) + len(str(v)) for k, v in content.items())

        if level == CompressionLevel.LIGHT:
            # Keep only key fields
            if key_count > 5:
                # Sort keys by length (assuming shorter keys are more important)
                sorted_keys = sorted(content.keys(), key=lambda k: len(str(k)))
                important_keys = set(sorted_keys[:5])
                result = {k: v for k, v in content.items() if k in important_keys}
                result["_compressed"] = True
                result["_total_keys"] = key_count
                return result

        elif level == CompressionLevel.MEDIUM:
            # Keep only a few key fields
            if key_count > 3:
                # Sort keys by length (assuming shorter keys are more important)
                sorted_keys = sorted(content.keys(), key=lambda k: len(str(k)))
                important_keys = set(sorted_keys[:3])
                result = {k: v for k, v in content.items() if k in important_keys}
                result["_compressed"] = True
                result["_total_keys"] = key_count
                return result

        elif level == CompressionLevel.HIGH:
            # Binary compression for large dictionaries
            if content_size > 500:
                try:
                    # Try to pickle and compress
                    pickled = pickle.dumps(content)
                    compressed = zlib.compress(pickled, level=6)
                    return {
                        "_compressed_data": compressed.hex(),
                        "_compression_type": "zlib+pickle",
                        "_original_type": "dict",
                        "_keys": list(content.keys()),
                        "_original_size": content_size,
                    }
                except (pickle.PickleError, TypeError):
                    # Fallback for non-picklable content: keep only keys
                    return {
                        "_compressed": True,
                        "_keys": list(content.keys()),
                        "_total_keys": key_count,
                        "_content_size": content_size,
                    }
            # Otherwise, keep only key names
            elif key_count > 3:
                return {
                    "_compressed": True,
                    "_keys": list(content.keys()),
                    "_total_keys": key_count,
                }

        elif level in [CompressionLevel.EXTREME, CompressionLevel.REFERENCE_ONLY]:
            # Keep only metadata for higher compression levels
            return {
                "_compressed": True,
                "_type": "dict",
                "_total_keys": key_count,
                "_content_size": content_size,
                "_keys_preview": list(content.keys())[:3] + (["..."] if key_count > 3 else []),
            }

        return content

    @staticmethod
    def _compress_list(content: list, level: CompressionLevel) -> Any:
        """Compress list content based on compression level.

        Args:
            content: The list content to compress
            level: The compression level to apply

        Returns:
            Any: The compressed content
        """
        # Get list size metrics
        item_count = len(content)
        try:
            content_size = len(json.dumps(content))
        except (TypeError, ValueError):
            # Fallback for non-serializable content
            content_size = sum(len(str(item)) for item in content)

        if level == CompressionLevel.LIGHT:
            # Keep only first few items
            if item_count > 10:
                return content[:5] + ["..."] + content[-2:]

        elif level == CompressionLevel.MEDIUM:
            # Keep only first and last items
            if item_count > 5:
                return content[:2] + ["..."] + content[-1:]

        elif level == CompressionLevel.HIGH:
            # Binary compression for large lists
            if content_size > 500:
                try:
                    # Try to pickle and compress
                    pickled = pickle.dumps(content)
                    compressed = zlib.compress(pickled, level=6)
                    return {
                        "_compressed_data": compressed.hex(),
                        "_compression_type": "zlib+pickle",
                        "_original_type": "list",
                        "_length": item_count,
                        "_original_size": content_size,
                    }
                except (pickle.PickleError, TypeError):
                    # Fallback for non-picklable content: keep only a few items
                    if item_count > 3:
                        return content[:1] + ["..."] + [f"[{item_count-2} items compressed]"]
            # Otherwise, keep only a few items
            elif item_count > 3:
                return content[:1] + ["..."] + [f"[{item_count-2} items compressed]"]

        elif level in [CompressionLevel.EXTREME, CompressionLevel.REFERENCE_ONLY]:
            # Keep only metadata for higher compression levels
            return {
                "_compressed": True,
                "_type": "list",
                "_length": item_count,
                "_content_size": content_size,
                "_items_preview": content[:1] + (["..."] if item_count > 1 else []),
            }

        return content

    @staticmethod
    def decompress(entry: MemoryEntry) -> MemoryEntry:
        """Decompress a memory entry if needed.

        Args:
            entry: The memory entry to decompress

        Returns:
            MemoryEntry: The decompressed memory entry
        """
        if not entry or entry.compression_level == CompressionLevel.NONE:
            return entry

        # Create a copy to avoid modifying the original
        decompressed_entry = copy.deepcopy(entry)

        # Check if content is a compressed object
        if isinstance(entry.content, dict):
            # Check for binary compression
            if "_compressed_data" in entry.content:
                compression_type = entry.content.get("_compression_type")
                original_type = entry.content.get("_original_type")

                try:
                    if compression_type == "zlib" and original_type == "str":
                        # Decompress zlib-compressed string
                        compressed_data = bytes.fromhex(entry.content["_compressed_data"])
                        decompressed_entry.content = zlib.decompress(compressed_data).decode()

                    elif compression_type == "zlib+pickle":
                        # Decompress zlib+pickle compressed object
                        compressed_data = bytes.fromhex(entry.content["_compressed_data"])
                        decompressed_data = zlib.decompress(compressed_data)
                        decompressed_entry.content = pickle.loads(decompressed_data)

                    logger.debug(f"Decompressed content of type {original_type}")
                except Exception as e:
                    logger.error(f"Failed to decompress content: {e}")
                    # Keep the compressed content if decompression fails
                    pass

        return decompressed_entry

    @staticmethod
    def get_compression_stats(entry: MemoryEntry) -> Dict[str, Any]:
        """Get compression statistics for a memory entry.

        Args:
            entry: The memory entry to get statistics for

        Returns:
            Dict[str, Any]: Compression statistics
        """
        stats = {
            "compression_level": entry.compression_level,
            "is_compressed": entry.compression_level != CompressionLevel.NONE,
        }

        if isinstance(entry.content, dict) and ("_compressed" in entry.content or "_compressed_data" in entry.content):
            stats["compressed_type"] = "binary" if "_compressed_data" in entry.content else "structural"

            if "_original_size" in entry.content:
                stats["original_size"] = entry.content["_original_size"]

            if "_original_type" in entry.content:
                stats["original_type"] = entry.content["_original_type"]

            if "_original_length" in entry.content:
                stats["original_length"] = entry.content["_original_length"]

            # Estimate compressed size
            try:
                compressed_size = len(json.dumps(entry.content))
                stats["compressed_size"] = compressed_size

                if "original_size" in stats:
                    stats["compression_ratio"] = round(stats["original_size"] / compressed_size, 2)
            except (TypeError, ValueError):
                pass

        return stats
