#!/usr/bin/env python3
"""
Weaviate Migration Validation Script
====================================
Validates the entire Weaviate-first migration workflow by testing:
- Collection creation and schema validation
- Data insertion and retrieval across all collections
- Embedding generation and vector search
- Performance benchmarks
- Domain-specific collection functionality

This script ensures that all three domain collections (Personal, PayReady, ParagonRX)
and the Session collection are working properly after migration.

Usage:
    python validate_weaviate_migration.py [--weaviate-endpoint ENDPOINT] [--weaviate-api-key API_KEY]
                                         [--postgres-dsn DSN] [--dragonfly-uri URI]

Author: Orchestra AI Platform
"""

import argparse
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

import numpy as np
import psycopg2
import psycopg2.extras
from sentence_transformers import SentenceTransformer
import weaviate
from tqdm import tqdm

# Optional Redis import for Dragonfly testing
try:
    import redis
except ImportError:
    redis = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("validation.log")
    ]
)
logger = logging.getLogger("validation")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Validate Weaviate migration")
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
        "--postgres-dsn",
        default=os.environ.get("POSTGRES_DSN"),
        help="PostgreSQL connection string (default: env POSTGRES_DSN)",
    )
    parser.add_argument(
        "--dragonfly-uri",
        default=os.environ.get("DRAGONFLY_URI"),
        help="Dragonfly Redis URI (default: env DRAGONFLY_URI)",
    )
    parser.add_argument(
        "--skip-performance",
        action="store_true",
        help="Skip performance tests",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    return parser.parse_args()


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


def connect_to_postgres(dsn: str) -> psycopg2.extensions.connection:
    """
    Connect to PostgreSQL database.
    
    Args:
        dsn: PostgreSQL connection string
        
    Returns:
        PostgreSQL connection
    """
    logger.info(f"Connecting to PostgreSQL")
    
    try:
        conn = psycopg2.connect(dsn)
        logger.info("Successfully connected to PostgreSQL")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
        raise


def connect_to_dragonfly(uri: str) -> Optional[redis.Redis]:
    """
    Connect to Dragonfly Redis instance.
    
    Args:
        uri: Dragonfly Redis URI
        
    Returns:
        Redis client or None if Redis is not available
    """
    if not redis or not uri:
        logger.info("Skipping Dragonfly connection (not configured or redis package not installed)")
        return None
    
    logger.info(f"Connecting to Dragonfly at {uri}")
    
    try:
        client = redis.from_url(uri, decode_responses=True)
        if client.ping():
            logger.info("Successfully connected to Dragonfly")
            return client
        else:
            logger.warning("Dragonfly ping failed")
            return None
    except Exception as e:
        logger.warning(f"Failed to connect to Dragonfly: {str(e)}")
        return None


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


def validate_collections(weaviate_client: weaviate.Client) -> bool:
    """
    Validate that all required collections exist in Weaviate.
    
    Args:
        weaviate_client: Weaviate client
        
    Returns:
        True if all collections exist, False otherwise
    """
    logger.info("Validating collections...")
    
    required_collections = ["Personal", "PayReady", "ParagonRX", "Session"]
    existing_collections = []
    
    try:
        schema = weaviate_client.schema.get()
        classes = schema.get("classes", [])
        existing_collections = [cls["class"] for cls in classes]
        
        missing_collections = [col for col in required_collections if col not in existing_collections]
        
        if missing_collections:
            logger.error(f"Missing collections: {', '.join(missing_collections)}")
            return False
        
        logger.info(f"All required collections exist: {', '.join(required_collections)}")
        return True
    except Exception as e:
        logger.error(f"Failed to validate collections: {str(e)}")
        return False


def validate_collection_schema(weaviate_client: weaviate.Client, collection_name: str) -> bool:
    """
    Validate the schema of a specific collection.
    
    Args:
        weaviate_client: Weaviate client
        collection_name: Name of the collection to validate
        
    Returns:
        True if schema is valid, False otherwise
    """
    logger.info(f"Validating schema for collection {collection_name}...")
    
    try:
        schema = weaviate_client.schema.get()
        classes = schema.get("classes", [])
        
        # Find the collection in the schema
        collection = next((cls for cls in classes if cls["class"] == collection_name), None)
        
        if not collection:
            logger.error(f"Collection {collection_name} not found in schema")
            return False
        
        # Check vectorizer
        if collection.get("vectorizer") != "text2vec-openai":
            logger.error(f"Collection {collection_name} has incorrect vectorizer: {collection.get('vectorizer')}")
            return False
        
        # Check if ACORN is enabled
        if "moduleConfig" not in collection:
            logger.warning(f"Collection {collection_name} has no moduleConfig")
        
        # Check required properties
        required_properties = ["content", "timestamp"]
        collection_properties = [prop["name"] for prop in collection.get("properties", [])]
        
        missing_properties = [prop for prop in required_properties if prop not in collection_properties]
        if missing_properties:
            logger.error(f"Collection {collection_name} is missing required properties: {', '.join(missing_properties)}")
            return False
        
        logger.info(f"Schema for collection {collection_name} is valid")
        return True
    except Exception as e:
        logger.error(f"Failed to validate schema for collection {collection_name}: {str(e)}")
        return False


def test_insert_retrieve(
    weaviate_client: weaviate.Client, 
    collection_name: str,
    embedding_model: SentenceTransformer
) -> Tuple[bool, Optional[str]]:
    """
    Test inserting and retrieving data from a collection.
    
    Args:
        weaviate_client: Weaviate client
        collection_name: Name of the collection to test
        embedding_model: SentenceTransformer model for generating embeddings
        
    Returns:
        Tuple of (success, object_id)
    """
    logger.info(f"Testing insert and retrieve for collection {collection_name}...")
    
    # Create a test object
    test_id = str(uuid.uuid4())
    test_content = f"Test content for {collection_name} at {datetime.now().isoformat()}"
    
    # Generate embedding
    embedding = embedding_model.encode(test_content).tolist()
    
    # Create object properties based on collection
    properties = {
        "content": test_content,
        "timestamp": datetime.now().isoformat(),
        "source": "validation-script",
    }
    
    # Add collection-specific properties
    if collection_name == "Personal":
        properties["owner"] = "test-user"
        properties["tags"] = ["test", "validation"]
    elif collection_name == "PayReady":
        properties["tenantId"] = "test-tenant"
        properties["unitNumber"] = "A123"
        properties["status"] = "active"
    elif collection_name == "ParagonRX":
        properties["trialId"] = "trial-123"
        properties["patientId"] = "patient-456"
        properties["phase"] = "Phase 1"
    elif collection_name == "Session":
        properties["threadId"] = "thread-123"
        properties["speaker"] = "user"
        properties["domain"] = "Personal"
        properties["tenant"] = datetime.now().strftime("%Y%m%d")
    
    try:
        # Insert the object
        weaviate_client.data_object.create(
            data_object=properties,
            class_name=collection_name,
            uuid=test_id,
            vector=embedding
        )
        
        # Retrieve the object
        retrieved = weaviate_client.data_object.get_by_id(
            uuid=test_id,
            class_name=collection_name,
            with_vector=True
        )
        
        if not retrieved:
            logger.error(f"Failed to retrieve object from collection {collection_name}")
            return False, None
        
        # Check if content matches
        if retrieved.get("content") != test_content:
            logger.error(f"Retrieved content does not match for collection {collection_name}")
            return False, None
        
        logger.info(f"Successfully inserted and retrieved object from collection {collection_name}")
        return True, test_id
    except Exception as e:
        logger.error(f"Failed to insert/retrieve for collection {collection_name}: {str(e)}")
        return False, None


def test_vector_search(
    weaviate_client: weaviate.Client, 
    collection_name: str,
    object_id: str,
    embedding_model: SentenceTransformer
) -> bool:
    """
    Test vector search functionality for a collection.
    
    Args:
        weaviate_client: Weaviate client
        collection_name: Name of the collection to test
        object_id: ID of a known object in the collection
        embedding_model: SentenceTransformer model for generating embeddings
        
    Returns:
        True if vector search works, False otherwise
    """
    logger.info(f"Testing vector search for collection {collection_name}...")
    
    try:
        # Get the object to use as search reference
        obj = weaviate_client.data_object.get_by_id(
            uuid=object_id,
            class_name=collection_name
        )
        
        if not obj or "content" not in obj:
            logger.error(f"Failed to get reference object for vector search in collection {collection_name}")
            return False
        
        # Generate embedding for the content
        query_text = obj["content"]
        query_vector = embedding_model.encode(query_text).tolist()
        
        # Perform vector search
        result = (
            weaviate_client.query
            .get(collection_name, ["content", "_additional { id distance }"])
            .with_near_vector({"vector": query_vector})
            .with_limit(5)
            .do()
        )
        
        # Check if we got results
        matches = result.get("data", {}).get("Get", {}).get(collection_name, [])
        if not matches:
            logger.error(f"No vector search results for collection {collection_name}")
            return False
        
        # Check if our reference object is in the results
        found = False
        for match in matches:
            if match.get("_additional", {}).get("id") == object_id:
                found = True
                break
        
        if not found:
            logger.error(f"Reference object not found in vector search results for collection {collection_name}")
            return False
        
        logger.info(f"Vector search successful for collection {collection_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to test vector search for collection {collection_name}: {str(e)}")
        return False


def test_hybrid_search(
    weaviate_client: weaviate.Client, 
    collection_name: str,
    object_id: str
) -> bool:
    """
    Test hybrid search functionality for a collection.
    
    Args:
        weaviate_client: Weaviate client
        collection_name: Name of the collection to test
        object_id: ID of a known object in the collection
        
    Returns:
        True if hybrid search works, False otherwise
    """
    logger.info(f"Testing hybrid search for collection {collection_name}...")
    
    try:
        # Get the object to use as search reference
        obj = weaviate_client.data_object.get_by_id(
            uuid=object_id,
            class_name=collection_name
        )
        
        if not obj or "content" not in obj:
            logger.error(f"Failed to get reference object for hybrid search in collection {collection_name}")
            return False
        
        # Extract a keyword from the content
        content = obj["content"]
        keyword = content.split()[1] if len(content.split()) > 1 else content.split()[0]
        
        # Perform hybrid search
        result = (
            weaviate_client.query
            .get(collection_name, ["content", "_additional { id distance }"])
            .with_hybrid(query=keyword, alpha=0.5)  # Hybrid search with ACORN
            .with_limit(5)
            .do()
        )
        
        # Check if we got results
        matches = result.get("data", {}).get("Get", {}).get(collection_name, [])
        if not matches:
            logger.error(f"No hybrid search results for collection {collection_name}")
            return False
        
        # Check if our reference object is in the results
        found = False
        for match in matches:
            if match.get("_additional", {}).get("id") == object_id:
                found = True
                break
        
        if not found:
            logger.error(f"Reference object not found in hybrid search results for collection {collection_name}")
            return False
        
        logger.info(f"Hybrid search successful for collection {collection_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to test hybrid search for collection {collection_name}: {str(e)}")
        return False


def test_postgres_integration(
    postgres_conn: psycopg2.extensions.connection,
    weaviate_client: weaviate.Client,
    collection_name: str,
    object_id: str
) -> bool:
    """
    Test PostgreSQL integration by storing and retrieving data.
    
    Args:
        postgres_conn: PostgreSQL connection
        weaviate_client: Weaviate client
        collection_name: Name of the Weaviate collection
        object_id: ID of an object in Weaviate
        
    Returns:
        True if PostgreSQL integration works, False otherwise
    """
    if not postgres_conn:
        logger.info("Skipping PostgreSQL integration test (not configured)")
        return True
    
    logger.info(f"Testing PostgreSQL integration...")
    
    try:
        # Get the object from Weaviate
        obj = weaviate_client.data_object.get_by_id(
            uuid=object_id,
            class_name=collection_name,
            with_vector=True
        )
        
        if not obj:
            logger.error(f"Failed to get object from Weaviate for PostgreSQL test")
            return False
        
        # Extract vector if available
        embedding = None
        if "_additional" in obj and "vector" in obj["_additional"]:
            embedding = obj["_additional"]["vector"]
            del obj["_additional"]
        
        # Store in PostgreSQL
        with postgres_conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS validation_test (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    collection TEXT NOT NULL,
                    data JSONB,
                    embedding VECTOR(384)
                )
                """
            )
            
            cursor.execute(
                """
                INSERT INTO validation_test (id, content, collection, data, embedding)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    object_id,
                    obj.get("content", ""),
                    collection_name,
                    psycopg2.extras.Json(obj),
                    embedding
                )
            )
            
            postgres_conn.commit()
        
        # Retrieve from PostgreSQL
        with postgres_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(
                """
                SELECT * FROM validation_test
                WHERE id = %s
                """,
                (object_id,)
            )
            
            row = cursor.fetchone()
            
            if not row:
                logger.error(f"Failed to retrieve object from PostgreSQL")
                return False
            
            # Check if content matches
            if row["content"] != obj.get("content", ""):
                logger.error(f"Retrieved content from PostgreSQL does not match")
                return False
        
        logger.info(f"PostgreSQL integration test successful")
        return True
    except Exception as e:
        logger.error(f"Failed to test PostgreSQL integration: {str(e)}")
        return False
    finally:
        # Clean up test table
        try:
            with postgres_conn.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS validation_test")
                postgres_conn.commit()
        except Exception as e:
            logger.warning(f"Failed to clean up PostgreSQL test table: {str(e)}")


