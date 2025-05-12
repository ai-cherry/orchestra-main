"""
Error handling example showing best practices.

This module demonstrates how to use the standardized error handling utilities
across different parts of the codebase to ensure consistency.
"""

import logging
import os
from typing import Dict, List, Optional, Any

# Import the standardized error handling utilities
from utils.error_handling import (
    BaseError,
    ErrorSeverity,
    handle_exception,
    error_context,
    safe_execute,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Define domain-specific error types
class ConfigError(BaseError):
    """Error related to configuration issues."""
    pass


class DataProcessingError(BaseError):
    """Error related to data processing."""
    pass


class NetworkError(BaseError):
    """Error related to network operations."""
    pass


# Example functions showing different error handling approaches
@handle_exception(target_error=ConfigError)
def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a file with error handling.
    
    This example shows how to use the handle_exception decorator to
    automatically handle exceptions and convert them to domain-specific errors.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        The loaded configuration
        
    Raises:
        ConfigError: If the configuration cannot be loaded
    """
    logger.info(f"Loading configuration from {config_path}")
    
    if not os.path.exists(config_path):
        raise ConfigError(
            f"Configuration file not found: {config_path}",
            severity=ErrorSeverity.ERROR,
            details={"path": config_path}
        )
    
    # This will raise an exception if the file doesn't exist or isn't valid JSON
    # The handle_exception decorator will catch it and convert it to a ConfigError
    import json
    with open(config_path, "r") as f:
        config = json.load(f)
    
    return config


def process_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process data with error context.
    
    This example shows how to use the error_context context manager
    to handle errors in a specific block of code.
    
    Args:
        data: The data to process
        
    Returns:
        The processed data
        
    Raises:
        DataProcessingError: If the data cannot be processed
    """
    logger.info(f"Processing {len(data)} data items")
    
    result = []
    
    for i, item in enumerate(data):
        try:
            # Use error_context to handle errors in this specific block
            with error_context(
                DataProcessingError,
                f"Error processing item {i}",
                details={"item_index": i}
            ):
                # Process the item (this might raise various exceptions)
                processed_item = {
                    "id": item["id"],
                    "value": item["value"] * 2,
                    "normalized": item["value"] / sum(i["value"] for i in data),
                }
                result.append(processed_item)
        except DataProcessingError as e:
            # Handle the error (log it, add to errors list, etc.)
            logger.warning(f"Skipping item {i}: {e}")
            continue
    
    return result


def fetch_remote_data(url: str) -> Optional[Dict[str, Any]]:
    """
    Fetch data from a remote URL with safe execution.
    
    This example shows how to use safe_execute to handle errors
    and return a default value if the operation fails.
    
    Args:
        url: The URL to fetch data from
        
    Returns:
        The fetched data, or None if fetching fails
    """
    logger.info(f"Fetching data from {url}")
    
    # Import here to avoid dependency issues
    import requests
    
    # Define the function to execute safely
    def _fetch(url: str) -> Dict[str, Any]:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raise an exception for 4xx/5xx responses
        return response.json()
    
    # Execute the function safely, returning None if it fails
    return safe_execute(
        _fetch,
        url,
        default=None,
        log_errors=True,
        logger=logger
    )


# Example usage of the error handling utilities
def main() -> None:
    """Main function demonstrating the error handling utilities."""
    try:
        # Try to load configuration (might raise ConfigError)
        config = load_config("config.json")
        
        # Try to process data (might raise DataProcessingError)
        data = [
            {"id": 1, "value": 10},
            {"id": 2, "value": 20},
            {"id": 3, "value": 30},
            {"id": 4, "value": "invalid"},  # This will cause an error
            {"id": 5, "value": 50},
        ]
        processed_data = process_data(data)
        
        # Try to fetch remote data (will return None if it fails)
        remote_data = fetch_remote_data("https://api.example.com/data")
        
        logger.info(f"Successfully processed {len(processed_data)} items")
        if remote_data:
            logger.info(f"Successfully fetched remote data")
        else:
            logger.warning("Failed to fetch remote data")
        
    except ConfigError as e:
        # Handle configuration errors specifically
        logger.error(f"Configuration error: {e}")
        # Maybe use a default configuration or exit
    except BaseError as e:
        # Handle all other domain-specific errors
        logger.error(f"Error in main: {e}")
    except Exception as e:
        # Handle unexpected errors
        logger.critical(f"Unexpected error: {e}")
        # Maybe send an alert or exit


if __name__ == "__main__":
    main()
