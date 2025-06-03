"""
"""
    """
    """
        """
        """
        """
        """
            raise ValueError(f"No processor registered for source type: {source_type}")
        processor = self.processors[source_type]
        try:

            pass
            total = await processor.ingest(
                source,
                enrich_fn=self.enrichment_fn,
                validate_fn=self.validation_fn,
                progress_cb=self.progress_cb,
                **kwargs,
            )
            return total
        except Exception:

            pass
            if self.error_handler:
                self.error_handler(e, {"source_type": source_type, "source": source})
            else:
                raise

    def register_processor(self, source_type: str, processor: BaseProcessor):
        """
        """