def test_dragonfly_integration(
    dragonfly_client: redis.Redis,
    weaviate_client: weaviate.Client,
    collection_name: str,
    object_id: str
) -> bool:
    """
    Test Dragonfly integration as a cache layer.
    
    Args:
        dragonfly_client: Redis client for Dragonfly
        weaviate_client: Weaviate client
        collection_name: Name of the Weaviate collection
        object_id: ID of an object in Weaviate
        
    Returns:
        True if Dragonfly integration works, False otherwise
    """
    if not dragonfly_client:
        logger.info("Skipping Dragonfly integration test (not configured)")
        return True
    
    logger.info(f"Testing Dragonfly integration...")
    
    try:
        # Get the object from Weaviate
        obj = weaviate_client.data_object.get_by_id(
            uuid=object_id,
            class_name=collection_name
        )
        
        if not obj:
            logger.error(f"Failed to get object from Weaviate for Dragonfly test")
            return False
        
        # Store in Dragonfly
        cache_key = f"memory:{object_id}"
        
        # Convert obj to string values for Redis
        redis_obj = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in obj.items()}
        
        dragonfly_client.hset(cache_key, mapping=redis_obj)
        
        # Retrieve from Dragonfly
        cached = dragonfly_client.hgetall(cache_key)
        
        if not cached:
            logger.error(f"Failed to retrieve object from Dragonfly")
            return False
        
        # Check if content matches (accounting for string conversion)
        if cached.get("content") != obj.get("content", ""):
            logger.error(f"Retrieved content from Dragonfly does not match")
            return False
        
        # Clean up
        dragonfly_client.delete(cache_key)
        
        logger.info(f"Dragonfly integration test successful")
        return True
    except Exception as e:
        logger.error(f"Failed to test Dragonfly integration: {str(e)}")
        return False


