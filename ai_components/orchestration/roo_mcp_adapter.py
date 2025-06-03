"""Roo MCP Adapter for wrapping Roo modes as MCP-compatible agents."""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx
from pydantic import BaseModel, Field

from shared.database import UnifiedDatabase
from shared.utils.error_handling import handle_errors
from shared.utils.performance import benchmark

logger = logging.getLogger(__name__)


class RooMode(str, Enum):
    """Available Roo modes."""

    CODE = "code"
    ARCHITECT = "architect"
    ASK = "ask"
    DEBUG = "debug"
    ORCHESTRATOR = "orchestrator"
    STRATEGY = "strategy"
    RESEARCH = "research"
    ANALYTICS = "analytics"
    IMPLEMENTATION = "implementation"
    QUALITY = "quality"
    DOCUMENTATION = "documentation"


class AgentCapability(BaseModel):
    """MCP-compatible agent capability."""

    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    performance_metrics: Dict[str, float] = Field(default_factory=dict)


class RooContext(BaseModel):
    """Roo-specific context format."""

    mode: RooMode
    task: str
    history: List[Dict[str, Any]] = Field(default_factory=list)
    files: List[str] = Field(default_factory=list)
    environment: Dict[str, Any] = Field(default_factory=dict)
    custom_instructions: Optional[str] = None


class MCPContext(BaseModel):
    """MCP-compatible context format."""

    agent_id: str
    task_id: str
    messages: List[Dict[str, str]] = Field(default_factory=list)
    resources: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class RooModeConfig:
    """Configuration for a Roo mode."""

    mode: RooMode
    model: str
    role: str
    capabilities: List[str]
    file_patterns: Optional[List[str]] = None
    max_tokens: int = 4096
    temperature: float = 0.7


