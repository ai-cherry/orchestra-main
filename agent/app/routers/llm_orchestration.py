"""
"""
router = APIRouter(prefix="/api/orchestration", tags=["orchestration"])

# Pydantic models for requests/responses

class TestRoutingRequest(BaseModel):
    """Test intelligent routing with a query"""
    """Create a new workflow"""
    """Execute a task with a specific agent"""
    agent_type: str = Field(..., description="Agent type: personal, pay_ready, or paragon_medical")
    task: Dict[str, Any] = Field(..., description="Task data for the agent")

class PersonalSearchRequest(BaseModel):
    """Personal agent search request"""
    search_type: str = "general"

class ApartmentAnalysisRequest(BaseModel):
    """Pay Ready agent apartment analysis"""
    """Paragon Medical agent trial search"""
    phases: List[str] = Field(default=["Phase 3", "Phase 4"])
    location: Optional[Dict[str, float]] = None
    max_distance_miles: float = 50

# Intelligent Routing Endpoints

@router.post("/test-routing")
async def test_intelligent_routing(request: TestRoutingRequest) -> Dict[str, Any]:
    """Test the intelligent routing system with a query"""
        context["query_type"] = request.force_query_type
    
    try:

    
        pass
        # Route the query
        response = await router.route_query(request.query, context)
        
        # Extract routing metadata
        routing_metadata = response.get("routing_metadata", {})
        
        return {
            "query": request.query,
            "query_type": routing_metadata.get("query_type"),
            "model_used": routing_metadata.get("model_used"),
            "temperature": routing_metadata.get("temperature"),
            "max_tokens": routing_metadata.get("max_tokens"),
            "latency_ms": routing_metadata.get("latency_ms"),
            "reasoning": routing_metadata.get("reasoning"),
            "response_preview": response.get("choices", [{}])[0].get("message", {}).get("content", "")[:200]
        }
        
    except Exception:

        
        pass
        raise HTTPException(status_code=500, detail=f"Routing failed: {str(e)}")

@router.get("/routing-analytics")
async def get_routing_analytics() -> Dict[str, Any]:
    """Get analytics on routing decisions and model performance"""
@router.get("/query-types")
async def get_query_types() -> List[Dict[str, str]]:
    """Get available query types for classification"""
            "value": qt.value,
            "name": qt.name,
            "description": f"Queries classified as {qt.value}"
        }
        for qt in QueryType
    ]

# Agent Management Endpoints

@router.get("/agents")
async def get_all_agents() -> Dict[str, Any]:
    """Get status of all specialized agents"""
                "error": str(e),
                "status": "unavailable"
            }
    
    return {
        "agents": agents_status,
        "total_agents": len(AgentType),
        "active_agents": sum(
            1 for status in agents_status.values()
            if status.get("status") == "active"
        )
    }

@router.post("/agents/{agent_type}/execute")
async def execute_agent_task(
    agent_type: str,
    request: AgentTaskRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Execute a task with a specific agent"""
            detail=f"Invalid agent type. Must be one of: {[at.value for at in AgentType]}"
        )
    
    try:

    
        pass
        # Execute task
        result = await process_agent_task(agent_type, request.task)
        
        return {
            "agent_type": agent_type,
            "task": request.task,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception:

        
        pass
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")

# Specialized Agent Endpoints

@router.post("/personal/search")
async def personal_agent_search(request: PersonalSearchRequest) -> Dict[str, Any]:
    """Perform adaptive search with the Personal Agent"""
@router.post("/personal/learn-preference")
async def learn_user_preference(
    user_id: str,
    category: str,
    signal_type: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Update user preferences based on feedback"""
    if signal_type not in ["positive", "negative"]:
        raise HTTPException(status_code=400, detail="Signal type must be 'positive' or 'negative'")
    
    agent = await get_specialized_agent(AgentType.PERSONAL.value)
    
    await agent.learn_preference(user_id, category, signal_type, context)
    
    return {
        "status": "preference_updated",
        "user_id": user_id,
        "category": category,
        "signal_type": signal_type
    }

@router.post("/payready/analyze")
async def analyze_apartment_listing(request: ApartmentAnalysisRequest) -> Dict[str, Any]:
    """Analyze an apartment listing with Pay Ready Agent"""
        "listing": listing.__dict__,
        "recommendation": "recommended" if listing.overall_score > 70 else "not_recommended",
        "top_features": [
            f"Tech Score: {listing.tech_score:.1f}/100",
            f"Neighborhood Score: {listing.neighborhood_score:.1f}/100",
            f"Overall Score: {listing.overall_score:.1f}/100"
        ]
    }

