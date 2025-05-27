import os
import shutil
import uuid
import json
import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends

# Ingestion components
# from shared.data_ingestion.ingestion_pipeline import IngestionPipeline
from shared.data_ingestion.file_processors import (
    CSVProcessor,
    JSONLProcessor,
    JSONProcessor,
)
from shared.data_ingestion.base_processor import StorageAdapter, BaseProcessor

# Core services
from core.orchestrator.src.services.memory_service import (
    get_memory_service,
    MemoryService,
)
from packages.shared.src.models.base_models import MemoryItem
from core.orchestrator.src.llm.litellm_client import LiteLLMClient
from core.logging_config import get_logger

# Weaviate Adapter
from shared.memory.weaviate_adapter import WeaviateAdapter

router = APIRouter()
logger = get_logger(__name__)

# Configurable temp directory for uploads (default: /tmp/uploads/)
TEMP_DIR = os.environ.get("UPLOAD_TEMP_DIR", "/tmp/uploads/")
DEFAULT_EMBEDDING_MODEL = "text-embedding-ada-002"  # Or fetch from settings
WEAVIATE_CLASS_NAME = "ResourceChunk"
MAX_UPLOAD_SIZE_MB = 50  # Basic file size limit (single-dev project, adjust as needed)
ALLOWED_EXTENSIONS = {".csv", ".jsonl", ".json"}


def sanitize_filename(filename: str) -> str:
    """
    Return a sanitized filename to prevent path traversal.
    """
    return os.path.basename(filename)


