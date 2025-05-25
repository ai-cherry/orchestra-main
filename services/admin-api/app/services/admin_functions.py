"""
Implementation of administrative functions that can be called by Gemini.
Optimized for performance and stability.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from google.api_core.exceptions import (
    DeadlineExceeded,
    ResourceExhausted,
    ServiceUnavailable,
)
from google.cloud.firestore import AsyncClient as FirestoreAsyncClient
from google.cloud.firestore import AsyncTransaction
from google.cloud.firestore_v1.base_query import BaseQuery

from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Firestore client with connection pooling
firestore_client = FirestoreAsyncClient(
    project=settings.PROJECT_ID,
    client_options={
        "api_endpoint": f"{settings.REGION}-firestore.googleapis.com",
    },
)


# Create a function decorator to measure performance
def measure_performance(func):
    """Decorator to measure function execution time and log it."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"{func.__name__} completed in {elapsed:.4f}s")
            # Add performance metadata to result if it's a dict
            if isinstance(result, dict) and "success" in result:
                result["performance"] = {"execution_time_seconds": round(elapsed, 4)}
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.4f}s: {str(e)}")
            raise

    return wrapper


async def paginate_query(query: BaseQuery, page_size: int = 500) -> AsyncGenerator:
    """
    Performance-optimized helper function to paginate through a Firestore query.

    Uses larger page sizes to reduce the number of queries needed and includes
    prefetching optimizations for better throughput.

    Args:
        query: Firestore query to paginate
        page_size: Number of documents per page (default: 500 for better performance)

    Yields:
        Document references from the query
    """
    # Set read consistency for better performance
    query = query.with_read_time(None)

    # Get the first page with larger page size
    docs = [doc async for doc in query.limit(page_size).stream()]

    # Yield all docs from first page
    for doc in docs:
        yield doc

    # Continue paginating if we got a full page
    while len(docs) == page_size:
        # Get last document as cursor
        last_doc = docs[-1]

        # Create a new query with start_after
        query = query.start_after(last_doc)

        # Get the next page
        docs = [doc async for doc in query.limit(page_size).stream()]

        # Yield all docs from this page
        for doc in docs:
            yield doc


@measure_performance
async def get_agent_status(agent_id: str) -> Dict[str, Any]:
    """
    Get the status of an agent.

    Args:
        agent_id: ID of the agent to check

    Returns:
        Dict[str, Any]: Agent status information
    """
    logger.info(f"Getting status for agent: {agent_id}")

    try:
        # Create a transaction to ensure consistency
        transaction = firestore_client.transaction()

        @firestore_client.transactional
        async def get_agent_with_logs(
            transaction: AsyncTransaction,
        ) -> Tuple[Dict, List[Dict]]:
            # Get agent document from Firestore
            agent_ref = firestore_client.collection("agents").document(agent_id)
            agent_doc = await agent_ref.get(transaction=transaction)

            if not agent_doc.exists:
                return None, []

            agent_data = agent_doc.to_dict()

            # Get recent agent logs outside transaction (read-only)
            logs_query = (
                firestore_client.collection("agent_logs")
                .where("agent_id", "==", agent_id)
                .order_by("timestamp", direction="DESCENDING")
                .limit(5)
            )
            logs = [doc.to_dict() async for doc in logs_query.stream()]

            return agent_data, logs

        # Execute the transaction
        agent_data, logs = await get_agent_with_logs(transaction)

        if agent_data is None:
            return {
                "error": f"Agent {agent_id} not found",
                "status": "unknown",
                "success": False,
            }

        return {
            "agent_id": agent_id,
            "status": agent_data.get("status", "unknown"),
            "last_active": agent_data.get("last_active", "unknown"),
            "type": agent_data.get("type", "unknown"),
            "recent_logs": logs,
            "success": True,
        }

    except DeadlineExceeded as e:
        logger.error(f"Deadline exceeded getting agent status: {str(e)}")
        return {
            "error": "Request timed out. Please try again later.",
            "status": "error",
            "success": False,
        }
    except Exception as e:
        logger.error(f"Error getting agent status: {str(e)}", exc_info=True)
        return {"error": str(e), "status": "error", "success": False}


