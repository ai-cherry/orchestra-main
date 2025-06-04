#!/usr/bin/env python3
"""
"""
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("weaviate_setup.log")],
)
logger = logging.getLogger("weaviate-setup")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Set up Weaviate collections for Cherry AI")
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("WEAVIATE_ENDPOINT", "http://localhost:8080"),
        help="Weaviate endpoint URL (default: env WEAVIATE_ENDPOINT or http://localhost:8080)",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("WEAVIATE_API_KEY"),
        help="Weaviate API key (default: env WEAVIATE_API_KEY)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify collections only, don't create them",
    )
    return parser.parse_args()

def connect_to_weaviate(endpoint: str, api_key: Optional[str] = None) -> weaviate.Client:
    """
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

            pass
            client = weaviate.Client(
                url=endpoint, auth_client_secret=auth_config, timeout_config=(5, 60)  # (connect_timeout, read_timeout)
            )

            # Verify connection
            if client.is_ready():
                logger.info("Successfully connected to Weaviate")
                return client
            else:
                logger.warning("Weaviate is not ready")
        except Exception:

            pass
            logger.warning(f"Connection attempt {attempt+1}/{max_retries} failed: {str(e)}")

        if attempt < max_retries - 1:
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

    # If we get here, all retries failed
    raise ConnectionError(f"Failed to connect to Weaviate at {endpoint} after {max_retries} attempts")

def collection_exists(client: weaviate.Client, class_name: str) -> bool:
    """
    """
        classes = schema.get("classes", [])
        return any(cls["class"] == class_name for cls in classes)
    except Exception:

        pass
        logger.error(f"Error checking if collection {class_name} exists: {str(e)}")
        return False

def create_collection(client: weaviate.Client, class_config: Dict[str, Any]) -> bool:
    """
    """
    class_name = class_config["class"]

    try:


        pass
        if collection_exists(client, class_name):
            logger.info(f"Collection {class_name} already exists, skipping creation")
            return True

        logger.info(f"Creating collection {class_name}")
        client.schema.create_class(class_config)
        logger.info(f"Successfully created collection {class_name}")
        return True
    except Exception:

        pass
        logger.error(f"Error creating collection {class_name}: {str(e)}")
        return False

def get_personal_collection_config() -> Dict[str, Any]:
    """
    """
        "class": "Personal",
        "description": "Personal information and use",
        "vectorizer": "text2vec-openai",
        "moduleConfig": {
            "text2vec-openai": {"model": "text-embedding-3-small", "modelVersion": "001", "type": "text"},
            "generative-openai": {},
        },
        "vectorIndexConfig": {
            "distance": "cosine",
            "ef": 256,
            "efConstruction": 256,
            "maxConnections": 64,
            "skip": False,
        },
        "invertedIndexConfig": {"indexNullState": True, "indexPropertyLength": True, "indexTimestamps": True},
        "properties": [
            {
                "name": "content",
                "dataType": ["text"],
                "description": "The main content of the personal information",
                "moduleConfig": {"text2vec-openai": {"skip": False, "vectorizePropertyName": False}},
                "indexFilterable": True,
                "indexSearchable": True,
            },
            {
                "name": "owner",
                "dataType": ["string"],
                "description": "Owner of the personal information",
                "moduleConfig": {"text2vec-openai": {"skip": True, "vectorizePropertyName": False}},
                "indexFilterable": True,
                "indexSearchable": True,
            },
            {
                "name": "tags",
                "dataType": ["string[]"],
                "description": "Tags associated with the personal information",
                "moduleConfig": {"text2vec-openai": {"skip": False, "vectorizePropertyName": True}},
                "indexFilterable": True,
                "indexSearchable": True,
            },
            {
                "name": "timestamp",
                "dataType": ["date"],
                "description": "When the information was created or updated",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": True,
                "indexSearchable": False,
            },
            {
                "name": "metadata",
                "dataType": ["object"],
                "description": "Additional metadata for the personal information",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": False,
                "indexSearchable": False,
            },
        ],
        "shardingConfig": {
            "virtualPerPhysical": 128,
            "desiredCount": 1,
            "actualCount": 1,
            "desiredVirtualCount": 128,
            "actualVirtualCount": 128,
        },
        "replicationConfig": {"factor": 1},
    }

def get_payready_collection_config() -> Dict[str, Any]:
    """
    """
        "class": "PayReady",
        "description": "Apartment-focused software company data",
        "vectorizer": "text2vec-openai",
        "moduleConfig": {
            "text2vec-openai": {"model": "text-embedding-3-small", "modelVersion": "001", "type": "text"},
            "generative-openai": {},
        },
        "vectorIndexConfig": {
            "distance": "cosine",
            "ef": 256,
            "efConstruction": 256,
            "maxConnections": 64,
            "skip": False,
        },
        "invertedIndexConfig": {"indexNullState": True, "indexPropertyLength": True, "indexTimestamps": True},
        "properties": [
            {
                "name": "content",
                "dataType": ["text"],
                "description": "The main content of the PayReady information",
                "moduleConfig": {"text2vec-openai": {"skip": False, "vectorizePropertyName": False}},
                "indexFilterable": True,
                "indexSearchable": True,
            },
            {
                "name": "tenantId",
                "dataType": ["string"],
                "description": "Tenant identifier",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": True,
                "indexSearchable": True,
            },
            {
                "name": "unitNumber",
                "dataType": ["string"],
                "description": "Apartment unit number",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": True,
                "indexSearchable": True,
            },
            {
                "name": "status",
                "dataType": ["string"],
                "description": "Current status of the tenant or unit",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": True,
                "indexSearchable": True,
            },
            {
                "name": "timestamp",
                "dataType": ["date"],
                "description": "When the information was created or updated",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": True,
                "indexSearchable": False,
            },
            {
                "name": "metadata",
                "dataType": ["object"],
                "description": "Additional metadata for the PayReady information",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": False,
                "indexSearchable": False,
            },
        ],
        "shardingConfig": {
            "virtualPerPhysical": 128,
            "desiredCount": 1,
            "actualCount": 1,
            "desiredVirtualCount": 128,
            "actualVirtualCount": 128,
        },
        "replicationConfig": {"factor": 1},
    }

def get_paragonrx_collection_config() -> Dict[str, Any]:
    """
    """
        "class": "ParagonRX",
        "description": "Clinical trial company data",
        "vectorizer": "text2vec-openai",
        "moduleConfig": {
            "text2vec-openai": {"model": "text-embedding-3-small", "modelVersion": "001", "type": "text"},
            "generative-openai": {},
        },
        "vectorIndexConfig": {
            "distance": "cosine",
            "ef": 256,
            "efConstruction": 256,
            "maxConnections": 64,
            "skip": False,
        },
        "invertedIndexConfig": {"indexNullState": True, "indexPropertyLength": True, "indexTimestamps": True},
        "properties": [
            {
                "name": "content",
                "dataType": ["text"],
                "description": "The main content of the clinical trial information",
                "moduleConfig": {"text2vec-openai": {"skip": False, "vectorizePropertyName": False}},
                "indexFilterable": True,
                "indexSearchable": True,
            },
            {
                "name": "trialId",
                "dataType": ["string"],
                "description": "Clinical trial identifier",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": True,
                "indexSearchable": True,
            },
            {
                "name": "patientId",
                "dataType": ["string"],
                "description": "Patient identifier (anonymized)",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": True,
                "indexSearchable": True,
            },
            {
                "name": "phase",
                "dataType": ["string"],
                "description": "Clinical trial phase",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": True,
                "indexSearchable": True,
            },
            {
                "name": "timestamp",
                "dataType": ["date"],
                "description": "When the information was created or updated",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": True,
                "indexSearchable": False,
            },
            {
                "name": "metadata",
                "dataType": ["object"],
                "description": "Additional metadata for the clinical trial information",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": False,
                "indexSearchable": False,
            },
        ],
        "shardingConfig": {
            "virtualPerPhysical": 128,
            "desiredCount": 1,
            "actualCount": 1,
            "desiredVirtualCount": 128,
            "actualVirtualCount": 128,
        },
        "replicationConfig": {"factor": 1},
    }

def get_session_collection_config() -> Dict[str, Any]:
    """
    """
        "class": "Session",
        "description": "Multi-tenant chat sessions with daily partitioning",
        "vectorizer": "text2vec-openai",
        "moduleConfig": {
            "text2vec-openai": {"model": "text-embedding-3-small", "modelVersion": "001", "type": "text"},
            "generative-openai": {},
        },
        "vectorIndexConfig": {
            "distance": "cosine",
            "ef": 256,
            "efConstruction": 256,
            "maxConnections": 64,
            "skip": False,
        },
        "invertedIndexConfig": {"indexNullState": True, "indexPropertyLength": True, "indexTimestamps": True},
        "properties": [
            {
                "name": "text",
                "dataType": ["text"],
                "description": "The message text content",
                "moduleConfig": {"text2vec-openai": {"skip": False, "vectorizePropertyName": False}},
                "indexFilterable": True,
                "indexSearchable": True,
            },
            {
                "name": "threadId",
                "dataType": ["string"],
                "description": "Conversation thread identifier",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": True,
                "indexSearchable": True,
            },
            {
                "name": "speaker",
                "dataType": ["string"],
                "description": "Who sent the message (user or assistant)",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": True,
                "indexSearchable": True,
            },
            {
                "name": "domain",
                "dataType": ["string"],
                "description": "Business domain (Personal, PayReady, ParagonRX)",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": True,
                "indexSearchable": True,
            },
            {
                "name": "tenant",
                "dataType": ["string"],
                "description": "Date-based tenant (YYYYMMDD) for multi-tenancy",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": True,
                "indexSearchable": True,
            },
            {
                "name": "timestamp",
                "dataType": ["date"],
                "description": "When the message was sent",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": True,
                "indexSearchable": False,
            },
            {
                "name": "metadata",
                "dataType": ["object"],
                "description": "Additional message metadata",
                "moduleConfig": {"text2vec-openai": {"skip": True}},
                "indexFilterable": False,
                "indexSearchable": False,
            },
        ],
        "shardingConfig": {
            "virtualPerPhysical": 128,
            "desiredCount": 1,
            "actualCount": 1,
            "desiredVirtualCount": 128,
            "actualVirtualCount": 128,
        },
        "replicationConfig": {"factor": 1},
    }

def verify_collection(client: weaviate.Client, class_name: str) -> bool:
    """
    """
            logger.error(f"Collection {class_name} does not exist")
            return False

        # Check if collection has data
        query = {"class": class_name, "limit": 1}
        result = client.query.get(class_name, ["_additional {count}"])
        count = result.get("data", {}).get("Get", {}).get(class_name, [])

        if count:
            logger.info(f"Collection {class_name} exists and contains data")
        else:
            logger.info(f"Collection {class_name} exists but is empty")

        return True
    except Exception:

        pass
        logger.error(f"Error verifying collection {class_name}: {str(e)}")
        return False

def enable_acorn(client: weaviate.Client) -> bool:
    """
    """
            if "config" in node and "query" in node["config"]:
                if node["config"]["query"].get("defaultACORNEnabled", False):
                    logger.info("ACORN is already enabled")
                    return True

        # Set ACORN configuration
        logger.info("Enabling ACORN hybrid search")

        # For Weaviate 1.30+, this is done via environment variables
        # QUERY_DEFAULT_ACORN_ENABLED=true in the docker-compose.yml
        # We'll log a message to remind the user
        logger.info("ACORN should be enabled via QUERY_DEFAULT_ACORN_ENABLED=true in docker-compose.yml")
        logger.info("If not enabled, please restart Weaviate with this environment variable set")

        return True
    except Exception:

        pass
        logger.error(f"Error enabling ACORN: {str(e)}")
        return False

def main():
    """Main entry point for the script."""
            class_name = collection_config["class"]

            if args.verify:
                # Verify only
                if verify_collection(client, class_name):
                    success_count += 1
            else:
                # Create and verify
                if create_collection(client, collection_config) and verify_collection(client, class_name):
                    success_count += 1

        # Report results
        total_collections = len(collections)
        if success_count == total_collections:
            logger.info(
                f"All {total_collections} collections successfully {'verified' if args.verify else 'created and verified'}"
            )
            return 0
        else:
            logger.error(
                f"Only {success_count}/{total_collections} collections were successfully {'verified' if args.verify else 'created and verified'}"
            )
            return 1

    except Exception:


        pass
        logger.error(f"An unexpected error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
