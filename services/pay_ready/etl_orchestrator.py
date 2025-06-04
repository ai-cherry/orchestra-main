# TODO: Consider adding connection pooling configuration
import nltk
import re
# It's good practice to import specific functions if they are used directly and frequently
# For NLTK, direct import of sent_tokenize might be cleaner if no other nltk parts are used in this file.
# However, the download logic uses nltk.data and nltk.downloader.
from dateutil.parser import isoparse # For robust date string parsing
import json # For json.dumps
import os
import asyncio
import aiohttp # For AirbyteClient
from enum import Enum
from typing import Any, Dict, List, Optional # Make sure Any is imported
from datetime import datetime

# Assuming these are defined elsewhere and imported if necessary
# from ..unified_data_model import UnifiedDataModel, InteractionType
from shared.db.postgresql_async import UnifiedPostgreSQLAsync # get_unified_postgresql_enhanced
from shared.llm.custom_llm import LLMConfig, CustomLLM, get_llm_factory # For entity resolver LLM
from shared.logger.logging_config import logger
from shared.config.vector_db_config import VectorDBConfig # WeaviateConfig
from services.weaviate_service import WeaviateService
from shared.config.app_config import app_config # For domain
from shared.config.llm_config import llm_config_from_env
from prefect import task # Assuming @task decorator is used as shown

# Local imports - adjust path as necessary if this file moves
from .pay_ready_entity_resolver import PayReadyEntityResolver
from .pay_ready_memory_manager import PayReadyMemoryManager


# Placeholder for get_unified_postgresql_enhanced if not directly available
async def get_unified_postgresql_enhanced():
    # This is a placeholder implementation.
    # Replace with your actual PostgreSQL connection setup.
    # logger.info("Placeholder: Initializing PostgreSQL connection")
    return UnifiedPostgreSQLAsync.get_instance() # Assuming singleton or factory method

"""
"""
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

