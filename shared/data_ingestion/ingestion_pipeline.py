"""
ingestion_pipeline.py
Intelligent orchestration layer for Orchestra AI data ingestion.

- Coordinates processors, connectors, enrichment, validation, and storage.
- Supports conditional routing, data enrichment, real-time monitoring, and error handling.
- Enables background task management, progress tracking, and audit logging.

Author: Orchestra AI Platform
"""

from typing import Any, Callable, Dict, Optional

from .base_processor import BaseProcessor, StorageAdapter

class IngestionPipeline:
    """
    Orchestrates data ingestion from multiple sources and formats.
    Supports conditional routing, enrichment, validation, and monitoring.
    """

    def __init__(
        self,
        processors: Dict[str, BaseProcessor],
        storage_adapter: StorageAdapter,
        enrichment_fn: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        validation_fn: Optional[Callable[[Dict[str, Any]], bool]] = None,
        error_handler: Optional[Callable[[Exception, Dict[str, Any]], None]] = None,
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ):
        """
        Args:
            processors: Mapping of source type to processor instance.
            storage_adapter: Unified storage backend.
            enrichment_fn: Optional data enrichment function.
            validation_fn: Optional validation function.
            error_handler: Optional error handler for failed records.
            progress_cb: Optional progress callback.
        """
        self.processors = processors
        self.storage = storage_adapter
        self.enrichment_fn = enrichment_fn
        self.validation_fn = validation_fn
        self.error_handler = error_handler
        self.progress_cb = progress_cb

    async def ingest(self, source_type: str, source: Any, **kwargs) -> int:
        """
        Ingests data from the specified source using the appropriate processor.

        Args:
            source_type: Key for the processor (e.g., 'csv', 'jsonl', 'rest').
            source: Data source (file, stream, API, etc.).
            kwargs: Additional processor-specific arguments.

        Returns:
            Total number of records ingested.
        """
        if source_type not in self.processors:
            raise ValueError(f"No processor registered for source type: {source_type}")
        processor = self.processors[source_type]
        try:
            total = await processor.ingest(
                source,
                enrich_fn=self.enrichment_fn,
                validate_fn=self.validation_fn,
                progress_cb=self.progress_cb,
                **kwargs,
            )
            return total
        except Exception as e:
            if self.error_handler:
                self.error_handler(e, {"source_type": source_type, "source": source})
            else:
                raise

    def register_processor(self, source_type: str, processor: BaseProcessor):
        """
        Registers a new processor for a given source type.
        """
        self.processors[source_type] = processor

    def set_enrichment_fn(self, fn: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self.enrichment_fn = fn

    def set_validation_fn(self, fn: Callable[[Dict[str, Any]], bool]):
        self.validation_fn = fn

    def set_error_handler(self, fn: Callable[[Exception, Dict[str, Any]], None]):
        self.error_handler = fn

    def set_progress_cb(self, fn: Callable[[int, int], None]):
        self.progress_cb = fn
