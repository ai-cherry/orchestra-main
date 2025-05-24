"""
Monitoring API endpoints for Claude usage tracking.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.monitoring.monitored_litellm_client import MonitoredLiteLLMClient
from core.orchestrator.src.api.dependencies.llm import get_llm_client
from core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class MonitoringSummaryResponse(BaseModel):
    """Response model for monitoring summary"""
    total_calls: int
    successful_calls: int
    failed_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    average_latency_ms: float
    calls_by_model: Dict[str, int]
    tokens_by_model: Dict[str, Dict[str, int]]
    cost_by_model: Dict[str, float]
    errors_by_type: Dict[str, int]
    period: Dict[str, Any]


class CostBreakdownResponse(BaseModel):
    """Response model for cost breakdown"""
    total_cost_usd: float
    cost_by_model: Dict[str, float]
    cost_by_day: Dict[str, float]
    cost_by_user: Dict[str, float]
    cost_by_session: Dict[str, float]


@router.get("/summary", response_model=MonitoringSummaryResponse)
async def get_monitoring_summary(
    hours: int = Query(24, description="Number of hours to look back"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    model: Optional[str] = Query(None, description="Filter by model name"),
    llm_client: MonitoredLiteLLMClient = Depends(get_llm_client)
) -> MonitoringSummaryResponse:
    """
    Get monitoring summary for Claude API usage.
    
    Returns aggregated metrics for the specified time period and filters.
    """
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Get monitoring summary
        summary = llm_client.get_monitoring_summary(
            start_time=start_time,
            end_time=end_time,
            user_id=user_id,
            session_id=session_id,
            model=model
        )
        
        # Add period information
        summary["period"] = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "hours": hours
        }
        
        return MonitoringSummaryResponse(**summary)
        
    except AttributeError:
        # Client is not a monitored client
        raise HTTPException(
            status_code=501,
            detail="Monitoring is not enabled. Use MonitoredLiteLLMClient."
        )
    except Exception as e:
        logger.error(f"Error getting monitoring summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs", response_model=CostBreakdownResponse)
async def get_cost_breakdown(
    days: int = Query(7, description="Number of days to analyze"),
    llm_client: MonitoredLiteLLMClient = Depends(get_llm_client)
) -> CostBreakdownResponse:
    """
    Get detailed cost breakdown for Claude API usage.
    
    Returns costs broken down by model, day, user, and session.
    """
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Get monitoring summary
        summary = llm_client.get_monitoring_summary(
            start_time=start_time,
            end_time=end_time
        )
        
        # Get detailed metrics for cost breakdown
        metrics = llm_client.monitor.metrics
        filtered_metrics = [
            m for m in metrics
            if start_time <= m.timestamp <= end_time
        ]
        
        # Calculate cost by day
        cost_by_day = {}
        cost_by_user = {}
        cost_by_session = {}
        
        for metric in filtered_metrics:
            # By day
            day_key = metric.timestamp.date().isoformat()
            cost_by_day[day_key] = cost_by_day.get(day_key, 0.0) + metric.cost_usd
            
            # By user
            if metric.user_id:
                cost_by_user[metric.user_id] = cost_by_user.get(metric.user_id, 0.0) + metric.cost_usd
            
            # By session
            if metric.session_id:
                cost_by_session[metric.session_id] = cost_by_session.get(metric.session_id, 0.0) + metric.cost_usd
        
        return CostBreakdownResponse(
            total_cost_usd=summary["total_cost_usd"],
            cost_by_model=summary["cost_by_model"],
            cost_by_day=cost_by_day,
            cost_by_user=cost_by_user,
            cost_by_session=cost_by_session
        )
        
    except AttributeError:
        # Client is not a monitored client
        raise HTTPException(
            status_code=501,
            detail="Monitoring is not enabled. Use MonitoredLiteLLMClient."
        )
    except Exception as e:
        logger.error(f"Error getting cost breakdown: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_monitoring_data(
    format: str = Query("json", description="Export format (json or csv)"),
    hours: int = Query(24, description="Number of hours to export"),
    llm_client: MonitoredLiteLLMClient = Depends(get_llm_client)
) -> Dict[str, Any]:
    """
    Export monitoring data in the specified format.
    
    Returns raw monitoring data for external analysis.
    """
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Export data
        exported_data = llm_client.export_monitoring_data(
            format=format,
            start_time=start_time,
            end_time=end_time
        )
        
        if format == "csv":
            return {
                "format": "csv",
                "data": exported_data,
                "filename": f"claude_monitoring_{start_time.strftime('%Y%m%d_%H%M%S')}.csv"
            }
        else:
            return {
                "format": "json",
                "data": exported_data,
                "filename": f"claude_monitoring_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
            }
        
    except AttributeError:
        # Client is not a monitored client
        raise HTTPException(
            status_code=501,
            detail="Monitoring is not enabled. Use MonitoredLiteLLMClient."
        )
    except Exception as e:
        logger.error(f"Error exporting monitoring data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/test")
async def test_monitoring_alerts(
    alert_type: str = Query(..., description="Alert type to test (cost or error)"),
    llm_client: MonitoredLiteLLMClient = Depends(get_llm_client)
) -> Dict[str, str]:
    """
    Test monitoring alerts.
    
    Useful for verifying that alerts are properly configured.
    """
    try:
        if alert_type == "cost":
            await llm_client.monitor._send_cost_alert("test_session", 100.0)
            return {"status": "success", "message": "Cost alert test sent"}
        elif alert_type == "error":
            await llm_client.monitor._send_error_alert("test_model", 10)
            return {"status": "success", "message": "Error alert test sent"}
        else:
            raise HTTPException(status_code=400, detail="Invalid alert type")
        
    except AttributeError:
        # Client is not a monitored client
        raise HTTPException(
            status_code=501,
            detail="Monitoring is not enabled. Use MonitoredLiteLLMClient."
        )
    except Exception as e:
        logger.error(f"Error testing alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def monitoring_health_check() -> Dict[str, Any]:
    """
    Check monitoring system health.
    """
    return {
        "status": "healthy",
        "service": "claude-monitoring",
        "timestamp": datetime.utcnow().isoformat()
    }