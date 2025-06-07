"""
"""
    """Definition of a task that can be executed by agents"""
    """Instance of a task being executed"""
    status: str = "pending"  # pending, assigned, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DistributedTaskQueue:
    """Redis-backed distributed task queue for agent coordination"""
        """Initialize the distributed task queue."""
        logger.info("DistributedTaskQueue initialized")

    async def initialize(self):
        """Initialize the Redis connection if enabled."""
            logger.info("Redis disabled via USE_REDIS; using Weaviate session cache")
            return
        if self._redis is None:
            try:

                pass
                self._redis = await aioredis.create_redis_pool(
                    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
                    password=settings.REDIS_PASSWORD,
                    encoding="utf-8",
                )
                logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            except Exception:

                pass
                logger.error(f"Failed to connect to Redis: {e}")
                raise

    async def close(self):
        """Close the Redis connection."""
            logger.info("DistributedTaskQueue closed")
        else:
            self._running = False

    async def enqueue_task(self, task_def: TaskDefinition) -> str:
        """
        """
            status="pending",
            created_at=now,
            updated_at=now,
        )

        if self._use_redis:
            # Store task definition
            await self._redis.set(f"task:def:{task_def.task_id}", json.dumps(task_def.dict()))

            # Store task instance
            await self._redis.set(f"task:instance:{instance_id}", json.dumps(task_instance.dict()))

            # Add to pending queue with priority
            await self._redis.zadd(f"task:queue:{task_def.task_type}", task_def.priority, instance_id)
        else:
            await weaviate_cache.set_json(f"task:def:{task_def.task_id}", task_def.dict())
            await weaviate_cache.set_json(f"task:instance:{instance_id}", task_instance.dict())

        # Publish event
        try:

            pass
            await self._event_bus.publish_async(
                "task_enqueued",
                {
                    "instance_id": instance_id,
                    "task_id": task_def.task_id,
                    "task_type": task_def.task_type,
                },
            )
        except Exception:

            pass
            logger.warning(f"Failed to publish task_enqueued event: {e}")

        return instance_id

    async def register_handler(
        self,
        task_type: str,
        handler: Callable[[TaskInstance], Awaitable[Dict[str, Any]]],
    ):
        """
        """
        logger.info(f"Handler registered for task type: {task_type}")

    async def start_workers(self, num_workers: int = 5):
        """
        """
            raise NotImplementedError("Non-Redis queue workers not implemented")
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
        """
        logger.info(f"Worker {worker_id} started")

        while self._running:
            try:

                pass
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


                            pass
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

                                pass
                                await self._event_bus.publish_async(
                                    "task_started",
                                    {
                                        "instance_id": instance_id,
                                        "task_id": instance.task_id,
                                        "worker_id": worker_id,
                                    },
                                )
                            except Exception:

                                pass
                                logger.warning(f"Failed to publish task_started event: {e}")

                            # Execute handler
                            try:

                                pass
                                handler = self._task_handlers[task_type]
                                result = await handler(instance)

                                # Update with success
                                instance.status = "completed"
                                instance.result = result
                                instance.completed_at = time.time()
                                instance.updated_at = time.time()

                                # Publish success event
                                try:

                                    pass
                                    await self._event_bus.publish_async(
                                        "task_completed",
                                        {
                                            "instance_id": instance_id,
                                            "task_id": instance.task_id,
                                            "worker_id": worker_id,
                                        },
                                    )
                                except Exception:

                                    pass
                                    logger.warning(f"Failed to publish task_completed event: {e}")

                            except Exception:


                                pass
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

                                        pass
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
                                    except Exception:

                                        pass
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

            except Exception:


                pass
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception:

                pass
                logger.error(f"Error in worker {worker_id}: {e}")
                await asyncio.sleep(1.0)  # Avoid tight loop on errors

    async def get_task_status(self, instance_id: str) -> Optional[TaskInstance]:
        """
        """
        instance_data = await self._redis.get(f"task:instance:{instance_id}")
        if not instance_data:
            return None

        # Parse instance
        return TaskInstance.parse_raw(instance_data)

    async def cancel_task(self, instance_id: str) -> bool:
        """
        """
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

            pass
            await self._event_bus.publish_async(
                "task_cancelled",
                {"instance_id": instance_id, "task_id": instance.task_id},
            )
        except Exception:

            pass
            logger.warning(f"Failed to publish task_cancelled event: {e}")

        return True

# Singleton instance
_task_queue = None

async def get_task_queue() -> DistributedTaskQueue:
    """
    """