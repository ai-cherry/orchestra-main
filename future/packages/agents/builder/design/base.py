"""
Base classes for the AI Design Guild agents.

This module contains the base classes and interfaces for the Design Guild agents,
defining the common functionality and protocols for design-focused agent roles.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import logging

from orchestrator.agents.agent_base import Agent

logger = logging.getLogger(__name__)


class DesignRoleType(Enum):
    """Enum defining the roles within the Design Guild structure."""

    PLANNER = "planner"
    DOER = "doer"
    REVIEWER = "reviewer"
    META_BUILDER = "meta_builder"


class DesignAgentCapabilities(Enum):
    """Capabilities that may be implemented by Design Guild agents."""

    UX_BRIEF = "ux_brief"
    WIREFRAMING = "wireframing"
    MOODBOARDING = "moodboarding"
    DIAGRAMS = "diagrams"
    PIXEL_ART = "pixel_art"
    ACCESSIBILITY = "accessibility"
    HEURISTIC_CRITIQUE = "heuristic_critique"
    HEATMAP_ANALYSIS = "heatmap_analysis"
    DESIGN_SYSTEM = "design_system"


class DesignBaseAgent(Agent, ABC):
    """Base class for all Design Guild agents."""

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: Optional[str] = None,
        role_type: DesignRoleType = None,
        capabilities: List[DesignAgentCapabilities] = None,
    ):
        """
        Initialize a Design Guild agent.

        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name
            description: Optional description of the agent's purpose
            role_type: The role this agent fulfills in the Design Guild
            capabilities: List of design capabilities this agent implements
        """
        super().__init__(agent_id, name, description)
        self.role_type = role_type
        self.capabilities = capabilities or []

    def to_data(self) -> Dict[str, Any]:
        """
        Convert this agent to a data model for serialization.

        Returns:
            A dictionary representing this agent
        """
        data = super().to_data()
        data.capabilities = [cap.value for cap in self.capabilities]
        data.config["role_type"] = self.role_type.value if self.role_type else None
        return data

    @abstractmethod
    async def process_design_task(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a design-related task and return the results.

        Args:
            task_input: Input data for the design task

        Returns:
            The processed design output
        """
        pass


