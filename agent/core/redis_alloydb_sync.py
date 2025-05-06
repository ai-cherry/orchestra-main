"""
Redis to AlloyDB Synchronization Worker

This module implements an asynchronous worker for real-time synchronization of data
between Redis (hot tier) and AlloyDB (persistent storage) in the AGI Baby Cherry project.
It ensures data consistency for agent memory and vector embeddings, with version-based
conflict resolution to handle concurrent updates.
"""

import asyncio
import logging
import os
from typing import List, Tuple, Dict, Any
import redis.asyncio as redis
import psycopg2
from psycopg2.extras import execute_batch
import crc32c

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisAlloyDBSyncWorker:
    """
    Asynchronous worker for syncing data from Redis to AlloyDB with conflict resolution.
    """
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        alloydb_host: str = "localhost",
        alloydb_port: int = 5432,
        alloydb_dbname: str = "agi_baby_cherry",
        alloydb_user: str = "postgres",
        alloydb_password: str = "",
        debounce_interval: float = 0.5,
        batch_size: int = 100
    ):
        """
        Initialize the sync worker with connection parameters.
        
        Args:
            redis_host: Hostname of the Redis server.
            redis_port: Port of the Redis server.
            alloydb_host: Hostname of the AlloyDB server.
            alloydb_port: Port of the AlloyDB server.
            alloydb_dbname: Database name in AlloyDB.
            alloydb_user: Username for AlloyDB connection.
            alloydb_password: Password for AlloyDB connection.
            debounce_interval: Time in seconds to debounce updates.
            batch_size: Maximum number of changes to process in a batch.
        """
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.alloydb_host = alloydb_host
        self.alloydb_port = alloydb_port
        self.alloydb_dbname = alloydb_dbname
        self.alloydb_user = alloydb_user
        self.alloydb_password = alloydb_password
        self.debounce_interval = debounce_interval
        self.batch_size = batch_size
        self.redis_client = None
        self.alloydb_conn = None
        self.is_running = False
        
    async def connect(self) -> None:
        """
        Establish connections to Redis and AlloyDB.
        """
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully.")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        
        try:
            self.alloydb_conn = psycopg2.connect(
                host=self.alloydb_host,
                port=self.alloydb_port,
                dbname=self.alloydb_dbname,
                user=self.alloydb_user,
                password=self.alloydb_password
            )
            self.alloydb_conn.autocommit = True
            logger.info("Connected to AlloyDB successfully.")
        except psycopg2.OperationalError as e:
            logger.error(f"Failed to connect to AlloyDB: {e}")
            raise
            
    async def disconnect(self) -> None:
        """
        Close connections to Redis and AlloyDB.
        """
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis.")
        if self.alloydb_conn:
            self.alloydb_conn.close()
            logger.info("Disconnected from AlloyDB.")
            
    def compute_checksum(self, data: Dict[str, Any]) -> int:
        """
        Compute CRC32 checksum for data integrity validation.
        
        Args:
            data: Dictionary containing the data to checksum.
            
        Returns:
            CRC32 checksum value.
        """
        data_str = str(data)
        return crc32c.crc32c(data_str.encode())
        
    async def sync_worker(self) -> None:
        """
        Asynchronous worker loop to sync changes from Redis to AlloyDB.
        Reads changes from a Redis stream and batches updates to AlloyDB with conflict resolution.
        Includes monitoring for sync performance and alerting for failures.
        """
        if not self.redis_client or not self.alloydb_conn:
            raise RuntimeError("Connections to Redis or AlloyDB not established.")
            
        logger.info("Starting Redis to AlloyDB sync worker.")
        self.is_running = True
        last_id = "$"  # Start reading from the latest messages
        sync_count = 0
        error_count = 0
        start_time = asyncio.get_event_loop().time()
        
        while self.is_running:
            try:
                # Read changes from Redis stream
                changes = await self.redis_client.xread(
                    {"agent_memory": last_id},
                    count=self.batch_size,
                    block=500
                )
                
                if changes:
                    batch = []
                    for stream, messages in changes:
                        for msg_id, msg_data in messages:
                            try:
                                # Extract data from Redis message
                                record_id = msg_data.get("id", "")
                                vector = msg_data.get("vector", "")
                                data = msg_data.get("data", "{}")
                                version = int(msg_data.get("version", "0"))
                                checksum = self.compute_checksum(msg_data)
                                
                                batch.append((record_id, vector, data, version, checksum))
                                last_id = msg_id
                            except Exception as e:
                                logger.error(f"Error processing message {msg_id}: {e}")
                                error_count += 1
                                continue
                
                    if batch:
                        # Batch update to AlloyDB with conflict resolution
                        try:
                            with self.alloydb_conn.cursor() as cur:
                                execute_batch(cur, """
                                    INSERT INTO memories (id, vector, data, version, checksum)
                                    VALUES (%s, %s, %s, %s, %s)
                                    ON CONFLICT (id) DO UPDATE
                                    SET vector = EXCLUDED.vector,
                                        data = EXCLUDED.data,
                                        version = EXCLUDED.version,
                                        checksum = EXCLUDED.checksum
                                    WHERE EXCLUDED.version > memories.version
                                """, batch)
                            logger.info(f"Successfully synced {len(batch)} records to AlloyDB.")
                            sync_count += len(batch)
                        except psycopg2.Error as e:
                            logger.error(f"Error updating AlloyDB: {e}")
                            self.alloydb_conn.rollback()
                            error_count += len(batch)
                            self._trigger_alert("AlloyDB Update Failure", f"Failed to sync {len(batch)} records: {str(e)}")
                
                # Log sync metrics periodically
                current_time = asyncio.get_event_loop().time()
                if current_time - start_time >= 60:  # Every minute
                    logger.info(f"Sync Metrics: {sync_count} records synced, {error_count} errors encountered.")
                    start_time = current_time
                    sync_count = 0
                    error_count = 0
                
                # Debounce to prevent overwhelming the database
                await asyncio.sleep(self.debounce_interval)
                
            except redis.RedisError as e:
                logger.error(f"Redis error in sync worker: {e}")
                error_count += 1
                self._trigger_alert("Redis Connection Error", str(e))
                await asyncio.sleep(5)  # Wait before retrying
            except Exception as e:
                logger.error(f"Unexpected error in sync worker: {e}")
                error_count += 1
                self._trigger_alert("Unexpected Sync Error", str(e))
                await asyncio.sleep(5)  # Wait before retrying
                
    def _trigger_alert(self, alert_type: str, message: str) -> None:
        """
        Trigger an alert for sync failures or anomalies.
        Placeholder for integration with monitoring systems like Google Cloud Monitoring.
        
        Args:
            alert_type: Type of alert (e.g., 'AlloyDB Update Failure').
            message: Detailed message describing the issue.
        """
        logger.critical(f"ALERT [{alert_type}]: {message}")
        # TODO: Integrate with Google Cloud Monitoring or other alerting system
        # Example: Send alert to Cloud Monitoring or custom alerting endpoint
        # self._send_alert_to_monitoring(alert_type, message)
        pass
                
    async def start(self) -> None:
        """
        Start the sync worker loop.
        """
        await self.connect()
        await self.sync_worker()
        
    async def stop(self) -> None:
        """
        Stop the sync worker loop and disconnect.
        """
        self.is_running = False
        await self.disconnect()

if __name__ == "__main__":
    # Load configuration from environment variables or defaults
    worker = RedisAlloyDBSyncWorker(
        redis_host=os.getenv("REDIS_HOST", "localhost"),
        redis_port=int(os.getenv("REDIS_PORT", "6379")),
        alloydb_host=os.getenv("ALLOYDB_HOST", "localhost"),
        alloydb_port=int(os.getenv("ALLOYDB_PORT", "5432")),
        alloydb_dbname=os.getenv("ALLOYDB_DBNAME", "agi_baby_cherry"),
        alloydb_user=os.getenv("ALLOYDB_USER", "postgres"),
        alloydb_password=os.getenv("ALLOYDB_PASSWORD", ""),
        debounce_interval=float(os.getenv("SYNC_DEBOUNCE_INTERVAL", "0.5")),
        batch_size=int(os.getenv("SYNC_BATCH_SIZE", "100"))
    )
    
    # Run the worker
    asyncio.run(worker.start())