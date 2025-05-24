"""
Distributed Task Queue for AI Orchestration System.

This module provides a Redis-backed distributed task queue for
coordinating work across multiple agents and services.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Any, Callable, Awaitable, Optional, List, Set, Tuple

import aioredis

from core.orchestrator.src.config.config import settings
from core.orchestrator.src.services.event_bus import get_event_bus

# Handle both pydantic v1 and v2
try:
    from pydantic.v1 import BaseModel, Field  # For pydantic v2
except ImportError:
    from pydantic import BaseModel, Field  # For pydantic v1

# Configure logging
logger = logging.getLogger(__name__)


class TaskDefinition(BaseModel):
    """Definition of a task that can be executed by agents"""

    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    required_capabilities: List[str] = Field(default_factory=list)
    priority: int = 0  # Higher values = higher priority
    timeout: Optional[int] = None  # Timeout in seconds
    retry_count: int = 0  # Number of retries
    max_retries: int = 3  # Maximum number of retries
    created_at: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskInstance(BaseModel):
    """Instance of a task being executed"""

    instance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    agent_id: Optional[str] = None
    status: str = "pending"  # pending, assigned, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DistributedTaskQueue:
    """Redis-backed distributed task queue for agent coordination"""

    def __init__(self):
        """Initialize the distributed task queue."""
        self._redis = None
        self._event_bus = get_event_bus()
        self._task_handlers: Dict[str, Callable[[TaskInstance], Awaitable[Dict[str, Any]]]] = {}
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
        self._processing_instances: Set[str] = set()
        logger.info("DistributedTaskQueue initialized")

    async def initialize(self):
        """Initialize the Redis connection."""
        if self._redis is None:
            try:
                self._redis = await aioredis.create_redis_pool(
                    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                    password=settings.REDIS_PASSWORD,
                    encoding="utf-8",
                )
                logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise

    async def close(self):
        """Close the Redis connection."""
        if self._redis is not None:
            self._running = False

            # Cancel worker tasks
            for task in self._worker_tasks:
                task.cancel()

            # Wait for tasks to complete
            if self._worker_tasks:
                await asyncio.gather(*self._worker_tasks, return_exceptions=True)

            # Close Redis connection
            self._redis.close()
            await self._redis.wait_closed()
            self._redis = None
            logger.info("DistributedTaskQueue closed")

    async def enqueue_task(self, task_def: TaskDefinition) -> str:
        """
        Add a task to the queue.

        Args:
            task_def: The task definition

        Returns:
            The instance ID

        Raises:
            ConnectionError: If Redis is not connected
        """
        if self._redis is None:
            await self.initialize()

        instance_id = str(uuid.uuid4())
        now = time.time()

        # Create task instance
        task_instance = TaskInstance(
            instance_id=instance_id,
            task_id=task_def.task_id,
            status="pending",
            created_at=now,
            updated_at=now,
        )

        # Store task definition
        await self._redis.set(f"task:def:{task_def.task_id}", json.dumps(task_def.dict()))

        # Store task instance
        await self._redis.set(f"task:instance:{instance_id}", json.dumps(task_instance.dict()))

        # Add to pending queue with priority
        await self._redis.zadd(f"task:queue:{task_def.task_type}", task_def.priority, instance_id)

        # Publish event
        try:
            await self._event_bus.publish_async(
                "task_enqueued",
                {
                    "instance_id": instance_id,
                    "task_id": task_def.task_id,
                    "task_type": task_def.task_type,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to publish task_enqueued event: {e}")

        logger.debug(f"Task enqueued: {instance_id} (type: {task_def.task_type})")
        return instance_id

    async def register_handler(
        self,
        task_type: str,
        handler: Callable[[TaskInstance], Awaitable[Dict[str, Any]]],
    ):
        """
        Register a handler for a task type.

        Args:
            task_type: The task type
            handler: Async function that handles the task
        """
        self._task_handlers[task_type] = handler
        logger.info(f"Handler registered for task type: {task_type}")

    async def start_workers(self, num_workers: int = 5):
        """
        Start worker tasks to process the queue.

        Args:
            num_workers: Number of worker tasks to start
        """
        if self._redis is None:
            await self.initialize()

        self._running = True

        # Start worker tasks
        for i in range(num_workers):
            task = asyncio.create_task(self._worker_loop(i))
            self._worker_tasks.append(task)

        logger.info(f"Started {num_workers} worker tasks")

    async def _worker_loop(self, worker_id: int):
        """
        Worker loop to process tasks.

        Args:
            worker_id: The worker ID
        """
        logger.info(f"Worker {worker_id} started")

        while self._running:
            try:
                # Check for tasks in queues for which we have handlers
                for task_type in self._task_handlers.keys():
                    # Try to get a task with the highest priority
                    result = await self._redis.zpopmax(f"task:queue:{task_type}")

                    if result:
                        # We got a task, process it
                        instance_id = result[0]

                        # Check if already being processed
                        if instance_id in self._processing_instances:
                            continue

                        # Mark as being processed
                        self._processing_instances.add(instance_id)

                        try:
                            # Get task instance
                            instance_data = await self._redis.get(f"task:instance:{instance_id}")
                            if not instance_data:
                                logger.warning(f"Task instance not found: {instance_id}")
                                self._processing_instances.remove(instance_id)
                                continue

                            # Parse instance
                            instance = TaskInstance.parse_raw(instance_data)

                            # Get task definition
                            task_def_data = await self._redis.get(f"task:def:{instance.task_id}")
                            if not task_def_data:
                                logger.warning(f"Task definition not found: {instance.task_id}")
                                self._processing_instances.remove(instance_id)
                                continue

                            task_def = TaskDefinition.parse_raw(task_def_data)

                            # Update status to running
                            instance.status = "running"
                            instance.updated_at = time.time()
                            instance.agent_id = f"worker-{worker_id}"

                            await self._redis.set(
                                f"task:instance:{instance_id}",
                                json.dumps(instance.dict()),
                            )

                            # Publish event
                            try:
                                await self._event_bus.publish_async(
                                    "task_started",
                                    {
                                        "instance_id": instance_id,
                                        "task_id": instance.task_id,
                                        "worker_id": worker_id,
                                    },
                                )
                            except Exception as e:
                                logger.warning(f"Failed to publish task_started event: {e}")

                            # Execute handler
                            try:
                                handler = self._task_handlers[task_type]
                                result = await handler(instance)

                                # Update with success
                                instance.status = "completed"
                                instance.result = result
                                instance.completed_at = time.time()
                                instance.updated_at = time.time()

                                # Publish success event
                                try:
                                    await self._event_bus.publish_async(
                                        "task_completed",
                                        {
                                            "instance_id": instance_id,
                                            "task_id": instance.task_id,
                                            "worker_id": worker_id,
                                        },
                                    )
                                except Exception as e:
                                    logger.warning(f"Failed to publish task_completed event: {e}")

                            except Exception as e:
                                # Update with failure
                                instance.status = "failed"
                                instance.error = str(e)
                                instance.updated_at = time.time()

                                # Increment retry count
                                task_def.retry_count += 1

                                # Check if we should retry
                                if task_def.retry_count < task_def.max_retries:
                                    # Re-queue with lower priority
                                    await self._redis.zadd(
                                        f"task:queue:{task_def.task_type}",
                                        task_def.priority - 1,
                                        instance_id,
                                    )

                                    # Update task definition
                                    await self._redis.set(
                                        f"task:def:{task_def.task_id}",
                                        json.dumps(task_def.dict()),
                                    )

                                    logger.warning(
                                        f"Task {instance_id} failed, retrying "
                                        f"({task_def.retry_count}/{task_def.max_retries}): {e}"
                                    )
                                else:
                                    # Max retries reached
                                    logger.error(
                                        f"Task {instance_id} failed after {task_def.max_retries} " f"retries: {e}"
                                    )

                                    # Publish failure event
                                    try:
                                        await self._event_bus.publish_async(
                                            "task_failed",
                                            {
                                                "instance_id": instance_id,
                                                "task_id": instance.task_id,
                                                "worker_id": worker_id,
                                                "error": str(e),
                                                "retries": task_def.retry_count,
                                            },
                                        )
                                    except Exception as event_error:
                                        logger.warning(f"Failed to publish task_failed event: {event_error}")

                            # Save updated instance
                            await self._redis.set(
                                f"task:instance:{instance_id}",
                                json.dumps(instance.dict()),
                            )

                        finally:
                            # Remove from processing set
                            self._processing_instances.remove(instance_id)

                # Sleep a bit to avoid tight loop
                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in worker {worker_id}: {e}")
                await asyncio.sleep(1.0)  # Avoid tight loop on errors

    async def get_task_status(self, instance_id: str) -> Optional[TaskInstance]:
        """
        Get the status of a task.

        Args:
            instance_id: The task instance ID

        Returns:
            The task instance or None if not found
        """
        if self._redis is None:
            await self.initialize()

        # Get task instance
        instance_data = await self._redis.get(f"task:instance:{instance_id}")
        if not instance_data:
            return None

        # Parse instance
        return TaskInstance.parse_raw(instance_data)

    async def cancel_task(self, instance_id: str) -> bool:
        """
        Cancel a pending task.

        Args:
            instance_id: The task instance ID

        Returns:
            True if the task was cancelled, False otherwise
        """
        if self._redis is None:
            await self.initialize()

        # Get task instance
        instance_data = await self._redis.get(f"task:instance:{instance_id}")
        if not instance_data:
            return False

        # Parse instance
        instance = TaskInstance.parse_raw(instance_data)

        # Can only cancel pending tasks
        if instance.status != "pending":
            return False

        # Get task definition
        task_def_data = await self._redis.get(f"task:def:{instance.task_id}")
        if not task_def_data:
            return False

        task_def = TaskDefinition.parse_raw(task_def_data)

        # Remove from queue
        await self._redis.zrem(f"task:queue:{task_def.task_type}", instance_id)

        # Update status
        instance.status = "cancelled"
        instance.updated_at = time.time()

        # Save updated instance
        await self._redis.set(f"task:instance:{instance_id}", json.dumps(instance.dict()))

        # Publish event
        try:
            await self._event_bus.publish_async(
                "task_cancelled",
                {"instance_id": instance_id, "task_id": instance.task_id},
            )
        except Exception as e:
            logger.warning(f"Failed to publish task_cancelled event: {e}")

        return True


# Singleton instance
_task_queue = None


async def get_task_queue() -> DistributedTaskQueue:
    """
    Get the global task queue instance.

    Returns:
        The global DistributedTaskQueue instance
    """
    global _task_queue
    if _task_queue is None:
        _task_queue = DistributedTaskQueue()
        await _task_queue.initialize()
    return _task_queue
