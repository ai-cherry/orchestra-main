"""
API endpoints for the workflow automation system.

This module implements the FastAPI endpoints for managing workflows,
including creating, starting, monitoring, and controlling workflow executions.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import asyncio
import logging
from .models import WorkflowDefinition, WorkflowStatus
from .engine import WorkflowEngine, WorkflowStorageManager, EventBus
from .connectors import ConnectorRegistry
from .integration import WorkflowIntegrationManager

# Create router
router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# Logger
logger = logging.getLogger(__name__)


# Dependency to get workflow engine
async def get_workflow_engine():
    # In a real application, this would be properly initialized and stored
    # For now, we'll create a new instance each time (not ideal for production)
    storage_manager = WorkflowStorageManager()
    event_bus = EventBus()
    engine = WorkflowEngine(storage_manager, event_bus)
    return engine


# Dependency to get workflow integration manager
async def get_integration_manager(workflow_engine: WorkflowEngine = Depends(get_workflow_engine)):
    # In a real application, this would be properly initialized with all systems
    integration_manager = WorkflowIntegrationManager(workflow_engine)
    return integration_manager


@router.post("/definitions", response_model=Dict[str, Any])
async def create_workflow_definition(
    definition: Dict[str, Any],
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """Create a new workflow definition."""
    try:
        # Convert to WorkflowDefinition object
        workflow_def = WorkflowDefinition(
            id=definition.get("id"),
            name=definition.get("name"),
            description=definition.get("description"),
            version=definition.get("version", "1.0.0")
            # Other fields would be properly converted here
        )
        
        # Save the definition
        await workflow_engine.storage_manager.save_definition(workflow_def)
        
        return {
            "status": "success",
            "message": f"Workflow definition created: {workflow_def.id}",
            "definition_id": workflow_def.id
        }
    except Exception as e:
        logger.exception(f"Error creating workflow definition: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/definitions", response_model=List[Dict[str, Any]])
async def list_workflow_definitions(
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """List all workflow definitions."""
    try:
        definitions = await workflow_engine.storage_manager.list_definitions()
        return [
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "version": d.version,
                "created_at": d.created_at,
                "updated_at": d.updated_at
            }
            for d in definitions
        ]
    except Exception as e:
        logger.exception(f"Error listing workflow definitions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/definitions/{definition_id}", response_model=Dict[str, Any])
async def get_workflow_definition(
    definition_id: str,
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """Get a workflow definition by ID."""
    try:
        definition = await workflow_engine.storage_manager.get_definition(definition_id)
        if not definition:
            raise HTTPException(status_code=404, detail=f"Workflow definition not found: {definition_id}")
        
        # Convert to dictionary
        return {
            "id": definition.id,
            "name": definition.name,
            "description": definition.description,
            "version": definition.version,
            "steps": [
                {
                    "id": step.id,
                    "type": step.type,
                    "parameters": step.parameters,
                    "depends_on": step.depends_on
                }
                for step in definition.steps
            ],
            "triggers": [
                {
                    "id": trigger.id,
                    "type": trigger.type,
                    "configuration": trigger.configuration
                }
                for trigger in definition.triggers
            ],
            "variables": definition.variables,
            "created_at": definition.created_at,
            "updated_at": definition.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting workflow definition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instances", response_model=Dict[str, Any])
async def start_workflow(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """Start a workflow execution."""
    try:
        workflow_id = request.get("workflow_id")
        if not workflow_id:
            raise HTTPException(status_code=400, detail="workflow_id is required")
        
        input_data = request.get("input_data", {})
        context = request.get("context", {})
        created_by = request.get("created_by")
        
        # Start the workflow in the background
        instance_id = await workflow_engine.start_workflow(
            workflow_id=workflow_id,
            input_data=input_data,
            context=context,
            created_by=created_by
        )
        
        return {
            "status": "success",
            "message": f"Workflow started: {instance_id}",
            "instance_id": instance_id
        }
    except Exception as e:
        logger.exception(f"Error starting workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instances", response_model=List[Dict[str, Any]])
async def list_workflow_instances(
    workflow_id: Optional[str] = None,
    status: Optional[str] = None,
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """List workflow instances with optional filtering."""
    try:
        # Convert status string to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = WorkflowStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        instances = await workflow_engine.storage_manager.list_instances(
            workflow_id=workflow_id,
            status=status_enum
        )
        
        return [instance.to_dict() for instance in instances]
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error listing workflow instances: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instances/{instance_id}", response_model=Dict[str, Any])
async def get_workflow_instance(
    instance_id: str,
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """Get a workflow instance by ID."""
    try:
        instance = await workflow_engine.storage_manager.get_instance(instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail=f"Workflow instance not found: {instance_id}")
        
        return instance.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting workflow instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instances/{instance_id}/cancel", response_model=Dict[str, Any])
async def cancel_workflow(
    instance_id: str,
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """Cancel a workflow execution."""
    try:
        success = await workflow_engine.cancel_workflow(instance_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Could not cancel workflow: {instance_id}")
        
        return {
            "status": "success",
            "message": f"Workflow cancelled: {instance_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error cancelling workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instances/{instance_id}/pause", response_model=Dict[str, Any])
async def pause_workflow(
    instance_id: str,
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """Pause a workflow execution."""
    try:
        success = await workflow_engine.pause_workflow(instance_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Could not pause workflow: {instance_id}")
        
        return {
            "status": "success",
            "message": f"Workflow paused: {instance_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error pausing workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instances/{instance_id}/resume", response_model=Dict[str, Any])
async def resume_workflow(
    instance_id: str,
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """Resume a paused workflow execution."""
    try:
        success = await workflow_engine.resume_workflow(instance_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Could not resume workflow: {instance_id}")
        
        return {
            "status": "success",
            "message": f"Workflow resumed: {instance_id}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error resuming workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/persona-workflow", response_model=Dict[str, Any])
async def execute_workflow_from_persona(
    request: Dict[str, Any],
    integration_manager: WorkflowIntegrationManager = Depends(get_integration_manager)
):
    """Execute a workflow requested by a persona."""
    try:
        session_id = request.get("session_id")
        persona_id = request.get("persona_id")
        workflow_id = request.get("workflow_id")
        input_data = request.get("input_data", {})
        
        if not session_id or not persona_id or not workflow_id:
            raise HTTPException(status_code=400, detail="session_id, persona_id, and workflow_id are required")
        
        instance_id = await integration_manager.execute_workflow_from_persona(
            session_id=session_id,
            persona_id=persona_id,
            workflow_id=workflow_id,
            input_data=input_data
        )
        
        return {
            "status": "success",
            "message": f"Workflow started from persona: {instance_id}",
            "instance_id": instance_id
        }
    except Exception as e:
        logger.exception(f"Error executing workflow from persona: {e}")
        raise HTTPException(status_code=500, detail=str(e))
