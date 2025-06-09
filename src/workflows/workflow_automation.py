"""
Workflow Automation Integration for Orchestra AI

This module implements a workflow automation system that enables Orchestra AI to automate
multi-step workflows across different systems, with connectors to common business systems,
conditional logic, and error handling capabilities.
"""

from typing import Dict, List, Optional, Any, Tuple, Set, Union, Callable
import uuid
from datetime import datetime
import json
import os
from enum import Enum
from dataclasses import dataclass, field
import logging
import importlib
import inspect
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkflowStatus(str, Enum):
    """Status of a workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class StepStatus(str, Enum):
    """Status of a workflow step execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class StepType(str, Enum):
    """Type of workflow step."""
    ACTION = "action"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    WAIT = "wait"
    CUSTOM = "custom"

class ConnectorType(str, Enum):
    """Type of external system connector."""
    API = "api"
    DATABASE = "database"
    EMAIL = "email"
    FILE_SYSTEM = "file_system"
    CRM = "crm"
    ERP = "erp"
    CUSTOM = "custom"

@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    step_type: StepType = StepType.ACTION
    action: str = ""  # Name of the action to execute
    parameters: Dict[str, Any] = field(default_factory=dict)
    next_steps: List[str] = field(default_factory=list)  # IDs of next steps
    condition: Optional[str] = None  # Condition expression for conditional steps
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 60
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "step_type": self.step_type,
            "action": self.action,
            "parameters": self.parameters,
            "next_steps": self.next_steps,
            "condition": self.condition,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowStep':
        """Create step from dictionary representation."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            step_type=data.get("step_type", StepType.ACTION),
            action=data.get("action", ""),
            parameters=data.get("parameters", {}),
            next_steps=data.get("next_steps", []),
            condition=data.get("condition"),
            status=data.get("status", StepStatus.PENDING),
            result=data.get("result"),
            error=data.get("error"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds", 60)
        )

@dataclass
class WorkflowDefinition:
    """Defines a workflow template that can be instantiated and executed."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    steps: Dict[str, WorkflowStep] = field(default_factory=dict)
    start_step_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: Set[str] = field(default_factory=set)
    author: str = "system"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow definition to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "steps": {step_id: step.to_dict() for step_id, step in self.steps.items()},
            "start_step_id": self.start_step_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tags": list(self.tags),
            "author": self.author
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowDefinition':
        """Create workflow definition from dictionary representation."""
        steps = {
            step_id: WorkflowStep.from_dict(step_data)
            for step_id, step_data in data.get("steps", {}).items()
        }
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            steps=steps,
            start_step_id=data.get("start_step_id", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            tags=set(data.get("tags", [])),
            author=data.get("author", "system")
        )
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the workflow definition."""
        errors = []
        
        # Check if start step exists
        if not self.start_step_id:
            errors.append("Start step ID is not defined")
        elif self.start_step_id not in self.steps:
            errors.append(f"Start step ID '{self.start_step_id}' does not exist in steps")
        
        # Check if all next_steps references are valid
        for step_id, step in self.steps.items():
            for next_step_id in step.next_steps:
                if next_step_id not in self.steps:
                    errors.append(f"Step '{step_id}' references non-existent next step '{next_step_id}'")
        
        # Check for cycles in the workflow
        visited = set()
        path = set()
        
        def check_cycle(current_id):
            if current_id in path:
                errors.append(f"Cycle detected in workflow: step '{current_id}' forms a loop")
                return
            
            if current_id in visited:
                return
            
            visited.add(current_id)
            path.add(current_id)
            
            current_step = self.steps.get(current_id)
            if current_step:
                for next_id in current_step.next_steps:
                    check_cycle(next_id)
            
            path.remove(current_id)
        
        if self.start_step_id:
            check_cycle(self.start_step_id)
        
        return len(errors) == 0, errors

@dataclass
class WorkflowExecution:
    """Represents an instance of a workflow being executed."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step_id: Optional[str] = None
    steps: Dict[str, WorkflowStep] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow execution to dictionary representation."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "current_step_id": self.current_step_id,
            "steps": {step_id: step.to_dict() for step_id, step in self.steps.items()},
            "context": self.context,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowExecution':
        """Create workflow execution from dictionary representation."""
        steps = {
            step_id: WorkflowStep.from_dict(step_data)
            for step_id, step_data in data.get("steps", {}).items()
        }
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            workflow_id=data.get("workflow_id", ""),
            status=data.get("status", WorkflowStatus.PENDING),
            current_step_id=data.get("current_step_id"),
            steps=steps,
            context=data.get("context", {}),
            created_at=data.get("created_at", datetime.now().isoformat()),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            error=data.get("error")
        )