def run_performance_tests(weaviate_client: weaviate.Client, embedding_model: SentenceTransformer) -> Dict[str, Any]:
    """
    Run performance tests on Weaviate.
    
    Args:
        weaviate_client: Weaviate client
        embedding_model: SentenceTransformer model for generating embeddings
        
    Returns:
        Dictionary with performance metrics
    """
    logger.info("Running performance tests...")
    
    results = {
        "vector_search_latency_ms": [],
        "hybrid_search_latency_ms": [],
        "insert_latency_ms": [],
        "get_latency_ms": []
    }
    
    try:
        # Generate test data
        test_texts = [
            f"Performance test text {i} with some additional context for embedding generation" 
            for i in range(10)
        ]
        test_embeddings = [embedding_model.encode(text).tolist() for text in test_texts]
        
        # Test vector search performance
        for i, embedding in enumerate(test_embeddings):
            start_time = time.time()
            
            weaviate_client.query.get(
                "Session", ["content", "_additional { id distance }"]
            ).with_near_vector(
                {"vector": embedding}
            ).with_limit(5).do()
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            results["vector_search_latency_ms"].append(latency_ms)
        
        # Test hybrid search performance
        for text in test_texts:
            start_time = time.time()
            
            weaviate_client.query.get(
                "Session", ["content", "_additional { id distance }"]
            ).with_hybrid(
                query=text, alpha=0.5
            ).with_limit(5).do()
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            results["hybrid_search_latency_ms"].append(latency_ms)
        
        # Test insert performance
        test_objects = []
        for i, (text, embedding) in enumerate(zip(test_texts, test_embeddings)):
            test_id = str(uuid.uuid4())
            test_objects.append((test_id, text, embedding))
            
            start_time = time.time()
            
            weaviate_client.data_object.create(
                data_object={
                    "content": text,
                    "timestamp": datetime.now().isoformat(),
                    "source": "performance-test",
                    "tenant": datetime.now().strftime("%Y%m%d"),
                    "threadId": f"perf-{i}"
                },
                class_name="Session",
                uuid=test_id,
                vector=embedding
            )
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            results["insert_latency_ms"].append(latency_ms)
        
        # Test get performance
        for test_id, _, _ in test_objects:
            start_time = time.time()
            
            weaviate_client.data_object.get_by_id(
                uuid=test_id,
                class_name="Session"
            )
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            results["get_latency_ms"].append(latency_ms)
            
            # Clean up
            weaviate_client.data_object.delete(
                uuid=test_id,
                class_name="Session"
            )
        
        # Calculate statistics
        for metric, values in results.items():
            if values:
                results[f"{metric}_avg"] = sum(values) / len(values)
                results[f"{metric}_p95"] = sorted(values)[int(len(values) * 0.95)]
                results[f"{metric}_min"] = min(values)
                results[f"{metric}_max"] = max(values)
        
        logger.info("Performance tests completed")
        return results
    except Exception as e:
        logger.error(f"Failed to run performance tests: {str(e)}")
        return results