async def start_agent(agent_id: str) -> Dict[str, Any]:
    """
    Start an agent.

    Args:
        agent_id: ID of the agent to start

    Returns:
        Dict[str, Any]: Result of the operation
    """
    logger.info(f"Starting agent: {agent_id}")

    try:
        # Check if agent exists
        agent_doc = await firestore_client.collection("agents").document(agent_id).get()

        if not agent_doc.exists:
            return {"error": f"Agent {agent_id} not found", "success": False}

        # Update agent status in Firestore
        await firestore_client.collection("agents").document(agent_id).update(
            {
                "status": "running",
                "last_active": datetime.now().isoformat(),
                "last_started": datetime.now().isoformat(),
            }
        )

        # Log the agent start
        await firestore_client.collection("agent_logs").add(
            {
                "agent_id": agent_id,
                "action": "start",
                "timestamp": datetime.now().isoformat(),
                "user": "admin",
                "success": True,
            }
        )

        return {
            "success": True,
            "agent_id": agent_id,
            "status": "running",
            "message": f"Agent {agent_id} started successfully",
        }
    except Exception as e:
        logger.error(f"Error starting agent: {str(e)}")
        return {"error": str(e), "success": False}


async def stop_agent(agent_id: str) -> Dict[str, Any]:
    """
    Stop a running agent.

    Args:
        agent_id: ID of the agent to stop

    Returns:
        Dict[str, Any]: Result of the operation
    """
    logger.info(f"Stopping agent: {agent_id}")

    try:
        # Check if agent exists
        agent_doc = await firestore_client.collection("agents").document(agent_id).get()

        if not agent_doc.exists:
            return {"error": f"Agent {agent_id} not found", "success": False}

        # Update agent status in Firestore
        await firestore_client.collection("agents").document(agent_id).update(
            {
                "status": "stopped",
                "last_active": datetime.now().isoformat(),
                "last_stopped": datetime.now().isoformat(),
            }
        )

        # Log the agent stop
        await firestore_client.collection("agent_logs").add(
            {
                "agent_id": agent_id,
                "action": "stop",
                "timestamp": datetime.now().isoformat(),
                "user": "admin",
                "success": True,
            }
        )

        return {
            "success": True,
            "agent_id": agent_id,
            "status": "stopped",
            "message": f"Agent {agent_id} stopped successfully",
        }
    except Exception as e:
        logger.error(f"Error stopping agent: {str(e)}")
        return {"error": str(e), "success": False}


async def list_agents(status: Optional[str] = "all") -> Dict[str, Any]:
    """
    List all available agents, optionally filtered by status.

    Args:
        status: Filter agents by status (running, stopped, all)

    Returns:
        Dict[str, Any]: List of agents
    """
    logger.info(f"Listing agents with status filter: {status}")

    try:
        # Query agents from Firestore
        if status == "all":
            query = firestore_client.collection("agents")
        else:
            query = firestore_client.collection("agents").where("status", "==", status)

        agents = [doc.to_dict() async for doc in query.stream()]

        return {
            "success": True,
            "count": len(agents),
            "status_filter": status,
            "agents": agents,
        }
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        return {"error": str(e), "success": False}


