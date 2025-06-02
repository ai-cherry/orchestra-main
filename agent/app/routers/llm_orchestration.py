"""
LLM Orchestration API endpoints for the administrative dashboard

This module provides endpoints for:
- Intelligent LLM routing management
- Agent orchestration control
- Workflow management
- Performance monitoring
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agent.app.core.database import get_db
from core.llm_intelligent_router import get_intelligent_llm_router, QueryType
from agent.app.services.agent_orchestrator import (
    get_agent_orchestrator,
    create_comprehensive_search_workflow,
    WorkflowStatus
)
from agent.app.services.specialized_agents import (
    get_specialized_agent,
    AgentType,
    process_agent_task
)

router = APIRouter(prefix="/api/orchestration", tags=["orchestration"])


# Pydantic models for requests/responses

class TestRoutingRequest(BaseModel):
    """Test intelligent routing with a query"""
    query: str
    context: Optional[Dict[str, Any]] = None
    force_query_type: Optional[str] = None


class WorkflowCreateRequest(BaseModel):
    """Create a new workflow"""
    name: str
    tasks: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]] = None


class AgentTaskRequest(BaseModel):
    """Execute a task with a specific agent"""
    agent_type: str = Field(..., description="Agent type: personal, pay_ready, or paragon_medical")
    task: Dict[str, Any] = Field(..., description="Task data for the agent")


class PersonalSearchRequest(BaseModel):
    """Personal agent search request"""
    user_id: str
    query: str
    search_type: str = "general"


class ApartmentAnalysisRequest(BaseModel):
    """Pay Ready agent apartment analysis"""
    listing_data: Dict[str, Any]
    user_preferences: Optional[Dict[str, Any]] = None


class ClinicalTrialSearchRequest(BaseModel):
    """Paragon Medical agent trial search"""
    conditions: List[str]
    phases: List[str] = Field(default=["Phase 3", "Phase 4"])
    location: Optional[Dict[str, float]] = None
    max_distance_miles: float = 50


# Intelligent Routing Endpoints

@router.post("/test-routing")
async def test_intelligent_routing(request: TestRoutingRequest) -> Dict[str, Any]:
    """Test the intelligent routing system with a query"""
    
    router = get_intelligent_llm_router()
    
    # Override query type if specified
    context = request.context or {}
    if request.force_query_type:
        context["query_type"] = request.force_query_type
    
    try:
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
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing failed: {str(e)}")


@router.get("/routing-analytics")
async def get_routing_analytics() -> Dict[str, Any]:
    """Get analytics on routing decisions and model performance"""
    
    router = get_intelligent_llm_router()
    analytics = await router.get_routing_analytics()
    
    return analytics


@router.get("/query-types")
async def get_query_types() -> List[Dict[str, str]]:
    """Get available query types for classification"""
    
    return [
        {
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
    
    agents_status = {}
    
    for agent_type in AgentType:
        try:
            agent = await get_specialized_agent(agent_type.value)
            status = await agent.get_status()
            agents_status[agent_type.value] = status
        except Exception as e:
            agents_status[agent_type.value] = {
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
    
    # Validate agent type
    try:
        agent_type_enum = AgentType(agent_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent type. Must be one of: {[at.value for at in AgentType]}"
        )
    
    try:
        # Execute task
        result = await process_agent_task(agent_type, request.task)
        
        return {
            "agent_type": agent_type,
            "task": request.task,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")


# Specialized Agent Endpoints

@router.post("/personal/search")
async def personal_agent_search(request: PersonalSearchRequest) -> Dict[str, Any]:
    """Perform adaptive search with the Personal Agent"""
    
    agent = await get_specialized_agent(AgentType.PERSONAL.value)
    
    result = await agent.adaptive_search(
        user_id=request.user_id,
        query=request.query,
        search_type=request.search_type
    )
    
    return result


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
    
    agent = await get_specialized_agent(AgentType.PAY_READY.value)
    
    listing = await agent.analyze_listing(
        request.listing_data,
        request.user_preferences
    )
    
    return {
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
    
    agent = await get_specialized_agent(AgentType.PAY_READY.value)
    
    result = await agent.market_analysis(location, criteria)
    
    return result


@router.post("/paragon/search-trials")
async def search_clinical_trials(request: ClinicalTrialSearchRequest) -> Dict[str, Any]:
    """Search for clinical trials with Paragon Medical Agent"""
    
    agent = await get_specialized_agent(AgentType.PARAGON_MEDICAL.value)
    
    trials = await agent.search_clinical_trials(
        conditions=request.conditions,
        phases=request.phases,
        location=request.location,
        max_distance_miles=request.max_distance_miles
    )
    
    return {
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
    
    agent = await get_specialized_agent(AgentType.PARAGON_MEDICAL.value)
    
    result = await agent.setup_trial_alert(user_id, criteria, notification_method)
    
    return result


# Workflow Management Endpoints

@router.post("/workflows")
async def create_workflow(
    request: WorkflowCreateRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Create and optionally execute a new workflow"""
    
    orchestrator = get_agent_orchestrator()
    
    try:
        workflow = await orchestrator.create_workflow(
            name=request.name,
            tasks=request.tasks,
            context=request.context
        )
        
        return {
            "workflow_id": workflow.id,
            "name": workflow.name,
            "status": workflow.status.value,
            "task_count": len(workflow.tasks),
            "created_at": workflow.created_at.isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Execute a workflow asynchronously"""
    
    orchestrator = get_agent_orchestrator()
    
    # Execute in background
    background_tasks.add_task(orchestrator.execute_workflow, workflow_id)
    
    return {
        "workflow_id": workflow_id,
        "status": "execution_started",
        "message": "Workflow execution started in background"
    }


@router.get("/workflows/{workflow_id}/status")
async def get_workflow_status(workflow_id: str) -> Dict[str, Any]:
    """Get detailed workflow execution status"""
    
    orchestrator = get_agent_orchestrator()
    
    try:
        status = await orchestrator.get_workflow_status(workflow_id)
        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/workflows/{workflow_id}/cancel")
async def cancel_workflow(workflow_id: str) -> Dict[str, Any]:
    """Cancel a running workflow"""
    
    orchestrator = get_agent_orchestrator()
    
    try:
        await orchestrator.cancel_workflow(workflow_id)
        return {
            "workflow_id": workflow_id,
            "status": "cancelled",
            "message": "Workflow cancelled successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workflows/comprehensive-search")
async def create_comprehensive_search(
    background_tasks: BackgroundTasks,
    user_id: str = Query(..., description="User ID"),
    query: str = Query(..., description="Search query"),
    include_medical: bool = Query(False, description="Include medical search")
) -> Dict[str, Any]:
    """Create and execute a comprehensive search workflow"""
    
    try:
        workflow = await create_comprehensive_search_workflow(
            user_id=user_id,
            search_query=query,
            include_medical=include_medical
        )
        
        orchestrator = get_agent_orchestrator()
        
        # Execute in background
        background_tasks.add_task(orchestrator.execute_workflow, workflow.id)
        
        return {
            "workflow_id": workflow.id,
            "name": workflow.name,
            "status": "started",
            "tasks": len(workflow.tasks),
            "message": "Comprehensive search workflow started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# System Monitoring Endpoints

@router.get("/system/metrics")
async def get_system_metrics() -> Dict[str, Any]:
    """Get overall system performance metrics"""
    
    orchestrator = get_agent_orchestrator()
    router = get_intelligent_llm_router()
    
    # Get orchestrator metrics
    orchestrator_metrics = orchestrator.metrics
    
    # Get routing analytics
    routing_analytics = await router.get_routing_analytics()
    
    return {
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
    
    health_status = {
        "status": "healthy",
        "components": {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Check LLM router
    try:
        router = get_intelligent_llm_router()
        health_status["components"]["llm_router"] = "healthy"
    except Exception as e:
        health_status["components"]["llm_router"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check orchestrator
    try:
        orchestrator = get_agent_orchestrator()
        health_status["components"]["orchestrator"] = "healthy"
    except Exception as e:
        health_status["components"]["orchestrator"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check agents
    for agent_type in AgentType:
        try:
            agent = await get_specialized_agent(agent_type.value)
            status = await agent.get_status()
            health_status["components"][f"agent_{agent_type.value}"] = status.get("status", "unknown")
        except Exception as e:
            health_status["components"][f"agent_{agent_type.value}"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
    
    return health_status