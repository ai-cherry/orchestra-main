#!/usr/bin/env python3
"""
Migration utility for transferring embeddings from Firestore to Vector Search.

This script migrates existing embeddings stored in Firestore to the configured
Vector Search backend. It supports incremental migration to avoid downtime
and provides progress reporting.

Usage:
    python migrate_embeddings_to_vector_search.py [--batch-size BATCH_SIZE] [--namespace NAMESPACE]
                                                 [--provider PROVIDER] [--dry-run]

Options:
    --batch-size BATCH_SIZE    Number of embeddings to process in each batch (default: 100)
    --namespace NAMESPACE      Namespace to migrate (default: "default")
    --provider PROVIDER        Vector search provider to use (default: "in_memory")
    --dry-run                  Run without making changes
"""

import argparse
import asyncio
import logging
import os
import sys
import time
from typing import Dict, List, Any, Optional, Tuple

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from packages.shared.src.storage.firestore.v2.adapter import FirestoreMemoryManagerV2
from packages.shared.src.storage.firestore.v2.constants import MEMORY_ITEMS_COLLECTION
from packages.shared.src.storage.vector.factory import VectorSearchFactory
from packages.shared.src.storage.vector.base import AbstractVectorSearch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("migrate_embeddings")


async def migrate_embeddings(
    batch_size: int = 100,
    namespace: str = "default",
    provider: str = "in_memory",
    vector_search_config: Optional[Dict[str, Any]] = None,
    dry_run: bool = False
) -> Tuple[int, int]:
    """
    Migrate embeddings from Firestore to Vector Search.
    
    Args:
        batch_size: Number of embeddings to process in each batch
        namespace: Namespace to migrate
        provider: Vector search provider to use
        vector_search_config: Configuration for the vector search provider
        dry_run: Run without making changes
        
    Returns:
        Tuple of (total_processed, total_migrated)
    """
    logger.info(f"Starting migration to {provider} vector search (namespace: {namespace})")
    if dry_run:
        logger.info("DRY RUN MODE: No changes will be made")
        
    # Initialize Firestore memory manager
    memory_manager = FirestoreMemoryManagerV2(
        namespace=namespace,
        vector_search_provider="in_memory"  # Use in-memory during migration to avoid conflicts
    )
    await memory_manager.initialize()
    
    # Initialize target vector search
    vector_search = VectorSearchFactory.create_vector_search(
        provider=provider,
        config=vector_search_config or {},
        log_level=logging.INFO
    )
    await vector_search.initialize()
    
    try:
        # Get all memory items with embeddings
        collection = memory_manager.firestore.config.get_collection_name(MEMORY_ITEMS_COLLECTION)
        
        # Process documents in batches
        cursor = None
        total_processed = 0
        total_migrated = 0
        start_time = time.time()
        
        while True:
            # Get next batch of documents
            docs = await memory_manager.firestore.query_documents(
                collection=collection,
                filters={},  # No filters to get all documents
                limit=batch_size,
                cursor=cursor
            )
            
            if not docs:
                break
                
            # Update cursor for next batch
            cursor = docs[-1]
            
            # Filter to documents with embeddings
            docs_with_embeddings = [doc for doc in docs if doc.get("embedding")]
            total_processed += len(docs)
            
            if not docs_with_embeddings:
                logger.info(f"Processed batch with {len(docs)} documents, no embeddings found")
                continue
                
            # Migrate embeddings
            for doc in docs_with_embeddings:
                doc_id = doc.get("id")
                embedding = doc.get("embedding")
                user_id = doc.get("user_id")
                persona = doc.get("persona")
                
                if not embedding or not doc_id:
                    continue
                    
                # Create metadata
                metadata = {
                    "user_id": user_id,
                    "namespace": namespace
                }
                
                if persona:
                    metadata["persona"] = persona
                
                # Store in vector search
                if not dry_run:
                    try:
                        await vector_search.store_embedding(
                            item_id=doc_id,
                            embedding=embedding,
                            metadata=metadata
                        )
                        total_migrated += 1
                    except Exception as e:
                        logger.error(f"Failed to migrate embedding {doc_id}: {e}")
                else:
                    # In dry run mode, just count
                    total_migrated += 1
                    
            elapsed = time.time() - start_time
            rate = total_processed / elapsed if elapsed > 0 else 0
            logger.info(
                f"Processed {total_processed} documents, migrated {total_migrated} embeddings "
                f"({rate:.2f} docs/sec)"
            )
            
            # Small delay to avoid overwhelming the system
            await asyncio.sleep(0.1)
            
        logger.info(f"Migration complete: {total_migrated} embeddings migrated to {provider}")
        return total_processed, total_migrated
        
    finally:
        # Clean up
        await memory_manager.close()
        await vector_search.close()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Migrate embeddings from Firestore to Vector Search"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of embeddings to process in each batch"
    )
    parser.add_argument(
        "--namespace",
        type=str,
        default="default",
        help="Namespace to migrate"
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="in_memory",
        choices=["in_memory", "vertex"],
        help="Vector search provider to use"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without making changes"
    )
    
    # Vertex AI Vector Search specific arguments
    parser.add_argument(
        "--project-id",
        type=str,
        help="Google Cloud project ID (for Vertex provider)"
    )
    parser.add_argument(
        "--location",
        type=str,
        default="us-west4",
        help="Google Cloud region (for Vertex provider)"
    )
    parser.add_argument(
        "--index-endpoint-id",
        type=str,
        help="Vector Search index endpoint ID (for Vertex provider)"
    )
    parser.add_argument(
        "--index-id",
        type=str,
        help="Vector Search index ID (for Vertex provider)"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()
    
    # Set up vector search config
    vector_search_config = {}
    if args.provider == "vertex":
        if not args.project_id or not args.index_endpoint_id or not args.index_id:
            logger.error(
                "For Vertex provider, --project-id, --index-endpoint-id, and --index-id are required"
            )
            sys.exit(1)
            
        vector_search_config = {
            "project_id": args.project_id,
            "location": args.location,
            "index_endpoint_id": args.index_endpoint_id,
            "index_id": args.index_id
        }
    
    # Run migration
    try:
        total_processed, total_migrated = await migrate_embeddings(
            batch_size=args.batch_size,
            namespace=args.namespace,
            provider=args.provider,
            vector_search_config=vector_search_config,
            dry_run=args.dry_run
        )
        
        logger.info(f"Migration summary:")
        logger.info(f"  Total documents processed: {total_processed}")
        logger.info(f"  Total embeddings migrated: {total_migrated}")
        logger.info(f"  Provider: {args.provider}")
        logger.info(f"  Namespace: {args.namespace}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())