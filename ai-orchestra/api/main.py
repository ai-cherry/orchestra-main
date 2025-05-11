"""
Main FastAPI application for AI Orchestra.

This module provides the main FastAPI application.
"""

import logging
import os
import uuid
import json
import tempfile
import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, Depends, HTTPException, Request, status, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ai_orchestra.core.config import settings, get_settings
from ai_orchestra.core.errors import AIServiceError
from ai_orchestra.infrastructure.gcp.vertex_ai_service import VertexAIService
from ai_orchestra.infrastructure.persistence.firestore_memory import FirestoreMemoryProvider
from ai_orchestra.infrastructure.persistence.failover_memory import FailoverMemoryProvider
from ai_orchestra.infrastructure.persistence.memory_provider import MemoryProvider
from ai_orchestra.infrastructure.vector.pgvector_service import PGVectorService, DocumentChunk
from ai_orchestra.services.document.document_processor import DocumentProcessor, ChunkingStrategy, TextExtractionError
from ai_orchestra.core.services.checkpointing import StateCheckpointManager
from ai_orchestra.infrastructure.versioning.model_version_manager import ModelVersionManager
from ai_orchestra.utils.logging import configure_logging, log_event

# Configure logging
configure_logging(level=settings.log_level, json_logs=True)
logger = logging.getLogger("ai_orchestra.api.main")


