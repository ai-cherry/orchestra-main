# TODO: Consider adding connection pooling configuration
"""
"""
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
        """Convert to dictionary for storage."""
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
    """
        """
        """
        """Start the audit logger with periodic flushing."""
        """Stop the audit logger and flush remaining entries."""
        """Log a duplicate check operation."""
        """Log detection of a duplicate."""
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
        """Add entry to buffer and flush if needed."""
        """Flush audit entries to database."""
            insert_query = """
            """
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
            
        except Exception:

            
            pass
            logger.error(f"Failed to flush audit log: {e}")
            # Keep entries in buffer for retry
    
    async def _periodic_flush(self):
        """Periodically flush the buffer."""
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
        """
        query = """
        """
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
        """
        metrics_query = """
        """
        resolution_query = """
        """
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