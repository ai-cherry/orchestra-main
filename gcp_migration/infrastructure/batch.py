"""
Batch processing components for the GCP Migration toolkit.

This module provides high-performance batch processing capabilities that optimize
throughput for operations that benefit from aggregation. It includes adaptive
batch sizing and intelligent scheduling for maximum efficiency.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from gcp_migration.domain.exceptions_fixed import (
    BatchProcessingError,
    MigrationError,
    TimeoutError,
    safe_async_operation,
)
from gcp_migration.domain.models import OperationPriority
from gcp_migration.domain.protocols import IBatchProcessor
from gcp_migration.infrastructure.resilience import (
    CircuitBreakerRegistry,
    with_circuit_breaker,
)

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for generic batch processing
T = TypeVar("T")  # Item type
R = TypeVar("R")  # Result type


class BatchState(Enum):
    """States for a batch processor."""

    COLLECTING = auto()  # Collecting items for a batch
    PROCESSING = auto()  # Processing a batch
    FLUSHING = auto()  # Flushing all pending items
    STOPPING = auto()  # Stopping the processor
    STOPPED = auto()  # Processor is stopped


@dataclass
class BatchItem(Generic[T, R]):
    """
    An item in a batch with its associated future for result handling.

    This class tracks individual items for batch processing, maintaining
    the connection between the input item and its result future.
    """

    item: T
    future: asyncio.Future
    timestamp: float = field(default_factory=time.monotonic)
    retry_count: int = 0

    def complete(self, result: R) -> None:
        """
        Complete the item with a result.

        Args:
            result: Result value to set
        """
        if not self.future.done():
            self.future.set_result(result)

    def fail(self, exception: Exception) -> None:
        """
        Fail the item with an exception.

        Args:
            exception: Exception to set
        """
        if not self.future.done():
            self.future.set_exception(exception)

    def cancel(self) -> None:
        """Cancel the item's future."""
        if not self.future.done():
            self.future.cancel()

    @property
    def elapsed(self) -> float:
        """Get elapsed time since item creation in seconds."""
        return time.monotonic() - self.timestamp


