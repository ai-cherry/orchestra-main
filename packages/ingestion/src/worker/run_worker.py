"""
Run Script for Ingestion Worker.

This script provides a standalone entry point for running the ingestion worker,
which processes tasks from the Pub/Sub queue asynchronously.
"""

import os
import sys
import logging
import asyncio
import signal
from typing import Optional

from packages.ingestion.src.worker.ingestion_worker import IngestionWorker
from packages.ingestion.src.config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("ingestion_worker.log")],
)
logger = logging.getLogger(__name__)


class WorkerRunner:
    """
    Runner for the ingestion worker.

    This class provides methods for starting and stopping the ingestion worker,
    including handling signals for graceful shutdown.
    """

    def __init__(self):
        """Initialize the worker runner."""
        self.settings = get_settings()
        self.worker: Optional[IngestionWorker] = None
        self.worker_task: Optional[asyncio.Task] = None
        self.running = False

    async def init_worker(self) -> None:
        """Initialize the ingestion worker."""
        logger.info("Initializing ingestion worker...")
        self.worker = await IngestionWorker.create_worker()
        logger.info("Ingestion worker initialized successfully")

    async def start(self, poll_interval: int = 30, max_messages: int = 10) -> None:
        """
        Start the ingestion worker.

        Args:
            poll_interval: Seconds to wait between polling for messages
            max_messages: Maximum number of messages to process in one poll
        """
        if not self.worker:
            await self.init_worker()

        if not self.running:
            self.running = True
            self.worker_task = asyncio.create_task(
                self.worker.run_worker(poll_interval, max_messages)
            )
            logger.info(f"Ingestion worker started with poll interval {poll_interval}s")

    async def stop(self) -> None:
        """Stop the ingestion worker gracefully."""
        if self.running and self.worker_task:
            logger.info("Stopping ingestion worker...")
            self.running = False

            # Cancel worker task
            self.worker_task.cancel()

            try:
                await self.worker_task
            except asyncio.CancelledError:
                logger.info("Worker task cancelled successfully")

            # Close worker connections
            if self.worker:
                await self.worker.close()

            logger.info("Ingestion worker stopped")
        else:
            logger.warning("No worker running to stop")


async def run_worker(poll_interval: int = 30, max_messages: int = 10) -> None:
    """
    Run the ingestion worker until interrupted.

    Args:
        poll_interval: Seconds to wait between polling for messages
        max_messages: Maximum number of messages to process in one poll
    """
    runner = WorkerRunner()

    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()

    def signal_handler():
        """Handle termination signals."""
        logger.info("Received termination signal, initiating shutdown...")
        asyncio.create_task(runner.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await runner.start(poll_interval, max_messages)

        # Keep running until stopped
        while runner.running:
            await asyncio.sleep(1)

    except asyncio.CancelledError:
        logger.info("Worker run task cancelled")
    except Exception as e:
        logger.error(f"Error in worker: {e}", exc_info=True)
    finally:
        await runner.stop()
        logger.info("Worker runner exited")


def parse_args():
    """Parse command-line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="Run the ingestion worker")
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=30,
        help="Interval in seconds between polling for messages (default: 30)",
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=10,
        help="Maximum number of messages to process in one poll (default: 10)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    return parser.parse_args()


if __name__ == "__main__":
    # Parse command-line args
    args = parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run the worker
    logger.info(f"Starting ingestion worker with poll interval {args.poll_interval}s")

    try:
        asyncio.run(run_worker(args.poll_interval, args.max_messages))
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in worker: {e}", exc_info=True)
        sys.exit(1)
