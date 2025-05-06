"""
Test Utility for File Ingestion System.

This script provides a simple way to test the ingestion system
by creating a task for a specified URL and monitoring its progress.
"""

import os
import sys
import json
import logging
import asyncio
import argparse
from typing import Dict, Any, Optional
import uuid

# Add parent directory to path to import ingestion modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from packages.ingestion.src.api.ingestion_api import IngestionAPI
from packages.ingestion.src.models.ingestion_models import IngestionStatus
from packages.ingestion.src.config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_ingestion(url: str, user_id: Optional[str] = None, wait: bool = True) -> None:
    """
    Test file ingestion by creating a task and optionally monitoring its progress.
    
    Args:
        url: URL of the file to ingest
        user_id: Optional user ID (defaults to a UUID)
        wait: Whether to wait and monitor task status
    """
    # Create user_id if not provided
    if not user_id:
        user_id = str(uuid.uuid4())
        
    logger.info(f"Testing ingestion for URL: {url}")
    logger.info(f"User ID: {user_id}")
    
    # Initialize API
    api = await IngestionAPI.create_api()
    
    try:
        # Create task
        task_id, result = await api.create_ingestion_task(
            url=url,
            user_id=user_id,
            session_id=str(uuid.uuid4()),
            metadata={"source": "test_ingestion"}
        )
        
        logger.info(f"Created task: {task_id}")
        logger.info(f"Initial status: {result.status}")
        logger.info(f"Message: {result.message}")
        
        if wait:
            # Poll for status updates
            logger.info("Monitoring task status...")
            
            status = result.status
            complete_statuses = [IngestionStatus.PROCESSED, IngestionStatus.FAILED]
            
            while status not in complete_statuses:
                # Wait before polling
                await asyncio.sleep(5)
                
                # Get latest status
                try:
                    result = await api.get_task_status(task_id)
                    
                    # Only log if status changed
                    if result.status != status:
                        status = result.status
                        logger.info(f"Status updated: {status}")
                        logger.info(f"Message: {result.message}")
                        
                        # If there are files, log them
                        if "files" in result.details:
                            for file in result.details["files"]:
                                logger.info(f"  File: {file['filename']} ({file['detected_type']})")
                except Exception as e:
                    logger.error(f"Error checking status: {e}")
                    continue
                    
            # Final status
            logger.info(f"Task completed with status: {status}")
            
            if status == IngestionStatus.PROCESSED:
                logger.info("Ingestion completed successfully!")
            else:
                logger.error(f"Ingestion failed: {result.details.get('error', 'Unknown error')}")
                
            # Print details
            logger.info("\nTask Details:")
            print(json.dumps(result.details, indent=2))
    except Exception as e:
        logger.error(f"Error in test ingestion: {e}")
    finally:
        # Close API
        await api.close()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Test file ingestion")
    
    parser.add_argument(
        "url",
        help="URL of the file to ingest"
    )
    parser.add_argument(
        "--user-id",
        help="User ID (defaults to a generated UUID)"
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Don't wait for task completion"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    try:
        # Run test
        asyncio.run(
            test_ingestion(
                url=args.url,
                user_id=args.user_id,
                wait=not args.no_wait
            )
        )
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Error in test: {e}")
        sys.exit(1)
