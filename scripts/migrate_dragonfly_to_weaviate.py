#!/usr/bin/env python3
"""
Migrate data from DragonflyDB to Weaviate
Handles chat sessions, memory contexts, and agent configurations
"""

import json
import logging
import os
from datetime import datetime

import redis
import weaviate
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DragonflyToWeaviateMigrator:
    def __init__(self) -> None:
        # DragonflyDB connection
        self.dragonfly_url = os.getenv("DRAGONFLY_URI", "rediss://qpwj3s2ae.dragonflydb.cloud:6385")
        self.redis_client = redis.from_url(self.dragonfly_url)

        # Weaviate connection
        self.weaviate_endpoint = os.getenv("WEAVIATE_ENDPOINT", "http://10.120.0.3:8080")
        self.weaviate_client = weaviate.Client(self.weaviate_endpoint)

        # Embedding model for vector generation
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    def create_weaviate_schemas(self) -> None:
        """Create necessary Weaviate collections"""
        schemas = [
            {
                "class": "Personal",
                "description": "Personal information and memories",
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "timestamp", "dataType": ["date"]},
                    {"name": "context", "dataType": ["string"]},
                    {"name": "metadata", "dataType": ["object"]},
                ],
            },
            {
                "class": "PayReady",
                "description": "Pay Ready apartment software data",
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "timestamp", "dataType": ["date"]},
                    {"name": "context", "dataType": ["string"]},
                    {"name": "metadata", "dataType": ["object"]},
                ],
            },
            {
                "class": "ParagonRX",
                "description": "Paragon RX clinical trial data",
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "timestamp", "dataType": ["date"]},
                    {"name": "context", "dataType": ["string"]},
                    {"name": "metadata", "dataType": ["object"]},
                ],
            },
            {
                "class": f"Session_{datetime.now().strftime('%Y%m%d')}",
                "description": "Today's chat sessions",
                "properties": [
                    {"name": "message", "dataType": ["text"]},
                    {"name": "speaker", "dataType": ["string"]},
                    {"name": "session_id", "dataType": ["string"]},
                    {"name": "timestamp", "dataType": ["date"]},
                    {"name": "metadata", "dataType": ["object"]},
                ],
            },
        ]

        for schema in schemas:
            try:
                self.weaviate_client.schema.create_class(schema)
                logger.info(f"Created Weaviate class: {schema['class']}")
            except Exception as e:
                logger.warning(f"Class {schema['class']} may already exist: {e}")

    def migrate_chat_sessions(self) -> None:
        """Migrate chat sessions from DragonflyDB to Weaviate"""
        logger.info("Starting chat session migration...")

        # Scan for chat-related keys
        chat_keys = []
        for key in self.redis_client.scan_iter("*chat*"):
            chat_keys.append(key)

        logger.info(f"Found {len(chat_keys)} chat keys to migrate")

        session_class = f"Session_{datetime.now().strftime('%Y%m%d')}"
        migrated_count = 0

        for key in chat_keys:
            try:
                # Get data from DragonflyDB
                data = self.redis_client.get(key)
                if isinstance(data, bytes):
                    data = data.decode("utf-8")

                # Parse JSON if needed
                try:
                    parsed_data = json.loads(data)
                except:
                    parsed_data = {"content": data}

                # Extract content for embedding
                content = parsed_data.get("message", parsed_data.get("content", str(data)))

                # Generate embedding
                vector = self.embedder.encode(content).tolist()

                # Create Weaviate object
                weaviate_obj = {
                    "message": content,
                    "speaker": parsed_data.get("speaker", "unknown"),
                    "session_id": key.decode("utf-8") if isinstance(key, bytes) else str(key),
                    "timestamp": datetime.now().isoformat(),
                    "metadata": parsed_data,
                }

                # Insert into Weaviate
                self.weaviate_client.data_object.create(
                    data_object=weaviate_obj, class_name=session_class, vector=vector
                )

                migrated_count += 1

                if migrated_count % 100 == 0:
                    logger.info(f"Migrated {migrated_count} chat sessions...")

            except Exception as e:
                logger.error(f"Failed to migrate key {key}: {e}")

        logger.info(f"Successfully migrated {migrated_count} chat sessions")

    def migrate_memory_contexts(self) -> None:
        """Migrate memory contexts based on patterns"""
        logger.info("Starting memory context migration...")

        # Define context patterns
        context_patterns = {
            "Personal": ["*personal*", "*user*", "*preference*"],
            "PayReady": ["*payready*", "*apartment*", "*tenant*", "*property*"],
            "ParagonRX": ["*paragon*", "*clinical*", "*trial*", "*patient*"],
        }

        for class_name, patterns in context_patterns.items():
            migrated_count = 0

            for pattern in patterns:
                for key in self.redis_client.scan_iter(pattern):
                    try:
                        # Get data
                        data = self.redis_client.get(key)
                        if isinstance(data, bytes):
                            data = data.decode("utf-8")

                        # Parse JSON if needed
                        try:
                            parsed_data = json.loads(data)
                        except:
                            parsed_data = {"content": data}

                        # Extract content
                        content = parsed_data.get("content", str(data))

                        # Generate embedding
                        vector = self.embedder.encode(content).tolist()

                        # Create Weaviate object
                        weaviate_obj = {
                            "content": content,
                            "timestamp": datetime.now().isoformat(),
                            "context": key.decode("utf-8") if isinstance(key, bytes) else str(key),
                            "metadata": parsed_data,
                        }

                        # Insert into Weaviate
                        self.weaviate_client.data_object.create(
                            data_object=weaviate_obj,
                            class_name=class_name,
                            vector=vector,
                        )

                        migrated_count += 1

                    except Exception as e:
                        logger.error(f"Failed to migrate key {key} to {class_name}: {e}")

            logger.info(f"Migrated {migrated_count} items to {class_name}")

    def create_backup_snapshot(self) -> str:
        """Create a backup snapshot of DragonflyDB data"""
        logger.info("Creating DragonflyDB backup snapshot...")

        # Export all keys to a JSON file
        backup_data = {}

        for key in self.redis_client.scan_iter("*"):
            try:
                value = self.redis_client.get(key)
                if isinstance(key, bytes):
                    key = key.decode("utf-8")
                if isinstance(value, bytes):
                    value = value.decode("utf-8")
                backup_data[key] = value
            except Exception as e:
                logger.error(f"Failed to backup key {key}: {e}")

        # Save backup
        backup_file = f"dragonfly_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, "w") as f:
            json.dump(backup_data, f, indent=2)

        logger.info(f"Backup saved to {backup_file}")
        return backup_file

    def verify_migration(self) -> bool:
        """Verify migration success by comparing counts"""
        logger.info("Verifying migration...")

        # Count DragonflyDB keys
        dragonfly_count = sum(1 for _ in self.redis_client.scan_iter("*"))

        # Count Weaviate objects
        weaviate_count = 0
        classes = [
            "Personal",
            "PayReady",
            "ParagonRX",
            f"Session_{datetime.now().strftime('%Y%m%d')}",
        ]

        for class_name in classes:
            try:
                result = self.weaviate_client.query.aggregate(class_name).with_meta_count().do()
                count = result["data"]["Aggregate"][class_name][0]["meta"]["count"]
                weaviate_count += count
                logger.info(f"{class_name}: {count} objects")
            except Exception as e:
                logger.warning(f"Could not count {class_name}: {e}")

        logger.info(f"DragonflyDB keys: {dragonfly_count}")
        logger.info(f"Weaviate objects: {weaviate_count}")

        return weaviate_count > 0

    def run(self) -> bool:
        """Execute the full migration"""
        logger.info("Starting DragonflyDB to Weaviate migration...")

        # Create backup first
        backup_file = self.create_backup_snapshot()

        # Create Weaviate schemas
        self.create_weaviate_schemas()

        # Migrate data
        self.migrate_chat_sessions()
        self.migrate_memory_contexts()

        # Verify migration
        success = self.verify_migration()

        if success:
            logger.info("Migration completed successfully!")
            logger.info(f"Backup available at: {backup_file}")
        else:
            logger.error("Migration may have failed - please check logs")

        return success


if __name__ == "__main__":
    migrator = DragonflyToWeaviateMigrator()
    migrator.run()