class DesignPlannerAgent(DesignBaseAgent):
    """
    Agent responsible for planning and coordinating design work.
    Converts high-level design requests into structured tasks for doer agents.
    """

    def __init__(self, agent_id: str, name: str, description: Optional[str] = None):
        """Initialize a Design Planner agent."""
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description
            or "Coordinates design processes and translates requirements into actionable tasks",
            role_type=DesignRoleType.PLANNER,
            capabilities=[DesignAgentCapabilities.UX_BRIEF],
        )

    async def process(self, input_text: str, context: Dict[str, Any] = None) -> str:
        """Process a user input to create a design plan."""
        context = context or {}

        # Extract active persona if available to influence design brief style
        active_persona = context.get("active_persona", {})

        # Create structured design brief from free-text input
        logger.info(f"Design Planner creating brief for: {input_text[:50]}...")

        # In a real implementation, this would use the LLM to generate a detailed design brief
        # and create a structured plan for the doer agents

        # For now, return a simple acknowledgment
        return f"Design brief created for: {input_text}. Ready to coordinate design workflow with appropriate doer agents."

    async def process_design_task(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a design planning task.

        Args:
            task_input: Input containing the design request

        Returns:
            Structured design brief and task assignments
        """
        # This would generate a full design brief with:
        # - User requirements analysis
        # - Design goals and constraints
        # - Task breakdown for doer agents
        # - Success criteria for reviewers

        # Return a placeholder for now
        return {
            "brief": {
                "title": task_input.get("title", "Untitled Design Project"),
                "description": task_input.get("description", ""),
                "goals": [],
                "constraints": [],
                "target_audience": [],
            },
            "tasks": [],
            "success_criteria": [],
        }


class DesignDoerAgent(DesignBaseAgent):
    """
    Agent responsible for executing specific design tasks.
    Implements specialized design capabilities like wireframing, moodboarding, etc.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: Optional[str] = None,
        capabilities: List[DesignAgentCapabilities] = None,
    ):
        """Initialize a Design Doer agent with specific capabilities."""
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description
            or "Executes specific design tasks based on the design brief",
            role_type=DesignRoleType.DOER,
            capabilities=capabilities or [],
        )

    async def process(self, input_text: str, context: Dict[str, Any] = None) -> str:
        """Process a design task based on input text."""
        context = context or {}

        # Extract design brief and task details
        design_brief = context.get("design_brief", {})
        task_type = context.get("task_type", "")

        # Check if we can handle this task type
        capability_map = {
            "wireframe": DesignAgentCapabilities.WIREFRAMING,
            "moodboard": DesignAgentCapabilities.MOODBOARDING,
            "diagram": DesignAgentCapabilities.DIAGRAMS,
            "pixel_art": DesignAgentCapabilities.PIXEL_ART,
        }

        required_capability = capability_map.get(task_type)
        if required_capability and required_capability not in self.capabilities:
            return f"I don't have the capability to handle {task_type} tasks."

        logger.info(f"Design Doer processing {task_type} task: {input_text[:50]}...")

        # In a real implementation, this would use the specific tools and APIs
        # to generate the requested design artifacts

        return f"Processed {task_type} design task based on the brief."

    async def process_design_task(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a specific design task.

        Args:
            task_input: Input containing the task details and design brief

        Returns:
            Design artifacts produced by this agent
        """
        # This would use the appropriate API/tool for the given capability
        # and generate specific design artifacts

        # For now, return a placeholder
        return {
            "task_type": task_input.get("task_type", "unknown"),
            "artifacts": [],
            "metadata": {"status": "placeholder"},
        }


class DesignReviewerAgent(DesignBaseAgent):
    """
    Agent responsible for reviewing and providing feedback on design work.
    Implements specialized evaluation capabilities like accessibility audits,
    heuristic critique, etc.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: Optional[str] = None,
        capabilities: List[DesignAgentCapabilities] = None,
    ):
        """Initialize a Design Reviewer agent with specific capabilities."""
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description
            or "Reviews design artifacts and provides expert feedback",
            role_type=DesignRoleType.REVIEWER,
            capabilities=capabilities or [],
        )

    async def process(self, input_text: str, context: Dict[str, Any] = None) -> str:
        """Process a design review task based on input text."""
        context = context or {}

        # Extract design artifacts and evaluation criteria
        design_artifacts = context.get("artifacts", [])
        evaluation_type = context.get("evaluation_type", "")

        # Check if we can handle this evaluation type
        capability_map = {
            "accessibility": DesignAgentCapabilities.ACCESSIBILITY,
            "heuristic": DesignAgentCapabilities.HEURISTIC_CRITIQUE,
            "heatmap": DesignAgentCapabilities.HEATMAP_ANALYSIS,
        }

        required_capability = capability_map.get(evaluation_type)
        if required_capability and required_capability not in self.capabilities:
            return (
                f"I don't have the capability to perform {evaluation_type} evaluations."
            )

        logger.info(f"Design Reviewer performing {evaluation_type} review")

        # In a real implementation, this would analyze the design artifacts
        # using the appropriate evaluation methods

        return f"Completed {evaluation_type} review of the provided design artifacts."

    async def process_design_task(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a design review task.

        Args:
            task_input: Input containing the artifacts to review and criteria

        Returns:
            Review results and feedback
        """
        # This would perform the appropriate analysis based on the capability
        # and generate detailed feedback

        # For now, return a placeholder
        return {
            "review_type": task_input.get("review_type", "unknown"),
            "feedback": [],
            "score": 0.0,
            "recommendations": [],
        }


class DesignMetaBuilderAgent(DesignBaseAgent):
    """
    Agent responsible for consolidating design outputs and preparing handoff.
    Transforms various design artifacts into structured deliverables for human designers.
    """

    def __init__(self, agent_id: str, name: str, description: Optional[str] = None):
        """Initialize a Design Meta-Builder agent."""
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description
            or "Consolidates design artifacts and prepares handoff materials",
            role_type=DesignRoleType.META_BUILDER,
            capabilities=[DesignAgentCapabilities.DESIGN_SYSTEM],
        )

    async def process(self, input_text: str, context: Dict[str, Any] = None) -> str:
        """Process a design consolidation task based on input text."""
        context = context or {}

        # Extract all design artifacts
        design_artifacts = context.get("artifacts", [])
        feedback = context.get("feedback", [])

        logger.info(
            f"Design Meta-Builder consolidating {len(design_artifacts)} artifacts"
        )

        # In a real implementation, this would organize and format all the
        # design outputs for handoff to human designers

        return "Design artifacts consolidated and prepared for handoff."

    async def process_design_task(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a design consolidation task.

        Args:
            task_input: Input containing all design artifacts and feedback

        Returns:
            Consolidated design package ready for handoff
        """
        # This would organize all artifacts, apply feedback revisions,
        # and create a coherent design package

        # For now, return a placeholder
        return {
            "project_title": task_input.get("project_title", "Untitled Project"),
            "consolidated_artifacts": [],
            "design_system": {},
            "handoff_materials": [],
        }