# Create FastAPI app
app = FastAPI(
    title="AI Orchestra API",
    description="API for AI Orchestra",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection
def get_ai_service() -> VertexAIService:
    """
    Get the AI service.

    Returns:
        The AI service
    """
    return VertexAIService()


def get_memory_provider() -> MemoryProvider:
    """
    Get the memory provider.

    Returns:
        The memory provider
    """
    # Create primary provider (Firestore)
    primary = FirestoreMemoryProvider()

    # Create secondary provider (Backup Firestore collection)
    secondary = FirestoreMemoryProvider(collection_name="memory_backup")

    # Create failover provider
    return FailoverMemoryProvider([
        (primary, "primary"),
        (secondary, "secondary"),
    ])


def get_checkpoint_manager() -> StateCheckpointManager:
    """
    Get the checkpoint manager.

    Returns:
        The checkpoint manager
    """
    return StateCheckpointManager(get_memory_provider())


def get_model_version_manager() -> ModelVersionManager:
    """
    Get the model version manager.

    Returns:
        The model version manager
    """
    return ModelVersionManager(
        memory_provider=get_memory_provider(),
        ai_service=get_ai_service(),
    )


def get_pgvector_service() -> PGVectorService:
    """
    Get the PGVector service.

    Returns:
        The PGVector service
    """
    return PGVectorService()


def get_document_processor() -> DocumentProcessor:
    """
    Get the document processor.

    Returns:
        The document processor
    """
    return DocumentProcessor(ai_service=get_ai_service())


# Request/response models
class TextGenerationRequest(BaseModel):
    """Text generation request."""

    prompt: str
    model_id: Optional[str] = "gemini-pro"
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    top_p: float = 1.0
    stop_sequences: Optional[List[str]] = None


class TextGenerationResponse(BaseModel):
    """Text generation response."""

    text: str
    model_id: str


class EmbeddingRequest(BaseModel):
    """Embedding request."""

    texts: List[str]
    model_id: Optional[str] = "text-embedding"


class EmbeddingResponse(BaseModel):
    """Embedding response."""

    embeddings: List[List[float]]
    model_id: str


class ClassificationRequest(BaseModel):
    """Classification request."""

    text: str
    categories: List[str]
    model_id: Optional[str] = "gemini-pro"


class ClassificationResponse(BaseModel):
    """Classification response."""

    classifications: Dict[str, float]
    model_id: str


class QuestionAnsweringRequest(BaseModel):
    """Question answering request."""

    question: str
    context: str
    model_id: Optional[str] = "gemini-pro"


class QuestionAnsweringResponse(BaseModel):
    """Question answering response."""

    answer: str
    model_id: str


class SummarizationRequest(BaseModel):
    """Summarization request."""

    text: str
    max_length: Optional[int] = None
    model_id: Optional[str] = "gemini-pro"


class SummarizationResponse(BaseModel):
    """Summarization response."""

    summary: str
    model_id: str


class MemoryStoreRequest(BaseModel):
    """Memory store request."""

    key: str
    value: Any
    ttl: Optional[int] = None


class MemoryStoreResponse(BaseModel):
    """Memory store response."""

    success: bool
    key: str


class MemoryRetrieveRequest(BaseModel):
    """Memory retrieve request."""

    key: str


class MemoryRetrieveResponse(BaseModel):
    """Memory retrieve response."""

    key: str
    value: Optional[Any] = None
    exists: bool


class ErrorResponse(BaseModel):
    """Error response."""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class DocumentMetadata(BaseModel):
    """Document metadata model."""

    id: str
    title: str
    source: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = None


class ChunkMetadata(BaseModel):
    """Chunk metadata model."""

    id: str
    document_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    document_title: Optional[str] = None
    document_source: Optional[str] = None
    similarity: Optional[float] = None
    sequence_number: Optional[int] = None


class DocumentProcessRequest(BaseModel):
    """Document processing request."""

    file_path: str
    document_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    chunking_strategy: str = ChunkingStrategy.PARAGRAPH


class DocumentProcessResponse(BaseModel):
    """Document processing response."""

    document_id: str
    chunk_count: int
    document_metadata: DocumentMetadata


class DocumentSearchRequest(BaseModel):
    """Document search request."""

    query: str
    limit: int = 5
    score_threshold: float = 0.7
    document_id: Optional[str] = None


class DocumentSearchResponse(BaseModel):
    """Document search response."""

    results: List[ChunkMetadata]
    query: str


class DocumentListResponse(BaseModel):
    """Document list response."""

    documents: List[DocumentMetadata]
    total_count: int


# Exception handlers
@app.exception_handler(AIServiceError)
async def ai_service_error_handler(request: Request, exc: AIServiceError) -> JSONResponse:
    """
    Handle AI service errors.

    Args:
        request: The request
        exc: The exception

    Returns:
        JSON response with error details
    """
    log_event(logger, "error", "handled", {
        "code": exc.code,
        "message": exc.message,
        "path": request.url.path,
    })

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            code=exc.code,
            message=exc.message,
            details=exc.details,
        ).dict(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle general exceptions.

    Args:
        request: The request
        exc: The exception

    Returns:
        JSON response with error details
    """
    log_event(logger, "error", "unhandled", {
        "type": type(exc).__name__,
        "message": str(exc),
        "path": request.url.path,
    })

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            code="INTERNAL_ERROR",
            message="An internal error occurred",
            details={"error_type": type(exc).__name__},
        ).dict(),
    )


# Routes
@app.get("/")
async def root():
    """
    Root endpoint.

    Returns:
        Basic API information
    """
    return {
        "name": "AI Orchestra API",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy"}


@app.post("/generate-text", response_model=TextGenerationResponse)
async def generate_text(
    request: TextGenerationRequest,
    ai_service: VertexAIService = Depends(get_ai_service),
):
    """
    Generate text from a prompt.

    Args:
        request: The text generation request
        ai_service: The AI service

    Returns:
        The generated text
    """
    text = await ai_service.generate_text(
        prompt=request.prompt,
        model_id=request.model_id,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        top_p=request.top_p,
        stop_sequences=request.stop_sequences,
    )

    return TextGenerationResponse(
        text=text,
        model_id=request.model_id,
    )


@app.post("/generate-embeddings", response_model=EmbeddingResponse)
async def generate_embeddings(
    request: EmbeddingRequest,
    ai_service: VertexAIService = Depends(get_ai_service),
):
    """
    Generate embeddings for a list of texts.

    Args:
        request: The embedding request
        ai_service: The AI service

    Returns:
        The generated embeddings
    """
    embeddings = await ai_service.generate_embeddings(
        texts=request.texts,
        model_id=request.model_id,
    )

    return EmbeddingResponse(
        embeddings=embeddings,
        model_id=request.model_id,
    )


@app.post("/classify-text", response_model=ClassificationResponse)
async def classify_text(
    request: ClassificationRequest,
    ai_service: VertexAIService = Depends(get_ai_service),
):
    """
    Classify text into categories.

    Args:
        request: The classification request
        ai_service: The AI service

    Returns:
        The classification results
    """
    classifications = await ai_service.classify_text(
        text=request.text,
        categories=request.categories,
        model_id=request.model_id,
    )

    return ClassificationResponse(
        classifications=classifications,
        model_id=request.model_id,
    )


@app.post("/answer-question", response_model=QuestionAnsweringResponse)
async def answer_question(
    request: QuestionAnsweringRequest,
    ai_service: VertexAIService = Depends(get_ai_service),
):
    """
    Answer a question based on context.

    Args:
        request: The question answering request
        ai_service: The AI service

    Returns:
        The answer to the question
    """
    answer = await ai_service.answer_question(
        question=request.question,
        context=request.context,
        model_id=request.model_id,
    )

    return QuestionAnsweringResponse(
        answer=answer,
        model_id=request.model_id,
    )


@app.post("/summarize-text", response_model=SummarizationResponse)
async def summarize_text(
    request: SummarizationRequest,
    ai_service: VertexAIService = Depends(get_ai_service),
):
    """
    Summarize text.

    Args:
        request: The summarization request
        ai_service: The AI service

    Returns:
        The summarized text
    """
    summary = await ai_service.summarize_text(
        text=request.text,
        max_length=request.max_length,
        model_id=request.model_id,
    )

    return SummarizationResponse(
        summary=summary,
        model_id=request.model_id,
    )


@app.get("/models")
async def get_models(
    ai_service: VertexAIService = Depends(get_ai_service),
):
    """
    Get available models.

    Args:
        ai_service: The AI service

    Returns:
        List of available models
    """
    models = await ai_service.get_available_models()
    return {"models": models}


@app.post("/memory/store", response_model=MemoryStoreResponse)
async def store_memory(
    request: MemoryStoreRequest,
    memory_provider: FirestoreMemoryProvider = Depends(get_memory_provider),
):
    """
    Store a value in memory.

    Args:
        request: The memory store request
        memory_provider: The memory provider

    Returns:
        The result of the store operation
    """
    success = await memory_provider.store(
        key=request.key,
        value=request.value,
        ttl=request.ttl,
    )

    return MemoryStoreResponse(
        success=success,
        key=request.key,
    )


@app.post("/memory/retrieve", response_model=MemoryRetrieveResponse)
async def retrieve_memory(
    request: MemoryRetrieveRequest,
    memory_provider: FirestoreMemoryProvider = Depends(get_memory_provider),
):
    """
    Retrieve a value from memory.

    Args:
        request: The memory retrieve request
        memory_provider: The memory provider

    Returns:
        The retrieved value
    """
    value = await memory_provider.retrieve(key=request.key)

    return MemoryRetrieveResponse(
        key=request.key,
        value=value,
        exists=value is not None,
    )


@app.delete("/memory/{key}")
async def delete_memory(
    key: str,
    memory_provider: FirestoreMemoryProvider = Depends(get_memory_provider),
):
    """
    Delete a value from memory.

    Args:
        key: The key to delete
        memory_provider: The memory provider

    Returns:
        The result of the delete operation
    """
    success = await memory_provider.delete(key=key)

    return {"success": success, "key": key}


@app.get("/memory/keys")
async def list_memory_keys(
    pattern: str = "*",
    memory_provider: MemoryProvider = Depends(get_memory_provider),
):
    """
    List memory keys matching a pattern.

    Args:
        pattern: The pattern to match keys against
        memory_provider: The memory provider

    Returns:
        List of matching keys
    """
    keys = await memory_provider.list_keys(pattern=pattern)

    return {"keys": keys, "pattern": pattern}


# Checkpointing endpoints
class CheckpointCreateRequest(BaseModel):
    """Checkpoint create request."""

    agent_id: str
    state: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class CheckpointResponse(BaseModel):
    """Checkpoint response."""

    checkpoint_id: str
    agent_id: str


class CheckpointRestoreRequest(BaseModel):
    """Checkpoint restore request."""

    agent_id: str
    checkpoint_id: Optional[str] = None


class CheckpointRestoreResponse(BaseModel):
    """Checkpoint restore response."""

    agent_id: str
    checkpoint_id: Optional[str]
    state: Optional[Dict[str, Any]]
    found: bool


@app.post("/checkpoints/create", response_model=CheckpointResponse)
async def create_checkpoint(
    request: CheckpointCreateRequest,
    checkpoint_manager: StateCheckpointManager = Depends(get_checkpoint_manager),
):
    """
    Create a checkpoint of agent state.

    Args:
        request: The checkpoint create request
        checkpoint_manager: The checkpoint manager

    Returns:
        The created checkpoint information
    """
    checkpoint_id = await checkpoint_manager.create_checkpoint(
        agent_id=request.agent_id,
        state=request.state,
        metadata=request.metadata,
    )

    return CheckpointResponse(
        checkpoint_id=checkpoint_id,
        agent_id=request.agent_id,
    )


@app.post("/checkpoints/restore", response_model=CheckpointRestoreResponse)
async def restore_checkpoint(
    request: CheckpointRestoreRequest,
    checkpoint_manager: StateCheckpointManager = Depends(get_checkpoint_manager),
):
    """
    Restore agent state from checkpoint.

    Args:
        request: The checkpoint restore request
        checkpoint_manager: The checkpoint manager

    Returns:
        The restored state
    """
    state = await checkpoint_manager.restore_checkpoint(
        agent_id=request.agent_id,
        checkpoint_id=request.checkpoint_id,
    )

    return CheckpointRestoreResponse(
        agent_id=request.agent_id,
        checkpoint_id=request.checkpoint_id,
        state=state,
        found=state is not None,
    )


@app.get("/checkpoints/{agent_id}")
async def list_checkpoints(
    agent_id: str,
    checkpoint_manager: StateCheckpointManager = Depends(get_checkpoint_manager),
):
    """
    List checkpoints for an agent.

    Args:
        agent_id: The agent ID
        checkpoint_manager: The checkpoint manager

    Returns:
        List of checkpoint information
    """
    checkpoints = await checkpoint_manager.list_checkpoints(agent_id)

    return {"agent_id": agent_id, "checkpoints": checkpoints}


@app.delete("/checkpoints/{agent_id}/{checkpoint_id}")
async def delete_checkpoint(
    agent_id: str,
    checkpoint_id: str,
    checkpoint_manager: StateCheckpointManager = Depends(get_checkpoint_manager),
):
    """
    Delete a checkpoint.

    Args:
        agent_id: The agent ID
        checkpoint_id: The checkpoint ID
        checkpoint_manager: The checkpoint manager

    Returns:
        The result of the delete operation
    """
    success = await checkpoint_manager.delete_checkpoint(
        agent_id=agent_id,
        checkpoint_id=checkpoint_id,
    )

    return {"success": success, "agent_id": agent_id, "checkpoint_id": checkpoint_id}


# Model version management endpoints
class ModelVersionRegisterRequest(BaseModel):
    """Model version register request."""

    model_id: str
    version: str
    endpoint: str
    capabilities: List[str]


class ModelVersionResponse(BaseModel):
    """Model version response."""

    model_id: str
    version: str
    endpoint: str
    capabilities: List[str]
    created_at: float


class DeploymentStrategyRequest(BaseModel):
    """Deployment strategy request."""

    model_id: str
    version: str
    traffic_percentage: int


class BlueGreenDeploymentRequest(BaseModel):
    """Blue/green deployment request."""

    model_id: str
    blue_version: str
    green_version: str
    green_traffic_percentage: int = 0


@app.post("/models/versions/register", response_model=ModelVersionResponse)
async def register_model_version(
    request: ModelVersionRegisterRequest,
    model_version_manager: ModelVersionManager = Depends(get_model_version_manager),
):
    """
    Register a new model version.

    Args:
        request: The model version register request
        model_version_manager: The model version manager

    Returns:
        The registered model version
    """
    model_version = await model_version_manager.register_model_version(
        model_id=request.model_id,
        version=request.version,
        endpoint=request.endpoint,
        capabilities=request.capabilities,
    )

    return ModelVersionResponse(
        model_id=model_version.model_id,
        version=model_version.version,
        endpoint=model_version.endpoint,
        capabilities=model_version.capabilities,
        created_at=model_version.created_at,
    )


@app.get("/models/{model_id}/versions")
async def list_model_versions(
    model_id: str,
    model_version_manager: ModelVersionManager = Depends(get_model_version_manager),
):
    """
    List versions for a model.

    Args:
        model_id: The model ID
        model_version_manager: The model version manager

    Returns:
        List of model versions
    """
    versions = await model_version_manager.list_model_versions(model_id)

    return {
        "model_id": model_id,
        "versions": [
            {
                "model_id": v.model_id,
                "version": v.version,
                "endpoint": v.endpoint,
                "capabilities": v.capabilities,
                "created_at": v.created_at,
            }
            for v in versions
        ],
    }


@app.post("/models/deployments/blue-green")
async def create_blue_green_deployment(
    request: BlueGreenDeploymentRequest,
    model_version_manager: ModelVersionManager = Depends(get_model_version_manager),
):
    """
    Create a blue/green deployment.

    Args:
        request: The blue/green deployment request
        model_version_manager: The model version manager

    Returns:
        The result of the deployment operation
    """
    success = await model_version_manager.create_blue_green_deployment(
        model_id=request.model_id,
        blue_version=request.blue_version,
        green_version=request.green_version,
        green_traffic_percentage=request.green_traffic_percentage,
    )

    return {"success": success}


@app.post("/models/{model_id}/traffic-shift")
async def shift_traffic(
    model_id: str,
    green_traffic_percentage: int,
    model_version_manager: ModelVersionManager = Depends(get_model_version_manager),
):
    """
    Shift traffic between blue and green versions.

    Args:
        model_id: The model ID
        green_traffic_percentage: Percentage of traffic to route to the green version
        model_version_manager: The model version manager

    Returns:
        The result of the traffic shift operation
    """
    success = await model_version_manager.shift_traffic(
        model_id=model_id,
        green_traffic_percentage=green_traffic_percentage,
    )

    return {"success": success}


@app.post("/models/{model_id}/promote-green")
async def promote_green_to_blue(
    model_id: str,
    model_version_manager: ModelVersionManager = Depends(get_model_version_manager),
):
    """
    Promote the green version to blue (make it the only version).

    Args:
        model_id: The model ID
        model_version_manager: The model version manager

    Returns:
        The result of the promotion operation
    """
    success = await model_version_manager.promote_green_to_blue(model_id)

    return {"success": success}


@app.post("/models/{model_id}/rollback")
async def rollback_to_blue(
    model_id: str,
    model_version_manager: ModelVersionManager = Depends(get_model_version_manager),
):
    """
    Rollback to the blue version (make it the only version).

    Args:
        model_id: The model ID
        model_version_manager: The model version manager

    Returns:
        The result of the rollback operation
    """
    success = await model_version_manager.rollback_to_blue(model_id)

    return {"success": success}


# RAG API Endpoints
@app.post("/documents/process", response_model=DocumentProcessResponse)
async def process_document(
    request: DocumentProcessRequest,
    document_processor: DocumentProcessor = Depends(get_document_processor),
    pgvector_service: PGVectorService = Depends(get_pgvector_service),
    ai_service: VertexAIService = Depends(get_ai_service),
):
    """
    Process a document and store it for retrieval.

    Args:
        request: The document processing request
        document_processor: The document processor
        pgvector_service: The PGVector service
        ai_service: The AI service

    Returns:
        The result of the document processing operation
    """
    try:
        # Process the document
        document_id, chunks, document_metadata = await document_processor.process_file(
            file_path=request.file_path,
            document_id=request.document_id,
            metadata=request.metadata,
            chunking_strategy=request.chunking_strategy
        )

        # Store document metadata
        await pgvector_service.store_document(
            document_id=document_id,
            title=document_metadata["title"],
            source=document_metadata["source"],
            metadata=document_metadata.get("metadata", {})
        )

        # Prepare chunks for storage
        document_chunks = []
        for chunk in chunks:
            document_chunks.append(DocumentChunk(
                chunk_id=chunk["id"],
                document_id=document_id,
                content=chunk["content"],
                metadata=chunk.get("metadata", {}),
                embedding=None  # We'll get embeddings from the AI service
            ))

        # Get embeddings for chunks
        for chunk in document_chunks:
            embedding = await ai_service.get_embedding(chunk.content)
            chunk.embedding = embedding

        # Store chunks
        await pgvector_service.store_chunks(document_chunks)

        # Prepare response
        return DocumentProcessResponse(
            document_id=document_id,
            chunk_count=len(chunks),
            document_metadata=DocumentMetadata(
                id=document_id,
                title=document_metadata["title"],
                source=document_metadata["source"],
                created_at=datetime.datetime.now().isoformat(),
                metadata=document_metadata.get("metadata", {})
            )
        )

    except TextExtractionError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract text from document: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


@app.post("/documents/upload", response_model=DocumentProcessResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_id: Optional[str] = Form(None),
    chunking_strategy: str = Form(ChunkingStrategy.PARAGRAPH),
    metadata_json: Optional[str] = Form(None),
    document_processor: DocumentProcessor = Depends(get_document_processor),
    pgvector_service: PGVectorService = Depends(get_pgvector_service),
    ai_service: VertexAIService = Depends(get_ai_service),
):
    """
    Upload and process a document.

    Args:
        file: The uploaded file
        document_id: Optional document ID
        chunking_strategy: Chunking strategy to use
        metadata_json: Optional metadata as JSON string
        document_processor: The document processor
        pgvector_service: The PGVector service
        ai_service: The AI service

    Returns:
        The result of the document processing operation
    """
    try:
        # Parse metadata if provided
        metadata = json.loads(metadata_json) if metadata_json else {}

        # Create a temporary file to store the uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            # Write uploaded file content to the temporary file
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Process the document using the temporary file
            document_id, chunks, document_metadata = await document_processor.process_file(
                file_path=temp_file_path,
                document_id=document_id,
                metadata=metadata,
                chunking_strategy=chunking_strategy
            )

            # Store document metadata
            await pgvector_service.store_document(
                document_id=document_id,
                title=document_metadata["title"],
                source=file.filename,  # Use original filename as source
                metadata=document_metadata.get("metadata", {})
            )

            # Prepare chunks for storage
            document_chunks = []
            for chunk in chunks:
                document_chunks.append(DocumentChunk(
                    chunk_id=chunk["id"],
                    document_id=document_id,
                    content=chunk["content"],
                    metadata=chunk.get("metadata", {}),
                    embedding=None  # We'll get embeddings from the AI service
                ))

            # Get embeddings for chunks
            for chunk in document_chunks:
                embedding = await ai_service.get_embedding(chunk.content)
                chunk.embedding = embedding

            # Store chunks
            await pgvector_service.store_chunks(document_chunks)

            # Prepare response
            return DocumentProcessResponse(
                document_id=document_id,
                chunk_count=len(chunks),
                document_metadata=DocumentMetadata(
                    id=document_id,
                    title=document_metadata["title"],
                    source=file.filename,
                    created_at=datetime.datetime.now().isoformat(),
                    metadata=document_metadata.get("metadata", {})
                )
            )

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except TextExtractionError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract text from document: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid metadata JSON format"
        )
    except Exception as e:
        logger.error(f"Error processing uploaded document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing uploaded document: {str(e)}"
        )