class WorkflowAction:
    """Base class for workflow actions."""
    
    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Execute the action with the given parameters and context."""
        raise NotImplementedError("Subclasses must implement execute method")

class SystemAction(WorkflowAction):
    """Action for interacting with the system."""
    
    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Execute a system action."""
        action_type = parameters.get("action_type")
        
        if action_type == "log":
            level = parameters.get("level", "info").lower()
            message = parameters.get("message", "")
            
            if level == "debug":
                logger.debug(message)
            elif level == "info":
                logger.info(message)
            elif level == "warning":
                logger.warning(message)
            elif level == "error":
                logger.error(message)
            
            return {"logged": True, "message": message, "level": level}
        
        elif action_type == "set_variable":
            variable_name = parameters.get("name")
            variable_value = parameters.get("value")
            
            if variable_name:
                context[variable_name] = variable_value
                return {"set": True, "variable": variable_name, "value": variable_value}
            
            return {"set": False, "error": "Variable name not provided"}
        
        return {"error": f"Unknown system action type: {action_type}"}

class HttpAction(WorkflowAction):
    """Action for making HTTP requests."""
    
    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Execute an HTTP request."""
        import requests
        
        url = parameters.get("url")
        method = parameters.get("method", "GET").upper()
        headers = parameters.get("headers", {})
        data = parameters.get("data")
        json_data = parameters.get("json")
        timeout = parameters.get("timeout", 30)
        
        if not url:
            return {"error": "URL not provided"}
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                json=json_data,
                timeout=timeout
            )
            
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text,
                "json": response.json() if response.headers.get("content-type", "").startswith("application/json") else None
            }
        except Exception as e:
            return {"error": str(e)}

class DatabaseAction(WorkflowAction):
    """Action for interacting with databases."""
    
    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Execute a database action."""
        db_type = parameters.get("db_type", "").lower()
        action_type = parameters.get("action_type", "").lower()
        connection_string = parameters.get("connection_string")
        query = parameters.get("query")
        params = parameters.get("params", [])
        
        if not connection_string:
            return {"error": "Connection string not provided"}
        
        if not query:
            return {"error": "Query not provided"}
        
        try:
            if db_type == "sqlite":
                import sqlite3
                
                conn = sqlite3.connect(connection_string)
                cursor = conn.cursor()
                
                if action_type == "query":
                    cursor.execute(query, params)
                    columns = [col[0] for col in cursor.description] if cursor.description else []
                    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    conn.close()
                    return {"results": results, "count": len(results)}
                
                elif action_type in ["insert", "update", "delete"]:
                    cursor.execute(query, params)
                    affected_rows = cursor.rowcount
                    conn.commit()
                    conn.close()
                    return {"affected_rows": affected_rows}
                
                else:
                    conn.close()
                    return {"error": f"Unknown action type: {action_type}"}
            
            elif db_type == "postgres":
                import psycopg2
                import psycopg2.extras
                
                conn = psycopg2.connect(connection_string)
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                
                if action_type == "query":
                    cursor.execute(query, params)
                    results = [dict(row) for row in cursor.fetchall()]
                    conn.close()
                    return {"results": results, "count": len(results)}
                
                elif action_type in ["insert", "update", "delete"]:
                    cursor.execute(query, params)
                    affected_rows = cursor.rowcount
                    conn.commit()
                    conn.close()
                    return {"affected_rows": affected_rows}
                
                else:
                    conn.close()
                    return {"error": f"Unknown action type: {action_type}"}
            
            else:
                return {"error": f"Unsupported database type: {db_type}"}
        
        except Exception as e:
            return {"error": str(e)}

class EmailAction(WorkflowAction):
    """Action for sending emails."""
    
    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Send an email."""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_server = parameters.get("smtp_server")
        smtp_port = parameters.get("smtp_port", 587)
        username = parameters.get("username")
        password = parameters.get("password")
        sender = parameters.get("sender")
        recipients = parameters.get("recipients", [])
        subject = parameters.get("subject", "")
        body = parameters.get("body", "")
        html = parameters.get("html")
        
        if not smtp_server or not username or not password or not sender or not recipients:
            return {"error": "Missing required email parameters"}
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = ", ".join(recipients)
            
            # Attach plain text and HTML parts
            if body:
                msg.attach(MIMEText(body, "plain"))
            
            if html:
                msg.attach(MIMEText(html, "html"))
            elif body:  # If no HTML but we have plain text, use that
                msg.attach(MIMEText(body, "html"))
            
            # Connect to SMTP server and send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.sendmail(sender, recipients, msg.as_string())
            server.quit()
            
            return {"sent": True, "recipients": recipients}
        
        except Exception as e:
            return {"error": str(e)}

class FileSystemAction(WorkflowAction):
    """Action for interacting with the file system."""
    
    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Execute a file system action."""
        action_type = parameters.get("action_type", "").lower()
        path = parameters.get("path")
        
        if not path:
            return {"error": "Path not provided"}
        
        try:
            if action_type == "read":
                encoding = parameters.get("encoding", "utf-8")
                with open(path, "r", encoding=encoding) as f:
                    content = f.read()
                return {"content": content}
            
            elif action_type == "write":
                content = parameters.get("content", "")
                encoding = parameters.get("encoding", "utf-8")
                mode = "a" if parameters.get("append", False) else "w"
                
                with open(path, mode, encoding=encoding) as f:
                    f.write(content)
                
                return {"written": True, "path": path}
            
            elif action_type == "delete":
                if os.path.exists(path):
                    if os.path.isdir(path):
                        import shutil
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    return {"deleted": True, "path": path}
                
                return {"deleted": False, "error": f"Path does not exist: {path}"}
            
            elif action_type == "list":
                if os.path.isdir(path):
                    items = os.listdir(path)
                    return {"items": items, "count": len(items)}
                
                return {"error": f"Not a directory: {path}"}
            
            else:
                return {"error": f"Unknown action type: {action_type}"}
        
        except Exception as e:
            return {"error": str(e)}