def main():
    """Main validation function."""
    args = parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Connect to services
        weaviate_client = connect_to_weaviate(args.weaviate_endpoint, args.weaviate_api_key)
        
        postgres_conn = None
        if args.postgres_dsn:
            postgres_conn = connect_to_postgres(args.postgres_dsn)
        
        dragonfly_client = None
        if args.dragonfly_uri:
            dragonfly_client = connect_to_dragonfly(args.dragonfly_uri)
        
        # Load embedding model
        embedding_model = load_embedding_model()
        
        # Track test results
        results = {
            "collections_exist": False,
            "schema_validation": {},
            "insert_retrieve": {},
            "vector_search": {},
            "hybrid_search": {},
            "postgres_integration": False,
            "dragonfly_integration": False,
            "performance": {}
        }
        
        # Validate collections
        results["collections_exist"] = validate_collections(weaviate_client)
        
        if not results["collections_exist"]:
            logger.error("Collection validation failed. Cannot proceed with further tests.")
            return 1
        
        # Validate schema for each collection
        collections = ["Personal", "PayReady", "ParagonRX", "Session"]
        for collection in collections:
            results["schema_validation"][collection] = validate_collection_schema(weaviate_client, collection)
        
        # Test insert and retrieve for each collection
        test_objects = {}
        for collection in collections:
            success, object_id = test_insert_retrieve(weaviate_client, collection, embedding_model)
            results["insert_retrieve"][collection] = success
            if success and object_id:
                test_objects[collection] = object_id
        
        # Test vector search for each collection
        for collection, object_id in test_objects.items():
            results["vector_search"][collection] = test_vector_search(
                weaviate_client, collection, object_id, embedding_model
            )
        
        # Test hybrid search for each collection
        for collection, object_id in test_objects.items():
            results["hybrid_search"][collection] = test_hybrid_search(
                weaviate_client, collection, object_id
            )
        
        # Test PostgreSQL integration
        if postgres_conn and "Session" in test_objects:
            results["postgres_integration"] = test_postgres_integration(
                postgres_conn, weaviate_client, "Session", test_objects["Session"]
            )
        
        # Test Dragonfly integration
        if dragonfly_client and "Session" in test_objects:
            results["dragonfly_integration"] = test_dragonfly_integration(
                dragonfly_client, weaviate_client, "Session", test_objects["Session"]
            )
        
        # Run performance tests
        if not args.skip_performance:
            results["performance"] = run_performance_tests(weaviate_client, embedding_model)
        
        # Print summary
        logger.info("\n----- VALIDATION SUMMARY -----")
        logger.info(f"Collections exist: {results['collections_exist']}")
        
        logger.info("\nSchema validation:")
        for collection, success in results["schema_validation"].items():
            logger.info(f"  {collection}: {'✅' if success else '❌'}")
        
        logger.info("\nInsert and retrieve:")
        for collection, success in results["insert_retrieve"].items():
            logger.info(f"  {collection}: {'✅' if success else '❌'}")
        
        logger.info("\nVector search:")
        for collection, success in results["vector_search"].items():
            logger.info(f"  {collection}: {'✅' if success else '❌'}")
        
        logger.info("\nHybrid search:")
        for collection, success in results["hybrid_search"].items():
            logger.info(f"  {collection}: {'✅' if success else '❌'}")
        
        logger.info(f"\nPostgreSQL integration: {'✅' if results['postgres_integration'] else '❌' if postgres_conn else 'SKIPPED'}")
        logger.info(f"Dragonfly integration: {'✅' if results['dragonfly_integration'] else '❌' if dragonfly_client else 'SKIPPED'}")
        
        if "vector_search_latency_ms_avg" in results["performance"]:
            logger.info("\nPerformance metrics:")
            logger.info(f"  Vector search avg latency: {results['performance']['vector_search_latency_ms_avg']:.2f} ms")
            logger.info(f"  Hybrid search avg latency: {results['performance']['hybrid_search_latency_ms_avg']:.2f} ms")
            logger.info(f"  Insert avg latency: {results['performance']['insert_latency_ms_avg']:.2f} ms")
            logger.info(f"  Get avg latency: {results['performance']['get_latency_ms_avg']:.2f} ms")
            
            # Check if micro-cache is recommended
            p95_latency = results["performance"].get("vector_search_latency_ms_p95", 0)
            if p95_latency > 50:
                logger.warning(f"\n⚠️ p95 latency ({p95_latency:.2f} ms) exceeds 50ms threshold")
                logger.warning("Consider enabling micro-cache with Dragonfly for improved performance")
            else:
                logger.info(f"\n✅ p95 latency ({p95_latency:.2f} ms) is below 50ms threshold")
                logger.info("No micro-cache needed for optimal performance")
        
        # Determine overall success
        all_schema_valid = all(results["schema_validation"].values())
        all_insert_retrieve = all(results["insert_retrieve"].values())
        all_vector_search = all(results["vector_search"].values())
        all_hybrid_search = all(results["hybrid_search"].values())
        
        overall_success = (
            results["collections_exist"] and
            all_schema_valid and
            all_insert_retrieve and
            all_vector_search and
            all_hybrid_search and
            (results["postgres_integration"] or not postgres_conn) and
            (results["dragonfly_integration"] or not dragonfly_client)
        )
        
        logger.info(f"\nOverall validation: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        # Save results to file
        with open("validation_results.json", "w") as f:
            json.dump(results, f, indent=2)
        logger.info("Detailed results saved to validation_results.json")
        
        return 0 if overall_success else 1
    
    except Exception as e:
        logger.error(f"Validation failed with error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
