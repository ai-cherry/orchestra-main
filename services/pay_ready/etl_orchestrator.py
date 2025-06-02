"""
Pay Ready ETL Orchestrator
=========================

Orchestrates ETL operations for the Pay Ready domain, managing data ingestion
from Gong, Slack, HubSpot, and Salesforce through Airbyte Cloud.
"""

import asyncio
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from enum import Enum
import json

import aiohttp
from prefect import task, flow
from prefect.task_runners import ConcurrentTaskRunner

from shared.database.unified_postgresql_enhanced import get_unified_postgresql_enhanced
from services.weaviate_service import WeaviateService, WeaviateConfig
from .entity_resolver import PayReadyEntityResolver
from .memory_manager import PayReadyMemoryManager

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Supported data source types"""

    GONG = "gong"
    SLACK = "slack"
    HUBSPOT = "hubspot"
    SALESFORCE = "salesforce"


class SyncStatus(Enum):
    """Sync job status"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class PayReadyETLOrchestrator:
    """
    Orchestrates ETL operations for Pay Ready domain.

    This class manages:
    - Airbyte sync triggering and monitoring
    - Data processing and transformation
    - Entity resolution
    - Vector storage in Weaviate
    - Checkpoint management
    """

    def __init__(self):
        self.domain = "pay_ready"
        self.postgres = None
        self.weaviate = None
        self.airbyte_client = None
        self.entity_resolver = None
        self.memory_manager = None
        self._initialized = False

    async def initialize(self):
        """Initialize all required connections and services"""
        if self._initialized:
            return

        logger.info("Initializing Pay Ready ETL Orchestrator")

        # Initialize database connection
        self.postgres = await get_unified_postgresql_enhanced()

        # Initialize Weaviate
        weaviate_config = WeaviateConfig(
            host=os.getenv("WEAVIATE_HOST", "localhost"),
            port=int(os.getenv("WEAVIATE_PORT", "8080")),
            api_key=os.getenv("WEAVIATE_API_KEY"),
        )
        self.weaviate = WeaviateService(weaviate_config)

        # Initialize Airbyte client
        self.airbyte_client = await self._init_airbyte_client()

        # Initialize entity resolver
        self.entity_resolver = PayReadyEntityResolver(self.postgres)

        # Initialize memory manager
        self.memory_manager = PayReadyMemoryManager(self.postgres, self.weaviate)
        await self.memory_manager.initialize()

        self._initialized = True
        logger.info("Pay Ready ETL Orchestrator initialized successfully")

    async def _init_airbyte_client(self) -> "AirbyteClient":
        """Initialize Airbyte Cloud API client"""
        return AirbyteClient(
            client_id=os.getenv("AIRBYTE_CLIENT_ID"),
            client_secret=os.getenv("AIRBYTE_CLIENT_SECRET"),
            api_url=os.getenv("AIRBYTE_API_URL", "https://api.airbyte.com/v1"),
        )

    @task(retries=3, retry_delay_seconds=60)
    async def trigger_airbyte_sync(self, source_type: SourceType) -> str:
        """
        Trigger Airbyte sync for a specific source.

        Args:
            source_type: The type of source to sync

        Returns:
            Job ID for the sync operation
        """
        logger.info(f"Triggering Airbyte sync for {source_type.value}")

        # Get connection ID from database
        connection_id = await self._get_connection_id(source_type)
        if not connection_id:
            raise ValueError(f"No connection configured for {source_type.value}")

        # Trigger sync via Airbyte API
        job_id = await self.airbyte_client.trigger_sync(connection_id)

        # Store sync state
        await self._update_sync_state(source_type, job_id, SyncStatus.RUNNING)

        logger.info(f"Sync triggered for {source_type.value} with job ID: {job_id}")
        return job_id

    async def _get_connection_id(self, source_type: SourceType) -> Optional[str]:
        """Get Airbyte connection ID for a source type"""
        result = await self.postgres.fetchrow(
            """
            SELECT connection_id 
            FROM pay_ready.data_sources 
            WHERE source_type = $1
        """,
            source_type.value,
        )

        return result["connection_id"] if result else None

    async def _update_sync_state(
        self, source_type: SourceType, job_id: str, status: SyncStatus, checkpoint_data: Optional[Dict] = None
    ):
        """Update sync state in database"""
        checkpoint = checkpoint_data or {}
        checkpoint.update({"job_id": job_id, "status": status.value, "updated_at": datetime.utcnow().isoformat()})

        await self.postgres.execute_raw(
            """
            INSERT INTO pay_ready.sync_state (source_type, stream_name, checkpoint_data)
            VALUES ($1, $2, $3)
            ON CONFLICT (source_type, stream_name) 
            DO UPDATE SET 
                checkpoint_data = $3,
                updated_at = CURRENT_TIMESTAMP
        """,
            source_type.value,
            f"{source_type.value}_sync",
            json.dumps(checkpoint),
        )

    @task(retries=5, retry_delay_seconds=30)
    async def wait_for_sync(self, job_id: str, timeout_minutes: int = 60) -> bool:
        """
        Wait for Airbyte sync to complete.

        Args:
            job_id: The sync job ID
            timeout_minutes: Maximum time to wait

        Returns:
            True if sync succeeded, False otherwise
        """
        start_time = datetime.utcnow()
        timeout = timedelta(minutes=timeout_minutes)

        while datetime.utcnow() - start_time < timeout:
            status = await self.airbyte_client.get_job_status(job_id)

            if status == "succeeded":
                logger.info(f"Sync job {job_id} completed successfully")
                return True
            elif status == "failed":
                logger.error(f"Sync job {job_id} failed")
                return False
            elif status == "cancelled":
                logger.warning(f"Sync job {job_id} was cancelled")
                return False

            # Still running, wait before checking again
            await asyncio.sleep(10)

        logger.error(f"Sync job {job_id} timed out after {timeout_minutes} minutes")
        return False

    @task
    async def process_new_data(self, source_type: SourceType, batch_size: int = 100) -> int:
        """
        Process new data from a source.

        Args:
            source_type: The source to process data from
            batch_size: Number of records to process in each batch

        Returns:
            Number of records processed
        """
        logger.info(f"Processing new data from {source_type.value}")

        # Get last processed checkpoint
        last_processed = await self._get_last_processed(source_type)

        # Fetch new records
        new_records = await self._fetch_new_records(source_type, last_processed, batch_size)

        if not new_records:
            logger.info(f"No new records found for {source_type.value}")
            return 0

        # Process based on source type
        processor_map = {
            SourceType.SLACK: self._process_slack_messages,
            SourceType.GONG: self._process_gong_calls,
            SourceType.HUBSPOT: self._process_hubspot_notes,
            SourceType.SALESFORCE: self._process_salesforce_records,
        }

        processor = processor_map.get(source_type)
        if processor:
            await processor(new_records)
        else:
            raise ValueError(f"No processor defined for {source_type.value}")

        # Update checkpoint
        await self._update_checkpoint(source_type, new_records[-1])

        logger.info(f"Processed {len(new_records)} records from {source_type.value}")
        return len(new_records)

    async def _get_last_processed(self, source_type: SourceType) -> Optional[Dict]:
        """Get last processed checkpoint for a source"""
        result = await self.postgres.fetchrow(
            """
            SELECT last_processed_timestamp, last_processed_id, checkpoint_data
            FROM pay_ready.sync_state
            WHERE source_type = $1 AND stream_name = $2
        """,
            source_type.value,
            f"{source_type.value}_processing",
        )

        if result:
            return {
                "timestamp": result["last_processed_timestamp"],
                "id": result["last_processed_id"],
                "data": result["checkpoint_data"],
            }
        return None

    async def _fetch_new_records(
        self, source_type: SourceType, last_processed: Optional[Dict], batch_size: int
    ) -> List[Dict]:
        """Fetch new records from PostgreSQL staging tables"""
        # Build query based on source type
        table_map = {
            SourceType.SLACK: "airbyte_slack_messages",
            SourceType.GONG: "airbyte_gong_calls",
            SourceType.HUBSPOT: "airbyte_hubspot_engagements",
            SourceType.SALESFORCE: "airbyte_salesforce_tasks",
        }

        table = table_map.get(source_type)
        if not table:
            raise ValueError(f"No table mapping for {source_type.value}")

        # Build WHERE clause based on checkpoint
        where_clause = ""
        params = [batch_size]

        if last_processed:
            if last_processed.get("timestamp"):
                where_clause = "WHERE created_at > $2"
                params.append(last_processed["timestamp"])
            elif last_processed.get("id"):
                where_clause = "WHERE id > $2"
                params.append(last_processed["id"])

        query = f"""
            SELECT * FROM {table}
            {where_clause}
            ORDER BY created_at ASC
            LIMIT $1
        """

        rows = await self.postgres.fetch_raw(query, *params)
        return [dict(row) for row in rows]

    async def _process_slack_messages(self, messages: List[Dict]):
        """Process Slack messages"""
        for msg in messages:
            # Resolve user to unified person ID
            unified_person_id = await self.entity_resolver.resolve_person(
                name=msg.get("user_name"), source_system="slack", source_id=msg.get("user_id")
            )

            # Extract company mentions
            unified_company_id = await self._extract_company_from_text(msg.get("text", ""))

            # Store in memory manager (handles caching and vectorization)
            await self.memory_manager.store_interaction(
                {
                    "id": msg["id"],
                    "type": "slack_message",
                    "text": msg.get("text", ""),
                    "channel": msg.get("channel"),
                    "user": msg.get("user"),
                    "timestamp": msg.get("ts"),
                    "thread_id": msg.get("thread_ts"),
                    "unified_person_id": unified_person_id,
                    "unified_company_id": unified_company_id,
                    "metadata": {"domain": self.domain, "source": "slack"},
                }
            )

    async def _process_gong_calls(self, calls: List[Dict]):
        """Process Gong call transcripts"""
        for call in calls:
            # Chunk transcript
            transcript = call.get("transcript", "")
            if not transcript:
                continue

            segments = self._chunk_transcript(transcript, call.get("speakers", []))

            for segment in segments:
                # Resolve speaker to unified person ID
                unified_person_id = await self.entity_resolver.resolve_person(
                    name=segment["speaker"], source_system="gong", source_id=f"{call['id']}_{segment['speaker']}"
                )

                # Resolve company
                unified_company_id = await self.entity_resolver.resolve_company(
                    name=call.get("account_name"), source_system="gong", source_id=call.get("account_id")
                )

                # Store segment
                await self.memory_manager.store_interaction(
                    {
                        "id": f"{call['id']}_{segment['index']}",
                        "type": "gong_call_segment",
                        "text": segment["text"],
                        "call_id": call["id"],
                        "speaker": segment["speaker"],
                        "start_time": segment["start_time"],
                        "call_date": call.get("date"),
                        "unified_person_id": unified_person_id,
                        "unified_company_id": unified_company_id,
                        "metadata": {
                            "domain": self.domain,
                            "source": "gong",
                            "call_title": call.get("title"),
                            "duration": call.get("duration"),
                        },
                    }
                )

    def _chunk_transcript(self, transcript: str, speakers: List[Dict], chunk_size: int = 500) -> List[Dict]:
        """
        Chunk transcript into segments.

        Args:
            transcript: Full transcript text
            speakers: List of speaker information
            chunk_size: Target size for each chunk in words

        Returns:
            List of transcript segments
        """
        segments = []

        # Simple implementation - can be enhanced with speaker detection
        words = transcript.split()
        current_chunk = []
        current_speaker = "Unknown"

        for i, word in enumerate(words):
            current_chunk.append(word)

            if len(current_chunk) >= chunk_size:
                segments.append(
                    {
                        "index": len(segments),
                        "text": " ".join(current_chunk),
                        "speaker": current_speaker,
                        "start_time": (i - len(current_chunk)) * 0.5,  # Rough estimate
                    }
                )
                current_chunk = []

        # Add remaining chunk
        if current_chunk:
            segments.append(
                {
                    "index": len(segments),
                    "text": " ".join(current_chunk),
                    "speaker": current_speaker,
                    "start_time": (len(words) - len(current_chunk)) * 0.5,
                }
            )

        return segments

    async def _process_hubspot_notes(self, notes: List[Dict]):
        """Process HubSpot notes"""
        for note in notes:
            # Resolve associated contact
            unified_person_id = None
            if note.get("contact_id"):
                unified_person_id = await self.entity_resolver.resolve_person(
                    source_system="hubspot", source_id=note["contact_id"]
                )

            # Store note
            await self.memory_manager.store_interaction(
                {
                    "id": note["id"],
                    "type": "hubspot_note",
                    "text": note.get("body", ""),
                    "hubspot_id": note["id"],
                    "associated_contact": note.get("contact_id"),
                    "timestamp": note.get("created_at"),
                    "unified_person_id": unified_person_id,
                    "metadata": {"domain": self.domain, "source": "hubspot", "note_type": note.get("type")},
                }
            )

    async def _process_salesforce_records(self, records: List[Dict]):
        """Process Salesforce records"""
        for record in records:
            # Determine record type and process accordingly
            if record.get("type") == "Task" and record.get("description"):
                # Process task descriptions
                unified_person_id = await self.entity_resolver.resolve_person(
                    source_system="salesforce", source_id=record.get("who_id")
                )

                await self.memory_manager.store_interaction(
                    {
                        "id": record["id"],
                        "type": "salesforce_note",
                        "text": record["description"],
                        "sf_id": record["id"],
                        "associated_record": record.get("what_id"),
                        "timestamp": record.get("created_date"),
                        "unified_person_id": unified_person_id,
                        "metadata": {
                            "domain": self.domain,
                            "source": "salesforce",
                            "record_type": "Task",
                            "subject": record.get("subject"),
                        },
                    }
                )

    async def _extract_company_from_text(self, text: str) -> Optional[str]:
        """Extract company mentions from text using NER or pattern matching"""
        # Simple implementation - can be enhanced with NLP
        # For now, return None and let entity resolver handle it
        return None

    async def _update_checkpoint(self, source_type: SourceType, last_record: Dict):
        """Update processing checkpoint"""
        await self.postgres.execute_raw(
            """
            INSERT INTO pay_ready.sync_state 
            (source_type, stream_name, last_processed_timestamp, last_processed_id)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (source_type, stream_name) 
            DO UPDATE SET 
                last_processed_timestamp = $3,
                last_processed_id = $4,
                updated_at = CURRENT_TIMESTAMP
        """,
            source_type.value,
            f"{source_type.value}_processing",
            last_record.get("created_at"),
            last_record.get("id"),
        )

    async def run_vector_enrichment(self):
        """Run Weaviate Transformation Agent for enrichment"""
        logger.info("Running vector enrichment with Transformation Agent")

        # This would use Weaviate's Transformation Agent
        # Implementation depends on Weaviate Cloud setup
        pass

    async def update_analytics_cache(self):
        """Update analytics and cache for quick access"""
        logger.info("Updating analytics cache")

        # Update interaction counts
        await self.postgres.execute_raw(
            """
            INSERT INTO pay_ready.analytics_cache (metric_name, metric_value, updated_at)
            SELECT 
                source_type || '_count' as metric_name,
                COUNT(*) as metric_value,
                CURRENT_TIMESTAMP as updated_at
            FROM pay_ready.interactions
            GROUP BY source_type
            ON CONFLICT (metric_name) 
            DO UPDATE SET 
                metric_value = EXCLUDED.metric_value,
                updated_at = EXCLUDED.updated_at
        """
        )

        # Cache recent interactions
        await self.memory_manager.warm_cache()