class PersonaAction(WorkflowAction):
    """Action for interacting with AI personas."""
    
    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Execute a persona action."""
        try:
            from src.personas.persona_manager import PersonaManager
            
            persona_type = parameters.get("persona_type")
            action_type = parameters.get("action_type")
            content = parameters.get("content", "")
            
            if not persona_type:
                return {"error": "Persona type not provided"}
            
            if not action_type:
                return {"error": "Action type not provided"}
            
            # Initialize persona manager
            persona_manager = PersonaManager()
            
            if action_type == "generate_response":
                response = persona_manager.generate_response(
                    persona_type=persona_type,
                    prompt=content,
                    context=parameters.get("context", {})
                )
                
                return {"response": response}
            
            elif action_type == "analyze":
                analysis = persona_manager.analyze(
                    persona_type=persona_type,
                    content=content,
                    analysis_type=parameters.get("analysis_type", "general")
                )
                
                return {"analysis": analysis}
            
            else:
                return {"error": f"Unknown action type: {action_type}"}
        
        except ImportError:
            return {"error": "Persona manager module not found"}
        except Exception as e:
            return {"error": str(e)}

class CollaborationAction(WorkflowAction):
    """Action for interacting with the AI Persona Collaboration Framework."""
    
    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Execute a collaboration action."""
        try:
            from src.personas.collaboration_framework import (
                CollaborationManager, PersonaType, HandoffType, CollaborationMessage
            )
            
            action_type = parameters.get("action_type")
            
            if not action_type:
                return {"error": "Action type not provided"}
            
            # Initialize collaboration manager
            collaboration_manager = CollaborationManager()
            
            if action_type == "create_session":
                task_description = parameters.get("task_description")
                primary_persona = parameters.get("primary_persona")
                
                if not task_description or not primary_persona:
                    return {"error": "Missing required parameters for create_session"}
                
                session = collaboration_manager.create_session(
                    task_description=task_description,
                    primary_persona=PersonaType(primary_persona)
                )
                
                return {"session_id": session.session_id}
            
            elif action_type == "add_message":
                session_id = parameters.get("session_id")
                content = parameters.get("content")
                persona = parameters.get("persona")
                message_type = parameters.get("message_type", "contribution")
                
                if not session_id or not content or not persona:
                    return {"error": "Missing required parameters for add_message"}
                
                session = collaboration_manager.get_session(session_id)
                if not session:
                    return {"error": f"Session not found: {session_id}"}
                
                message = CollaborationMessage(
                    content=content,
                    persona=PersonaType(persona),
                    message_type=message_type,
                    references=parameters.get("references"),
                    metadata=parameters.get("metadata")
                )
                
                message_id = session.add_message(message)
                return {"message_id": message_id}
            
            elif action_type == "create_handoff":
                session_id = parameters.get("session_id")
                from_persona = parameters.get("from_persona")
                to_persona = parameters.get("to_persona")
                handoff_type = parameters.get("handoff_type")
                content = parameters.get("content")
                
                if not session_id or not from_persona or not to_persona or not handoff_type or not content:
                    return {"error": "Missing required parameters for create_handoff"}
                
                session = collaboration_manager.get_session(session_id)
                if not session:
                    return {"error": f"Session not found: {session_id}"}
                
                handoff_id = session.create_handoff(
                    from_persona=PersonaType(from_persona),
                    to_persona=PersonaType(to_persona),
                    handoff_type=HandoffType(handoff_type),
                    content=content,
                    context_keys=parameters.get("context_keys")
                )
                
                return {"handoff_id": handoff_id}
            
            else:
                return {"error": f"Unknown action type: {action_type}"}
        
        except ImportError:
            return {"error": "Collaboration framework module not found"}
        except Exception as e:
            return {"error": str(e)}

