#!/usr/bin/env python3
"""
Worker Pool Implementation

This module provides a thread pool implementation for parallel processing
of I/O-bound tasks during the migration process. It's designed for high
efficiency and clean resource management.
"""

import concurrent.futures
import contextlib
import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Set, TypeVar, Union, cast

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("worker_pool")

# Type definitions
T = TypeVar("T")  # Task type
R = TypeVar("R")  # Result type


class TaskPriority(Enum):
    """Task priority levels for the worker pool."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass(order=True)
class PrioritizedTask(Generic[T]):
    """A task with an associated priority."""
    priority: TaskPriority = field(compare=True)
    created_at: float = field(compare=True)
    task: T = field(compare=False)


class TaskResult(Generic[R]):
    """Result of a task execution."""
    
    def __init__(self, 
                 success: bool, 
                 value: Optional[R] = None, 
                 error: Optional[Exception] = None):
        """Initialize the task result.
        
        Args:
            success: Whether the task was successful
            value: The result value if successful
            error: The exception if unsuccessful
        """
        self.success = success
        self.value = value
        self.error = error
        self.completed_at = time.time()
    
    @classmethod
    def success_result(cls, value: R) -> 'TaskResult[R]':
        """Create a successful task result.
        
        Args:
            value: The result value
            
        Returns:
            A successful task result
        """
        return cls(True, value)
    
    @classmethod
    def error_result(cls, error: Exception) -> 'TaskResult[R]':
        """Create an error task result.
        
        Args:
            error: The exception
            
        Returns:
            An error task result
        """
        return cls(False, error=error)


class WorkerPool:
    """A pool of worker threads for parallel task execution."""
    
    def __init__(
        self,
        num_workers: int = 8,
        max_queue_size: int = 1000,
        name: str = "worker_pool",
    ):
        """Initialize the worker pool.
        
        Args:
            num_workers: Number of worker threads
            max_queue_size: Maximum number of queued tasks
            name: Name of the worker pool
        """
        self.name = name
        self.num_workers = num_workers
        self.task_queue: queue.PriorityQueue[PrioritizedTask] = queue.PriorityQueue(max_queue_size)
        self.results: Dict[int, TaskResult] = {}
        self.result_lock = threading.Lock()
        self.task_counter = 0
        self.task_counter_lock = threading.Lock()
        self.shutdown_event = threading.Event()
        self.workers: List[threading.Thread] = []
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=num_workers,
            thread_name_prefix=f"{name}-worker",
        )
        
        logger.info(f"Initialized worker pool '{name}' with {num_workers} workers")
    
    def start(self) -> None:
        """Start the worker threads."""
        if self.workers:
            logger.warning(f"Worker pool '{self.name}' already started")
            return
        
        logger.info(f"Starting worker pool '{self.name}'")
        
        for i in range(self.num_workers):
            self.workers.append(
                threading.Thread(
                    target=self._worker_loop,
                    name=f"{self.name}-worker-{i}",
                    daemon=True,
                )
            )
        
        for worker in self.workers:
            worker.start()
    
    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the worker pool.
        
        Args:
            wait: Whether to wait for all tasks to complete
        """
        logger.info(f"Shutting down worker pool '{self.name}'")
        
        self.shutdown_event.set()
        
        if wait:
            # Wait for all workers to complete
            for worker in self.workers:
                worker.join()
            
            # Wait for all tasks to complete
            self.task_queue.join()
        
        self.executor.shutdown(wait=wait)
        logger.info(f"Worker pool '{self.name}' shutdown complete")
    
    def submit(
        self,
        func: Callable[..., R],
        *args: Any,
        priority: TaskPriority = TaskPriority.NORMAL,
        **kwargs: Any,
    ) -> int:
        """Submit a task to the worker pool.
        
        Args:
            func: Function to execute
            *args: Arguments to pass to the function
            priority: Task priority
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Task ID
        """
        with self.task_counter_lock:
            task_id = self.task_counter
            self.task_counter += 1
        
        task = (task_id, func, args, kwargs)
        
        # Prioritize the task
        prioritized_task = PrioritizedTask(
            priority=priority,
            created_at=time.time(),
            task=task,
        )
        
        # Add to queue
        self.task_queue.put(prioritized_task)
        
        return task_id
    
    def wait_for(self, task_id: int, timeout: Optional[float] = None) -> TaskResult:
        """Wait for a task to complete.
        
        Args:
            task_id: Task ID to wait for
            timeout: Timeout in seconds (None for no timeout)
            
        Returns:
            Task result
            
        Raises:
            TimeoutError: If the task didn't complete within the timeout
        """
        start_time = time.time()
        
        while timeout is None or time.time() - start_time < timeout:
            with self.result_lock:
                if task_id in self.results:
                    return self.results[task_id]
            
            # Check every 10ms
            time.sleep(0.01)
        
        raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")
    
    def wait_all(self, task_ids: List[int], timeout: Optional[float] = None) -> Dict[int, TaskResult]:
        """Wait for all specified tasks to complete.
        
        Args:
            task_ids: List of task IDs to wait for
            timeout: Timeout in seconds (None for no timeout)
            
        Returns:
            Dictionary of task IDs to results
            
        Raises:
            TimeoutError: If not all tasks completed within the timeout
        """
        results = {}
        remaining_ids = set(task_ids)
        start_time = time.time()
        
        while remaining_ids and (timeout is None or time.time() - start_time < timeout):
            with self.result_lock:
                for task_id in list(remaining_ids):
                    if task_id in self.results:
                        results[task_id] = self.results[task_id]
                        remaining_ids.remove(task_id)
            
            if not remaining_ids:
                break
            
            # Check every 10ms
            time.sleep(0.01)
        
        if remaining_ids and timeout is not None:
            raise TimeoutError(f"Tasks {remaining_ids} did not complete within {timeout} seconds")
        
        return results
    
    def _worker_loop(self) -> None:
        """Worker thread loop."""
        thread_name = threading.current_thread().name
        logger.debug(f"Worker thread {thread_name} started")
        
        while not self.shutdown_event.is_set():
            try:
                # Get a task from the queue with a timeout
                # This allows checking the shutdown event periodically
                try:
                    prioritized_task = self.task_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                task_id, func, args, kwargs = prioritized_task.task
                
                # Execute the task
                try:
                    logger.debug(f"Worker {thread_name} executing task {task_id}")
                    result = func(*args, **kwargs)
                    task_result = TaskResult.success_result(result)
                except Exception as e:
                    logger.exception(f"Error executing task {task_id}: {str(e)}")
                    task_result = TaskResult.error_result(e)
                
                # Store the result
                with self.result_lock:
                    self.results[task_id] = task_result
                
                # Mark the task as done
                self.task_queue.task_done()
                
            except Exception as e:
                logger.exception(f"Error in worker thread {thread_name}: {str(e)}")
        
        logger.debug(f"Worker thread {thread_name} stopped")