def validate_file_extension(filename: str) -> None:
    """
    Raise HTTPException if file extension is not allowed.
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"Unsupported file type: {ext} for file '{filename}'")
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")


def validate_file_size(file_path: str) -> None:
    """
    Raise HTTPException if file size exceeds MAX_UPLOAD_SIZE_MB.
    """
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_SIZE_MB:
        logger.warning(
            f"File '{file_path}' exceeds max size ({size_mb:.2f} MB > {MAX_UPLOAD_SIZE_MB} MB)"
        )
        raise HTTPException(
            status_code=400, detail=f"File exceeds max size of {MAX_UPLOAD_SIZE_MB} MB"
        )


class MemoryServiceStorageAdapter(StorageAdapter):
    """
    Storage adapter that writes to both Firestore (via MemoryService) and Weaviate.
    Optimized for batch upserts and embedding generation.
    """

    def __init__(
        self,
        memory_service: MemoryService,
        litellm_client: LiteLLMClient,
        weaviate_adapter: WeaviateAdapter,
        filename: str,
        file_type: str,
    ):
        self.memory_service = memory_service
        self.litellm_client = litellm_client
        self.weaviate_adapter = weaviate_adapter
        self.filename = filename
        self.file_type = file_type
        logger.info(
            f"MemoryServiceStorageAdapter initialized for {filename} ({file_type}) with Weaviate support."
        )

    def exists(self, fingerprint: str) -> bool:
        logger.debug(f"Exists check for fingerprint: {fingerprint} (returning False)")
        return False

    async def upsert_batch(self, records: List[Dict[str, Any]]) -> None:
        """
        Upsert a batch of records to Firestore and Weaviate.
        Embeddings are generated concurrently for efficiency.
        """
        logger.info(
            f"Upserting batch of {len(records)} records for {self.filename} to Firestore and Weaviate."
        )
        memory_items_to_add: List[MemoryItem] = []
        weaviate_objects_to_add: List[Dict[str, Any]] = []

        # --- Embedding generation with async concurrency ---
        async def embed_record(record: Dict[str, Any], idx: int):
            try:
                content_to_embed = json.dumps(record, ensure_ascii=False)
                logger.debug(
                    f"Record {idx+1}/{len(records)}: Generating embedding for content: {content_to_embed[:100]}..."
                )
                embedding_response = await self.litellm_client.get_embedding(
                    text=content_to_embed, model=DEFAULT_EMBEDDING_MODEL
                )
                embedding = embedding_response.embedding
                logger.debug(
                    f"Record {idx+1}/{len(records)}: Embedding generated successfully."
                )

                item_id = str(uuid.uuid4())
                memory_item = MemoryItem(
                    id=item_id,
                    content=content_to_embed,
                    embedding=embedding,
                    source="file_upload",
                    metadata={
                        "original_record": record,
                        "filename": self.filename,
                        "file_type": self.file_type,
                        "record_index_in_batch": idx,
                    },
                )
                # Prepare Weaviate object
                weaviate_object = {
                    "id": memory_item.id,
                    "vector": memory_item.embedding,
                    "properties": {
                        "text_content": memory_item.content,
                        "filename": self.filename,
                        "file_type": self.file_type,
                        **{
                            k: v
                            for k, v in memory_item.metadata.items()
                            if k != "original_record"
                        },
                    },
                }
                # Add original_record fields if simple types
                if isinstance(record, dict):
                    for key, value in record.items():
                        if isinstance(value, (str, int, float, bool)):
                            weaviate_object["properties"][f"original_{key}"] = value

                return memory_item, weaviate_object, None
            except Exception as e:
                logger.error(
                    f"Error processing record {idx+1} in batch for {self.filename}: {e}",
                    exc_info=True,
                )
                return None, None, str(e)

        # Run embedding generation concurrently
        embed_tasks = [embed_record(record, i) for i, record in enumerate(records)]
        results = await asyncio.gather(*embed_tasks)

        errors = []
        for memory_item, weaviate_object, error in results:
            if memory_item and weaviate_object:
                memory_items_to_add.append(memory_item)
                weaviate_objects_to_add.append(weaviate_object)
            if error:
                errors.append(error)

        # --- Firestore upsert ---
        firestore_success = False
        if memory_items_to_add:
            try:
                logger.info(
                    f"Adding {len(memory_items_to_add)} memory items to MemoryService (Firestore) for {self.filename}."
                )
                if hasattr(self.memory_service, "add_memory_items_async"):
                    await self.memory_service.add_memory_items_async(
                        memory_items_to_add
                    )
                else:
                    for item in memory_items_to_add:
                        await self.memory_service.add_memory_item_async(item)
                logger.info(
                    f"Successfully added {len(memory_items_to_add)} items to MemoryService (Firestore) for {self.filename}."
                )
                firestore_success = True
            except Exception as e:
                logger.error(
                    f"Error adding batch to MemoryService (Firestore) for {self.filename}: {e}",
                    exc_info=True,
                )
                errors.append(f"Firestore error: {e}")

        # --- Weaviate upsert ---
        weaviate_success = False
        if weaviate_objects_to_add:
            try:
                logger.info(
                    f"Adding {len(weaviate_objects_to_add)} objects to Weaviate for {self.filename}."
                )
                await self.weaviate_adapter.batch_upsert(weaviate_objects_to_add)
                logger.info(
                    f"Successfully added {len(weaviate_objects_to_add)} objects to Weaviate for {self.filename}."
                )
                weaviate_success = True
            except Exception as e:
                logger.error(
                    f"Error adding batch to Weaviate for {self.filename}: {e}",
                    exc_info=True,
                )
                errors.append(f"Weaviate error: {e}")

        # --- Partial failure reporting ---
        if errors:
            logger.warning(f"Partial failures occurred during upsert: {errors}")
            raise HTTPException(
                status_code=207,
                detail={
                    "message": "Partial failure during upsert.",
                    "firestore_success": firestore_success,
                    "weaviate_success": weaviate_success,
                    "errors": errors,
                },
            )

    async def close(self) -> None:
        """
        Cleanup resources if needed (no-op for current adapters).
        """
        logger.info(f"MemoryServiceStorageAdapter closed for {self.filename}")
        pass


@router.post("/upload")
async def upload_file(
    uploaded_file: UploadFile = File(...),
    memory_service: MemoryService = Depends(get_memory_service),
):
    """
    Upload a file, validate, process, and ingest its data into Firestore and Weaviate.
    """
    litellm_client = LiteLLMClient()
    weaviate_adapter = WeaviateAdapter(class_name=WEAVIATE_CLASS_NAME)

    temp_file_path: Optional[str] = None
    storage_adapter: Optional[MemoryServiceStorageAdapter] = None

    try:
        await weaviate_adapter.connect()
        logger.info(f"Weaviate adapter connected for class: {WEAVIATE_CLASS_NAME}")

        if not uploaded_file.filename:
            raise HTTPException(status_code=400, detail="No filename provided.")

        # Sanitize filename and validate extension
        safe_filename = sanitize_filename(uploaded_file.filename)
        validate_file_extension(safe_filename)

        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR, exist_ok=True)

        temp_file_path = os.path.join(TEMP_DIR, safe_filename)
        logger.info(f"Saving uploaded file '{safe_filename}' to '{temp_file_path}'")

        # Save file to disk
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(uploaded_file.file, buffer)
        logger.info(f"File '{safe_filename}' saved successfully to temporary path.")

        # Validate file size
        validate_file_size(temp_file_path)

        file_ext = os.path.splitext(safe_filename)[1].lower()
        processor: Optional[BaseProcessor] = None

        # Instantiate Storage Adapter
        storage_adapter = MemoryServiceStorageAdapter(
            memory_service=memory_service,
            litellm_client=litellm_client,
            weaviate_adapter=weaviate_adapter,
            filename=safe_filename,
            file_type=file_ext,
        )

        # Select processor based on file extension
        if file_ext == ".csv":
            processor = CSVProcessor(storage_adapter=storage_adapter)
        elif file_ext == ".jsonl":
            processor = JSONLProcessor(storage_adapter=storage_adapter)
        elif file_ext == ".json":
            processor = JSONProcessor(storage_adapter=storage_adapter)
        else:
            # Should not occur due to earlier validation
            raise HTTPException(
                status_code=400, detail=f"Unsupported file type: {file_ext}"
            )

        logger.info(
            f"Starting ingestion for '{safe_filename}' with {processor.__class__.__name__}"
        )
        with open(temp_file_path, "rb") as file_object:
            await processor.ingest(source=file_object)
        logger.info(f"Successfully processed and ingested data from '{safe_filename}'")

        return {
            "message": "File processed and ingested successfully to Firestore and Weaviate",
            "filename": safe_filename,
        }

    except HTTPException as http_exc:
        logger.error(
            f"HTTPException during file upload of '{uploaded_file.filename if uploaded_file else 'unknown file'}': {http_exc.detail}",
            exc_info=True,
        )
        raise
    except Exception as e:
        logger.error(
            f"Unhandled exception during file upload of '{uploaded_file.filename if uploaded_file else 'unknown file'}': {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}"
        )
    finally:
        # Ensure file and resources are cleaned up
        if (
            hasattr(uploaded_file, "file")
            and uploaded_file.file
            and not uploaded_file.file.closed
        ):
            uploaded_file.file.close()

        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.error(
                    f"Error deleting temporary file '{temp_file_path}': {e}",
                    exc_info=True,
                )

        if storage_adapter and hasattr(storage_adapter, "close"):
            await storage_adapter.close()

        logger.debug(
            f"Upload process finished for '{uploaded_file.filename if uploaded_file else 'unknown file'}'"
        )