class ContextAction(WorkflowAction):
    """Action for interacting with the Adaptive Context Management system."""
    
    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Execute a context action."""
        try:
            from src.context.adaptive_context_manager import (
                AdaptiveContextManager, ContextItemType, ContextLayerType
            )
            
            action_type = parameters.get("action_type")
            
            if not action_type:
                return {"error": "Action type not provided"}
            
            # Initialize context manager
            context_manager = AdaptiveContextManager()
            
            if action_type == "add_item":
                content = parameters.get("content")
                item_type = parameters.get("item_type")
                source = parameters.get("source", "workflow")
                
                if not content or not item_type:
                    return {"error": "Missing required parameters for add_item"}
                
                item_id = context_manager.add_item(
                    content=content,
                    item_type=ContextItemType(item_type),
                    source=source,
                    layer=ContextLayerType(parameters.get("layer", "PRIMARY")),
                    metadata=parameters.get("metadata"),
                    tags=set(parameters.get("tags", [])),
                    embedding=parameters.get("embedding")
                )
                
                return {"item_id": item_id}
            
            elif action_type == "search":
                query = parameters.get("query")
                limit = parameters.get("limit", 10)
                
                if not query:
                    return {"error": "Query not provided"}
                
                items = context_manager.search_by_content(query, limit)
                return {"items": [item.to_dict() for item in items]}
            
            elif action_type == "update_relevance":
                context_manager.update_relevance_scores()
                return {"updated": True}
            
            else:
                return {"error": f"Unknown action type: {action_type}"}
        
        except ImportError:
            return {"error": "Adaptive context manager module not found"}
        except Exception as e:
            return {"error": str(e)}

class KnowledgeGraphAction(WorkflowAction):
    """Action for interacting with the Unified Knowledge Graph."""
    
    def execute(self, parameters: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Execute a knowledge graph action."""
        try:
            from src.knowledge.unified_knowledge_graph import (
                UnifiedKnowledgeGraph, NodeType, RelationType
            )
            
            action_type = parameters.get("action_type")
            
            if not action_type:
                return {"error": "Action type not provided"}
            
            # Initialize knowledge graph
            knowledge_graph = UnifiedKnowledgeGraph()
            
            if action_type == "add_node":
                name = parameters.get("name")
                node_type = parameters.get("node_type")
                
                if not name or not node_type:
                    return {"error": "Missing required parameters for add_node"}
                
                node_id = knowledge_graph.add_node(
                    name=name,
                    node_type=NodeType(node_type),
                    properties=parameters.get("properties"),
                    embedding=parameters.get("embedding"),
                    confidence=parameters.get("confidence", 1.0),
                    source=parameters.get("source", "workflow"),
                    verify=parameters.get("verify", True)
                )
                
                return {"node_id": node_id}
            
            elif action_type == "add_relation":
                source_id = parameters.get("source_id")
                target_id = parameters.get("target_id")
                relation_type = parameters.get("relation_type")
                
                if not source_id or not target_id or not relation_type:
                    return {"error": "Missing required parameters for add_relation"}
                
                relation_id = knowledge_graph.add_relation(
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=RelationType(relation_type),
                    properties=parameters.get("properties"),
                    confidence=parameters.get("confidence", 1.0),
                    source=parameters.get("source", "workflow"),
                    verify=parameters.get("verify", True)
                )
                
                return {"relation_id": relation_id}
            
            elif action_type == "search_nodes":
                query = parameters.get("query")
                limit = parameters.get("limit", 10)
                
                if not query:
                    return {"error": "Query not provided"}
                
                nodes = knowledge_graph.search_nodes(query, limit)
                return {"nodes": [node.to_dict() for node in nodes]}
            
            else:
                return {"error": f"Unknown action type: {action_type}"}
        
        except ImportError:
            return {"error": "Unified knowledge graph module not found"}
        except Exception as e:
            return {"error": str(e)}