@contextlib.contextmanager
def worker_pool_context(
    num_workers: int = 8,
    max_queue_size: int = 1000,
    name: str = "worker_pool",
) -> WorkerPool:
    """Context manager for a worker pool.
    
    Args:
        num_workers: Number of worker threads
        max_queue_size: Maximum number of queued tasks
        name: Name of the worker pool
        
    Yields:
        Worker pool instance
    """
    pool = WorkerPool(num_workers, max_queue_size, name)
    pool.start()
    
    try:
        yield pool
    finally:
        pool.shutdown()


# More convenient alias
WorkerPoolContext = worker_pool_context


if __name__ == "__main__":
    """Run a simple demo of the worker pool."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Worker pool demo")
    parser.add_argument("--num-workers", type=int, default=4, help="Number of workers")
    parser.add_argument("--num-tasks", type=int, default=20, help="Number of tasks")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    def demo_task(task_id: int, sleep_time: float) -> str:
        """Demo task that sleeps for a specified time."""
        logger.info(f"Task {task_id} started, sleeping for {sleep_time:.2f}s")
        time.sleep(sleep_time)
        logger.info(f"Task {task_id} completed")
        return f"Result from task {task_id}"
    
    # Use the context manager
    with worker_pool_context(num_workers=args.num_workers) as pool:
        # Submit tasks
        task_ids = []
        for i in range(args.num_tasks):
            # Random sleep time between 0.1 and 1.0 seconds
            sleep_time = 0.1 + (i % 10) / 10.0
            
            # Random priority
            priority = TaskPriority(i % 4)
            
            task_id = pool.submit(demo_task, i, sleep_time, priority=priority)
            task_ids.append(task_id)
            logger.info(f"Submitted task {i} with ID {task_id} and priority {priority.name}")
        
        # Wait for all tasks to complete
        results = pool.wait_all(task_ids)
        
        # Print results
        for task_id, result in results.items():
            if result.success:
                print(f"Task {task_id} succeeded: {result.value}")
            else:
                print(f"Task {task_id} failed: {result.error}")