class RooMCPAdapter:
    """Adapter for wrapping Roo modes as MCP-compatible agents."""

    def __init__(self, openrouter_api_key: str):
        """Initialize the adapter.

        Args:
            openrouter_api_key: API key for OpenRouter
        """
        if not openrouter_api_key:
            raise ValueError("OpenRouter API key is required")
        
        self.api_key = openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        self.mode_configs = self._initialize_mode_configs()
        self.active_sessions: Dict[str, RooContext] = {}
        self._capability_cache: Dict[RooMode, List[AgentCapability]] = {}
        
        # Log API key info without exposing it
        masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}" if len(self.api_key) > 12 else "***"
        logger.info(f"RooMCPAdapter initialized with API key: {masked_key}")

    def _initialize_mode_configs(self) -> Dict[RooMode, RooModeConfig]:
        """Initialize configurations for all Roo modes."""
        return {
            RooMode.CODE: RooModeConfig(
                mode=RooMode.CODE,
                model="anthropic/claude-opus-4",
                role="Expert Python/TypeScript developer",
                capabilities=[
                    "code_generation",
                    "code_review",
                    "refactoring",
                    "debugging",
                    "testing",
                ],
                file_patterns=["*.py", "*.ts", "*.js", "*.tsx", "*.jsx"],
            ),
            RooMode.ARCHITECT: RooModeConfig(
                mode=RooMode.ARCHITECT,
                model="anthropic/claude-opus-4",
                role="AI architect for modular systems",
                capabilities=[
                    "system_design",
                    "architecture_review",
                    "component_design",
                    "integration_planning",
                ],
                file_patterns=["*.md"],
            ),
            RooMode.ASK: RooModeConfig(
                mode=RooMode.ASK,
                model="anthropic/claude-3.5-sonnet",
                role="Technical assistant",
                capabilities=["question_answering", "explanation", "guidance"],
            ),
            RooMode.DEBUG: RooModeConfig(
                mode=RooMode.DEBUG,
                model="anthropic/claude-opus-4",
                role="Systematic debugger",
                capabilities=[
                    "error_analysis",
                    "root_cause_analysis",
                    "fix_suggestion",
                    "testing",
                ],
            ),
            RooMode.ORCHESTRATOR: RooModeConfig(
                mode=RooMode.ORCHESTRATOR,
                model="anthropic/claude-opus-4",
                role="AI workflow orchestrator",
                capabilities=[
                    "task_decomposition",
                    "agent_coordination",
                    "context_management",
                    "workflow_optimization",
                ],
            ),
            RooMode.STRATEGY: RooModeConfig(
                mode=RooMode.STRATEGY,
                model="anthropic/claude-opus-4",
                role="Technical strategist",
                capabilities=[
                    "technology_selection",
                    "optimization_planning",
                    "risk_assessment",
                    "roadmap_creation",
                ],
            ),
            RooMode.RESEARCH: RooModeConfig(
                mode=RooMode.RESEARCH,
                model="anthropic/claude-3.5-sonnet",
                role="AI research assistant",
                capabilities=[
                    "best_practices_research",
                    "benchmarking",
                    "solution_exploration",
                    "documentation_analysis",
                ],
            ),
            RooMode.ANALYTICS: RooModeConfig(
                mode=RooMode.ANALYTICS,
                model="anthropic/claude-3.5-sonnet",
                role="Data analysis expert",
                capabilities=[
                    "metrics_analysis",
                    "performance_monitoring",
                    "reporting",
                    "visualization",
                ],
            ),
            RooMode.IMPLEMENTATION: RooModeConfig(
                mode=RooMode.IMPLEMENTATION,
                model="anthropic/claude-opus-4",
                role="Operations implementation expert",
                capabilities=[
                    "deployment",
                    "process_execution",
                    "infrastructure_as_code",
                    "automation",
                ],
            ),
            RooMode.QUALITY: RooModeConfig(
                mode=RooMode.QUALITY,
                model="anthropic/claude-3.5-sonnet",
                role="Quality assurance specialist",
                capabilities=[
                    "validation",
                    "performance_verification",
                    "compliance_checking",
                    "test_automation",
                ],
            ),
            RooMode.DOCUMENTATION: RooModeConfig(
                mode=RooMode.DOCUMENTATION,
                model="anthropic/claude-3.5-sonnet",
                role="Knowledge management specialist",
                capabilities=[
                    "documentation_generation",
                    "process_documentation",
                    "standard_maintenance",
                    "knowledge_organization",
                ],
            ),
        }

    @benchmark
    async def wrap_mode_as_agent(
        self, mode: RooMode
    ) -> Tuple[str, List[AgentCapability]]:
        """Wrap a Roo mode as an MCP-compatible agent.

        Args:
            mode: The Roo mode to wrap

        Returns:
            Tuple of (agent_id, capabilities)
        """
        if mode in self._capability_cache:
            agent_id = f"roo_{mode.value}_agent"
            return agent_id, self._capability_cache[mode]

        config = self.mode_configs.get(mode)
        if not config:
            raise ValueError(f"Unknown Roo mode: {mode}")

        agent_id = f"roo_{mode.value}_agent"
        capabilities = []

        for cap_name in config.capabilities:
            capability = AgentCapability(
                name=cap_name,
                description=f"{cap_name.replace('_', ' ').title()} capability for {mode.value} mode",
                input_schema={
                    "type": "object",
                    "properties": {
                        "task": {"type": "string"},
                        "context": {"type": "object"},
                        "files": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["task"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "result": {"type": "string"},
                        "artifacts": {"type": "array"},
                        "next_steps": {"type": "array"},
                    },
                },
            )
            capabilities.append(capability)

        self._capability_cache[mode] = capabilities
        return agent_id, capabilities

    @handle_errors
    async def transform_context(
        self, source_format: str, target_format: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform context between Roo and MCP formats.

        Args:
            source_format: Source format ('roo' or 'mcp')
            target_format: Target format ('roo' or 'mcp')
            context: Context to transform

        Returns:
            Transformed context
        """
        if source_format == target_format:
            return context

        if source_format == "roo" and target_format == "mcp":
            roo_ctx = RooContext(**context)
            return MCPContext(
                agent_id=f"roo_{roo_ctx.mode.value}_agent",
                task_id=f"task_{datetime.utcnow().timestamp()}",
                messages=[
                    {"role": "user", "content": roo_ctx.task},
                    *[
                        {"role": msg.get("role", "assistant"), "content": msg.get("content", "")}
                        for msg in roo_ctx.history
                    ],
                ],
                resources=[{"type": "file", "path": f} for f in roo_ctx.files],
                metadata={
                    "mode": roo_ctx.mode.value,
                    "environment": roo_ctx.environment,
                    "custom_instructions": roo_ctx.custom_instructions,
                },
            ).dict()

        elif source_format == "mcp" and target_format == "roo":
            mcp_ctx = MCPContext(**context)
            mode_str = mcp_ctx.metadata.get("mode", "code")
            return RooContext(
                mode=RooMode(mode_str),
                task=mcp_ctx.messages[0]["content"] if mcp_ctx.messages else "",
                history=[
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in mcp_ctx.messages[1:]
                ],
                files=[r["path"] for r in mcp_ctx.resources if r["type"] == "file"],
                environment=mcp_ctx.metadata.get("environment", {}),
                custom_instructions=mcp_ctx.metadata.get("custom_instructions"),
            ).dict()

        raise ValueError(f"Unsupported transformation: {source_format} -> {target_format}")

    @benchmark
    async def execute_mode_task(
        self, mode: RooMode, task: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a task using a specific Roo mode.

        Args:
            mode: The Roo mode to use
            task: Task description
            context: Optional context

        Returns:
            Execution result
        """
        config = self.mode_configs.get(mode)
        if not config:
            raise ValueError(f"Unknown Roo mode: {mode}")

        # Prepare the request
        messages = [
            {
                "role": "system",
                "content": f"You are {config.role}. {context.get('custom_instructions', '') if context else ''}",
            },
            {"role": "user", "content": task},
        ]

        if context and "history" in context:
            messages.extend(context["history"])

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/orchestra-ai",
                    "X-Title": "Orchestra AI Integration",
                },
                json={
                    "model": config.model,
                    "messages": messages,
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                },
            )
            response.raise_for_status()

            result = response.json()
            
            # Validate response structure
            if "choices" not in result or not result["choices"]:
                raise ValueError("Invalid API response: missing choices")
                
            completion = result["choices"][0]["message"]["content"]

            # Store in database
            async with UnifiedDatabase() as db:
                await db.execute(
                    """
                    INSERT INTO roo_mode_executions 
                    (mode, task, context, result, created_at)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    mode.value,
                    task,
                    json.dumps(context or {}),
                    completion,
                    datetime.utcnow(),
                )

            return {
                "result": completion,
                "mode": mode.value,
                "model": config.model,
                "artifacts": [],
                "next_steps": [],
            }

        except Exception as e:
            logger.error(f"Error executing mode task: {e}")
            raise

    async def get_mode_capabilities(self, mode: RooMode) -> List[Dict[str, Any]]:
        """Get capabilities for a specific mode.

        Args:
            mode: The Roo mode

        Returns:
            List of capability definitions
        """
        _, capabilities = await self.wrap_mode_as_agent(mode)
        return [cap.dict() for cap in capabilities]

    async def create_session(self, mode: RooMode, task: str) -> str:
        """Create a new Roo session.

        Args:
            mode: The Roo mode
            task: Initial task

        Returns:
            Session ID
        """
        session_id = f"session_{datetime.utcnow().timestamp()}"
        self.active_sessions[session_id] = RooContext(mode=mode, task=task)
        return session_id

    async def update_session(
        self, session_id: str, message: Dict[str, str]
    ) -> None:
        """Update an existing session.

        Args:
            session_id: Session ID
            message: Message to add
        """
        if session_id in self.active_sessions:
            self.active_sessions[session_id].history.append(message)

    async def close_session(self, session_id: str) -> None:
        """Close a session.

        Args:
            session_id: Session ID to close
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

    async def close(self) -> None:
        """Close the adapter and clean up resources."""
        await self.client.aclose()