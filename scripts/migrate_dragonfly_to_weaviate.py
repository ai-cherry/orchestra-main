#!/usr/bin/env python3
"""
Dragonfly to Weaviate Migration Script
======================================
Migrates memory data from Paperspace Dragonfly instance to DigitalOcean Weaviate.
Handles domain-specific collections, embedding generation, and data validation.

Features:
- Idempotent execution (safe to run multiple times)
- Progress tracking and detailed logging
- Batch processing for efficiency
- Validation checks to ensure data integrity
- Domain-specific collection mapping
- Automatic embedding generation for text content

Usage:
    python migrate_dragonfly_to_weaviate.py [--dragonfly-host DRAGONFLY_HOST] [--dragonfly-port DRAGONFLY_PORT]
                                           [--weaviate-endpoint WEAVIATE_ENDPOINT] [--weaviate-api-key WEAVIATE_API_KEY]
                                           [--batch-size BATCH_SIZE] [--dry-run]

Author: Orchestra AI Platform
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set
import uuid

import redis
import weaviate
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("migration.log")
    ]
)
logger = logging.getLogger("migration")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Migrate data from Dragonfly to Weaviate")
    parser.add_argument(
        "--dragonfly-host",
        default=os.environ.get("DRAGONFLY_HOST", "localhost"),
        help="Dragonfly host (default: env DRAGONFLY_HOST or localhost)",
    )
    parser.add_argument(
        "--dragonfly-port",
        type=int,
        default=int(os.environ.get("DRAGONFLY_PORT", "6379")),
        help="Dragonfly port (default: env DRAGONFLY_PORT or 6379)",
    )
    parser.add_argument(
        "--weaviate-endpoint",
        default=os.environ.get("WEAVIATE_ENDPOINT", "http://localhost:8080"),
        help="Weaviate endpoint URL (default: env WEAVIATE_ENDPOINT or http://localhost:8080)",
    )
    parser.add_argument(
        "--weaviate-api-key",
        default=os.environ.get("WEAVIATE_API_KEY"),
        help="Weaviate API key (default: env WEAVIATE_API_KEY)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of items to process in a batch (default: 100)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without writing to Weaviate",
    )
    parser.add_argument(
        "--skip-embedding",
        action="store_true",
        help="Skip embedding generation (faster but less complete)",
    )
    parser.add_argument(
        "--tenant",
        default=datetime.now().strftime("%Y%m%d"),
        help="Tenant ID for Session collection (default: current date YYYYMMDD)",
    )
    return parser.parse_args()


def connect_to_dragonfly(host: str, port: int) -> redis.Redis:
    """
    Connect to Dragonfly instance with retry logic.
    
    Args:
        host: Dragonfly host
        port: Dragonfly port
        
    Returns:
        Redis client connected to Dragonfly
    """
    logger.info(f"Connecting to Dragonfly at {host}:{port}")
    
    # Retry connection up to 5 times
    max_retries = 5
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            client = redis.Redis(host=host, port=port, decode_responses=True)
            
            # Verify connection
            if client.ping():
                logger.info("Successfully connected to Dragonfly")
                return client
            else:
                logger.warning("Dragonfly ping failed")
        except Exception as e:
            logger.warning(f"Connection attempt {attempt+1}/{max_retries} failed: {str(e)}")
        
        if attempt < max_retries - 1:
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    # If we get here, all retries failed
    raise ConnectionError(f"Failed to connect to Dragonfly at {host}:{port} after {max_retries} attempts")


def connect_to_weaviate(endpoint: str, api_key: Optional[str] = None) -> weaviate.Client:
    """
    Connect to Weaviate instance with retry logic.
    
    Args:
        endpoint: Weaviate endpoint URL
        api_key: Weaviate API key (optional)
        
    Returns:
        Weaviate client
    """
    logger.info(f"Connecting to Weaviate at {endpoint}")
    
    auth_config = None
    if api_key:
        auth_config = weaviate.AuthApiKey(api_key=api_key)
    
    # Retry connection up to 5 times
    max_retries = 5
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            client = weaviate.Client(
                url=endpoint,
                auth_client_secret=auth_config,
                timeout_config=(5, 60)  # (connect_timeout, read_timeout)
            )
            
            # Verify connection
            if client.is_ready():
                logger.info("Successfully connected to Weaviate")
                return client
            else:
                logger.warning("Weaviate is not ready")
        except Exception as e:
            logger.warning(f"Connection attempt {attempt+1}/{max_retries} failed: {str(e)}")
        
        if attempt < max_retries - 1:
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    # If we get here, all retries failed
    raise ConnectionError(f"Failed to connect to Weaviate at {endpoint} after {max_retries} attempts")


def load_embedding_model() -> SentenceTransformer:
    """
    Load the sentence transformer model for generating embeddings.
    
    Returns:
        SentenceTransformer model
    """
    logger.info("Loading embedding model (MiniLM)...")
    try:
        # Use a small, efficient model for embedding generation
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embedding model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to load embedding model: {str(e)}")
        raise


def get_memory_keys_from_dragonfly(dragonfly_client: redis.Redis) -> List[str]:
    """
    Get all memory keys from Dragonfly.
    
    Args:
        dragonfly_client: Redis client connected to Dragonfly
        
    Returns:
        List of memory keys
    """
    logger.info("Retrieving memory keys from Dragonfly...")
    try:
        # Use scan_iter to efficiently iterate through keys
        memory_keys = list(dragonfly_client.scan_iter(match="memory:*"))
        logger.info(f"Found {len(memory_keys)} memory keys")
        return memory_keys
    except Exception as e:
        logger.error(f"Failed to retrieve memory keys: {str(e)}")
        raise


def get_memory_item(dragonfly_client: redis.Redis, key: str) -> Dict[str, Any]:
    """
    Get a memory item from Dragonfly.
    
    Args:
        dragonfly_client: Redis client connected to Dragonfly
        key: Memory key
        
    Returns:
        Memory item as a dictionary
    """
    try:
        # Get all fields for the hash
        data = dragonfly_client.hgetall(key)
        if not data:
            return None
        
        # Extract memory ID from key
        memory_id = key.split(":", 1)[1] if ":" in key else key
        
        # Ensure ID is present in the data
        if "id" not in data:
            data["id"] = memory_id
            
        # Parse metadata if it's a JSON string
        if "metadata" in data and isinstance(data["metadata"], str):
            try:
                data["metadata"] = json.loads(data["metadata"])
            except json.JSONDecodeError:
                # Keep as string if not valid JSON
                pass
                
        # Parse embedding if it's a JSON string
        if "embedding" in data and isinstance(data["embedding"], str):
            try:
                data["embedding"] = json.loads(data["embedding"])
            except json.JSONDecodeError:
                # Remove invalid embedding
                data.pop("embedding")
        
        return data
    except Exception as e:
        logger.error(f"Failed to get memory item {key}: {str(e)}")
        return None


def determine_domain(memory_item: Dict[str, Any]) -> str:
    """
    Determine the appropriate domain for a memory item.
    
    Args:
        memory_item: Memory item as a dictionary
        
    Returns:
        Domain name (Personal, PayReady, ParagonRX, or Session)
    """
    # Check if domain is already specified
    if "domain" in memory_item and memory_item["domain"] in ["Personal", "PayReady", "ParagonRX"]:
        return memory_item["domain"]
    
    # Check metadata for domain indicators
    metadata = memory_item.get("metadata", {})
    if isinstance(metadata, dict):
        # Check for PayReady indicators
        if any(key in metadata for key in ["tenantId", "unitNumber", "apartmentId"]):
            return "PayReady"
        
        # Check for ParagonRX indicators
        if any(key in metadata for key in ["trialId", "patientId", "clinicalTrial"]):
            return "ParagonRX"
    
    # Check content for domain indicators
    content = memory_item.get("content", "").lower()
    if content:
        if any(term in content for term in ["apartment", "tenant", "rent", "lease", "unit"]):
            return "PayReady"
        if any(term in content for term in ["trial", "patient", "clinical", "medical", "drug"]):
            return "ParagonRX"
    
    # Default to Personal domain
    return "Personal"


def generate_embedding(model: SentenceTransformer, text: str) -> List[float]:
    """
    Generate an embedding for text content.
    
    Args:
        model: SentenceTransformer model
        text: Text to embed
        
    Returns:
        Embedding vector as a list of floats
    """
    try:
        # Generate embedding
        embedding = model.encode(text)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Failed to generate embedding: {str(e)}")
        # Return a zero vector as fallback (384 dimensions for MiniLM)
        return [0.0] * 384


def prepare_memory_item_for_weaviate(
    memory_item: Dict[str, Any], 
    model: Optional[SentenceTransformer] = None,
    tenant: str = None
) -> Tuple[Dict[str, Any], str, Optional[List[float]]]:
    """
    Prepare a memory item for import into Weaviate.
    
    Args:
        memory_item: Memory item from Dragonfly
        model: SentenceTransformer model for generating embeddings
        tenant: Tenant ID for Session collection
        
    Returns:
        Tuple of (prepared item dict, collection name, embedding vector)
    """
    # Create a copy to avoid modifying the original
    item = memory_item.copy()
    
    # Ensure required fields are present
    if "id" not in item or not item["id"]:
        item["id"] = str(uuid.uuid4())
    
    if "timestamp" not in item or not item["timestamp"]:
        item["timestamp"] = datetime.now().isoformat()
    
    # Determine domain/collection
    domain = determine_domain(item)
    
    # Set domain field
    item["domain"] = domain
    
    # For Session collection, add tenant field
    if domain == "Session" and tenant:
        item["tenant"] = tenant
    
    # Extract embedding if present
    embedding = item.pop("embedding", None)
    
    # Generate embedding if not present and model is provided
    if not embedding and model and "content" in item and item["content"]:
        embedding = generate_embedding(model, item["content"])
    
    # Determine collection name
    collection_name = domain
    
    # Remove any fields that shouldn't be stored in Weaviate
    # (embedding will be stored separately)
    if "_additional" in item:
        item.pop("_additional")
    
    return item, collection_name, embedding


def batch_import_to_weaviate(
    weaviate_client: weaviate.Client,
    items: List[Tuple[Dict[str, Any], str, Optional[List[float]]]], 
    dry_run: bool = False
) -> Tuple[int, int, Set[str]]:
    """
    Import a batch of items into Weaviate.
    
    Args:
        weaviate_client: Weaviate client
        items: List of tuples (item_dict, collection_name, embedding)
        dry_run: If True, don't actually import
        
    Returns:
        Tuple of (success_count, error_count, set of imported IDs)
    """
    if dry_run:
        logger.info(f"[DRY RUN] Would import {len(items)} items to Weaviate")
        return len(items), 0, {item[0]["id"] for item in items}
    
    success_count = 0
    error_count = 0
    imported_ids = set()
    
    # Group items by collection for batch efficiency
    collections = {}
    for item, collection, embedding in items:
        if collection not in collections:
            collections[collection] = []
        collections[collection].append((item, embedding))
    
    # Process each collection
    for collection, collection_items in collections.items():
        try:
            with weaviate_client.batch as batch:
                for item, embedding in collection_items:
                    item_id = item["id"]
                    try:
                        # Configure batch
                        batch.configure(batch_size=100, dynamic=True)
                        
                        # Add to batch
                        batch.add_data_object(
                            data_object=item,
                            class_name=collection,
                            uuid=item_id,
                            vector=embedding
                        )
                        
                        success_count += 1
                        imported_ids.add(item_id)
                    except Exception as e:
                        logger.error(f"Error adding item {item_id} to batch: {str(e)}")
                        error_count += 1
        except Exception as e:
            logger.error(f"Error processing batch for collection {collection}: {str(e)}")
            error_count += len(collection_items)
    
    logger.info(f"Batch import: {success_count} succeeded, {error_count} failed")
    return success_count, error_count, imported_ids


def validate_migration(
    dragonfly_client: redis.Redis,
    weaviate_client: weaviate.Client,
    migrated_ids: Set[str]
) -> bool:
    """
    Validate that migration was successful by checking a sample of migrated items.
    
    Args:
        dragonfly_client: Redis client connected to Dragonfly
        weaviate_client: Weaviate client
        migrated_ids: Set of IDs that were migrated
        
    Returns:
        True if validation passed, False otherwise
    """
    logger.info("Validating migration...")
    
    # Sample up to 10 items for validation
    sample_size = min(10, len(migrated_ids))
    sample_ids = list(migrated_ids)[:sample_size]
    
    validation_passed = True
    
    for memory_id in sample_ids:
        try:
            # Get original item from Dragonfly
            dragonfly_key = f"memory:{memory_id}"
            dragonfly_item = get_memory_item(dragonfly_client, dragonfly_key)
            
            if not dragonfly_item:
                logger.warning(f"Validation: Item {memory_id} not found in Dragonfly")
                validation_passed = False
                continue
                
            # Determine domain/collection
            domain = determine_domain(dragonfly_item)
            
            # Get migrated item from Weaviate
            try:
                weaviate_item = weaviate_client.data_object.get_by_id(
                    uuid=memory_id,
                    class_name=domain
                )
                
                if not weaviate_item:
                    logger.warning(f"Validation: Item {memory_id} not found in Weaviate")
                    validation_passed = False
                    continue
                
                # Check content field matches
                if dragonfly_item.get("content") != weaviate_item.get("content"):
                    logger.warning(f"Validation: Content mismatch for item {memory_id}")
                    validation_passed = False
                
            except Exception as e:
                logger.warning(f"Validation: Error retrieving item {memory_id} from Weaviate: {str(e)}")
                validation_passed = False
                
        except Exception as e:
            logger.warning(f"Validation: Error processing item {memory_id}: {str(e)}")
            validation_passed = False
    
    if validation_passed:
        logger.info("Validation passed successfully")
    else:
        logger.warning("Validation failed - some items may not have been migrated correctly")
    
    return validation_passed


def delete_from_dragonfly(
    dragonfly_client: redis.Redis, 
    keys: List[str],
    dry_run: bool = False
) -> int:
    """
    Delete successfully migrated items from Dragonfly.
    
    Args:
        dragonfly_client: Redis client connected to Dragonfly
        keys: List of keys to delete
        dry_run: If True, don't actually delete
        
    Returns:
        Number of keys deleted
    """
    if dry_run:
        logger.info(f"[DRY RUN] Would delete {len(keys)} keys from Dragonfly")
        return len(keys)
    
    deleted_count = 0
    
    for key in keys:
        try:
            dragonfly_client.delete(key)
            deleted_count += 1
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {str(e)}")
    
    logger.info(f"Deleted {deleted_count} keys from Dragonfly")
    return deleted_count


def main():
    """Main migration function."""
    args = parse_args()
    
    try:
        # Connect to Dragonfly
        dragonfly_client = connect_to_dragonfly(args.dragonfly_host, args.dragonfly_port)
        
        # Connect to Weaviate
        weaviate_client = connect_to_weaviate(args.weaviate_endpoint, args.weaviate_api_key)
        
        # Load embedding model if needed
        model = None
        if not args.skip_embedding:
            model = load_embedding_model()
        
        # Get all memory keys from Dragonfly
        memory_keys = get_memory_keys_from_dragonfly(dragonfly_client)
        
        if not memory_keys:
            logger.info("No memory keys found in Dragonfly. Nothing to migrate.")
            return 0
        
        # Track statistics
        total_keys = len(memory_keys)
        processed_count = 0
        success_count = 0
        error_count = 0
        migrated_ids = set()
        
        # Process in batches
        batch_size = args.batch_size
        
        logger.info(f"Starting migration of {total_keys} items in batches of {batch_size}")
        
        # Setup progress bar
        with tqdm(total=total_keys, desc="Migrating") as pbar:
            for i in range(0, total_keys, batch_size):
                batch_keys = memory_keys[i:i+batch_size]
                batch_items = []
                
                # Prepare batch items
                for key in batch_keys:
                    try:
                        # Get memory item from Dragonfly
                        memory_item = get_memory_item(dragonfly_client, key)
                        
                        if not memory_item:
                            logger.warning(f"Skipping empty or invalid item: {key}")
                            error_count += 1
                            processed_count += 1
                            pbar.update(1)
                            continue
                        
                        # Prepare item for Weaviate
                        prepared_item, collection, embedding = prepare_memory_item_for_weaviate(
                            memory_item, model, args.tenant
                        )
                        
                        batch_items.append((prepared_item, collection, embedding))
                    except Exception as e:
                        logger.error(f"Error preparing item {key}: {str(e)}")
                        error_count += 1
                        processed_count += 1
                        pbar.update(1)
                
                # Import batch to Weaviate
                if batch_items:
                    batch_success, batch_error, batch_ids = batch_import_to_weaviate(
                        weaviate_client, batch_items, args.dry_run
                    )
                    
                    success_count += batch_success
                    error_count += batch_error
                    migrated_ids.update(batch_ids)
                
                # Update progress
                processed_count += len(batch_keys)
                pbar.update(len(batch_keys))
                
                # Log progress
                logger.info(f"Progress: {processed_count}/{total_keys} items processed")
        
        # Validate migration
        if not args.dry_run and migrated_ids:
            validate_migration(dragonfly_client, weaviate_client, migrated_ids)
        
        # Delete successfully migrated items from Dragonfly
        if success_count > 0:
            # Only delete keys for successfully migrated items
            keys_to_delete = [f"memory:{item_id}" for item_id in migrated_ids]
            delete_from_dragonfly(dragonfly_client, keys_to_delete, args.dry_run)
        
        # Log final statistics
        logger.info(f"Migration completed: {success_count} succeeded, {error_count} failed")
        logger.info(f"Total items migrated: {len(migrated_ids)}")
        
        return 0 if error_count == 0 else 1
    
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