@router.post("/payready/market-analysis")
async def apartment_market_analysis(
    location: str = Query(..., description="Location for market analysis"),
    criteria: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Perform apartment market analysis"""
@router.post("/paragon/search-trials")
async def search_clinical_trials(request: ClinicalTrialSearchRequest) -> Dict[str, Any]:
    """Search for clinical trials with Paragon Medical Agent"""
        "trials": [trial.__dict__ for trial in trials[:20]],  # Top 20
        "total_found": len(trials),
        "search_criteria": {
            "conditions": request.conditions,
            "phases": request.phases,
            "max_distance": request.max_distance_miles
        }
    }

@router.post("/paragon/setup-alert")
async def setup_trial_alert(
    user_id: str,
    criteria: Dict[str, Any],
    notification_method: str = "email"
) -> Dict[str, Any]:
    """Set up automated clinical trial alerts"""
@router.post("/workflows")
async def create_workflow(
    request: WorkflowCreateRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Create and optionally execute a new workflow"""
            "workflow_id": workflow.id,
            "name": workflow.name,
            "status": workflow.status.value,
            "task_count": len(workflow.tasks),
            "created_at": workflow.created_at.isoformat()
        }
        
    except Exception:

        
        pass
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Execute a workflow asynchronously"""
        "workflow_id": workflow_id,
        "status": "execution_started",
        "message": "Workflow execution started in background"
    }

@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str) -> Dict[str, Any]:
    """Get detailed workflow execution status"""
@router.post("/workflows/{workflow_id}/cancel")
async def cancel_workflow(workflow_id: str) -> Dict[str, Any]:
    """Cancel a running workflow"""
            "workflow_id": workflow_id,
            "status": "cancelled",
            "message": "Workflow cancelled successfully"
        }
    except Exception:

        pass
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/workflows/comprehensive-search")
async def create_comprehensive_search(
    background_tasks: BackgroundTasks,
    user_id: str = Query(..., description="User ID"),
    query: str = Query(..., description="Search query"),
    include_medical: bool = Query(False, description="Include medical search")
) -> Dict[str, Any]:
    """Create and execute a comprehensive search workflow"""
            "workflow_id": workflow.id,
            "name": workflow.name,
            "status": "started",
            "tasks": len(workflow.tasks),
            "message": "Comprehensive search workflow started"
        }
        
    except Exception:

        
        pass
        raise HTTPException(status_code=500, detail=str(e))

# System Monitoring Endpoints

@router.get("/system/metrics")
async def get_system_metrics() -> Dict[str, Any]:
    """Get overall system performance metrics"""
        "orchestrator": orchestrator_metrics,
        "routing": {
            "total_queries": routing_analytics.get("total_queries_routed", 0),
            "query_distribution": routing_analytics.get("query_type_distribution", {}),
            "model_performance": routing_analytics.get("model_performance", {})
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/system/health")
async def get_system_health() -> Dict[str, Any]:
    """Get system health status"""
        "status": "healthy",
        "components": {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Check LLM router
    try:

        pass
        router = get_intelligent_llm_router()
        health_status["components"]["llm_router"] = "healthy"
    except Exception:

        pass
        health_status["components"]["llm_router"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check orchestrator
    try:

        pass
        orchestrator = get_agent_orchestrator()
        health_status["components"]["orchestrator"] = "healthy"
    except Exception:

        pass
        health_status["components"]["orchestrator"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check agents
    for agent_type in AgentType:
        try:

            pass
            agent = await get_specialized_agent(agent_type.value)
            status = await agent.get_status()
            health_status["components"][f"agent_{agent_type.value}"] = status.get("status", "unknown")
        except Exception:

            pass
            health_status["components"][f"agent_{agent_type.value}"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
    
    return health_status