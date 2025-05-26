"""
Memory optimization utilities for AI Orchestra.

This module provides utilities for optimizing memory usage in the application,
including efficient string operations, resource cleanup, and large object handling.
"""

import gc
import io
import logging
import weakref
from contextlib import contextmanager
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Generic,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ResourceManager:
    """
    Resource manager for tracking and cleaning up resources.

    This class provides a way to track resources that need to be cleaned up,
    such as file handles, network connections, and other system resources.
    """

    _resources: Dict[int, Tuple[Any, Callable[[Any], None]]] = {}

    @classmethod
    def register(cls, resource: Any, cleanup_func: Callable[[Any], None]) -> Any:
        """
        Register a resource for cleanup.

        Args:
            resource: The resource to register
            cleanup_func: The function to call to clean up the resource

        Returns:
            The registered resource
        """
        resource_id = id(resource)
        cls._resources[resource_id] = (weakref.ref(resource), cleanup_func)
        return resource

    @classmethod
    def unregister(cls, resource: Any) -> None:
        """
        Unregister a resource.

        Args:
            resource: The resource to unregister
        """
        resource_id = id(resource)
        if resource_id in cls._resources:
            del cls._resources[resource_id]

    @classmethod
    def cleanup(cls, resource: Any) -> None:
        """
        Clean up a specific resource.

        Args:
            resource: The resource to clean up
        """
        resource_id = id(resource)
        if resource_id in cls._resources:
            _, cleanup_func = cls._resources[resource_id]
            cleanup_func(resource)
            cls.unregister(resource)

    @classmethod
    def cleanup_all(cls) -> None:
        """
        Clean up all registered resources.
        """
        for resource_id, (resource_ref, cleanup_func) in list(cls._resources.items()):
            resource = resource_ref()
            if resource is not None:
                try:
                    cleanup_func(resource)
                except Exception as e:
                    logger.error(f"Error cleaning up resource: {str(e)}")

            del cls._resources[resource_id]

    @classmethod
    def get_resource_count(cls) -> int:
        """
        Get the number of registered resources.

        Returns:
            The number of registered resources
        """
        return len(cls._resources)


@contextmanager
def managed_resource(
    resource: T, cleanup_func: Callable[[T], None]
) -> Generator[T, None, None]:
    """
    Context manager for automatically cleaning up resources.

    Args:
        resource: The resource to manage
        cleanup_func: The function to call to clean up the resource

    Yields:
        The managed resource
    """
    try:
        ResourceManager.register(resource, cleanup_func)
        yield resource
    finally:
        ResourceManager.cleanup(resource)


class StringBuilderIO(io.StringIO):
    """
    Efficient string builder using StringIO.

    This class provides an efficient way to build strings by appending
    to a StringIO buffer, which avoids the overhead of string concatenation.
    """

    def __init__(self, initial_value: str = "") -> None:
        """
        Initialize the string builder.

        Args:
            initial_value: The initial value of the string builder
        """
        super().__init__(initial_value)

    def append(self, text: str) -> "StringBuilderIO":
        """
        Append text to the string builder.

        Args:
            text: The text to append

        Returns:
            The string builder for method chaining
        """
        self.write(text)
        return self

    def append_line(self, text: str = "") -> "StringBuilderIO":
        """
        Append a line of text to the string builder.

        Args:
            text: The text to append

        Returns:
            The string builder for method chaining
        """
        self.write(text + "\n")
        return self

    def to_string(self) -> str:
        """
        Get the string value of the string builder.

        Returns:
            The string value
        """
        return self.getvalue()


def build_string(parts: List[str]) -> str:
    """
    Build a string from a list of parts efficiently.

    Args:
        parts: The parts to join

    Returns:
        The joined string
    """
    builder = StringBuilderIO()
    for part in parts:
        builder.append(part)
    return builder.to_string()


def build_string_with_separator(parts: List[str], separator: str = "") -> str:
    """
    Build a string from a list of parts with a separator.

    Args:
        parts: The parts to join
        separator: The separator to use

    Returns:
        The joined string
    """
    builder = StringBuilderIO()
    for i, part in enumerate(parts):
        if i > 0:
            builder.append(separator)
        builder.append(part)
    return builder.to_string()


