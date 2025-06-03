"""
"""
router = APIRouter(prefix="/monitoring", tags=["monitoring"])

class MonitoringSummaryResponse(BaseModel):
    """Response model for monitoring summary"""
    """Response model for cost breakdown"""
@router.get("/summary", response_model=MonitoringSummaryResponse)
async def get_monitoring_summary(
    hours: int = Query(24, description="Number of hours to look back"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    model: Optional[str] = Query(None, description="Filter by model name"),
    llm_client: MonitoredLiteLLMClient = Depends(get_llm_client),
) -> MonitoringSummaryResponse:
    """
    """
        summary["period"] = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "hours": hours,
        }

        return MonitoringSummaryResponse(**summary)

    except Exception:


        pass
        # Client is not a monitored client
        raise HTTPException(
            status_code=501,
            detail="Monitoring is not enabled. Use MonitoredLiteLLMClient.",
        )
    except Exception:

        pass
        logger.error(f"Error getting monitoring summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/costs", response_model=CostBreakdownResponse)
async def get_cost_breakdown(
    days: int = Query(7, description="Number of days to analyze"),
    llm_client: MonitoredLiteLLMClient = Depends(get_llm_client),
) -> CostBreakdownResponse:
    """
    """
            total_cost_usd=summary["total_cost_usd"],
            cost_by_model=summary["cost_by_model"],
            cost_by_day=cost_by_day,
            cost_by_user=cost_by_user,
            cost_by_session=cost_by_session,
        )

    except Exception:


        pass
        # Client is not a monitored client
        raise HTTPException(
            status_code=501,
            detail="Monitoring is not enabled. Use MonitoredLiteLLMClient.",
        )
    except Exception:

        pass
        logger.error(f"Error getting cost breakdown: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export")
async def export_monitoring_data(
    format: str = Query("json", description="Export format (json or csv)"),
    hours: int = Query(24, description="Number of hours to export"),
    llm_client: MonitoredLiteLLMClient = Depends(get_llm_client),
) -> Dict[str, Any]:
    """
    """
        if format == "csv":
            return {
                "format": "csv",
                "data": exported_data,
                "filename": f"claude_monitoring_{start_time.strftime('%Y%m%d_%H%M%S')}.csv",
            }
        else:
            return {
                "format": "json",
                "data": exported_data,
                "filename": f"claude_monitoring_{start_time.strftime('%Y%m%d_%H%M%S')}.json",
            }

    except Exception:


        pass
        # Client is not a monitored client
        raise HTTPException(
            status_code=501,
            detail="Monitoring is not enabled. Use MonitoredLiteLLMClient.",
        )
    except Exception:

        pass
        logger.error(f"Error exporting monitoring data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/test")
async def test_monitoring_alerts(
    alert_type: str = Query(..., description="Alert type to test (cost or error)"),
    llm_client: MonitoredLiteLLMClient = Depends(get_llm_client),
) -> Dict[str, str]:
    """
    """
        if alert_type == "cost":
            await llm_client.monitor._send_cost_alert("test_session", 100.0)
            return {"status": "success", "message": "Cost alert test sent"}
        elif alert_type == "error":
            await llm_client.monitor._send_error_alert("test_model", 10)
            return {"status": "success", "message": "Error alert test sent"}
        else:
            raise HTTPException(status_code=400, detail="Invalid alert type")

    except Exception:


        pass
        # Client is not a monitored client
        raise HTTPException(
            status_code=501,
            detail="Monitoring is not enabled. Use MonitoredLiteLLMClient.",
        )
    except Exception:

        pass
        logger.error(f"Error testing alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def monitoring_health_check() -> Dict[str, Any]:
    """
    """
        "status": "healthy",
        "service": "claude-monitoring",
        "timestamp": datetime.utcnow().isoformat(),
    }