class AirbyteClient:
    """Client for Airbyte Cloud API"""

    def __init__(self, client_id: str, client_secret: str, api_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = api_url
        self.session = None
        self.token = None

    async def _ensure_session(self):
        """Ensure we have an active session with auth token"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        if not self.token:
            await self._authenticate()

    async def _authenticate(self):
        """Authenticate with Airbyte Cloud"""
        async with self.session.post(
            f"{self.api_url}/auth/token",
            json={"client_id": self.client_id, "client_secret": self.client_secret, "grant_type": "client_credentials"},
        ) as resp:
            data = await resp.json()
            self.token = data["access_token"]

    async def trigger_sync(self, connection_id: str) -> str:
        """Trigger a sync for a connection"""
        await self._ensure_session()

        headers = {"Authorization": f"Bearer {self.token}"}
        async with self.session.post(f"{self.api_url}/connections/{connection_id}/sync", headers=headers) as resp:
            data = await resp.json()
            return data["job"]["id"]

    async def get_job_status(self, job_id: str) -> str:
        """Get status of a sync job"""
        await self._ensure_session()

        headers = {"Authorization": f"Bearer {self.token}"}
        async with self.session.get(f"{self.api_url}/jobs/{job_id}", headers=headers) as resp:
            data = await resp.json()
            return data["job"]["status"]

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