class WorkflowEngine:
    """Executes and manages workflows."""
    
    def __init__(self, storage_dir: str = "./workflows"):
        self.storage_dir = storage_dir
        self.definitions: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.actions: Dict[str, WorkflowAction] = {
            "system": SystemAction(),
            "http": HttpAction(),
            "database": DatabaseAction(),
            "email": EmailAction(),
            "file_system": FileSystemAction(),
            "persona": PersonaAction(),
            "collaboration": CollaborationAction(),
            "context": ContextAction(),
            "knowledge_graph": KnowledgeGraphAction()
        }
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        os.makedirs(os.path.join(storage_dir, "definitions"), exist_ok=True)
        os.makedirs(os.path.join(storage_dir, "executions"), exist_ok=True)
    
    def register_action(self, name: str, action: WorkflowAction) -> None:
        """Register a custom action."""
        self.actions[name] = action
    
    def create_workflow(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        start_step_id: str,
        tags: List[str] = None,
        author: str = "system"
    ) -> str:
        """Create a new workflow definition."""
        workflow = WorkflowDefinition(
            name=name,
            description=description,
            tags=set(tags or []),
            author=author
        )
        
        # Add steps to workflow
        for step_data in steps:
            step = WorkflowStep(
                id=step_data.get("id", str(uuid.uuid4())),
                name=step_data.get("name", ""),
                description=step_data.get("description", ""),
                step_type=step_data.get("step_type", StepType.ACTION),
                action=step_data.get("action", ""),
                parameters=step_data.get("parameters", {}),
                next_steps=step_data.get("next_steps", []),
                condition=step_data.get("condition"),
                max_retries=step_data.get("max_retries", 3),
                timeout_seconds=step_data.get("timeout_seconds", 60)
            )
            workflow.steps[step.id] = step
        
        workflow.start_step_id = start_step_id
        
        # Validate workflow
        is_valid, errors = workflow.validate()
        if not is_valid:
            raise ValueError(f"Invalid workflow definition: {', '.join(errors)}")
        
        # Save workflow
        self.definitions[workflow.id] = workflow
        self._save_workflow_definition(workflow)
        
        return workflow.id
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by ID."""
        if workflow_id in self.definitions:
            return self.definitions[workflow_id]
        
        # Try to load from storage
        try:
            return self._load_workflow_definition(workflow_id)
        except:
            return None
    
    def list_workflows(self, tags: List[str] = None) -> List[Dict[str, Any]]:
        """List all workflow definitions, optionally filtered by tags."""
        # Load all workflow definitions from storage
        self._load_all_workflow_definitions()
        
        if tags:
            tag_set = set(tags)
            filtered_workflows = [
                {
                    "id": wf.id,
                    "name": wf.name,
                    "description": wf.description,
                    "version": wf.version,
                    "tags": list(wf.tags),
                    "created_at": wf.created_at,
                    "updated_at": wf.updated_at,
                    "author": wf.author
                }
                for wf in self.definitions.values()
                if tag_set.intersection(wf.tags)
            ]
            return filtered_workflows
        
        return [
            {
                "id": wf.id,
                "name": wf.name,
                "description": wf.description,
                "version": wf.version,
                "tags": list(wf.tags),
                "created_at": wf.created_at,
                "updated_at": wf.updated_at,
                "author": wf.author
            }
            for wf in self.definitions.values()
        ]
    
    def execute_workflow(
        self,
        workflow_id: str,
        context: Dict[str, Any] = None
    ) -> str:
        """Start a new workflow execution."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Create a new execution instance
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            steps={step_id: WorkflowStep(**step.to_dict()) for step_id, step in workflow.steps.items()},
            context=context or {},
            current_step_id=workflow.start_step_id
        )
        
        # Save execution
        self.executions[execution.id] = execution
        self._save_workflow_execution(execution)
        
        # Start execution
        self._run_workflow(execution.id)
        
        return execution.id
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID."""
        if execution_id in self.executions:
            return self.executions[execution_id]
        
        # Try to load from storage
        try:
            return self._load_workflow_execution(execution_id)
        except:
            return None
    
    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None
    ) -> List[Dict[str, Any]]:
        """List all workflow executions, optionally filtered by workflow ID and status."""
        # Load all executions from storage
        self._load_all_workflow_executions()
        
        filtered_executions = self.executions.values()
        
        if workflow_id:
            filtered_executions = [
                execution for execution in filtered_executions
                if execution.workflow_id == workflow_id
            ]
        
        if status:
            filtered_executions = [
                execution for execution in filtered_executions
                if execution.status == status
            ]
        
        return [
            {
                "id": execution.id,
                "workflow_id": execution.workflow_id,
                "status": execution.status,
                "created_at": execution.created_at,
                "started_at": execution.started_at,
                "completed_at": execution.completed_at,
                "error": execution.error
            }
            for execution in filtered_executions
        ]
    
    def pause_execution(self, execution_id: str) -> bool:
        """Pause a running workflow execution."""
        execution = self.get_execution(execution_id)
        if not execution:
            return False
        
        if execution.status == WorkflowStatus.RUNNING:
            execution.status = WorkflowStatus.PAUSED
            self._save_workflow_execution(execution)
            return True
        
        return False
    
    def resume_execution(self, execution_id: str) -> bool:
        """Resume a paused workflow execution."""
        execution = self.get_execution(execution_id)
        if not execution:
            return False
        
        if execution.status == WorkflowStatus.PAUSED:
            execution.status = WorkflowStatus.RUNNING
            self._save_workflow_execution(execution)
            self._run_workflow(execution_id)
            return True
        
        return False
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a workflow execution."""
        execution = self.get_execution(execution_id)
        if not execution:
            return False
        
        if execution.status in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED, WorkflowStatus.PENDING]:
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.now().isoformat()
            self._save_workflow_execution(execution)
            return True
        
        return False
    
    def _run_workflow(self, execution_id: str) -> None:
        """Run a workflow execution."""
        execution = self.get_execution(execution_id)
        if not execution:
            logger.error(f"Execution not found: {execution_id}")
            return
        
        # Skip if not in a runnable state
        if execution.status not in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]:
            return
        
        # Update status to running
        if execution.status == WorkflowStatus.PENDING:
            execution.status = WorkflowStatus.RUNNING
            execution.started_at = datetime.now().isoformat()
            self._save_workflow_execution(execution)
        
        # Execute steps until completion or failure
        try:
            # Track if any step has failed
            workflow_failed = False
            
            while execution.status == WorkflowStatus.RUNNING and execution.current_step_id:
                current_step = execution.steps.get(execution.current_step_id)
                if not current_step:
                    raise ValueError(f"Step not found: {execution.current_step_id}")
                
                # Skip if step is already completed
                if current_step.status == StepStatus.COMPLETED:
                    # Move to next step
                    execution.current_step_id = self._get_next_step_id(execution, current_step)
                    self._save_workflow_execution(execution)
                    continue
                
                # Check if step has failed and no more retries
                if current_step.status == StepStatus.FAILED and current_step.retry_count >= current_step.max_retries:
                    # Mark workflow as failed and stop execution
                    workflow_failed = True
                    execution.status = WorkflowStatus.FAILED
                    execution.error = f"Step '{current_step.id}' failed: {current_step.error}"
                    execution.completed_at = datetime.now().isoformat()
                    self._save_workflow_execution(execution)
                    break
                
                # Execute step
                self._execute_step(execution, current_step)
                
                # Check if step failed
                if current_step.status == StepStatus.FAILED:
                    if current_step.retry_count >= current_step.max_retries:
                        # Mark workflow as failed and stop execution
                        workflow_failed = True
                        execution.status = WorkflowStatus.FAILED
                        execution.error = f"Step '{current_step.id}' failed: {current_step.error}"
                        execution.completed_at = datetime.now().isoformat()
                        self._save_workflow_execution(execution)
                        break
                
                # Check if workflow is still running (might have been paused or cancelled)
                execution = self.get_execution(execution_id)
                if execution.status != WorkflowStatus.RUNNING:
                    break
                
                # Move to next step
                execution.current_step_id = self._get_next_step_id(execution, current_step)
                self._save_workflow_execution(execution)
            
            # Check if workflow is complete
            if execution.status == WorkflowStatus.RUNNING:
                if workflow_failed:
                    # If any step failed, mark workflow as failed
                    execution.status = WorkflowStatus.FAILED
                    if not execution.error:
                        execution.error = "One or more steps failed during execution"
                elif not execution.current_step_id:
                    # If no more steps, mark workflow as completed
                    execution.status = WorkflowStatus.COMPLETED
                
                execution.completed_at = datetime.now().isoformat()
                self._save_workflow_execution(execution)
        
        except Exception as e:
            logger.error(f"Error executing workflow: {str(e)}")
            logger.error(traceback.format_exc())
            
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.now().isoformat()
            self._save_workflow_execution(execution)
    
    def _execute_step(self, execution: WorkflowExecution, step: WorkflowStep) -> None:
        """Execute a workflow step."""
        # Update step status
        step.status = StepStatus.RUNNING
        step.start_time = datetime.now().isoformat()
        self._save_workflow_execution(execution)
        
        try:
            # Handle different step types
            if step.step_type == StepType.CONDITION:
                self._execute_condition_step(execution, step)
            elif step.step_type == StepType.LOOP:
                self._execute_loop_step(execution, step)
            elif step.step_type == StepType.PARALLEL:
                self._execute_parallel_step(execution, step)
            elif step.step_type == StepType.WAIT:
                self._execute_wait_step(execution, step)
            else:  # ACTION or CUSTOM
                self._execute_action_step(execution, step)
            
            # Update step status
            step.status = StepStatus.COMPLETED
            step.end_time = datetime.now().isoformat()
            self._save_workflow_execution(execution)
        
        except Exception as e:
            logger.error(f"Error executing step {step.id}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Update step status
            step.status = StepStatus.FAILED
            step.error = str(e)
            step.end_time = datetime.now().isoformat()
            
            # Check if retry is possible
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                step.status = StepStatus.PENDING
                logger.info(f"Retrying step {step.id} (attempt {step.retry_count} of {step.max_retries})")
            
            self._save_workflow_execution(execution)
            
            # If step failed and no more retries, mark all remaining steps as skipped
            if step.status == StepStatus.FAILED and step.retry_count >= step.max_retries:
                # Mark all subsequent steps as skipped
                for next_step_id in self._get_all_subsequent_steps(execution, step.id):
                    next_step = execution.steps.get(next_step_id)
                    if next_step and next_step.status == StepStatus.PENDING:
                        next_step.status = StepStatus.SKIPPED
                
                self._save_workflow_execution(execution)
    
    def _get_all_subsequent_steps(self, execution: WorkflowExecution, step_id: str) -> List[str]:
        """Get all steps that follow the given step in the workflow."""
        visited = set()
        result = []
        
        def dfs(current_id):
            if current_id in visited:
                return
            
            visited.add(current_id)
            current_step = execution.steps.get(current_id)
            
            if current_step:
                for next_id in current_step.next_steps:
                    result.append(next_id)
                    dfs(next_id)
        
        dfs(step_id)
        return result
    
    def _execute_action_step(self, execution: WorkflowExecution, step: WorkflowStep) -> None:
        """Execute an action step."""
        action_name = step.action.split(".")[0] if "." in step.action else step.action
        action_method = step.action.split(".")[1] if "." in step.action else "execute"
        
        # Get action handler
        action_handler = self.actions.get(action_name)
        if not action_handler:
            # Try to dynamically import custom action
            try:
                module_path, class_name = action_name.rsplit(".", 1)
                module = importlib.import_module(module_path)
                action_class = getattr(module, class_name)
                action_handler = action_class()
            except (ImportError, AttributeError) as e:
                raise ValueError(f"Action not found: {action_name}")
        
        # Execute action
        if action_method == "execute" or not hasattr(action_handler, action_method):
            result = action_handler.execute(step.parameters, execution.context)
        else:
            method = getattr(action_handler, action_method)
            result = method(step.parameters, execution.context)
        
        # Store result
        step.result = result
        
        # Check for error in result
        if isinstance(result, dict) and "error" in result:
            raise ValueError(result["error"])
    
    def _execute_condition_step(self, execution: WorkflowExecution, step: WorkflowStep) -> None:
        """Execute a condition step."""
        if not step.condition:
            raise ValueError("Condition expression not provided")
        
        # Evaluate condition
        try:
            # Create a safe evaluation environment
            eval_globals = {"__builtins__": {}}
            eval_locals = {**execution.context}
            
            # Add safe functions
            eval_locals.update({
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "set": set,
                "min": min,
                "max": max,
                "sum": sum,
                "any": any,
                "all": all
            })
            
            # Evaluate condition
            result = eval(step.condition, eval_globals, eval_locals)
            step.result = {"condition": step.condition, "result": result}
            
            # Update next steps based on condition result
            if not result and len(step.next_steps) > 1:
                # If condition is false and there are multiple next steps,
                # skip the first one (true branch) and use the second one (false branch)
                step.next_steps = step.next_steps[1:]
            elif not result:
                # If condition is false and there's only one next step,
                # skip it by clearing next steps
                step.next_steps = []
            elif len(step.next_steps) > 1:
                # If condition is true and there are multiple next steps,
                # use only the first one (true branch)
                step.next_steps = [step.next_steps[0]]
        
        except Exception as e:
            raise ValueError(f"Error evaluating condition: {str(e)}")
    
    def _execute_loop_step(self, execution: WorkflowExecution, step: WorkflowStep) -> None:
        """Execute a loop step."""
        # Get loop parameters
        loop_type = step.parameters.get("loop_type", "for")
        loop_variable = step.parameters.get("variable", "item")
        
        if loop_type == "for":
            # For loop over a collection
            collection = step.parameters.get("collection")
            if not collection:
                # Try to get collection from context
                collection_name = step.parameters.get("collection_name")
                if not collection_name or collection_name not in execution.context:
                    raise ValueError("Loop collection not provided")
                collection = execution.context[collection_name]
            
            # Store current loop index and item in context
            current_index = step.parameters.get("current_index", 0)
            
            if current_index >= len(collection):
                # Loop complete
                step.result = {"iterations": current_index}
                return
            
            # Set loop variable in context
            execution.context[loop_variable] = collection[current_index]
            execution.context[f"{loop_variable}_index"] = current_index
            
            # Update parameters for next iteration
            step.parameters["current_index"] = current_index + 1
            
            # Modify next steps to loop back to this step
            if step.id not in step.next_steps:
                step.next_steps.append(step.id)
        
        elif loop_type == "while":
            # While loop with a condition
            condition = step.parameters.get("condition")
            if not condition:
                raise ValueError("Loop condition not provided")
            
            # Evaluate condition
            try:
                # Create a safe evaluation environment
                eval_globals = {"__builtins__": {}}
                eval_locals = {**execution.context}
                
                # Add safe functions
                eval_locals.update({
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "set": set,
                    "min": min,
                    "max": max,
                    "sum": sum,
                    "any": any,
                    "all": all
                })
                
                # Evaluate condition
                result = eval(condition, eval_globals, eval_locals)
                
                # Update iteration count
                current_iterations = step.parameters.get("iterations", 0)
                step.parameters["iterations"] = current_iterations + 1
                
                if not result:
                    # Condition is false, exit loop
                    step.result = {"iterations": current_iterations}
                    step.next_steps = [s for s in step.next_steps if s != step.id]
                    return
                
                # Condition is true, continue loop
                if step.id not in step.next_steps:
                    step.next_steps.append(step.id)
            
            except Exception as e:
                raise ValueError(f"Error evaluating loop condition: {str(e)}")
        
        else:
            raise ValueError(f"Unknown loop type: {loop_type}")
    
    def _execute_parallel_step(self, execution: WorkflowExecution, step: WorkflowStep) -> None:
        """Execute a parallel step."""
        # This is a simplified implementation that doesn't actually run steps in parallel
        # In a real implementation, you would use threading or async/await
        
        parallel_steps = step.parameters.get("steps", [])
        if not parallel_steps:
            raise ValueError("No parallel steps provided")
        
        results = []
        
        for parallel_step_id in parallel_steps:
            parallel_step = execution.steps.get(parallel_step_id)
            if not parallel_step:
                raise ValueError(f"Parallel step not found: {parallel_step_id}")
            
            # Execute parallel step
            self._execute_step(execution, parallel_step)
            
            # Collect result
            results.append({
                "step_id": parallel_step_id,
                "status": parallel_step.status,
                "result": parallel_step.result,
                "error": parallel_step.error
            })
        
        # Store results
        step.result = {"parallel_results": results}
    
    def _execute_wait_step(self, execution: WorkflowExecution, step: WorkflowStep) -> None:
        """Execute a wait step."""
        import time
        
        # Get wait parameters
        wait_seconds = step.parameters.get("seconds", 0)
        wait_until = step.parameters.get("until")
        
        if wait_until:
            # Wait until a specific time
            try:
                target_time = datetime.fromisoformat(wait_until)
                now = datetime.now()
                
                if target_time > now:
                    wait_seconds = (target_time - now).total_seconds()
                else:
                    # Target time is in the past, no need to wait
                    wait_seconds = 0
            
            except ValueError:
                raise ValueError(f"Invalid wait_until format: {wait_until}")
        
        # Wait for the specified duration
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        
        # Store result
        step.result = {"waited_seconds": wait_seconds}
    
    def _get_next_step_id(self, execution: WorkflowExecution, current_step: WorkflowStep) -> Optional[str]:
        """Get the ID of the next step to execute."""
        if not current_step.next_steps:
            return None
        
        return current_step.next_steps[0]
    
    def _save_workflow_definition(self, workflow: WorkflowDefinition) -> None:
        """Save a workflow definition to storage."""
        filepath = os.path.join(self.storage_dir, "definitions", f"{workflow.id}.json")
        with open(filepath, "w") as f:
            json.dump(workflow.to_dict(), f, indent=2)
    
    def _load_workflow_definition(self, workflow_id: str) -> WorkflowDefinition:
        """Load a workflow definition from storage."""
        filepath = os.path.join(self.storage_dir, "definitions", f"{workflow_id}.json")
        with open(filepath, "r") as f:
            data = json.load(f)
        
        workflow = WorkflowDefinition.from_dict(data)
        self.definitions[workflow.id] = workflow
        return workflow
    
    def _load_all_workflow_definitions(self) -> None:
        """Load all workflow definitions from storage."""
        definitions_dir = os.path.join(self.storage_dir, "definitions")
        for filename in os.listdir(definitions_dir):
            if filename.endswith(".json"):
                workflow_id = filename[:-5]  # Remove .json extension
                if workflow_id not in self.definitions:
                    try:
                        self._load_workflow_definition(workflow_id)
                    except Exception as e:
                        logger.error(f"Error loading workflow definition {workflow_id}: {str(e)}")
    
    def _save_workflow_execution(self, execution: WorkflowExecution) -> None:
        """Save a workflow execution to storage."""
        filepath = os.path.join(self.storage_dir, "executions", f"{execution.id}.json")
        with open(filepath, "w") as f:
            json.dump(execution.to_dict(), f, indent=2)
    
    def _load_workflow_execution(self, execution_id: str) -> WorkflowExecution:
        """Load a workflow execution from storage."""
        filepath = os.path.join(self.storage_dir, "executions", f"{execution_id}.json")
        with open(filepath, "r") as f:
            data = json.load(f)
        
        execution = WorkflowExecution.from_dict(data)
        self.executions[execution.id] = execution
        return execution
    
    def _load_all_workflow_executions(self) -> None:
        """Load all workflow executions from storage."""
        executions_dir = os.path.join(self.storage_dir, "executions")
        for filename in os.listdir(executions_dir):
            if filename.endswith(".json"):
                execution_id = filename[:-5]  # Remove .json extension
                if execution_id not in self.executions:
                    try:
                        self._load_workflow_execution(execution_id)
                    except Exception as e:
                        logger.error(f"Error loading workflow execution {execution_id}: {str(e)}")
