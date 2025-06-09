"""
Integration with existing Orchestra AI systems.

This module implements the integration points between the workflow automation system
and other Orchestra AI components like personas, context management, knowledge graph,
and adaptive learning.
"""

from typing import Dict, List, Optional, Any, Union, Type
import logging
from .models import WorkflowStep, WorkflowInstance, WorkflowDefinition
from .engine import WorkflowEngine, StepExecutor

# Import from other Orchestra AI modules
from personas.collaboration_framework import (
    CollaborationManager, 
    CollaborationSession,
    PersonaType,
    CollaborationRole,
    HandoffType,
    CollaborationMessage
)
from context.adaptive_context_manager import (
    AdaptiveContextManager,
    ContextItem,
    ContextItemType,
    ContextLayerType
)
from knowledge.unified_knowledge_graph import (
    UnifiedKnowledgeGraph,
    NodeType,
    RelationType
)
from learning.adaptive_learning_system import (
    AdaptiveLearningSystem,
    FeedbackType,
    MetricCategory
)

logger = logging.getLogger(__name__)


class PersonaWorkflowConnector:
    """Connects workflows with the persona collaboration framework."""
    
    def __init__(
        self,
        workflow_engine: WorkflowEngine,
        collaboration_manager: CollaborationManager
    ):
        """Initialize the persona workflow connector."""
        self.workflow_engine = workflow_engine
        self.collaboration_manager = collaboration_manager
        self.workflow_sessions: Dict[str, str] = {}  # Maps workflow_instance_id to session_id
    
    async def handle_persona_workflow_request(
        self,
        session_id: str,
        persona_id: PersonaType,
        workflow_id: str,
        input_data: Dict[str, Any]
    ) -> str:
        """Handle a workflow request from a persona."""
        # Get the collaboration session
        session = self.collaboration_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Collaboration session not found: {session_id}")
        
        # Start the workflow
        instance_id = await self.workflow_engine.start_workflow(
            workflow_id=workflow_id,
            input_data=input_data,
            context={"session_id": session_id, "persona_id": persona_id},
            created_by=f"persona:{persona_id}"
        )
        
        # Associate the workflow with the session
        self.workflow_sessions[instance_id] = session_id
        
        # Add a message to the collaboration session
        session.add_message(CollaborationMessage(
            content=f"Started workflow: {workflow_id}",
            persona=persona_id,
            message_type="workflow_start",
            metadata={
                "workflow_id": workflow_id,
                "instance_id": instance_id
            }
        ))
        
        return instance_id
    
    async def send_workflow_update_to_persona(
        self,
        workflow_instance_id: str,
        update_type: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """Send a workflow status update to a persona."""
        # Get the associated session
        session_id = self.workflow_sessions.get(workflow_instance_id)
        if not session_id:
            logger.warning(f"No collaboration session found for workflow: {workflow_instance_id}")
            return False
        
        session = self.collaboration_manager.get_session(session_id)
        if not session:
            logger.warning(f"Collaboration session not found: {session_id}")
            return False
        
        # Determine which persona should receive the update
        # For now, send to the primary persona
        persona_id = session.primary_persona
        
        # Create an appropriate message based on update type
        if update_type == "completed":
            message = CollaborationMessage(
                content=f"Workflow completed successfully",
                persona=PersonaType.CHERRY,  # System message
                message_type="workflow_update",
                metadata={
                    "update_type": update_type,
                    "instance_id": workflow_instance_id,
                    "output_data": update_data.get("output_data", {})
                }
            )
        elif update_type == "failed":
            message = CollaborationMessage(
                content=f"Workflow failed: {update_data.get('error', {}).get('error', 'Unknown error')}",
                persona=PersonaType.CHERRY,  # System message
                message_type="workflow_update",
                metadata={
                    "update_type": update_type,
                    "instance_id": workflow_instance_id,
                    "error": update_data.get("error", {})
                }
            )
        elif update_type == "step_completed":
            step_id = update_data.get("step_id", "unknown")
            message = CollaborationMessage(
                content=f"Workflow step completed: {step_id}",
                persona=PersonaType.CHERRY,  # System message
                message_type="workflow_update",
                metadata={
                    "update_type": update_type,
                    "instance_id": workflow_instance_id,
                    "step_id": step_id,
                    "output_data": update_data.get("output_data", {})
                }
            )
        else:
            message = CollaborationMessage(
                content=f"Workflow update: {update_type}",
                persona=PersonaType.CHERRY,  # System message
                message_type="workflow_update",
                metadata={
                    "update_type": update_type,
                    "instance_id": workflow_instance_id,
                    "data": update_data
                }
            )
        
        # Add the message to the session
        session.add_message(message)
        
        # If this is a completion or failure, clean up the association
        if update_type in ["completed", "failed", "cancelled"]:
            del self.workflow_sessions[workflow_instance_id]
        
        return True
    
    async def register_event_handlers(self) -> None:
        """Register event handlers for workflow events."""
        # In a real implementation, this would use the event bus
        # to subscribe to workflow events
        pass


class ContextAwareStepExecutor(StepExecutor):
    """Step executor that can access and update the context system."""
    
    def __init__(self, context_manager: AdaptiveContextManager):
        """Initialize the context-aware step executor."""
        self.context_manager = context_manager
    
    async def execute(
        self,
        step: WorkflowStep,
        input_data: Dict[str, Any],
        workflow_instance: WorkflowInstance
    ) -> Dict[str, Any]:
        """Execute a workflow step with context awareness."""
        # Get relevant context
        context_items = self._get_relevant_context(step, input_data)
        
        # Add context to input data
        input_data_with_context = input_data.copy()
        input_data_with_context["context"] = context_items
        
        # Execute step logic
        result = await self._execute_with_context(step, input_data_with_context)
        
        # Update context with results if needed
        if step.parameters.get("update_context", False):
            self._update_context_with_results(step, result)
        
        return result
    
    def _get_relevant_context(
        self,
        step: WorkflowStep,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get relevant context items for this step."""
        context_items = {}
        
        # Get context tags from step parameters
        context_tags = step.parameters.get("context_tags", [])
        if context_tags:
            items = self.context_manager.get_items_by_tags(set(context_tags))
            for item in items:
                context_items[item.id] = {
                    "content": item.content,
                    "type": item.item_type,
                    "tags": list(item.tags)
                }
        
        # Get context by type if specified
        context_types = step.parameters.get("context_types", [])
        for context_type in context_types:
            try:
                item_type = ContextItemType(context_type)
                items = self.context_manager.get_items_by_type(item_type)
                for item in items:
                    context_items[item.id] = {
                        "content": item.content,
                        "type": item.item_type,
                        "tags": list(item.tags)
                    }
            except ValueError:
                logger.warning(f"Invalid context type: {context_type}")
        
        return context_items
    
    async def _execute_with_context(
        self,
        step: WorkflowStep,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the step logic with context."""
        # This is a placeholder implementation
        # In a real system, this would use the context to inform the step execution
        
        # For now, just return a simple result
        return {
            "status": "success",
            "message": "Step executed with context",
            "context_item_count": len(input_data.get("context", {}))
        }
    
    def _update_context_with_results(
        self,
        step: WorkflowStep,
        result: Dict[str, Any]
    ) -> None:
        """Update the context system with step results."""
        # Check if we should update context
        context_updates = step.parameters.get("context_updates", [])
        
        for update in context_updates:
            content = update.get("content")
            if not content:
                # Try to get content from result
                content_path = update.get("content_path")
                if content_path:
                    parts = content_path.split(".")
                    content_value = result
                    try:
                        for part in parts:
                            content_value = content_value[part]
                        content = str(content_value)
                    except (KeyError, TypeError):
                        logger.warning(f"Could not find content at path: {content_path}")
                        continue
            
            if not content:
                continue
            
            # Add the item to context
            self.context_manager.add_item(
                content=content,
                item_type=ContextItemType(update.get("type", "FACT")),
                source=f"workflow:{step.id}",
                layer=ContextLayerType(update.get("layer", "PRIMARY")),
                tags=set(update.get("tags", [])),
                metadata=update.get("metadata", {})
            )


class KnowledgeGraphStepExecutor(StepExecutor):
    """Step executor that interacts with the knowledge graph."""
    
    def __init__(self, knowledge_graph: UnifiedKnowledgeGraph):
        """Initialize the knowledge graph step executor."""
        self.knowledge_graph = knowledge_graph
    
    async def execute(
        self,
        step: WorkflowStep,
        input_data: Dict[str, Any],
        workflow_instance: WorkflowInstance
    ) -> Dict[str, Any]:
        """Execute a workflow step with knowledge graph integration."""
        operation = step.parameters.get("operation")
        if not operation:
            raise ValueError(f"No operation specified for knowledge graph step: {step.id}")
        
        if operation == "query":
            return await self._query_knowledge(step, input_data)
        elif operation == "add_nodes":
            return await self._add_nodes(step, input_data)
        elif operation == "add_relations":
            return await self._add_relations(step, input_data)
        else:
            raise ValueError(f"Unsupported knowledge graph operation: {operation}")
    
    async def _query_knowledge(
        self,
        step: WorkflowStep,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Query the knowledge graph."""
        query_params = step.parameters.get("query_params", {})
        
        # Get query type
        query_type = query_params.get("type", "search")
        
        if query_type == "search":
            # Search for nodes by name or properties
            query = query_params.get("query", "")
            limit = query_params.get("limit", 10)
            
            nodes = self.knowledge_graph.search_nodes(query, limit)
            
            return {
                "status": "success",
                "node_count": len(nodes),
                "nodes": [node.to_dict() for node in nodes]
            }
        
        elif query_type == "get_by_type":
            # Get nodes by type
            node_type_str = query_params.get("node_type")
            try:
                node_type = NodeType(node_type_str)
                nodes = self.knowledge_graph.get_nodes_by_type(node_type)
                
                return {
                    "status": "success",
                    "node_count": len(nodes),
                    "nodes": [node.to_dict() for node in nodes]
                }
            except ValueError:
                return {
                    "status": "error",
                    "error": f"Invalid node type: {node_type_str}"
                }
        
        elif query_type == "path":
            # Find path between nodes
            start_node_id = query_params.get("start_node_id")
            end_node_id = query_params.get("end_node_id")
            max_depth = query_params.get("max_depth", 3)
            
            if not start_node_id or not end_node_id:
                return {
                    "status": "error",
                    "error": "Both start_node_id and end_node_id are required"
                }
            
            paths = self.knowledge_graph.find_path(start_node_id, end_node_id, max_depth)
            
            return {
                "status": "success",
                "path_count": len(paths),
                "paths": paths
            }
        
        else:
            return {
                "status": "error",
                "error": f"Unsupported query type: {query_type}"
            }
    
    async def _add_nodes(
        self,
        step: WorkflowStep,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add nodes to the knowledge graph."""
        nodes_data = step.parameters.get("nodes", [])
        added_nodes = []
        
        for node_data in nodes_data:
            name = node_data.get("name")
            node_type_str = node_data.get("node_type")
            properties = node_data.get("properties", {})
            
            if not name or not node_type_str:
                continue
            
            try:
                node_type = NodeType(node_type_str)
                node_id = self.knowledge_graph.add_node(
                    name=name,
                    node_type=node_type,
                    properties=properties,
                    source=f"workflow:{step.id}"
                )
                
                if node_id:
                    added_nodes.append(node_id)
            except ValueError:
                logger.warning(f"Invalid node type: {node_type_str}")
        
        return {
            "status": "success",
            "added_count": len(added_nodes),
            "added_nodes": added_nodes
        }
    
    async def _add_relations(
        self,
        step: WorkflowStep,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add relations to the knowledge graph."""
        relations_data = step.parameters.get("relations", [])
        added_relations = []
        
        for relation_data in relations_data:
            source_id = relation_data.get("source_id")
            target_id = relation_data.get("target_id")
            relation_type_str = relation_data.get("relation_type")
            properties = relation_data.get("properties", {})
            
            if not source_id or not target_id or not relation_type_str:
                continue
            
            try:
                relation_type = RelationType(relation_type_str)
                relation_id = self.knowledge_graph.add_relation(
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=relation_type,
                    properties=properties,
                    source=f"workflow:{step.id}"
                )
                
                if relation_id:
                    added_relations.append(relation_id)
            except ValueError:
                logger.warning(f"Invalid relation type: {relation_type_str}")
        
        return {
            "status": "success",
            "added_count": len(added_relations),
            "added_relations": added_relations
        }


class LearningEnabledWorkflowExecutor:
    """Wrapper for workflow execution with learning capabilities."""
    
    def __init__(
        self,
        workflow_engine: WorkflowEngine,
        learning_system: AdaptiveLearningSystem
    ):
        """Initialize the learning-enabled workflow executor."""
        self.workflow_engine = workflow_engine
        self.learning_system = learning_system
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        created_by: Optional[str] = None
    ) -> str:
        """Execute a workflow with learning capabilities."""
        # Get adaptation parameters
        adaptation_params = self._get_adaptation_parameters(workflow_id, input_data, context)
        
        # Apply adaptations to input data
        adapted_input = self._apply_adaptations(input_data or {}, adaptation_params)
        
        # Start the workflow
        start_time = datetime.now()
        instance_id = await self.workflow_engine.start_workflow(
            workflow_id=workflow_id,
            input_data=adapted_input,
            context=context,
            created_by=created_by
        )
        
        # Register completion handler to collect metrics
        # In a real implementation, this would use the event bus
        
        return instance_id
    
    def _get_adaptation_parameters(
        self,
        workflow_id: str,
        input_data: Dict[str, Any] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get adaptation parameters from the learning system."""
        # In a real implementation, this would query the learning system
        # for adaptation parameters based on the workflow and context
        
        # For now, return empty parameters
        return {}
    
    def _apply_adaptations(
        self,
        input_data: Dict[str, Any],
        adaptation_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply adaptations to the input data."""
        # In a real implementation, this would modify the input data
        # based on the adaptation parameters
        
        # For now, just return the original input data
        return input_data
    
    async def record_workflow_completion(
        self,
        instance_id: str,
        success: bool,
        output_data: Dict[str, Any] = None,
        error: Dict[str, Any] = None,
        execution_time: float = 0
    ) -> None:
        """Record metrics about the workflow execution."""
        # Collect feedback based on execution result
        feedback_type = FeedbackType.IMPLICIT_POSITIVE if success else FeedbackType.IMPLICIT_NEGATIVE
        
        metrics = {
            MetricCategory.EFFICIENCY: 1.0 if success else 0.0
        }
        
        if execution_time > 0:
            # Calculate efficiency based on execution time
            # This is a simplified example
            efficiency = min(1.0, 10.0 / execution_time) if execution_time > 0 else 1.0
            metrics[MetricCategory.EFFICIENCY] = efficiency
        
        # Record the feedback
        self.learning_system.collect_feedback(
            feedback_type=feedback_type,
            content=f"Workflow execution: {instance_id}",
            metrics=metrics,
            metadata={
                "workflow_instance_id": instance_id,
                "execution_time": execution_time,
                "success": success,
                "error": error
            }
        )


class WorkflowIntegrationManager:
    """Manages integration between workflow automation and other Orchestra AI systems."""
    
    def __init__(
        self,
        workflow_engine: WorkflowEngine,
        collaboration_manager: CollaborationManager = None,
        context_manager: AdaptiveContextManager = None,
        knowledge_graph: UnifiedKnowledgeGraph = None,
        learning_system: AdaptiveLearningSystem = None
    ):
        """Initialize the workflow integration manager."""
        self.workflow_engine = workflow_engine
        self.collaboration_manager = collaboration_manager
        self.context_manager = context_manager
        self.knowledge_graph = knowledge_graph
        self.learning_system = learning_system
        
        # Initialize integration components
        self.persona_connector = None
        if collaboration_manager:
            self.persona_connector = PersonaWorkflowConnector(
                workflow_engine=workflow_engine,
                collaboration_manager=collaboration_manager
            )
        
        # Register specialized step executors
        if context_manager:
            self.workflow_engine.register_step_executor(
                "context_operation",
                ContextAwareStepExecutor(context_manager)
            )
        
        if knowledge_graph:
            self.workflow_engine.register_step_executor(
                "knowledge_graph_operation",
                KnowledgeGraphStepExecutor(knowledge_graph)
            )
        
        # Create learning-enabled workflow executor
        self.learning_executor = None
        if learning_system:
            self.learning_executor = LearningEnabledWorkflowExecutor(
                workflow_engine=workflow_engine,
                learning_system=learning_system
            )
    
    async def register_event_handlers(self) -> None:
        """Register event handlers for workflow events."""
        if self.persona_connector:
            await self.persona_connector.register_event_handlers()
    
    async def execute_workflow_from_persona(
        self,
        session_id: str,
        persona_id: PersonaType,
        workflow_id: str,
        input_data: Dict[str, Any]
    ) -> str:
        """Execute a workflow requested by a persona."""
        if not self.persona_connector:
            raise ValueError("Persona integration is not available")
        
        return await self.persona_connector.handle_persona_workflow_request(
            session_id=session_id,
            persona_id=persona_id,
            workflow_id=workflow_id,
            input_data=input_data
        )
    
    async def execute_workflow_with_learning(
        self,
        workflow_id: str,
        input_data: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        created_by: Optional[str] = None
    ) -> str:
        """Execute a workflow with learning capabilities."""
        if not self.learning_executor:
            raise ValueError("Learning integration is not available")
        
        return await self.learning_executor.execute_workflow(
            workflow_id=workflow_id,
            input_data=input_data,
            context=context,
            created_by=created_by
        )