class LargeObjectCache(Generic[T]):
    """
    Cache for large objects with automatic cleanup.

    This class provides a way to cache large objects that are expensive to create,
    with automatic cleanup when the objects are no longer needed.
    """

    def __init__(self, max_size: int = 100) -> None:
        """
        Initialize the cache.

        Args:
            max_size: The maximum number of objects to cache
        """
        self.max_size = max_size
        self.cache: Dict[str, T] = {}
        self.access_count: Dict[str, int] = {}

    def get(self, key: str) -> Optional[T]:
        """
        Get an object from the cache.

        Args:
            key: The key to look up

        Returns:
            The cached object, or None if not found
        """
        if key in self.cache:
            self.access_count[key] += 1
            return self.cache[key]
        return None

    def put(self, key: str, value: T) -> None:
        """
        Put an object in the cache.

        Args:
            key: The key to store the object under
            value: The object to cache
        """
        if len(self.cache) >= self.max_size:
            # Evict the least recently used object
            least_used_key = min(self.access_count.items(), key=lambda x: x[1])[0]
            del self.cache[least_used_key]
            del self.access_count[least_used_key]

        self.cache[key] = value
        self.access_count[key] = 1

    def remove(self, key: str) -> None:
        """
        Remove an object from the cache.

        Args:
            key: The key to remove
        """
        if key in self.cache:
            del self.cache[key]
            del self.access_count[key]

    def clear(self) -> None:
        """
        Clear the cache.
        """
        self.cache.clear()
        self.access_count.clear()

    def get_or_create(self, key: str, creator: Callable[[], T]) -> T:
        """
        Get an object from the cache, or create it if not found.

        Args:
            key: The key to look up
            creator: A function to create the object if not found

        Returns:
            The cached or newly created object
        """
        value = self.get(key)
        if value is None:
            value = creator()
            self.put(key, value)
        return value


@contextmanager
def memory_optimized_context() -> Generator[None, None, None]:
    """
    Context manager for optimizing memory usage.

    This context manager disables the garbage collector during execution
    and then forces a collection afterward, which can improve performance
    for memory-intensive operations.

    Yields:
        None
    """
    # Disable garbage collection
    gc_enabled = gc.isenabled()
    gc.disable()

    try:
        yield
    finally:
        # Force garbage collection
        gc.collect()

        # Restore previous garbage collection state
        if gc_enabled:
            gc.enable()


def get_memory_usage() -> int:
    """
    Get the current memory usage of the process.

    Returns:
        The memory usage in bytes
    """
    import psutil

    process = psutil.Process()
    return process.memory_info().rss


def format_memory_size(size_bytes: int) -> str:
    """
    Format a memory size in a human-readable format.

    Args:
        size_bytes: The size in bytes

    Returns:
        A human-readable string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"

    size_kb = size_bytes / 1024
    if size_kb < 1024:
        return f"{size_kb:.2f} KB"

    size_mb = size_kb / 1024
    if size_mb < 1024:
        return f"{size_mb:.2f} MB"

    size_gb = size_mb / 1024
    return f"{size_gb:.2f} GB"


@contextmanager
def memory_profiler(label: str = "Operation") -> Generator[None, None, None]:
    """
    Context manager for profiling memory usage.

    Args:
        label: A label for the operation being profiled

    Yields:
        None
    """
    try:
        import psutil
    except ImportError:
        logger.warning("psutil not installed, memory profiling disabled")
        yield
        return

    process = psutil.Process()
    start_memory = process.memory_info().rss

    try:
        yield
    finally:
        end_memory = process.memory_info().rss
        memory_diff = end_memory - start_memory

        logger.info(
            f"{label} - Memory usage: "
            f"Start: {format_memory_size(start_memory)}, "
            f"End: {format_memory_size(end_memory)}, "
            f"Diff: {format_memory_size(memory_diff)}"
        )


class MemoryOptimizedList(Generic[T]):
    """
    Memory-optimized list implementation.

    This class provides a memory-efficient list implementation that
    uses a chunked storage approach to reduce memory fragmentation.
    """

    def __init__(self, chunk_size: int = 1000) -> None:
        """
        Initialize the list.

        Args:
            chunk_size: The size of each chunk
        """
        self.chunk_size = chunk_size
        self.chunks: List[List[T]] = []
        self.size = 0

    def append(self, item: T) -> None:
        """
        Append an item to the list.

        Args:
            item: The item to append
        """
        if not self.chunks or len(self.chunks[-1]) >= self.chunk_size:
            self.chunks.append([])

        self.chunks[-1].append(item)
        self.size += 1

    def extend(self, items: List[T]) -> None:
        """
        Extend the list with items.

        Args:
            items: The items to append
        """
        for item in items:
            self.append(item)

    def __getitem__(self, index: int) -> T:
        """
        Get an item by index.

        Args:
            index: The index to look up

        Returns:
            The item at the specified index

        Raises:
            IndexError: If the index is out of range
        """
        if index < 0:
            index += self.size

        if index < 0 or index >= self.size:
            raise IndexError("Index out of range")

        chunk_index = index // self.chunk_size
        item_index = index % self.chunk_size

        return self.chunks[chunk_index][item_index]

    def __setitem__(self, index: int, value: T) -> None:
        """
        Set an item by index.

        Args:
            index: The index to set
            value: The value to set

        Raises:
            IndexError: If the index is out of range
        """
        if index < 0:
            index += self.size

        if index < 0 or index >= self.size:
            raise IndexError("Index out of range")

        chunk_index = index // self.chunk_size
        item_index = index % self.chunk_size

        self.chunks[chunk_index][item_index] = value

    def __len__(self) -> int:
        """
        Get the length of the list.

        Returns:
            The length of the list
        """
        return self.size

    def __iter__(self) -> Iterator[T]:
        """
        Get an iterator over the list.

        Returns:
            An iterator over the list
        """
        for chunk in self.chunks:
            yield from chunk

    def clear(self) -> None:
        """
        Clear the list.
        """
        self.chunks = []
        self.size = 0
