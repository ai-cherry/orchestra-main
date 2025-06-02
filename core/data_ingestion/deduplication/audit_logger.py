"""
Audit logging system for deduplication operations.

This module provides comprehensive audit trail functionality for all
duplicate detection and resolution operations.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select

from .deduplication_engine import DuplicateMatch, UploadChannel
from .duplicate_resolver import ResolutionResult

logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    """Types of audit events."""
    DUPLICATE_CHECK = "duplicate_check"
    DUPLICATE_DETECTED = "duplicate_detected"
    RESOLUTION_APPLIED = "resolution_applied"
    MANUAL_REVIEW_QUEUED = "manual_review_queued"
    MANUAL_REVIEW_COMPLETED = "manual_review_completed"
    BULK_OPERATION = "bulk_operation"
    ERROR = "error"

@dataclass
class AuditEntry:
    """Represents an audit log entry."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: AuditEventType = AuditEventType.DUPLICATE_CHECK
    timestamp: datetime = field(default_factory=datetime.utcnow)
    upload_channel: Optional[UploadChannel] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    content_id: Optional[str] = None
    duplicate_match: Optional[DuplicateMatch] = None
    resolution_result: Optional[ResolutionResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_details: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = {
            "id": self.id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "upload_channel": self.upload_channel.value if self.upload_channel else None,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "content_id": self.content_id,
            "metadata": self.metadata,
            "error_details": self.error_details
        }
        
        if self.duplicate_match:
            data["duplicate_match"] = self.duplicate_match.to_dict()
        
        if self.resolution_result:
            data["resolution_result"] = self.resolution_result.to_dict()
        
        return data

class DeduplicationAuditLogger:
    """
    Comprehensive audit logger for deduplication operations.
    
    Features:
    - Async logging to database
    - Structured audit trail
    - Query capabilities
    - Compliance support
    - Performance metrics
    """
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        Initialize audit logger.
        
        Args:
            db_session: Async database session for persistence
        """
        self.db_session = db_session
        self._buffer: List[AuditEntry] = []
        self._buffer_size = 100
        self._flush_interval = 5.0  # seconds
        self._flush_task = None
        
    async def start(self):
        """Start the audit logger with periodic flushing."""
        if not self._flush_task:
            self._flush_task = asyncio.create_task(self._periodic_flush())
    
    async def stop(self):
        """Stop the audit logger and flush remaining entries."""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining entries
        await self._flush_buffer()
    
    async def log_duplicate_check(
        self,
        content_id: str,
        upload_channel: UploadChannel,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a duplicate check operation."""
        entry = AuditEntry(
            event_type=AuditEventType.DUPLICATE_CHECK,
            upload_channel=upload_channel,
            user_id=user_id,
            session_id=session_id,
            content_id=content_id,
            metadata=metadata or {}
        )
        
        await self._add_entry(entry)
    
    async def log_duplicate_detected(
        self,
        content_id: str,
        duplicate_match: DuplicateMatch,
        upload_channel: UploadChannel,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log detection of a duplicate."""
        entry = AuditEntry(
            event_type=AuditEventType.DUPLICATE_DETECTED,
            upload_channel=upload_channel,
            user_id=user_id,
            session_id=session_id,
            content_id=content_id,
            duplicate_match=duplicate_match,
            metadata={
                "duplicate_type": duplicate_match.duplicate_type.value,
                "similarity_score": duplicate_match.similarity_score,
                "detection_method": duplicate_match.detection_method,
                **(metadata or {})
            }
        )
        
        await self._add_entry(entry)
    
    async def log_resolution(
        self,
        content_id: str,
        resolution_result: ResolutionResult,
        upload_channel: UploadChannel,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log resolution of a duplicate."""
        entry = AuditEntry(
            event_type=AuditEventType.RESOLUTION_APPLIED,
            upload_channel=upload_channel,
            user_id=user_id,
            session_id=session_id,
            content_id=content_id,
            resolution_result=resolution_result,
            metadata={
                "action": resolution_result.action.value,
                "strategy": resolution_result.strategy.value,
                "resolved_by": resolution_result.resolved_by,
                **(metadata or {})
            }
        )
        
        await self._add_entry(entry)
    
    async def log_manual_review(
        self,
        content_id: str,
        review_queue_id: str,
        duplicate_match: DuplicateMatch,
        upload_channel: UploadChannel,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log queueing for manual review."""
        entry = AuditEntry(
            event_type=AuditEventType.MANUAL_REVIEW_QUEUED,
            upload_channel=upload_channel,
            user_id=user_id,
            content_id=content_id,
            duplicate_match=duplicate_match,
            metadata={
                "review_queue_id": review_queue_id,
                "reason": "Ambiguous duplicate requiring manual review",
                **(metadata or {})
            }
        )
        
        await self._add_entry(entry)
    
    async def log_bulk_operation(
        self,
        operation_id: str,
        item_count: int,
        duplicates_found: int,
        resolutions_applied: Dict[str, int],
        upload_channel: UploadChannel,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log bulk deduplication operation."""
        entry = AuditEntry(
            event_type=AuditEventType.BULK_OPERATION,
            upload_channel=upload_channel,
            user_id=user_id,
            metadata={
                "operation_id": operation_id,
                "item_count": item_count,
                "duplicates_found": duplicates_found,
                "resolutions": resolutions_applied,
                **(metadata or {})
            }
        )
        
        await self._add_entry(entry)
    
    async def log_error(
        self,
        error_message: str,
        content_id: Optional[str] = None,
        upload_channel: Optional[UploadChannel] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log an error during deduplication."""
        entry = AuditEntry(
            event_type=AuditEventType.ERROR,
            upload_channel=upload_channel,
            user_id=user_id,
            content_id=content_id,
            error_details=error_message,
            metadata=metadata or {}
        )
        
        await self._add_entry(entry)
    
    async def _add_entry(self, entry: AuditEntry):
        """Add entry to buffer and flush if needed."""
        self._buffer.append(entry)
        
        if len(self._buffer) >= self._buffer_size:
            await self._flush_buffer()
    
    async def _flush_buffer(self):
        """Flush audit entries to database."""
        if not self._buffer or not self.db_session:
            return
        
        try:
            # Prepare entries for bulk insert
            entries_data = [entry.to_dict() for entry in self._buffer]
            
            # Insert into audit log table
            insert_query = """
                INSERT INTO data_ingestion.deduplication_audit_log
                (id, event_type, timestamp, upload_channel, user_id, 
                 session_id, content_id, duplicate_match, resolution_result,
                 metadata, error_details)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """
            
            for entry_data in entries_data:
                await self.db_session.execute(
                    insert_query,
                    entry_data["id"],
                    entry_data["event_type"],
                    entry_data["timestamp"],
                    entry_data["upload_channel"],
                    entry_data["user_id"],
                    entry_data["session_id"],
                    entry_data["content_id"],
                    json.dumps(entry_data.get("duplicate_match")),
                    json.dumps(entry_data.get("resolution_result")),
                    json.dumps(entry_data["metadata"]),
                    entry_data["error_details"]
                )
            
            await self.db_session.commit()
            
            # Clear buffer after successful flush
            self._buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to flush audit log: {e}")
            # Keep entries in buffer for retry
    
    async def _periodic_flush(self):
        """Periodically flush the buffer."""
        while True:
            try:
                await asyncio.sleep(self._flush_interval)
                await self._flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")
    
    async def query_audit_log(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        user_id: Optional[str] = None,
        content_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query audit log with filters.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            event_types: Filter by event types
            user_id: Filter by user
            content_id: Filter by content
            limit: Maximum results
            
        Returns:
            List of audit entries
        """
        if not self.db_session:
            return []
        
        query = """
            SELECT * FROM data_ingestion.deduplication_audit_log
            WHERE 1=1
        """
        
        params = []
        param_count = 0
        
        if start_time:
            param_count += 1
            query += f" AND timestamp >= ${param_count}"
            params.append(start_time)
        
        if end_time:
            param_count += 1
            query += f" AND timestamp <= ${param_count}"
            params.append(end_time)
        
        if event_types:
            param_count += 1
            event_type_values = [et.value for et in event_types]
            query += f" AND event_type = ANY(${param_count})"
            params.append(event_type_values)
        
        if user_id:
            param_count += 1
            query += f" AND user_id = ${param_count}"
            params.append(user_id)
        
        if content_id:
            param_count += 1
            query += f" AND content_id = ${param_count}"
            params.append(content_id)
        
        query += f" ORDER BY timestamp DESC LIMIT ${param_count + 1}"
        params.append(limit)
        
        results = await self.db_session.fetch_all(query, *params)
        
        return [dict(row) for row in results]
    
    async def get_deduplication_metrics(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Get deduplication metrics for a time period.
        
        Args:
            start_time: Start of period
            end_time: End of period
            
        Returns:
            Dictionary with metrics
        """
        if not self.db_session:
            return {}
        
        # Query for metrics
        metrics_query = """
            SELECT 
                COUNT(*) FILTER (WHERE event_type = 'duplicate_check') as total_checks,
                COUNT(*) FILTER (WHERE event_type = 'duplicate_detected') as duplicates_found,
                COUNT(*) FILTER (WHERE event_type = 'resolution_applied') as resolutions_applied,
                COUNT(*) FILTER (WHERE event_type = 'manual_review_queued') as manual_reviews,
                COUNT(*) FILTER (WHERE event_type = 'error') as errors,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT upload_channel) as channels_used
            FROM data_ingestion.deduplication_audit_log
            WHERE timestamp BETWEEN $1 AND $2
        """
        
        result = await self.db_session.fetch_one(
            metrics_query, start_time, end_time
        )
        
        if not result:
            return {}
        
        # Resolution breakdown
        resolution_query = """
            SELECT 
                resolution_result->>'action' as action,
                COUNT(*) as count
            FROM data_ingestion.deduplication_audit_log
            WHERE event_type = 'resolution_applied'
                AND timestamp BETWEEN $1 AND $2
            GROUP BY resolution_result->>'action'
        """
        
        resolution_results = await self.db_session.fetch_all(
            resolution_query, start_time, end_time
        )
        
        resolution_breakdown = {
            row["action"]: row["count"] 
            for row in resolution_results
        }
        
        return {
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "total_checks": result["total_checks"],
            "duplicates_found": result["duplicates_found"],
            "duplicate_rate": (
                result["duplicates_found"] / result["total_checks"] 
                if result["total_checks"] > 0 else 0
            ),
            "resolutions_applied": result["resolutions_applied"],
            "manual_reviews": result["manual_reviews"],
            "errors": result["errors"],
            "unique_users": result["unique_users"],
            "channels_used": result["channels_used"],
            "resolution_breakdown": resolution_breakdown
        }