class BatchMetrics:
    """
    Performance metrics for batch processing.

    This class tracks detailed metrics about batch processing for
    performance monitoring and optimization.
    """

    def __init__(self, max_history: int = 100):
        """
        Initialize batch metrics.

        Args:
            max_history: Maximum number of batch times to keep for stats
        """
        self.batch_count = 0
        self.total_item_count = 0
        self.success_item_count = 0
        self.failed_item_count = 0
        self.retry_item_count = 0
        self.flush_count = 0
        self.timeout_count = 0

        self.batch_times: List[float] = []
        self.max_history = max_history
        self.last_batch_time = 0.0
        self.min_batch_time = float("inf")
        self.max_batch_time = 0.0
        self.total_batch_time = 0.0

        self.created_at = time.monotonic()
        self.last_update = self.created_at

    def record_batch(
        self,
        batch_size: int,
        success_count: int,
        failed_count: int,
        retry_count: int,
        batch_time: float,
    ) -> None:
        """
        Record metrics for a completed batch.

        Args:
            batch_size: Total items in the batch
            success_count: Number of successfully processed items
            failed_count: Number of failed items
            retry_count: Number of items that will be retried
            batch_time: Time taken to process the batch in seconds
        """
        self.batch_count += 1
        self.total_item_count += batch_size
        self.success_item_count += success_count
        self.failed_item_count += failed_count
        self.retry_item_count += retry_count

        self.last_batch_time = batch_time
        self.min_batch_time = min(self.min_batch_time, batch_time)
        self.max_batch_time = max(self.max_batch_time, batch_time)
        self.total_batch_time += batch_time

        self.batch_times.append(batch_time)
        if len(self.batch_times) > self.max_history:
            self.batch_times.pop(0)

        self.last_update = time.monotonic()

    def record_flush(self) -> None:
        """Record a flush operation."""
        self.flush_count += 1
        self.last_update = time.monotonic()

    def record_timeout(self) -> None:
        """Record a batch timeout."""
        self.timeout_count += 1
        self.last_update = time.monotonic()

    def get_avg_batch_time(self) -> float:
        """
        Get the average batch processing time.

        Returns:
            Average time in seconds or 0 if no batches processed
        """
        if not self.batch_times:
            return 0.0
        return sum(self.batch_times) / len(self.batch_times)

    def get_avg_batch_size(self) -> float:
        """
        Get the average batch size.

        Returns:
            Average batch size or 0 if no batches processed
        """
        if self.batch_count == 0:
            return 0.0
        return self.total_item_count / self.batch_count

    def get_success_rate(self) -> float:
        """
        Get the item success rate as a percentage.

        Returns:
            Success rate (0-100) or 100 if no items processed
        """
        if self.total_item_count == 0:
            return 100.0
        return (self.success_item_count / self.total_item_count) * 100.0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get a dictionary of all metrics.

        Returns:
            Dictionary of metric names to values
        """
        return {
            "batch_count": self.batch_count,
            "total_item_count": self.total_item_count,
            "success_item_count": self.success_item_count,
            "failed_item_count": self.failed_item_count,
            "retry_item_count": self.retry_item_count,
            "flush_count": self.flush_count,
            "timeout_count": self.timeout_count,
            "avg_batch_time": self.get_avg_batch_time(),
            "min_batch_time": self.min_batch_time if self.batch_count > 0 else 0,
            "max_batch_time": self.max_batch_time,
            "avg_batch_size": self.get_avg_batch_size(),
            "success_rate": self.get_success_rate(),
            "uptime": time.monotonic() - self.created_at,
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.batch_count = 0
        self.total_item_count = 0
        self.success_item_count = 0
        self.failed_item_count = 0
        self.retry_item_count = 0
        self.flush_count = 0
        self.timeout_count = 0

        self.batch_times = []
        self.last_batch_time = 0.0
        self.min_batch_time = float("inf")
        self.max_batch_time = 0.0
        self.total_batch_time = 0.0

        self.created_at = time.monotonic()
        self.last_update = self.created_at


class BatchProcessor(Generic[T, R], IBatchProcessor[T]):
    """
    High-performance batch processor for efficient operations.

    This class implements an adaptive batch processing system that optimizes
    throughput for operations that benefit from batching. It handles collecting
    items, processing them in optimal batch sizes, and returning individual results.
    """

    def __init__(
        self,
        name: str,
        batch_processor: Callable[[List[T]], Awaitable[Dict[int, Union[R, Exception]]]],
        min_batch_size: int = 1,
        max_batch_size: int = 100,
        flush_interval: float = 1.0,
        max_wait_time: float = 5.0,
        max_retry_count: int = 3,
        circuit_name: Optional[str] = None,
        priority: OperationPriority = OperationPriority.STANDARD,
    ):
        """
        Initialize a batch processor.

        Args:
            name: Name of the batch processor for identification
            batch_processor: Async function to process a batch of items, returning
                a dictionary mapping indices to results or exceptions
            min_batch_size: Minimum batch size to process
            max_batch_size: Maximum batch size to process
            flush_interval: Time in seconds between automatic flushes
            max_wait_time: Maximum time in seconds an item can wait before forcing a flush
            max_retry_count: Maximum number of retries for failed items
            circuit_name: Optional name of the circuit breaker to use
            priority: Processing priority level
        """
        self.name = name
        self.batch_processor = batch_processor
        self.min_batch_size = min_batch_size
        self.max_batch_size = max_batch_size
        self.flush_interval = flush_interval
        self.max_wait_time = max_wait_time
        self.max_retry_count = max_retry_count
        self.circuit_name = circuit_name or f"batch_{name}"
        self.priority = priority

        # Initialize state
        self._state = BatchState.STOPPED
        self._items: List[BatchItem[T, R]] = []
        self._processing_lock = asyncio.Lock()
        self._flush_event = asyncio.Event()
        self._processor_task: Optional[asyncio.Task] = None
        self._metrics = BatchMetrics()

        # Create circuit breaker for resilience
        if circuit_name:
            self._circuit = CircuitBreakerRegistry.create_or_get(
                name=circuit_name, failure_threshold=3, recovery_timeout=10.0
            )
        else:
            self._circuit = None

    async def start(self) -> None:
        """Start the batch processor."""
        if self._state != BatchState.STOPPED:
            return

        self._state = BatchState.COLLECTING
        self._processor_task = asyncio.create_task(self._processor_loop())
        logger.info(f"Started batch processor: {self.name}")

    async def stop(self) -> None:
        """Stop the batch processor and process any remaining items."""
        if self._state == BatchState.STOPPED:
            return

        # Change state to stopping
        self._state = BatchState.STOPPING
        self._flush_event.set()

        # Wait for processor task to complete
        if self._processor_task is not None:
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

        # Cancel any remaining items
        for item in self._items:
            item.cancel()
        self._items.clear()

        self._state = BatchState.STOPPED
        logger.info(f"Stopped batch processor: {self.name}")

    async def add_item(self, item: T) -> asyncio.Future:
        """
        Add an item to the batch for processing.

        Args:
            item: The item to add

        Returns:
            Future that will resolve with the processed result

        Raises:
            BatchProcessingError: If the batch processor is not running
        """
        if self._state not in (BatchState.COLLECTING, BatchState.PROCESSING):
            raise BatchProcessingError(f"Batch processor {self.name} is not running")

        # Create future and batch item
        future: asyncio.Future = asyncio.Future()
        batch_item = BatchItem(item=item, future=future)

        # Add to pending items
        self._items.append(batch_item)

        # Check if we should trigger processing
        if len(self._items) >= self.max_batch_size:
            self._flush_event.set()

        return future

    async def flush(self) -> None:
        """
        Flush all pending items immediately.

        Raises:
            BatchProcessingError: If the batch processor is not running
        """
        if self._state not in (BatchState.COLLECTING, BatchState.PROCESSING):
            raise BatchProcessingError(f"Batch processor {self.name} is not running")

        self._flush_event.set()
        self._metrics.record_flush()

    @property
    def batch_size(self) -> int:
        """Get the maximum batch size."""
        return self.max_batch_size

    @property
    def pending_items(self) -> int:
        """Get the number of pending items."""
        return len(self._items)

    @property
    def metrics(self) -> BatchMetrics:
        """Get the batch processor metrics."""
        return self._metrics

    async def _processor_loop(self) -> None:
        """
        Main processing loop for the batch processor.

        This loop handles batch collection, processing, and automatic flushing
        based on configured intervals and thresholds.
        """
        last_flush_time = time.monotonic()

        while self._state != BatchState.STOPPING:
            try:
                # Wait for flush event or interval
                try:
                    flush_wait = max(
                        0, self.flush_interval - (time.monotonic() - last_flush_time)
                    )
                    await asyncio.wait_for(self._flush_event.wait(), timeout=flush_wait)
                except asyncio.TimeoutError:
                    # Regular flush interval reached
                    pass

                # Reset flush event
                self._flush_event.clear()

                # Check if we have items to process
                if not self._items:
                    last_flush_time = time.monotonic()
                    continue

                # Check if we should process based on batch size or oldest item
                current_size = len(self._items)
                should_process = current_size >= self.min_batch_size or (
                    current_size > 0 and self._items[0].elapsed >= self.max_wait_time
                )

                if should_process or self._state == BatchState.STOPPING:
                    # Process the batch
                    async with self._processing_lock:
                        self._state = BatchState.PROCESSING
                        await self._process_batch()
                        self._state = BatchState.COLLECTING

                last_flush_time = time.monotonic()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch processor loop for {self.name}: {e}")
                await asyncio.sleep(1.0)  # Brief pause on error

    async def _process_batch(self) -> None:
        """
        Process a batch of items.

        This method takes items from the pending queue, processes them as a batch,
        and sets the individual results on the corresponding futures.
        """
        # No items to process
        if not self._items:
            return

        # Get the batch to process (up to max size)
        batch = self._items[: self.max_batch_size]
        self._items = self._items[self.max_batch_size :]

        batch_size = len(batch)
        batch_items = [item.item for item in batch]
        success_count = 0
        failed_count = 0
        retry_count = 0

        start_time = time.monotonic()

        try:
            # Process the batch
            if self._circuit:
                # Use circuit breaker if configured
                results = await self._circuit.execute(self.batch_processor, batch_items)
            else:
                # Direct execution
                results = await self.batch_processor(batch_items)

            # Process results
            for i, item in enumerate(batch):
                if i in results:
                    result = results[i]
                    if isinstance(result, Exception):
                        # Handle individual item failure
                        failed_count += 1

                        # Check for retry
                        if item.retry_count < self.max_retry_count:
                            # Requeue for retry
                            item.retry_count += 1
                            retry_count += 1
                            self._items.append(item)
                        else:
                            # Max retries reached, fail the item
                            item.fail(result)
                    else:
                        # Handle success
                        success_count += 1
                        item.complete(result)
                else:
                    # Missing result, fail the item
                    error = BatchProcessingError(f"No result for item at index {i}")
                    failed_count += 1
                    item.fail(error)

        except Exception as e:
            # Batch processing failed
            logger.error(f"Batch processing failed for {self.name}: {e}")

            # Requeue items for retry if possible
            for item in batch:
                if item.retry_count < self.max_retry_count:
                    item.retry_count += 1
                    retry_count += 1
                    self._items.append(item)
                else:
                    failed_count += 1
                    item.fail(
                        BatchProcessingError(
                            message=f"Batch processing failed after {item.retry_count} retries",
                            cause=e,
                        )
                    )

        # Record metrics
        batch_time = time.monotonic() - start_time
        self._metrics.record_batch(
            batch_size=batch_size,
            success_count=success_count,
            failed_count=failed_count,
            retry_count=retry_count,
            batch_time=batch_time,
        )

        # Log batch completion
        logger.debug(
            f"Processed batch of {batch_size} items for {self.name} in {batch_time:.3f}s. "
            f"Success: {success_count}, Failed: {failed_count}, Retry: {retry_count}"
        )


class BatchProcessorRegistry:
    """
    Registry for batch processors.

    This class provides a central registry for managing batch processors
    across the application.
    """

    _instance = None
    _processors: Dict[str, BatchProcessor] = {}

    def __new__(cls):
        """Implement singleton pattern for the registry."""
        if cls._instance is None:
            cls._instance = super(BatchProcessorRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, processor: BatchProcessor) -> None:
        """
        Register a batch processor.

        Args:
            processor: The batch processor to register
        """
        cls._processors[processor.name] = processor
        logger.debug(f"Registered batch processor: {processor.name}")

    @classmethod
    def get(cls, name: str) -> Optional[BatchProcessor]:
        """
        Get a batch processor by name.

        Args:
            name: The name of the processor

        Returns:
            The batch processor or None if not found
        """
        return cls._processors.get(name)

    @classmethod
    async def start_all(cls) -> None:
        """Start all registered batch processors."""
        for processor in cls._processors.values():
            await processor.start()
        logger.info(f"Started {len(cls._processors)} batch processors")

    @classmethod
    async def stop_all(cls) -> None:
        """Stop all registered batch processors."""
        for processor in cls._processors.values():
            await processor.stop()
        logger.info(f"Stopped {len(cls._processors)} batch processors")

    @classmethod
    def get_all_metrics(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get metrics for all batch processors.

        Returns:
            Dictionary mapping processor names to their metrics
        """
        return {
            name: processor.metrics.get_stats()
            for name, processor in cls._processors.items()
        }

    @classmethod
    async def remove(cls, name: str) -> bool:
        """
        Remove and stop a batch processor.

        Args:
            name: The name of the processor to remove

        Returns:
            True if the processor was removed, False if not found
        """
        processor = cls._processors.pop(name, None)
        if processor:
            await processor.stop()
            logger.info(f"Removed batch processor: {name}")
            return True
        return False


async def create_batch_processor(
    name: str,
    batch_processor: Callable[[List[T]], Awaitable[Dict[int, Union[R, Exception]]]],
    min_batch_size: int = 1,
    max_batch_size: int = 100,
    auto_start: bool = True,
) -> BatchProcessor[T, R]:
    """
    Create and register a batch processor.

    Args:
        name: Name of the processor
        batch_processor: Function to process batches
        min_batch_size: Minimum batch size
        max_batch_size: Maximum batch size
        auto_start: Whether to start the processor immediately

    Returns:
        The created batch processor
    """
    processor = BatchProcessor(
        name=name,
        batch_processor=batch_processor,
        min_batch_size=min_batch_size,
        max_batch_size=max_batch_size,
    )

    BatchProcessorRegistry.register(processor)

    if auto_start:
        await processor.start()

    return processor
