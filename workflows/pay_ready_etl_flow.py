"""
"""
    name="Initialize Services",
    description="Initialize all required services for the ETL pipeline",
    retries=2,
    retry_delay_seconds=30,
)
async def initialize_services() -> Dict[str, Any]:
    """Initialize and return all required services."""
    logger.info("Initializing Pay Ready ETL services")

    conductor = PayReadyETLconductor()
    await conductor.initialize()

    return {
        "conductor": conductor,
        "entity_resolver": conductor.entity_resolver,
        "memory_manager": conductor.memory_manager,
    }

@task(
    name="Trigger Source Sync",
    description="Trigger Airbyte sync for a specific source",
    retries=3,
    retry_delay_seconds=60,
)
async def trigger_source_sync(conductor: PayReadyETLconductor, source: str) -> Dict[str, Any]:
    """Trigger sync for a specific source."""
    logger.info(f"Triggering sync for {source}")

    try:
        source_type = SourceType(source)
        job_id = await conductor.trigger_airbyte_sync(source_type)

        return {"source": source, "job_id": job_id, "status": "triggered", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Failed to trigger sync for {source}: {e}", exc_info=True) # Added exc_info for stack trace
        return {
            "source": source,
            "job_id": None,
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }

@task(
    name="Wait for Sync Completion",
    description="Wait for Airbyte sync job to complete",
    retries=5,
    retry_delay_seconds=30,
)
async def wait_for_sync_completion(
    conductor: PayReadyETLconductor, sync_info: Dict[str, Any], timeout_minutes: int = 60
) -> Dict[str, Any]:
    """Wait for a sync job to complete."""
    if sync_info["status"] == "failed":
        logger.warning(f"Skipping wait for failed sync: {sync_info['source']}")
        return sync_info

    job_id = sync_info["job_id"]
    source = sync_info["source"]

    logger.info(f"Waiting for {source} sync job {job_id}")

    success = await conductor.wait_for_sync(job_id, timeout_minutes)

    sync_info.update({"status": "completed" if success else "failed", "completed_at": datetime.utcnow().isoformat()})

    return sync_info

@task(name="Process Source Data", description="Process new data from a source", retries=2, retry_delay_seconds=60)
async def process_source_data(
    conductor: PayReadyETLconductor, source: str, batch_size: int = 100
) -> Dict[str, Any]:
    """Process new data from a source."""
    logger.info(f"Processing data from {source}")

    try:


        pass
        source_type = SourceType(source)
        records_processed = await conductor.process_new_data(source_type, batch_size)

        return {
            "source": source,
            "records_processed": records_processed,
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception:

        pass
        logger.error(f"Failed to process data from {source}: {e}")
        return {
            "source": source,
            "records_processed": 0,
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }

@task(name="Run Entity Resolution", description="Run batch entity resolution", retries=2, retry_delay_seconds=30)
async def run_entity_resolution(entity_resolver: PayReadyEntityResolver) -> Dict[str, Any]:
    """Run batch entity resolution."""
    logger.info("Running entity resolution batch")

    start_time = datetime.utcnow()

    try:


        pass
        await entity_resolver.run_resolution_batch()

        duration = (datetime.utcnow() - start_time).total_seconds()

        return {"status": "success", "duration_seconds": duration, "timestamp": datetime.utcnow().isoformat()}
    except Exception:

        pass
        logger.error(f"Entity resolution failed: {e}")
        return {"status": "failed", "error": str(e), "timestamp": datetime.utcnow().isoformat()}

@task(name="Update Analytics Cache", description="Update analytics and warm caches", retries=1, retry_delay_seconds=30)
async def update_analytics_cache(conductor: PayReadyETLconductor) -> Dict[str, Any]:
    """Update analytics cache and warm memory caches."""
    logger.info("Updating analytics cache")

    try:


        pass
        await conductor.update_analytics_cache()

        # Get memory stats
        memory_stats = await conductor.memory_manager.get_memory_stats()

        return {"status": "success", "memory_stats": memory_stats, "timestamp": datetime.utcnow().isoformat()}
    except Exception:

        pass
        logger.error(f"Failed to update analytics cache: {e}")
        return {"status": "failed", "error": str(e), "timestamp": datetime.utcnow().isoformat()}

@task(
    name="Flush Pending Vectors", description="Flush any pending vectors to Weaviate", retries=2, retry_delay_seconds=30
)
async def flush_pending_vectors(memory_manager: PayReadyMemoryManager) -> Dict[str, Any]:
    """Flush pending vectors to ensure all data is indexed."""
    logger.info("Flushing pending vectors")

    try:


        pass
        await memory_manager.flush_pending_vectors()

        return {"status": "success", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e: # Ensure 'e' is captured
        logger.error(f"Failed to flush vectors: {e}", exc_info=True)
        return {"status": "failed", "error": str(e), "timestamp": datetime.utcnow().isoformat()}

@task(
    name="Run Vector Enrichment Schema Prep",
    description="Prepare Weaviate schema for vector enrichment (add properties)",
    retries=1,
    retry_delay_seconds=30,
)
async def run_vector_enrichment_task(conductor: PayReadyETLconductor) -> Dict[str, Any]:
    """Run Weaviate schema preparation for vector enrichment."""
    logger.info("Running vector enrichment schema preparation task")
    try:
        result = await conductor.run_vector_enrichment() # This now returns a dict
        logger.info(f"Vector enrichment schema preparation completed with status: {result.get('status')}")
        return result
    except Exception as e:
        logger.error(f"Vector enrichment schema preparation failed: {e}", exc_info=True)
        return {"status": "failed", "error": str(e), "timestamp": datetime.utcnow().isoformat()}

@task(name="Generate Pipeline Report", description="Generate a summary report of the pipeline execution", retries=1)
async def generate_pipeline_report(
    sync_results: List[Dict],
    processing_results: List[Dict],
    entity_resolution_result: Dict,
    analytics_result: Dict,
    enrichment_result: Dict # Added new parameter
) -> str:
    """Generate a markdown report of the pipeline execution."""
    total_records = sum(r.get("records_processed", 0) for r in processing_results)
    successful_syncs = sum(1 for r in sync_results if r.get("status") == "completed")
    failed_syncs = sum(1 for r in sync_results if r.get("status") == "failed")

    # Build report
    report = f"""
"""
        duration = "N/A"
        if sync.get("completed_at") and sync.get("timestamp"):
            start = datetime.fromisoformat(sync["timestamp"])
            end = datetime.fromisoformat(sync["completed_at"])
            duration = f"{(end - start).total_seconds():.1f}s"

        report += f"| {sync['source']} | {sync['status']} | {sync.get('job_id', 'N/A')} | {duration} |\n"

    report += f"""
"""
            result.get("error", "None")[:50] + "..."
            if result.get("error") and len(result.get("error", "")) > 50
            else result.get("error", "None")
        )
        report += f"| {result['source']} | {result['records_processed']:,} | {result['status']} | {error} |\n"

    report += f"""
### Entity Resolution
- **Status:** {entity_resolution_result.get('status', 'N/A')}
- **Duration:** {entity_resolution_result.get('duration_seconds', 'N/A')} seconds
"""

    # Add Vector Enrichment Status
    report += f"""
### Vector Enrichment Schema Preparation
- **Status:** {enrichment_result.get('status', 'N/A')}
"""
    if enrichment_result.get("status") == "success" and enrichment_result.get("details"):
        for key, value in enrichment_result["details"].items():
            report += f"- **{key}:** {'Ensured' if value else 'Failed/Error'}\n"
    elif enrichment_result.get("error"):
        report += f"- **Error:** {enrichment_result.get('error')}\n"

    report += f"""
### Analytics Cache & Memory Stats
- **Status:** {analytics_result.get('status', 'N/A')}
"""
    if analytics_result.get("status") == "success" and analytics_result.get("memory_stats"):
        stats = analytics_result["memory_stats"]
        # hot_cache = stats.get("hot_cache", {}) # Assuming hot_cache structure might change or not be primary focus
        report += f"""- **Total Interactions in Memory:** {stats.get('total_interactions', 'N/A'):,}
- **Interactions by Type:**
"""
        for key, value in stats.get("interactions_by_type", {}).items():
            report += f"  - {key}: {value:,}\n"

    report += "\n"

    # Save report as artifact
    await create_markdown_artifact(
        key="pipeline-report", markdown=report, description="Pay Ready ETL Pipeline Execution Report"
    )

    return report

@flow(
    name="pay-ready-etl-pipeline",
    description="Main ETL pipeline for Pay Ready domain",
    task_runner=ConcurrentTaskRunner(max_workers=4),
    persist_result=True,
    result_storage_key_fn=lambda context: f"pay-ready-etl-{context.flow_run.name}",
    retries=1,
    retry_delay_seconds=300,
)
async def pay_ready_etl_pipeline(
    sources: List[str] = None, full_sync: bool = False, batch_size: int = 100
) -> Dict[str, Any]:
    """
    """
    logger.info(f"Starting Pay Ready ETL Pipeline - Full Sync: {full_sync}")

    # Default sources if not specified
    if sources is None:
        sources = ["gong", "slack", "hubspot", "salesforce"]

    # Initialize services
    services = await initialize_services()
    conductor = services["conductor"]
    entity_resolver = services["entity_resolver"]
    memory_manager = services["memory_manager"]

    # Phase 1: Trigger syncs in parallel
    logger.info(f"Phase 1: Triggering syncs for {len(sources)} sources")
    sync_tasks = [trigger_source_sync.submit(conductor, source) for source in sources]
    sync_results = await asyncio.gather(*[task.result() for task in sync_tasks])

    # Phase 2: Wait for syncs to complete
    logger.info("Phase 2: Waiting for syncs to complete")
    wait_tasks = [wait_for_sync_completion.submit(conductor, sync_info) for sync_info in sync_results]
    completed_syncs = await asyncio.gather(*[task.result() for task in wait_tasks])

    # Phase 3: Process data in parallel
    logger.info("Phase 3: Processing new data")
    process_tasks = [process_source_data.submit(conductor, source, batch_size) for source in sources]
    processing_results = await asyncio.gather(*[task.result() for task in process_tasks])

    # Phase 4: Entity resolution
    logger.info("Phase 4: Running entity resolution")
    entity_resolution_result = await run_entity_resolution(entity_resolver) # This is a task, so use .submit() if run in parallel

    # Phase 5: Vector Enrichment (Schema Preparation)
    logger.info("Phase 5: Running vector enrichment schema preparation")
    enrichment_task = run_vector_enrichment_task.submit(conductor) # Submit as a task

    # Phase 6: Update analytics and flush vectors (can run in parallel with enrichment or after)
    logger.info("Phase 6: Updating analytics and flushing vectors")
    analytics_task = update_analytics_cache.submit(conductor)
    flush_task = flush_pending_vectors.submit(memory_manager)

    # Wait for parallel tasks from Phase 5 and 6
    enrichment_result = await enrichment_task.result()
    analytics_result = await analytics_task.result()
    flush_result = await flush_task.result()


    # Generate report
    logger.info("Generating pipeline report")
    report = await generate_pipeline_report(
        completed_syncs,
        processing_results,
        entity_resolution_result,
        analytics_result,
        enrichment_result # Pass new result
    )

    # Calculate summary
    total_records = sum(r.get("records_processed", 0) for r in processing_results)
    successful_sources = sum(1 for r in processing_results if r.get("status") == "success")

    summary = {
        "sources_synced": sources,
        "total_records_processed": total_records,
        "successful_sources": successful_sources,
        "failed_sources": len(sources) - successful_sources,
        "entity_resolution_status": entity_resolution_result.get("status", "N/A"),
        "vector_enrichment_status": enrichment_result.get("status", "N/A"),
        "analytics_update_status": analytics_result.get("status", "N/A"),
        "vector_flush_status": flush_result.get("status", "N/A"),
        "execution_time": datetime.utcnow().isoformat(),
        "report": report,
    }

    logger.info(f"Pipeline completed - {total_records} records processed")

    return summary

@flow(
    name="pay-ready-incremental-sync",
    description="Incremental sync for a specific Pay Ready source",
    retries=2,
    retry_delay_seconds=60,
)
async def pay_ready_incremental_sync(source: str, batch_size: int = 100) -> Dict[str, Any]:
    """
    """
    logger.info(f"Running incremental sync for {source}")

    # Initialize services
    services = await initialize_services()
    conductor = services["conductor"]

    # Trigger sync
    sync_result = await trigger_source_sync(conductor, source)

    if sync_result["status"] == "triggered":
        # Wait for completion
        sync_result = await wait_for_sync_completion(conductor, sync_result)

        # Process data
        if sync_result["status"] == "completed":
            process_result = await process_source_data(conductor, source, batch_size)

            # Flush vectors
            await services["memory_manager"].flush_pending_vectors()

            return {
                "source": source,
                "sync_status": sync_result["status"],
                "records_processed": process_result.get("records_processed", 0),
                "timestamp": datetime.utcnow().isoformat(),
            }

    return {
        "source": source,
        "sync_status": sync_result["status"],
        "records_processed": 0,
        "error": sync_result.get("error"),
        "timestamp": datetime.utcnow().isoformat(),
    }

# CLI entry point for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Pay Ready ETL Pipeline")
    parser.add_argument(
        "--sources", nargs="+", default=["gong", "slack", "hubspot", "salesforce"], help="Sources to sync"
    )
    parser.add_argument("--full-sync", action="store_true", help="Perform full sync")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")

    args = parser.parse_args()

    # Run the flow
    asyncio.run(pay_ready_etl_pipeline(sources=args.sources, full_sync=args.full_sync, batch_size=args.batch_size))