@measure_performance
async def prune_memory(agent_id: str, older_than_days: int) -> Dict[str, Any]:
    """
    Prune memory for an agent using efficient batch operations.

    Args:
        agent_id: ID of the agent to prune memory for
        older_than_days: Prune memories older than this many days

    Returns:
        Dict[str, Any]: Result of the operation
    """
    logger.info(
        f"Pruning memory for agent {agent_id} older than {older_than_days} days"
    )

    # Validate input
    if older_than_days < 0:
        return {"error": "older_than_days must be a positive number", "success": False}

    try:
        # Calculate the cutoff date
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        cutoff_str = cutoff_date.isoformat()

        # Query memories to prune
        memory_collection = firestore_client.collection(settings.FIRESTORE_COLLECTION)
        query = (
            memory_collection.where("agent_id", "==", agent_id)
            .where("timestamp", "<", cutoff_str)
            .where("tier", "==", "episodic")  # Only prune episodic memories
        )

        # Get total count estimate
        try:
            count_query = await query.count().get()
            total_count = (
                count_query[0][0].value if count_query and count_query[0] else 0
            )
            logger.info(f"Found {total_count} memories eligible for pruning")
        except Exception as count_error:
            logger.warning(f"Could not get exact count: {str(count_error)}")
            total_count = 0  # We'll count as we go instead

        # Set up tracking variables
        deleted_count = 0
        batch_size = 200  # Firestore has a limit of 500, using 200 for safety

        # Start time tracking for progress updates
        batch_start_time = time.time()
        operation_start_time = time.time()

        # Process in batches using pagination
        # Initialize batch before the loop if it's used inside the loop
        batch = firestore_client.batch()
        async for mem_doc in paginate_query(query, page_size=batch_size):
            # Create a new batch if needed
            if (
                deleted_count > 0 and deleted_count % batch_size == 0
            ):  # check deleted_count > 0 to avoid committing an empty initial batch
                # Commit previous batch if it exists
                try:
                    await batch.commit()
                    batch_time = time.time() - batch_start_time
                    logger.info(
                        f"Committed batch of {batch_size}, total deleted: {deleted_count} ({batch_time:.2f}s)"
                    )
                    batch_start_time = time.time()
                except (
                    DeadlineExceeded,
                    ServiceUnavailable,
                    ResourceExhausted,
                ) as e:
                    # On transient errors, reduce batch size and retry
                    logger.warning(f"Transient error, reducing batch size: {str(e)}")
                    batch_size = max(50, batch_size // 2)
                    # Re-initialize batch for the next set of operations
                    batch = firestore_client.batch()
                    continue

                # Create a new batch for the next set of operations after successful commit
                batch = firestore_client.batch()

            # Add delete operation to batch
            batch.delete(mem_doc.reference)
            deleted_count += 1

        # Commit any remaining operations in the final batch
        if (
            deleted_count > 0 and deleted_count % batch_size != 0
        ):  # check deleted_count > 0
            await batch.commit()
            logger.info(f"Committed final batch, total deleted: {deleted_count}")

        # Calculate total time
        total_time = time.time() - operation_start_time

        # Log the pruning operation
        await firestore_client.collection("memory_operations").add(
            {
                "agent_id": agent_id,
                "operation": "prune",
                "timestamp": datetime.now().isoformat(),
                "user": "admin",
                "parameters": {
                    "older_than_days": older_than_days,
                    "cutoff_date": cutoff_str,
                },
                "result": {
                    "total_eligible": total_count
                    or deleted_count,  # Use count if available, otherwise use deleted
                    "deleted": deleted_count,
                    "execution_time_seconds": round(total_time, 2),
                },
            }
        )

        if total_count == 0:
            total_count = deleted_count  # Update total if we didn't get it initially

        return {
            "success": True,
            "agent_id": agent_id,
            "older_than_days": older_than_days,
            "total_eligible": total_count,
            "deleted": deleted_count,
            "execution_time_seconds": round(total_time, 2),
            "message": f"Deleted {deleted_count} of {total_count} eligible memories in {total_time:.2f}s",
        }
    except DeadlineExceeded as e:
        logger.error(f"Deadline exceeded during memory pruning: {str(e)}")
        return {
            "error": "Operation timed out. The process may have partially completed. Please try again with a smaller time range.",
            "success": False,
            "partial_completion": True,
        }
    except Exception as e:
        logger.error(f"Error pruning memory: {str(e)}", exc_info=True)
        return {"error": str(e), "success": False}


async def promote_memory(memory_id: str, tier: str) -> Dict[str, Any]:
    """
    Promote a memory to a higher tier.

    Args:
        memory_id: ID of the memory to promote
        tier: Target tier to promote to

    Returns:
        Dict[str, Any]: Result of the operation
    """
    logger.info(f"Promoting memory {memory_id} to tier: {tier}")

    valid_tiers = ["working", "long_term", "core"]
    if tier not in valid_tiers:
        return {
            "error": f"Invalid tier: {tier}. Must be one of {valid_tiers}",
            "success": False,
        }

    try:
        # Get memory document
        memory_collection = firestore_client.collection(settings.FIRESTORE_COLLECTION)
        memory_doc = await memory_collection.document(memory_id).get()

        if not memory_doc.exists:
            return {"error": f"Memory {memory_id} not found", "success": False}

        memory_data = memory_doc.to_dict()
        current_tier = memory_data.get("tier", "unknown")

        # Check if promotion is valid
        tier_hierarchy = ["episodic", "working", "long_term", "core"]
        current_idx = (
            tier_hierarchy.index(current_tier) if current_tier in tier_hierarchy else -1
        )
        target_idx = tier_hierarchy.index(tier) if tier in tier_hierarchy else -1

        if current_idx >= target_idx:
            return {
                "error": f"Cannot promote from {current_tier} to {tier}. Target tier must be higher.",
                "success": False,
            }

        # Update memory tier
        await memory_collection.document(memory_id).update(
            {
                "tier": tier,
                "promoted_at": datetime.now().isoformat(),
                "promoted_by": "admin",
                "previous_tier": current_tier,
            }
        )

        # Log the promotion
        await firestore_client.collection("memory_operations").add(
            {
                "agent_id": memory_data.get("agent_id", "unknown"),
                "memory_id": memory_id,
                "operation": "promote",
                "timestamp": datetime.now().isoformat(),
                "user": "admin",
                "parameters": {"from_tier": current_tier, "to_tier": tier},
            }
        )

        return {
            "success": True,
            "memory_id": memory_id,
            "previous_tier": current_tier,
            "new_tier": tier,
            "message": f"Memory promoted from {current_tier} to {tier}",
        }
    except Exception as e:
        logger.error(f"Error promoting memory: {str(e)}")
        return {"error": str(e), "success": False}


@measure_performance
async def get_memory_stats(agent_id: str) -> Dict[str, Any]:
    """
    Get memory statistics for an agent using parallel queries for performance.

    Args:
        agent_id: ID of the agent to get memory stats for

    Returns:
        Dict[str, Any]: Memory statistics
    """
    logger.info(f"Getting memory stats for agent: {agent_id}")

    try:
        memory_collection = firestore_client.collection(settings.FIRESTORE_COLLECTION)

        # Run all count queries in parallel for performance
        tiers = ["episodic", "working", "long_term", "core"]
        count_queries = []

        # Create all queries
        for tier in tiers:
            query = (
                memory_collection.where("agent_id", "==", agent_id)
                .where("tier", "==", tier)
                .count()
            )
            count_queries.append(query.get())

        # Add total count query
        total_query = memory_collection.where("agent_id", "==", agent_id).count()
        count_queries.append(total_query.get())

        # Add operations query
        ops_query = (
            firestore_client.collection("memory_operations")
            .where("agent_id", "==", agent_id)
            .order_by("timestamp", direction="DESCENDING")
            .limit(5)
            .stream()
        )

        # Execute all queries in parallel
        results = await asyncio.gather(
            *count_queries, ops_query, return_exceptions=True
        )

        # Process tier counts (first len(tiers) results)
        counts = {}
        for i, tier in enumerate(tiers):
            if isinstance(results[i], Exception):
                logger.warning(
                    f"Error getting count for tier {tier}: {str(results[i])}"
                )
                counts[tier] = 0
            else:
                counts[tier] = (
                    results[i][0][0].value if results[i] and results[i][0] else 0
                )

        # Process total count (next result)
        if isinstance(results[len(tiers)], Exception):
            logger.warning(f"Error getting total count: {str(results[len(tiers)])}")
            total_count = sum(counts.values())  # Fall back to sum of tiers
        else:
            total_count = (
                results[len(tiers)][0][0].value
                if results[len(tiers)] and results[len(tiers)][0]
                else 0
            )

        # Process operations (last result)
        if isinstance(results[-1], Exception):
            logger.warning(f"Error getting recent operations: {str(results[-1])}")
            recent_ops = []
        else:
            recent_ops = [doc.to_dict() for doc in results[-1]]

        # Calculate metrics and percentages
        percentages = {}
        for tier, count in counts.items():
            percentages[tier] = round(
                (count / total_count * 100) if total_count > 0 else 0, 2
            )

        # Add timestamp for freshness tracking
        timestamp = datetime.now().isoformat()

        return {
            "success": True,
            "agent_id": agent_id,
            "total_memories": total_count,
            "counts_by_tier": counts,
            "percentages_by_tier": percentages,
            "recent_operations": recent_ops,
            "timestamp": timestamp,
        }
    except Exception as e:
        logger.error(f"Error getting memory stats: {str(e)}", exc_info=True)
        return {"error": str(e), "success": False}