class PayReadyETLconductor:
    """
    """
        self.domain = "pay_ready"
        self.postgres = None
        self.weaviate = None
        self.airbyte_client = None
        self.entity_resolver = None
        self.memory_manager = None
        self._initialized = False

    async def initialize(self):
        """Initialize all required connections and services"""
        logger.info("Initializing Pay Ready ETL conductor")

        # Initialize database connection
        self.postgres = await get_unified_postgresql_enhanced()

        # Initialize Weaviate
        weaviate_host = os.getenv("WEAVIATE_CLUSTER_URL", os.getenv("WEAVIATE_HOST", "http://localhost:8080"))
        logger.info(f"Initializing Weaviate connection to: {weaviate_host}")
        weaviate_config = WeaviateConfig(
            host=weaviate_host,
            port=int(os.getenv("WEAVIATE_PORT", "8080")), # Port might not be relevant for cloud URLs
            api_key=os.getenv("WEAVIATE_API_KEY"),
            # Pass OpenAI API key for Weaviate Service to use
            additional_config={"openai_api_key": os.getenv("OPENAI_API_KEY")}
        )
        self.weaviate = WeaviateService(weaviate_config)
        logger.info(f"Weaviate service initialized. OpenAI API key {'provided' if os.getenv('OPENAI_API_KEY') else 'not provided'}.")
        await self._ensure_weaviate_schemas_exist()

        # Initialize Airbyte client
        self.airbyte_client = await self._init_airbyte_client()

        # Initialize entity resolver
        self.entity_resolver = PayReadyEntityResolver(self.postgres)

        # Initialize memory manager
        self.memory_manager = PayReadyMemoryManager(self.postgres, self.weaviate)
        await self.memory_manager.initialize()

        self._initialized = True
        logger.info("Pay Ready ETL conductor initialized successfully")

    # Define company patterns as a class attribute
    _COMPANY_PATTERNS = {
        r"acme\s*corp(?:oration)?": "Acme Corporation",
        r"initech": "Initech",
        r"globex\s*corp(?:oration)?": "Globex Corporation",
        r"umbrella\s*corp(?:oration)?": "Umbrella Corporation",
        # Add more patterns here. Keep it manageable or load from config.
    }

    async def _extract_company_from_text(self, text: str) -> Optional[List[str]]:
        """Extract company mentions from text using regex patterns."""
        if not text:
            return None

        found_companies = set()
        for pattern, canonical_name in self._COMPANY_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found_companies.add(canonical_name)

        if found_companies:
            logger.debug(f"Extracted companies: {list(found_companies)} from text snippet: {text[:100]}...")
            return list(found_companies)
        return None

    def _chunk_transcript(self, transcript: str, speakers: List[Dict], chunk_size_words: int = 250) -> List[Dict]:
        """
        Chunks a transcript into segments based on sentence tokenization and word count.
        `speakers` argument is currently unused but kept for potential future speaker diarization per sentence.
        """
        if not transcript:
            return []

        try:
            nltk.data.find('tokenizers/punkt')
        except nltk.downloader.DownloadError:
            logger.info("NLTK 'punkt' resource not found. Downloading...")
            try:
                nltk.download('punkt', quiet=True)
            except Exception as e:
                logger.warning(f"Could not download nltk 'punkt': {e}. Sentence tokenization might be suboptimal.")
        except Exception as e:
             logger.warning(f"Error checking for nltk 'punkt': {e}. Sentence tokenization might be suboptimal.")

        try:
            # Ensure nltk.sent_tokenize is used, not a redefinition from import
            sentences = nltk.sent_tokenize(transcript)
        except Exception as e:
            logger.warning(f"NLTK sent_tokenize failed: {e}. Falling back to paragraph splitting for transcript chunking.")
            sentences = [p.strip() for p in transcript.split('\n\n') if p.strip()]
            if not sentences:
                 sentences = [p.strp() for p in transcript.split('\n') if p.strip()] # Corrected typo srtip->strip

        segments = []
        current_chunk_sentences = []
        current_chunk_word_count = 0
        segment_index = 0

        # For rough start_time estimation if no other data is available
        # This is very approximate and should be replaced if better timestamps are available
        # total_chars = len(transcript)
        # chars_processed = 0

        for sentence in sentences:
            sentence_word_count = len(sentence.split())

            if current_chunk_word_count + sentence_word_count > chunk_size_words and current_chunk_sentences:
                segment_text = " ".join(current_chunk_sentences)
                segments.append({
                    "index": segment_index,
                    "text": segment_text,
                    "speaker": "Unknown", # Speaker per sentence not determined here
                    # Rough time estimation - placeholder logic
                    # "start_time": (chars_processed - len(segment_text)) / total_chars * estimated_duration_if_any
                })
                segment_index += 1
                current_chunk_sentences = []
                current_chunk_word_count = 0

            current_chunk_sentences.append(sentence)
            current_chunk_word_count += sentence_word_count
            # chars_processed += len(sentence) +1 # +1 for space

        if current_chunk_sentences:
            segment_text = " ".join(current_chunk_sentences)
            segments.append({
                "index": segment_index,
                "text": segment_text,
                "speaker": "Unknown",
                # "start_time": (chars_processed - len(segment_text)) / total_chars * estimated_duration_if_any
            })

        # Add approximate start_time based on segment position if not otherwise available
        # This is very basic and assumes equal time per segment or character count.
        # A more robust solution would use actual timestamps from the source if available.
        num_segments = len(segments)
        for i, segment in enumerate(segments):
            segment["start_time"] = i * (1.0 / num_segments if num_segments > 0 else 0) # Normalized time, or use char offset

        return segments

    async def _ensure_weaviate_schemas_exist(self):
        """Define and ensure all necessary Weaviate schemas exist."""
        logger.info("Ensuring Weaviate schemas exist...")

        # Common module config for text2vec-openai focusing on 'text' property
        openai_module_config = {
            "text2vec-openai": {
                "vectorizeClassName": False, # Default, usually false
                "model": "ada", # Can be configured via env var later if needed
                "type": "text",
                # We need to tell Weaviate which properties to vectorize.
                # This is often done per-property if not all text properties are to be vectorized by default.
                # Or, if the class vectorizer is set, it might attempt to vectorize all 'text' properties.
                # For Weaviate v4, property vectorization is often implicit or defined per-property in `vectorizerConfig`.
                # The goal is that the main "text" field of each class is what gets vectorized.
            }
        }
        # Property-specific vectorization for 'text' field.
        # In Weaviate v4, this is typically handled by NOT skipping it in the property definition
        # when a class vectorizer is active.
        # If a property should NOT be vectorized, you'd mark it with "skip: true" in its moduleConfig.
        # So, by default, 'text' will be vectorized if it's of dataType 'text'.

        schemas = [
            {
                "class": "PayReadySlackMessage",
                "vectorizer": "text2vec-openai",
                "moduleConfig": openai_module_config,
                "properties": [
                    {"name": "messageId", "dataType": ["text"], "tokenization": "word"}, # Keyword for filtering
                    {"name": "text", "dataType": ["text"]}, # This will be vectorized
                    {"name": "channel", "dataType": ["text"], "tokenization": "word"},
                    {"name": "userId", "dataType": ["text"], "tokenization": "word"},
                    {"name": "ts", "dataType": ["text"]}, # Timestamp string
                    {"name": "threadTs", "dataType": ["text"], "tokenization": "word"},
                    {"name": "unifiedPersonId", "dataType": ["text"], "tokenization": "word"},
                    {"name": "unifiedCompanyId", "dataType": ["text"], "tokenization": "word"},
                    {"name": "source", "dataType": ["text"], "tokenization": "word"},
                    {"name": "domain", "dataType": ["text"], "tokenization": "word"},
                ],
            },
            {
                "class": "PayReadyGongCallSegment",
                "vectorizer": "text2vec-openai",
                "moduleConfig": openai_module_config,
                "properties": [
                    {"name": "segmentId", "dataType": ["text"], "tokenization": "word"},
                    {"name": "callId", "dataType": ["text"], "tokenization": "word"},
                    {"name": "text", "dataType": ["text"]}, # Vectorized
                    {"name": "speaker", "dataType": ["text"], "tokenization": "word"},
                    {"name": "startTime", "dataType": ["number"]},
                    {"name": "callDate", "dataType": ["date"]},
                    {"name": "unifiedPersonId", "dataType": ["text"], "tokenization": "word"},
                    {"name": "unifiedCompanyId", "dataType": ["text"], "tokenization": "word"},
                    {"name": "callTitle", "dataType": ["text"]}, # Not tokenized as keyword, can be full text
                    {"name": "source", "dataType": ["text"], "tokenization": "word"},
                    {"name": "domain", "dataType": ["text"], "tokenization": "word"},
                ],
            },
            {
                "class": "PayReadyHubSpotNote",
                "vectorizer": "text2vec-openai",
                "moduleConfig": openai_module_config,
                "properties": [
                    {"name": "noteId", "dataType": ["text"], "tokenization": "word"},
                    {"name": "text", "dataType": ["text"]}, # Vectorized
                    {"name": "hubspotObjectId", "dataType": ["text"], "tokenization": "word"},
                    {"name": "objectType", "dataType": ["text"], "tokenization": "word"},
                    {"name": "createdAt", "dataType": ["date"]},
                    {"name": "authorEmail", "dataType": ["text"], "tokenization": "word"},
                    {"name": "unifiedPersonId", "dataType": ["text"], "tokenization": "word"},
                    {"name": "unifiedCompanyId", "dataType": ["text"], "tokenization": "word"},
                    {"name": "source", "dataType": ["text"], "tokenization": "word"},
                    {"name": "domain", "dataType": ["text"], "tokenization": "word"},
                ],
            },
            {
                "class": "PayReadySalesforceNote",
                "vectorizer": "text2vec-openai",
                "moduleConfig": openai_module_config,
                "properties": [
                    {"name": "noteId", "dataType": ["text"], "tokenization": "word"},
                    {"name": "text", "dataType": ["text"]}, # Vectorized
                    {"name": "sfObjectId", "dataType": ["text"], "tokenization": "word"},
                    {"name": "relatedToId", "dataType": ["text"], "tokenization": "word"},
                    {"name": "whoId", "dataType": ["text"], "tokenization": "word"},
                    {"name": "createdAt", "dataType": ["date"]},
                    {"name": "subject", "dataType": ["text"]}, # Not tokenized as keyword
                    {"name": "recordType", "dataType": ["text"], "tokenization": "word"},
                    {"name": "unifiedPersonId", "dataType": ["text"], "tokenization": "word"},
                    {"name": "unifiedCompanyId", "dataType": ["text"], "tokenization": "word"},
                    {"name": "source", "dataType": ["text"], "tokenization": "word"},
                    {"name": "domain", "dataType": ["text"], "tokenization": "word"},
                ],
            },
        ]

        for schema_def in schemas:
            try:
                logger.info(f"Attempting to create or verify schema for class: {schema_def['class']}")
                created = await self.weaviate.create_schema(schema_def)
                if created:
                    logger.info(f"Schema for class {schema_def['class']} ensured.")
                else:
                    logger.info(f"Schema for class {schema_def['class']} already existed or failed to create (see previous logs).")
            except Exception as e:
                logger.error(f"Failed to create schema for class {schema_def['class']}: {e}", exc_info=True)
                # Decide if one failure should stop the process or not. For now, it continues.

    async def _init_airbyte_client(self) -> "AirbyteClient":
        """Initialize Airbyte Cloud API client"""
            client_id=os.getenv("AIRBYTE_CLIENT_ID"),
            client_secret=os.getenv("AIRBYTE_CLIENT_SECRET"),
            api_url=os.getenv("AIRBYTE_API_URL", "https://api.airbyte.com/v1"),
        )

    @task(retries=3, retry_delay_seconds=60)
    async def trigger_airbyte_sync(self, source_type: SourceType) -> str:
        """
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
            """
        """
        return result["connection_id"] if result else None

    async def _update_sync_state(
        self, source_type: SourceType, job_id: str, status: SyncStatus, checkpoint_data: Optional[Dict] = None
    ):
        """Update sync state in database"""
        checkpoint.update({"job_id": job_id, "status": status.value, "updated_at": datetime.utcnow().isoformat()})

        await self.postgres.execute_raw(
            """
        """
            f"{source_type.value}_sync",
            json.dumps(checkpoint),
        )

    @task(retries=5, retry_delay_seconds=30)
    async def wait_for_sync(self, job_id: str, timeout_minutes: int = 60) -> bool:
        """
        """
        start_time = datetime.utcnow()
        last_status = "unknown" # Initialize last_status
        while (datetime.utcnow() - start_time).total_seconds() < timeout_minutes * 60:
            try:
                status = await self.airbyte_client.get_job_status(job_id)
                last_status = status # Update last known status
            except Exception as e:
                logger.error(f"Error getting job status for {job_id} during wait_for_sync: {e}", exc_info=True)
                # Special status to indicate polling issue, will retry after sleep
                status = "unknown_error_polling"

            if status == "succeeded":
                elapsed_seconds = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"Sync job {job_id} completed successfully after {elapsed_seconds:.2f} seconds.")
                return True
            elif status == "failed":
                elapsed_seconds = (datetime.utcnow() - start_time).total_seconds()
                logger.error(f"Sync job {job_id} failed after {elapsed_seconds:.2f} seconds. Status: {status}")
                # TODO: Consider fetching more details:
                # job_details = await self.airbyte_client.get_job_status_details(job_id)
                # logger.error(f"Job {job_id} failure details: {job_details}")
                return False
            elif status == "cancelled":
                elapsed_seconds = (datetime.utcnow() - start_time).total_seconds()
                logger.warning(f"Sync job {job_id} was cancelled after {elapsed_seconds:.2f} seconds. Status: {status}")
                # TODO: Consider fetching more details.
                return False
            elif status == "unknown_error_polling":
                logger.warning(f"Sync job {job_id} status could not be determined due to a polling error. Will retry.")

            # Log current status and wait
            logger.info(f"Job {job_id} status is '{status}'. Waiting for 30 seconds before retrying...")
            await asyncio.sleep(30)

        elapsed_seconds_timeout = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"Sync job {job_id} timed out after {timeout_minutes} minutes ({elapsed_seconds_timeout:.2f} seconds). Last known status: {last_status}")
        return False

    @task
    async def process_new_data(self, source_type: SourceType, batch_size: int = 100) -> int:
        """
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
            """
        """
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
            # These table names MUST match what Airbyte creates in your PostgreSQL database.
            SourceType.SLACK: "airbyte_slack_messages", # Example, verify
            SourceType.GONG: "airbyte_gong_calls", # Example, verify
            SourceType.HUBSPOT: "airbyte_hubspot_engagements_notes", # Example, verify - often engagements are split by type
            SourceType.SALESFORCE: "airbyte_salesforce_tasks", # Example, verify
        }

        table = table_map.get(source_type)
        if not table:
            raise ValueError(f"No table mapping for {source_type.value}")

        # Determine checkpoint fields based on source type
        # These are critical and must match actual column names and types in Airbyte's output tables.
        timestamp_field = "created_at" # Default timestamp field
        id_field = "_airbyte_ab_id"    # Airbyte typically adds a unique ID field like this. Or use a primary key if known.
                                       # Using _airbyte_ab_id is often safer than 'id' if 'id' is not guaranteed unique/sequential.
                                       # Or, if the source has a reliable updated_at field, that's usually best.

        if source_type == SourceType.SLACK:
            timestamp_field = "ts" # Slack uses 'ts' (epoch string) as its primary sortable timestamp.
            # For Slack, 'ts' is often unique enough to be the effective ID for checkpointing messages.
            # If not, a compound key or _airbyte_ab_id would be needed.
            # Let's assume 'ts' can function as both timestamp and effectively an ID for ordering if _airbyte_ab_id is problematic to sort.
            # For this example, we'll use 'ts' as timestamp_field and assume an _airbyte_ab_id for id_field for consistency.
            # If 'ts' should be the sole checkpoint field, the logic below would simplify.

        where_clause = ""
        params = [batch_size]

        if last_processed:
            last_ts_val = last_processed.get("timestamp")
            last_id_val = last_processed.get("id")

            if last_ts_val is not None and last_id_val is not None:
                # Fetches records newer than the last processed timestamp,
                # or records with the same timestamp but a greater ID (tie-breaker).
                # This handles cases where multiple records might share the exact same primary timestamp.
                where_clause = f"WHERE ({timestamp_field} > $2 OR ({timestamp_field} = $2 AND {id_field} > $3))"
                params.extend([last_ts_val, last_id_val])
            elif last_ts_val is not None: # Fallback if only timestamp was checkpointed
                where_clause = f"WHERE {timestamp_field} > $2"
                params.append(last_ts_val)
            else: # Should not happen if checkpointing is done correctly
                logger.warning(f"Invalid checkpoint for {source_type.value}: {last_processed}. Full sync might occur.")

        order_by_clause = f"ORDER BY {timestamp_field} ASC, {id_field} ASC"

        query = f"""
            SELECT * FROM {table}
            {where_clause}
            {order_by_clause}
            LIMIT $1
        """
        # Log the query structure without actual data for security/privacy.
        # Parameters are logged separately if needed, but generally avoid logging raw data.
        logger.info(f"Fetching new records for {source_type.value} from table {table} using checkpoint fields: ts='{timestamp_field}', id='{id_field}'. Batch size: {batch_size}.")
        logger.debug(f"Query structure for {source_type.value}: SELECT * FROM {table} {where_clause} {order_by_clause} LIMIT $1")
        if last_processed:
             logger.debug(f"Last processed checkpoint values for {source_type.value}: timestamp='{last_processed.get('timestamp')}', id='{last_processed.get('id')}'")


        records = await self.postgres.fetch_all_raw(query, *params)
        logger.info(f"Fetched {len(records)} new records for {source_type.value} from {table}.")
        return records

    async def _process_slack_messages(self, messages: List[Dict]):
        """Process Slack messages."""
        for msg_idx, msg_data in enumerate(messages): # Renamed msg to msg_data to avoid conflict
            # Hypothetical field names from Airbyte: client_msg_id, text, channel_name, user_email, user_real_name, user, ts, thread_ts
            # These MUST be verified against the actual output of the Airbyte Slack connector.
            message_id = msg_data.get("client_msg_id") or msg_data.get("ts") # Use 'ts' as fallback ID

            try:
                text_content = msg_data.get("text")
                if not text_content:
                    logger.info(f"Skipping Slack message {message_id} (index {msg_idx}) due to empty text content.")
                    continue

                # Use 'channel_name' if available, otherwise fallback to 'channel' (which might be an ID)
                channel_display = msg_data.get("channel_name", msg_data.get("channel", "UnknownChannel"))
                user_id_slack = msg_data.get("user")
                timestamp_slack = msg_data.get("ts") # Keep as string, Weaviate schema uses "text" for this
                thread_ts_slack = msg_data.get("thread_ts")

                # Entity Resolution for Person
                # Assumes Airbyte provides 'user_email' and 'user_real_name'. If not, adapt resolver call.
                resolved_person_id = await self.entity_resolver.resolve_person(
                    email=msg_data.get("user_email"),
                    name=msg_data.get("user_real_name"),
                    source_system="slack",
                    source_id=user_id_slack
                )

                # Company Extraction from text
                extracted_company_names = await self._extract_company_from_text(text_content)
                resolved_company_ids = []
                if extracted_company_names:
                    for name in extracted_company_names:
                        # Using "text_extraction_slack" to denote the source system for company resolution
                        comp_id = await self.entity_resolver.resolve_company(name=name, source_system="text_extraction_slack")
                        if comp_id:
                            resolved_company_ids.append(comp_id)

                interaction_data = {
                    "type": "PayReadySlackMessage", # Matches Weaviate class name
                    "messageId": str(message_id),
                    "text": text_content,
                    "channel": channel_display,
                    "userId": user_id_slack,
                    "ts": timestamp_slack,
                    "threadTs": thread_ts_slack,
                    "unifiedPersonId": resolved_person_id,
                    "unifiedCompanyId": resolved_company_ids[0] if resolved_company_ids else None, # Take first found company
                    "source": "slack",
                    "domain": self.domain,
                }

                await self.memory_manager.store_interaction(interaction_data)

            except Exception as e:
                logger.error(f"Failed processing Slack message {message_id} (index {msg_idx}): {e}", exc_info=True)

    async def _process_gong_calls(self, calls: List[Dict]):
        """Process Gong call transcripts"""
        # Field names like 'id', 'transcript', 'speakers_timeline', 'title', 'started', 'company_id_from_gong'
        # are HYPOTHETICAL based on common Gong API structures but MUST be verified with Airbyte's output.
        for call_idx, call_data in enumerate(calls): # Renamed call to call_data
            gong_call_id = call_data.get("id")
            try:
                transcript_text = call_data.get("transcript")
                # speakers_info is used by _chunk_transcript if it can leverage it, currently it does not actively use it.
                speakers_info = call_data.get("speakers_timeline", []) # Default to empty list

                account_name_gong = call_data.get("title") # Often call title contains company name or other context
                # Or, if Airbyte syncs a specific company/account field associated with the call:
                # account_name_gong = call_data.get("associated_company_name")

                call_date_gong = call_data.get("started") # e.g., "2023-01-15T10:00:00Z"

                if not transcript_text:
                    logger.info(f"Skipping Gong call {gong_call_id} (index {call_idx}) due to empty transcript.")
                    continue

                if call_date_gong and not isinstance(call_date_gong, str):
                    try:
                        # Ensure it's parsed and reformatted to strict ISO 8601 string if not already
                        call_date_gong = isoparse(str(call_date_gong)).isoformat()
                    except ValueError:
                        logger.warning(f"Could not parse call_date '{call_date_gong}' for Gong call {gong_call_id}. Setting to None.")
                        call_date_gong = None

                segments = self._chunk_transcript(transcript_text, speakers_info, chunk_size_words=250)

                # Resolve company associated with the call
                # This might use a company ID from Gong if available, or fall back to name extraction.
                resolved_call_company_id = await self.entity_resolver.resolve_company(
                    name=account_name_gong, # Name extracted from call title or other metadata
                    source_system="gong_call_metadata",
                    source_id=call_data.get("company_id_from_gong") # Hypothetical field for a Gong company ID
                )
                # If no direct company link, try extracting from transcript title or other text fields
                if not resolved_call_company_id and account_name_gong: # Check account_name_gong as it might be the call title
                    extracted_companies = await self._extract_company_from_text(account_name_gong)
                    if extracted_companies:
                        resolved_call_company_id = await self.entity_resolver.resolve_company(
                            name=extracted_companies[0], source_system="text_extraction_gong_title"
                        )


                for segment in segments:
                    # Speaker resolution: segment["speaker"] is "Unknown" from current _chunk_transcript.
                    # If speakers_info contained actual speaker names mapped to parts of the transcript,
                    # _chunk_transcript would need to be enhanced to assign them.
                    # For now, if speaker names are in speakers_info, we might try to match them here,
                    # but that's advanced. Defaulting to "Unknown" or a generic call participant.
                    speaker_name_from_segment = segment.get("speaker", "Unknown Speaker")
                     # The source_id for speaker should ideally be a stable Gong participant ID if available
                    resolved_speaker_id = await self.entity_resolver.resolve_person(
                        name=speaker_name_from_segment,
                        source_system="gong_speaker",
                        source_id=f"{gong_call_id}_{speaker_name_from_segment}" # Creates a unique ID for this speaker in this call
                    )

                    segment_id = f"{gong_call_id}_{segment['index']}"

                    interaction_data = {
                        "type": "PayReadyGongCallSegment", # Matches Weaviate class name
                        "segmentId": segment_id,
                        "callId": gong_call_id,
                        "text": segment["text"],
                        "speaker": speaker_name_from_segment,
                        "startTime": segment.get("start_time"), # This is a normalized/rough estimate from _chunk_transcript
                        "callDate": call_date_gong, # ISO 8601 string
                        "unifiedPersonId": resolved_speaker_id,
                        "unifiedCompanyId": resolved_call_company_id,
                        "callTitle": call_data.get("title"),
                        "source": "gong",
                        "domain": self.domain,
                    }
                    await self.memory_manager.store_interaction(interaction_data)
            except Exception as e:
                logger.error(f"Failed processing Gong call {gong_call_id} (index {call_idx}): {e}", exc_info=True)

    def _chunk_transcript(self, transcript: str, speakers: List[Dict], chunk_size: int = 500) -> List[Dict]:
        """
        """
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
        """Process HubSpot notes."""
        # Field names like 'hs_object_id', 'hs_note_body', 'hs_createdate',
        # 'hubspot_owner_id', 'associations' (and its internal structure) are HYPOTHETICAL.
        # These MUST be verified against Airbyte's HubSpot connector output.
        for note_idx, note_data in enumerate(notes): # Renamed note to note_data
            note_id_hs = note_data.get("hs_object_id") # Assuming hs_object_id is the unique ID for the note itself.
            try:
                text_content = note_data.get("hs_note_body")
                if not text_content:
                    logger.info(f"Skipping HubSpot note {note_id_hs} (index {note_idx}) due to empty body.")
                    continue

                created_at_hs = note_data.get("hs_createdate") # e.g., "2023-02-20T15:00:00Z"
                if created_at_hs and not isinstance(created_at_hs, str):
                    try:
                        created_at_hs = isoparse(str(created_at_hs)).isoformat()
                    except ValueError:
                        logger.warning(f"Could not parse hs_createdate '{created_at_hs}' for HubSpot note {note_id_hs}. Setting to None.")
                        created_at_hs = None

                # Hypothetical: Airbyte might provide owner's email directly or only owner_id that needs further resolution.
                author_email_hs = note_data.get("author_email_from_owner_id") # If Airbyte pre-resolves owner email
                hubspot_owner_id = note_data.get("hubspot_owner_id")

                # Hypothetical association paths from Airbyte. This needs careful verification.
                associations = note_data.get("associations", {})
                contact_ids_raw = associations.get("contacts") # This could be a list of IDs or a more complex object.
                company_ids_raw = associations.get("companies")

                # Assuming contact_ids_raw and company_ids_raw are lists of simple dicts like [{"id": "123"}]
                contact_id_hs = None
                if isinstance(contact_ids_raw, list) and contact_ids_raw:
                    contact_id_hs = contact_ids_raw[0].get("id")
                elif isinstance(contact_ids_raw, dict) and contact_ids_raw.get("results"): # Another possible structure
                     contact_results = contact_ids_raw.get("results", [])
                     if contact_results: contact_id_hs = contact_results[0].get("id")


                company_id_hs = None
                if isinstance(company_ids_raw, list) and company_ids_raw:
                    company_id_hs = company_ids_raw[0].get("id")
                elif isinstance(company_ids_raw, dict) and company_ids_raw.get("results"):
                     company_results = company_ids_raw.get("results", [])
                     if company_results: company_id_hs = company_results[0].get("id")


                # Person Resolution: Prioritize associated contact, fallback to note author/owner.
                resolved_person_id = None
                if contact_id_hs:
                     resolved_person_id = await self.entity_resolver.resolve_person(
                        source_system="hubspot_contact", source_id=str(contact_id_hs)
                    )
                elif hubspot_owner_id:
                    resolved_person_id = await self.entity_resolver.resolve_person(
                        email=author_email_hs, # May be None
                        source_system="hubspot_owner",
                        source_id=str(hubspot_owner_id)
                    )

                # Company Resolution: Prioritize associated company, fallback to text extraction.
                resolved_company_id = None
                if company_id_hs:
                    resolved_company_id = await self.entity_resolver.resolve_company(
                        source_system="hubspot_company", source_id=str(company_id_hs)
                    )

                if not resolved_company_id: # Fallback to text extraction from note body
                    extracted_companies = await self._extract_company_from_text(text_content)
                    if extracted_companies:
                        resolved_company_id = await self.entity_resolver.resolve_company(
                            name=extracted_companies[0], source_system="text_extraction_hs_note"
                        )

                interaction_data = {
                    "type": "PayReadyHubSpotNote", # Matches Weaviate class name
                    "noteId": str(note_id_hs),
                    "text": text_content,
                    "hubspotObjectId": str(note_data.get("hs_object_id")), # ID of the note itself
                    "objectType": note_data.get("engagement_type", "NOTE"), # Type of engagement, e.g., NOTE, EMAIL
                    "createdAt": created_at_hs, # ISO 8601 string
                    "authorEmail": author_email_hs, # Resolved owner/author email if available
                    "unifiedPersonId": resolved_person_id,
                    "unifiedCompanyId": resolved_company_id,
                    "source": "hubspot",
                    "domain": self.domain,
                }
                await self.memory_manager.store_interaction(interaction_data)
            except Exception as e:
                logger.error(f"Failed processing HubSpot note {note_id_hs} (index {note_idx}): {e}", exc_info=True)

    async def _process_salesforce_records(self, records: List[Dict]):
        """Process Salesforce records (assuming Tasks for now)."""
        # Field names like 'Id', 'Description', 'CreatedDate', 'WhoId', 'WhatId', 'Subject', 'Type', 'attributes'
        # MUST be verified against Airbyte's Salesforce connector output for Task objects.
        for rec_idx, record_data in enumerate(records): # Renamed record to record_data
            task_id_sf = record_data.get("Id")
            try:
                # Determine record type, default to "Task"
                # Salesforce API often nests type information under 'attributes': record_data.get("attributes", {}).get("type")
                # Or, a top-level 'Type' field might exist from Airbyte transformations.
                record_type = record_data.get("attributes", {}).get("type", record_data.get("Type", "Task"))

                if record_type != "Task": # Process only Tasks for now, as per original logic
                    logger.debug(f"Skipping Salesforce record {task_id_sf} as it is not a Task (type: {record_type}).")
                    continue

                description = record_data.get("Description")
                if not description:
                    logger.info(f"Skipping Salesforce Task {task_id_sf} (index {rec_idx}) due to empty description.")
                    continue

                created_date_sf = record_data.get("CreatedDate")
                if created_date_sf and not isinstance(created_date_sf, str):
                     try:
                        # Attempt to parse if not already an ISO string (e.g., if it's a datetime object or different string format)
                        created_date_sf = isoparse(str(created_date_sf)).isoformat()
                     except ValueError:
                        logger.warning(f"Could not parse CreatedDate '{created_date_sf}' for SF Task {task_id_sf}. Setting to None.")
                        created_date_sf = None

                who_id_sf = record_data.get("WhoId") # Relates to a Lead or Contact
                what_id_sf = record_data.get("WhatId") # Relates to an Account, Opportunity, etc.
                subject_sf = record_data.get("Subject")

                resolved_person_id = None
                if who_id_sf:
                    # Resolver needs to handle that WhoId can be a Lead or Contact.
                    # A more specific source_system like "salesforce_lead" or "salesforce_contact" might be needed if IDs overlap.
                    resolved_person_id = await self.entity_resolver.resolve_person(
                        source_system="salesforce_who",
                        source_id=str(who_id_sf)
                    )

                resolved_company_id = None
                if what_id_sf:
                    # WhatId can refer to various objects. Assuming primarily Account for company context.
                    # Resolver needs to handle this, potentially checking type of WhatId if possible.
                    resolved_company_id = await self.entity_resolver.resolve_company(
                        source_system="salesforce_what",
                        source_id=str(what_id_sf)
                    )

                if not resolved_company_id: # Fallback to text extraction
                    text_for_company_extraction = f"{subject_sf or ''} {description}" # Ensure subject is not None
                    extracted_companies = await self._extract_company_from_text(text_for_company_extraction)
                    if extracted_companies:
                        resolved_company_id = await self.entity_resolver.resolve_company(
                            name=extracted_companies[0], source_system="text_extraction_sf_task"
                        )

                interaction_data = {
                    "type": "PayReadySalesforceNote", # Matches Weaviate class name
                    "noteId": str(task_id_sf),
                    "text": description,
                    "sfObjectId": str(task_id_sf),
                    "relatedToId": str(what_id_sf) if what_id_sf else None,
                    "whoId": str(who_id_sf) if who_id_sf else None,
                    "createdAt": created_date_sf,
                    "subject": subject_sf,
                    "recordType": record_type,
                    "unifiedPersonId": resolved_person_id,
                    "unifiedCompanyId": resolved_company_id,
                    "source": "salesforce",
                    "domain": self.domain,
                }
                await self.memory_manager.store_interaction(interaction_data)
            except Exception as e:
                logger.error(f"Failed processing Salesforce record {task_id_sf} (index {rec_idx}): {e}", exc_info=True)

    async def _update_checkpoint(self, source_type: SourceType, last_record: Dict):
        """Update processing checkpoint in the database."""
        # This method is now correctly defined as per the previous successful overwrite.
        # The search block for the diff tool needs to be precise.
        # It should find the exact start of this method as it currently exists.
        timestamp_field = "created_at"
        id_field = "_airbyte_ab_id"
        if source_type == SourceType.SLACK:
            timestamp_field = "ts"
        last_processed_timestamp = last_record.get(timestamp_field)
        last_processed_id = last_record.get(id_field)
        if last_processed_timestamp is None or last_processed_id is None:
            logger.warning(
                f"Checkpoint for {source_type.value} could not be updated. "
                f"Missing '{timestamp_field}' (value: {last_processed_timestamp}) or "
                f"'{id_field}' (value: {last_processed_id}) in last_record. "
                f"Available keys: {list(last_record.keys())}"
            )
            return
        logger.info(f"Updating checkpoint for {source_type.value} to: {timestamp_field}='{last_processed_timestamp}', {id_field}='{last_processed_id}'")
        checkpoint_metadata = {
            "notes": f"Checkpoint for {source_type.value}",
            "timestamp_field_name": timestamp_field,
            "id_field_name": id_field
        }
        # Ensure self.postgres is initialized before calling methods on it.
        if not self.postgres:
            logger.error("PostgreSQL connection not initialized. Cannot update checkpoint.")
            # Or raise an exception: raise Exception("Postgres not initialized")
            return
        await self.postgres.execute_raw(
            """
            INSERT INTO etl_checkpoints (source_system, last_processed_timestamp, last_processed_id, checkpoint_data, created_at, updated_at)
            VALUES ($1, $2, $3, $4, NOW(), NOW())
            ON CONFLICT (source_system) DO UPDATE SET
                last_processed_timestamp = EXCLUDED.last_processed_timestamp,
                last_processed_id = EXCLUDED.last_processed_id,
                checkpoint_data = EXCLUDED.checkpoint_data,
                updated_at = NOW();
            """,
            f"{source_type.value}_processing",
            str(last_processed_timestamp),
            str(last_processed_id),
            json.dumps(checkpoint_metadata) # Make sure json is imported
        )

    async def _add_property_if_not_exists(self, collection_name: str, prop_config: Any): # WeaviateProperty (type hint as Any due to late import)
        """Helper to add a property to a Weaviate collection if it doesn't exist."""
        if not self.weaviate or not self.weaviate.client:
            logger.error(f"Weaviate client not available, cannot add property {prop_config.name} to {collection_name}")
            return False

        sdk_client = self.weaviate.client
        try:
            collection = sdk_client.collections.get(collection_name)
            current_config = collection.config.get() # Get current collection configuration

            prop_exists = any(p.name == prop_config.name for p in current_config.properties)

            if not prop_exists:
                logger.info(f"Property '{prop_config.name}' does not exist in '{collection_name}'. Adding it...")
                collection.config.add_property(prop_config) # Add the new property
                logger.info(f"Property '{prop_config.name}' added to '{collection_name}'.")
                return True
            else:
                logger.info(f"Property '{prop_config.name}' already exists in '{collection_name}'. No action taken.")
                return True # Property already exists, consider it a success for this check
        except Exception as e:
            logger.error(f"Failed to check or add property '{prop_config.name}' to collection '{collection_name}': {e}", exc_info=True)
            return False

    async def run_vector_enrichment(self):
        """
        Ensures necessary properties for Weaviate-based vector enrichment (like summaries or sentiment) exist in the schema.
        Actual data population for these properties would require a separate batch processing job.
        """
        logger.info("Starting vector enrichment schema preparation...")

        if not self.weaviate or not self.weaviate.client:
            logger.error("Weaviate client not initialized. Skipping vector enrichment schema changes.")
            return {"status": "skipped", "reason": "Weaviate client not initialized."}

        try:
            from weaviate.collections.classes.properties import Property as WeaviateSchemaProperty
            from weaviate.collections.classes.config import DataType as WeaviateSchemaDataType
        except ImportError:
            logger.error("Failed to import Weaviate schema configuration classes. Ensure 'weaviate-client' v4+ is installed.")
            return {"status": "failed", "reason": "Weaviate client libraries not found."}

        gong_collection = "PayReadyGongCallSegment"
        slack_collection = "PayReadySlackMessage"

        summary_prop = WeaviateSchemaProperty(name="segmentSummary", data_type=WeaviateSchemaDataType.TEXT)
        summary_added = await self._add_property_if_not_exists(gong_collection, summary_prop)

        sentiment_prop = WeaviateSchemaProperty(name="sentiment", data_type=WeaviateSchemaDataType.TEXT)
        sentiment_added = await self._add_property_if_not_exists(slack_collection, sentiment_prop)

        logger.info(
            "Vector enrichment schema preparation completed. "
            "Actual data enrichment for 'segmentSummary' and 'sentiment' "
            "will require separate batch jobs."
        )

        return {
            "status": "success",
            "details": {
                f"{gong_collection}.segmentSummary_prepared": summary_added,
                f"{slack_collection}.sentiment_prepared": sentiment_added,
            }
        }

    async def update_analytics_cache(self):
        """Update analytics and cache for quick access"""
        logger.info("Updating analytics cache")

        # Update interaction counts
        await self.postgres.execute_raw(
            """
        """
    """Client for Airbyte Cloud API"""
        self.api_url = api_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = None
        self.token = None
        self.api_token = os.getenv("AIRBYTE_API_TOKEN")

    async def _ensure_session(self):
        """Ensure we have an active session with auth token"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        if self.api_token:
            logger.info("Using Airbyte API Token for authentication.")
            self.token = self.api_token
        elif self.client_id and self.client_secret:
            logger.info("Using OAuth 2.0 client credentials for Airbyte authentication.")
            await self._authenticate_oauth()
        else:
            raise ValueError("Airbyte API token or client ID/secret must be provided.")

    async def _authenticate_oauth(self):
        """Authenticate with Airbyte Cloud using OAuth 2.0"""
        if not self.session: # Should be created in _ensure_session
            self.session = aiohttp.ClientSession()

        token_url = f"{self.api_url}/auth/token"
        logger.info(f"Authenticating with Airbyte Cloud at {token_url}")
        async with self.session.post(
            token_url,
            json={"client_id": self.client_id, "client_secret": self.client_secret, "grant_type": "client_credentials"},
        ) as resp:
            resp.raise_for_status()  # Raise an exception for bad status codes
            data = await resp.json()
            self.token = data["access_token"]
            logger.info("Successfully authenticated with Airbyte Cloud and obtained token.")

    async def trigger_sync(self, connection_id: str) -> str:
        """Trigger a sync for a connection"""
        await self._ensure_session()
        logger.info(f"Triggering Airbyte sync for connection_id: {connection_id}")
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}

        try:
            async with self.session.post(f"{self.api_url}/connections/{connection_id}/sync", headers=headers) as resp:
                resp.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                data = await resp.json()
                logger.debug(f"Airbyte sync trigger response for connection {connection_id}: {data}")
                try:
                    return data["job"]["id"]
                except KeyError as e:
                    logger.error(f"Failed to parse job ID from Airbyte response for connection {connection_id}. Data: {data}, Error: {e}")
                    raise ValueError(f"Airbyte response did not contain job ID. Error: {e}") from e
        except aiohttp.ClientResponseError as e:
            logger.error(f"Airbyte API request failed for trigger_sync on connection {connection_id}: {e.status} {e.message} - {e.headers} - {await e.text()}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during trigger_sync for connection {connection_id}: {e}", exc_info=True)
            raise

    async def get_job_status(self, job_id: str) -> str:
        """Get status of a sync job"""
        await self._ensure_session()
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
        logger.debug(f"Polling Airbyte job status for job_id: {job_id}")

        try:
            async with self.session.get(f"{self.api_url}/jobs/{job_id}", headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()
                logger.debug(f"Airbyte job status response for job_id {job_id}: {data}")
                try:
                    return data["job"]["status"]
                except KeyError as e:
                    logger.error(f"Failed to parse job status from Airbyte response for job {job_id}. Data: {data}, Error: {e}")
                    raise ValueError(f"Airbyte response did not contain job status. Error: {e}") from e
        except aiohttp.ClientResponseError as e:
            logger.error(f"Airbyte API request failed for get_job_status on job {job_id}: {e.status} {e.message} - {e.headers} - {await e.text()}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during get_job_status for job {job_id}: {e}", exc_info=True)
            raise

    # Placeholder for a method to get more job details, if needed in future.
    # async def get_job_status_details(self, job_id: str) -> Dict:
    #     """Get full details of a sync job."""
    #     await self._ensure_session()
    #     headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
    #     logger.debug(f"Fetching Airbyte job details for job_id: {job_id}")
    #     async with self.session.get(f"{self.api_url}/jobs/{job_id}", headers=headers) as resp:
    #         resp.raise_for_status()
    #         data = await resp.json()
    #         logger.debug(f"Airbyte job details response for job_id {job_id}: {data}")
    #         return data # Or data["job"] depending on structure

    async def close(self):
        """Close the session"""