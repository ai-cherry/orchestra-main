"""
AI Operators Management System
Implements human-in-the-loop operators that manage AI agent teams
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid

from shared.database import UnifiedDatabase
from core.memory.advanced_memory_system import MemoryRouter, MemoryLayer
from core.monitoring import MetricsCollector
from core.agents.multi_agent_swarm import AgentTask, TaskStatus, TaskPriority


class OperatorRole(Enum):
    """Roles for AI operators"""
    TEAM_SUPERVISOR = "team_supervisor"
    QUALITY_CONTROLLER = "quality_controller"
    ESCALATION_HANDLER = "escalation_handler"
    STRATEGIC_PLANNER = "strategic_planner"


class OperatorPermission(Enum):
    """Permissions for AI operators"""
    VIEW_TASKS = "view_tasks"
    ASSIGN_TASKS = "assign_tasks"
    OVERRIDE_DECISIONS = "override_decisions"
    MODIFY_AGENTS = "modify_agents"
    ACCESS_SENSITIVE_DATA = "access_sensitive_data"
    APPROVE_ACTIONS = "approve_actions"
    MANAGE_TEAMS = "manage_teams"


@dataclass
class AIOperator:
    """AI Operator entity for managing agent teams"""
    operator_id: str
    name: str
    email: str
    role: OperatorRole
    permissions: Set[OperatorPermission]
    managed_domains: List[str]
    managed_teams: List[str]
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperatorAction:
    """Action taken by an operator"""
    action_id: str
    operator_id: str
    action_type: str
    target_type: str  # 'task', 'agent', 'team'
    target_id: str
    description: str
    parameters: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    result: Optional[Dict[str, Any]] = None


@dataclass
class EscalationRequest:
    """Request for operator intervention"""
    escalation_id: str
    source_agent_id: str
    task_id: str
    reason: str
    priority: TaskPriority
    context: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    assigned_operator_id: Optional[str] = None
    status: str = "pending"  # pending, assigned, resolved, dismissed


class AIOperatorManager:
    """Manages AI operators and their interactions with agent teams"""
    
    def __init__(
        self,
        db: UnifiedDatabase,
        memory_router: MemoryRouter,
        metrics: MetricsCollector
    ):
        self.db = db
        self.memory_router = memory_router
        self.metrics = metrics
        self.logger = logging.getLogger(__name__)
        
        # Operator registry
        self.operators: Dict[str, AIOperator] = {}
        
        # Escalation queue
        self.escalation_queue: List[EscalationRequest] = []
        
        # Action history
        self.action_history: List[OperatorAction] = []
        
        # Performance tracking
        self.operator_metrics = {
            "total_actions": 0,
            "avg_response_time": 0.0,
            "escalations_handled": 0,
            "success_rate": 1.0
        }
        
        # Initialize database schema
        asyncio.create_task(self._initialize_database())
    
    async def _initialize_database(self):
        """Initialize database tables for operators"""
        try:
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS ai_operators (
                    operator_id UUID PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    role VARCHAR(50) NOT NULL,
                    permissions JSONB NOT NULL DEFAULT '[]',
                    managed_domains JSONB NOT NULL DEFAULT '[]',
                    managed_teams JSONB NOT NULL DEFAULT '[]',
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    last_active TIMESTAMP NOT NULL DEFAULT NOW(),
                    metadata JSONB DEFAULT '{}'
                );
                
                CREATE INDEX IF NOT EXISTS idx_operators_email ON ai_operators(email);
                CREATE INDEX IF NOT EXISTS idx_operators_role ON ai_operators(role);
                CREATE INDEX IF NOT EXISTS idx_operators_active ON ai_operators(active);
            """)
            
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS operator_actions (
                    action_id UUID PRIMARY KEY,
                    operator_id UUID REFERENCES ai_operators(operator_id),
                    action_type VARCHAR(50) NOT NULL,
                    target_type VARCHAR(50) NOT NULL,
                    target_id VARCHAR(255) NOT NULL,
                    description TEXT,
                    parameters JSONB DEFAULT '{}',
                    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
                    result JSONB
                );
                
                CREATE INDEX IF NOT EXISTS idx_actions_operator ON operator_actions(operator_id);
                CREATE INDEX IF NOT EXISTS idx_actions_timestamp ON operator_actions(timestamp);
            """)
            
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS escalation_requests (
                    escalation_id UUID PRIMARY KEY,
                    source_agent_id VARCHAR(255) NOT NULL,
                    task_id VARCHAR(255) NOT NULL,
                    reason TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    context JSONB DEFAULT '{}',
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    assigned_operator_id UUID REFERENCES ai_operators(operator_id),
                    status VARCHAR(50) NOT NULL DEFAULT 'pending'
                );
                
                CREATE INDEX IF NOT EXISTS idx_escalations_status ON escalation_requests(status);
                CREATE INDEX IF NOT EXISTS idx_escalations_priority ON escalation_requests(priority);
            """)
            
            self.logger.info("AI Operator database schema initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize operator database: {e}")
    
    async def create_operator(
        self,
        name: str,
        email: str,
        role: OperatorRole,
        permissions: Set[OperatorPermission],
        managed_domains: List[str],
        managed_teams: List[str]
    ) -> AIOperator:
        """Create a new AI operator"""
        operator = AIOperator(
            operator_id=str(uuid.uuid4()),
            name=name,
            email=email,
            role=role,
            permissions=permissions,
            managed_domains=managed_domains,
            managed_teams=managed_teams
        )
        
        # Store in database
        await self._store_operator(operator)
        
        # Add to registry
        self.operators[operator.operator_id] = operator
        
        # Log creation
        self.logger.info(f"Created AI Operator: {name} ({email}) with role {role.value}")
        
        return operator
    
    async def _store_operator(self, operator: AIOperator):
        """Store operator in database"""
        query = """
            INSERT INTO ai_operators (
                operator_id, name, email, role, permissions,
                managed_domains, managed_teams, active,
                created_at, last_active, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (operator_id) DO UPDATE SET
                last_active = EXCLUDED.last_active,
                metadata = EXCLUDED.metadata
        """
        
        await self.db.execute(
            query,
            operator.operator_id,
            operator.name,
            operator.email,
            operator.role.value,
            json.dumps([p.value for p in operator.permissions]),
            json.dumps(operator.managed_domains),
            json.dumps(operator.managed_teams),
            operator.active,
            operator.created_at,
            operator.last_active,
            json.dumps(operator.metadata)
        )
    
    async def get_operator(self, operator_id: str) -> Optional[AIOperator]:
        """Get operator by ID"""
        if operator_id in self.operators:
            return self.operators[operator_id]
        
        # Load from database
        query = """
            SELECT * FROM ai_operators WHERE operator_id = $1
        """
        
        result = await self.db.fetchone(query, operator_id)
        if result:
            operator = self._operator_from_db_row(result)
            self.operators[operator_id] = operator
            return operator
        
        return None
    
    def _operator_from_db_row(self, row: Dict[str, Any]) -> AIOperator:
        """Convert database row to AIOperator object"""
        return AIOperator(
            operator_id=row["operator_id"],
            name=row["name"],
            email=row["email"],
            role=OperatorRole(row["role"]),
            permissions={OperatorPermission(p) for p in row["permissions"]},
            managed_domains=row["managed_domains"],
            managed_teams=row["managed_teams"],
            active=row["active"],
            created_at=row["created_at"],
            last_active=row["last_active"],
            metadata=row["metadata"]
        )
    
    async def create_escalation(
        self,
        source_agent_id: str,
        task_id: str,
        reason: str,
        priority: TaskPriority,
        context: Dict[str, Any]
    ) -> EscalationRequest:
        """Create an escalation request for operator intervention"""
        escalation = EscalationRequest(
            escalation_id=str(uuid.uuid4()),
            source_agent_id=source_agent_id,
            task_id=task_id,
            reason=reason,
            priority=priority,
            context=context
        )
        
        # Store in database
        await self._store_escalation(escalation)
        
        # Add to queue
        self.escalation_queue.append(escalation)
        
        # Sort queue by priority
        self.escalation_queue.sort(key=lambda e: e.priority.value)
        
        # Notify available operators
        await self._notify_operators(escalation)
        
        # Record metric
        self.metrics.record_counter("escalations_created", 1)
        
        return escalation
    
    async def _store_escalation(self, escalation: EscalationRequest):
        """Store escalation in database"""
        query = """
            INSERT INTO escalation_requests (
                escalation_id, source_agent_id, task_id,
                reason, priority, context, created_at,
                assigned_operator_id, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        
        await self.db.execute(
            query,
            escalation.escalation_id,
            escalation.source_agent_id,
            escalation.task_id,
            escalation.reason,
            escalation.priority.value,
            json.dumps(escalation.context),
            escalation.created_at,
            escalation.assigned_operator_id,
            escalation.status
        )
    
    async def _notify_operators(self, escalation: EscalationRequest):
        """Notify relevant operators about escalation"""
        # Find operators who can handle this escalation
        eligible_operators = []
        
        for operator in self.operators.values():
            if operator.active and self._can_handle_escalation(operator, escalation):
                eligible_operators.append(operator)
        
        # Send notifications (in production, this would use actual notification system)
        for operator in eligible_operators:
            self.logger.info(
                f"Notifying operator {operator.name} about escalation {escalation.escalation_id}"
            )
    
    def _can_handle_escalation(
        self,
        operator: AIOperator,
        escalation: EscalationRequest
    ) -> bool:
        """Check if operator can handle the escalation"""
        # Check if operator has permission
        if OperatorPermission.APPROVE_ACTIONS not in operator.permissions:
            return False
        
        # Check if escalation is from a managed domain/team
        agent_domain = escalation.context.get("domain", "")
        agent_team = escalation.context.get("team", "")
        
        return (
            agent_domain in operator.managed_domains or
            agent_team in operator.managed_teams
        )
    
    async def assign_escalation(
        self,
        escalation_id: str,
        operator_id: str
    ) -> bool:
        """Assign escalation to an operator"""
        # Find escalation
        escalation = next(
            (e for e in self.escalation_queue if e.escalation_id == escalation_id),
            None
        )
        
        if not escalation:
            return False
        
        # Verify operator exists and can handle it
        operator = await self.get_operator(operator_id)
        if not operator or not self._can_handle_escalation(operator, escalation):
            return False
        
        # Assign escalation
        escalation.assigned_operator_id = operator_id
        escalation.status = "assigned"
        
        # Update database
        await self.db.execute(
            """
            UPDATE escalation_requests
            SET assigned_operator_id = $1, status = $2
            WHERE escalation_id = $3
            """,
            operator_id,
            "assigned",
            escalation_id
        )
        
        # Update operator activity
        operator.last_active = datetime.now()
        await self._store_operator(operator)
        
        return True
    
    async def record_operator_action(
        self,
        operator_id: str,
        action_type: str,
        target_type: str,
        target_id: str,
        description: str,
        parameters: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None
    ) -> OperatorAction:
        """Record an action taken by an operator"""
        action = OperatorAction(
            action_id=str(uuid.uuid4()),
            operator_id=operator_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            description=description,
            parameters=parameters,
            result=result
        )
        
        # Store in database
        await self._store_action(action)
        
        # Add to history
        self.action_history.append(action)
        
        # Update metrics
        self.operator_metrics["total_actions"] += 1
        
        # Update operator activity
        operator = await self.get_operator(operator_id)
        if operator:
            operator.last_active = datetime.now()
            await self._store_operator(operator)
        
        return action
    
    async def _store_action(self, action: OperatorAction):
        """Store operator action in database"""
        query = """
            INSERT INTO operator_actions (
                action_id, operator_id, action_type,
                target_type, target_id, description,
                parameters, timestamp, result
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """
        
        await self.db.execute(
            query,
            action.action_id,
            action.operator_id,
            action.action_type,
            action.target_type,
            action.target_id,
            action.description,
            json.dumps(action.parameters),
            action.timestamp,
            json.dumps(action.result) if action.result else None
        )
    
    async def override_agent_decision(
        self,
        operator_id: str,
        task_id: str,
        new_decision: Dict[str, Any],
        reason: str
    ) -> Dict[str, Any]:
        """Allow operator to override an agent's decision"""
        # Verify operator has permission
        operator = await self.get_operator(operator_id)
        if not operator or OperatorPermission.OVERRIDE_DECISIONS not in operator.permissions:
            return {"error": "Operator not authorized to override decisions"}
        
        # Record the override action
        action = await self.record_operator_action(
            operator_id=operator_id,
            action_type="override_decision",
            target_type="task",
            target_id=task_id,
            description=f"Override decision: {reason}",
            parameters=new_decision
        )
        
        # Apply the override (this would integrate with task management)
        result = {
            "success": True,
            "action_id": action.action_id,
            "task_id": task_id,
            "new_decision": new_decision,
            "operator": operator.name,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update action result
        action.result = result
        await self._store_action(action)
        
        return result
    
    async def approve_sensitive_action(
        self,
        operator_id: str,
        action_request: Dict[str, Any],
        approved: bool,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """Approve or reject a sensitive action requiring human approval"""
        # Verify operator has permission
        operator = await self.get_operator(operator_id)
        if not operator or OperatorPermission.APPROVE_ACTIONS not in operator.permissions:
            return {"error": "Operator not authorized to approve actions"}
        
        # Record the approval
        action = await self.record_operator_action(
            operator_id=operator_id,
            action_type="approve_action",
            target_type="sensitive_action",
            target_id=action_request.get("request_id", ""),
            description=f"{'Approved' if approved else 'Rejected'}: {comments or 'No comments'}",
            parameters={
                "approved": approved,
                "action_request": action_request,
                "comments": comments
            }
        )
        
        result = {
            "success": True,
            "action_id": action.action_id,
            "approved": approved,
            "operator": operator.name,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update action result
        action.result = result
        await self._store_action(action)
        
        return result
    
    async def get_operator_dashboard_data(
        self,
        operator_id: str
    ) -> Dict[str, Any]:
        """Get dashboard data for an operator"""
        operator = await self.get_operator(operator_id)
        if not operator:
            return {"error": "Operator not found"}
        
        # Get pending escalations
        pending_escalations = [
            e for e in self.escalation_queue
            if e.status == "pending" and self._can_handle_escalation(operator, e)
        ]
        
        # Get assigned escalations
        assigned_escalations = [
            e for e in self.escalation_queue
            if e.assigned_operator_id == operator_id and e.status == "assigned"
        ]
        
        # Get recent actions
        recent_actions = [
            a for a in self.action_history[-20:]
            if a.operator_id == operator_id
        ]
        
        # Get team performance metrics
        team_metrics = await self._get_team_metrics(operator.managed_teams)
        
        return {
            "operator": {
                "id": operator.operator_id,
                "name": operator.name,
                "role": operator.role.value,
                "permissions": [p.value for p in operator.permissions],
                "last_active": operator.last_active.isoformat()
            },
            "escalations": {
                "pending": len(pending_escalations),
                "assigned": len(assigned_escalations),
                "details": {
                    "pending": [self._escalation_summary(e) for e in pending_escalations[:5]],
                    "assigned": [self._escalation_summary(e) for e in assigned_escalations]
                }
            },
            "recent_actions": [self._action_summary(a) for a in recent_actions],
            "team_metrics": team_metrics,
            "system_health": await self._get_system_health()
        }
    
    def _escalation_summary(self, escalation: EscalationRequest) -> Dict[str, Any]:
        """Create summary of escalation for dashboard"""
        return {
            "id": escalation.escalation_id,
            "reason": escalation.reason,
            "priority": escalation.priority.name,
            "age_minutes": (datetime.now() - escalation.created_at).total_seconds() / 60,
            "source_agent": escalation.source_agent_id,
            "context": escalation.context
        }
    
    def _action_summary(self, action: OperatorAction) -> Dict[str, Any]:
        """Create summary of action for dashboard"""
        return {
            "id": action.action_id,
            "type": action.action_type,
            "target": f"{action.target_type}:{action.target_id}",
            "description": action.description,
            "timestamp": action.timestamp.isoformat(),
            "success": action.result.get("success", True) if action.result else True
        }
    
    async def _get_team_metrics(self, team_ids: List[str]) -> Dict[str, Any]:
        """Get performance metrics for managed teams"""
        # This would integrate with the agent monitoring system
        return {
            "total_agents": 25,
            "active_agents": 22,
            "tasks_completed_today": 156,
            "average_task_time_ms": 2340,
            "success_rate": 0.94,
            "teams": {
                team_id: {
                    "agents": 5,
                    "tasks_today": 30,
                    "health": "good"
                }
                for team_id in team_ids
            }
        }
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics"""
        return {
            "status": "operational",
            "uptime_hours": 168,
            "total_operators": len(self.operators),
            "active_operators": sum(1 for op in self.operators.values() if op.active),
            "pending_escalations": len([e for e in self.escalation_queue if e.status == "pending"]),
            "system_load": 0.65
        }
    
    async def get_operator_count(self) -> int:
        """Get total number of operators"""
        return len(self.operators)
    
    async def handle_operator_login(self, email: str) -> Optional[Dict[str, Any]]:
        """Handle operator login and return operator info"""
        query = "SELECT * FROM ai_operators WHERE email = $1 AND active = TRUE"
        result = await self.db.fetchone(query, email)
        
        if result:
            operator = self._operator_from_db_row(result)
            
            # Update last active
            operator.last_active = datetime.now()
            await self._store_operator(operator)
            
            # Add to cache
            self.operators[operator.operator_id] = operator
            
            return {
                "operator_id": operator.operator_id,
                "name": operator.name,
                "role": operator.role.value,
                "permissions": [p.value for p in operator.permissions],
                "managed_domains": operator.managed_domains,
                "managed_teams": operator.managed_teams
            }
        
        return None


# Example usage for creating default operators
async def create_default_operators(manager: AIOperatorManager):
    """Create default AI operators for each domain"""
    
    # Cherry domain operator
    await manager.create_operator(
        name="Cherry Finance Supervisor",
        email="cherry.supervisor@company.com",
        role=OperatorRole.TEAM_SUPERVISOR,
        permissions={
            OperatorPermission.VIEW_TASKS,
            OperatorPermission.ASSIGN_TASKS,
            OperatorPermission.OVERRIDE_DECISIONS,
            OperatorPermission.MANAGE_TEAMS
        },
        managed_domains=["cherry"],
        managed_teams=["finance", "ranch_management"]
    )
    
    # Sophia domain operator
    await manager.create_operator(
        name="Sophia Analytics Manager",
        email="sophia.manager@company.com",
        role=OperatorRole.TEAM_SUPERVISOR,
        permissions={
            OperatorPermission.VIEW_TASKS,
            OperatorPermission.ASSIGN_TASKS,
            OperatorPermission.OVERRIDE_DECISIONS,
            OperatorPermission.MANAGE_TEAMS,
            OperatorPermission.ACCESS_SENSITIVE_DATA
        },
        managed_domains=["sophia"],
        managed_teams=["analytics"]
    )
    
    # ParagonRX domain operator
    await manager.create_operator(
        name="Karen Research Director",
        email="karen.director@company.com",
        role=OperatorRole.TEAM_SUPERVISOR,
        permissions={
            OperatorPermission.VIEW_TASKS,
            OperatorPermission.ASSIGN_TASKS,
            OperatorPermission.OVERRIDE_DECISIONS,
            OperatorPermission.MANAGE_TEAMS,
            OperatorPermission.APPROVE_ACTIONS
        },
        managed_domains=["paragon_rx"],
        managed_teams=["research"]
    )
    
    # Quality control operator (cross-domain)
    await manager.create_operator(
        name="Quality Control Specialist",
        email="qc.specialist@company.com",
        role=OperatorRole.QUALITY_CONTROLLER,
        permissions={
            OperatorPermission.VIEW_TASKS,
            OperatorPermission.OVERRIDE_DECISIONS,
            OperatorPermission.APPROVE_ACTIONS
        },
        managed_domains=["cherry", "sophia", "paragon_rx"],
        managed_teams=[]
    )