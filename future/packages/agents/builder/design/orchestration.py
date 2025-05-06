"""
DEPRECATED: This file is deprecated and will be removed in a future release.

This legacy file has been replaced by a newer implementation with improved architecture 
and error handling. Please consult the project documentation for the recommended 
replacement module.

Example migration:
from orchestration import * # Old
# Change to:
# Import the appropriate replacement module
"""

"""
Design Guild Orchestration.

This module implements the orchestration layer for the AI Design Guild,
coordinating the workflow between planner, doer, reviewer, and meta-builder agents.
It handles the state management, transitions, and data flow between agents.
"""

import logging
import asyncio
import json
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4

from packages.agents.builder.design.base import (
    DesignBaseAgent,
    DesignRoleType,
    DesignAgentCapabilities,
)

logger = logging.getLogger(__name__)


class DesignProjectStatus(Enum):
    """Status values for tracking design project progress."""

    INITIATED = "initiated"
    PLANNING = "planning"
    EXECUTION = "execution"
    REVIEW = "review"
    CONSOLIDATION = "consolidation"
    COMPLETE = "complete"
    FAILED = "failed"


class DesignTask:
    """
    Represents a design task assigned to a specific agent.
    Tracks task progress, input/output data, and status.
    """

    def __init__(
        self,
        task_id: str,
        agent_id: str,
        task_type: str,
        input_data: Dict[str, Any],
        capability_required: Optional[DesignAgentCapabilities] = None,
    ):
        """
        Initialize a design task.

        Args:
            task_id: Unique identifier for this task
            agent_id: ID of the agent assigned to this task
            task_type: Type of task (e.g., "wireframe", "accessibility_audit")
            input_data: Input data required for the task
            capability_required: Specific capability needed for this task
        """
        self.task_id = task_id
        self.agent_id = agent_id
        self.task_type = task_type
        self.input_data = input_data
        self.capability_required = capability_required
        self.output_data = None
        self.status = "pending"
        self.created_at = None  # Would be set to current timestamp
        self.updated_at = None  # Would be updated whenever the task changes
        self.error = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "task_type": self.task_type,
            "status": self.status,
            "capability_required": (
                self.capability_required.value if self.capability_required else None
            ),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def update_status(self, status: str) -> None:
        """Update the task status."""
        self.status = status
        self.updated_at = None  # Would be set to current timestamp

    def complete(self, output_data: Dict[str, Any]) -> None:
        """Mark the task as complete with output data."""
        self.output_data = output_data
        self.update_status("completed")

    def fail(self, error: str) -> None:
        """Mark the task as failed with error details."""
        self.error = error
        self.update_status("failed")


class DesignOrchestrator:
    """
    Orchestrates the AI Design Guild workflow.

    Manages the state machine for design projects, dispatches tasks to appropriate agents,
    tracks progress, and handles the flow of data between planner, doer, reviewer, and meta-builder agents.
    """

    def __init__(self):
        """Initialize the Design Orchestrator."""
        self.agents: Dict[str, DesignBaseAgent] = {}
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, DesignTask] = {}

        # Registry of agent capabilities
        self.capability_registry: Dict[DesignAgentCapabilities, List[str]] = {
            cap: [] for cap in DesignAgentCapabilities
        }

        # Map role types to agent IDs
        self.role_registry: Dict[DesignRoleType, List[str]] = {
            role: [] for role in DesignRoleType
        }

        logger.info("Design Orchestrator initialized")

    def register_agent(self, agent: DesignBaseAgent) -> None:
        """
        Register a Design Guild agent with the orchestrator.

        Args:
            agent: The agent to register
        """
        agent_id = agent.id
        self.agents[agent_id] = agent

        # Register capabilities
        for capability in agent.capabilities:
            if capability in self.capability_registry:
                self.capability_registry[capability].append(agent_id)

        # Register role
        if agent.role_type:
            self.role_registry[agent.role_type].append(agent_id)

        logger.info(f"Registered agent: {agent.name} (ID: {agent_id})")

    def create_project(self, title: str, description: str, user_id: str) -> str:
        """
        Create a new design project.

        Args:
            title: Project title
            description: Project description
            user_id: ID of the user creating the project

        Returns:
            The project ID
        """
        project_id = str(uuid4())

        # Create initial project state
        self.projects[project_id] = {
            "project_id": project_id,
            "title": title,
            "description": description,
            "user_id": user_id,
            "status": DesignProjectStatus.INITIATED.value,
            "created_at": None,  # Would be set to current timestamp
            "updated_at": None,  # Would be set to current timestamp
            "tasks": [],
            "artifacts": {},
            "active_persona": None,  # Would be populated from context
        }

        logger.info(f"Created design project: {title} (ID: {project_id})")
        return project_id

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get a project by ID.

        Args:
            project_id: The project ID

        Returns:
            The project data

        Raises:
            KeyError: If project not found
        """
        if project_id not in self.projects:
            raise KeyError(f"Project not found: {project_id}")

        return self.projects[project_id]

    def update_project_status(
        self, project_id: str, status: DesignProjectStatus
    ) -> None:
        """
        Update a project's status.

        Args:
            project_id: The project ID
            status: The new status

        Raises:
            KeyError: If project not found
        """
        if project_id not in self.projects:
            raise KeyError(f"Project not found: {project_id}")

        self.projects[project_id]["status"] = status.value
        self.projects[project_id][
            "updated_at"
        ] = None  # Would be set to current timestamp

        logger.info(f"Updated project {project_id} status to {status.value}")

    def create_task(
        self,
        project_id: str,
        task_type: str,
        input_data: Dict[str, Any],
        capability_required: Optional[DesignAgentCapabilities] = None,
    ) -> str:
        """
        Create a new design task for a project.

        Args:
            project_id: The project ID
            task_type: Type of task
            input_data: Input data for the task
            capability_required: Specific capability needed for this task

        Returns:
            The task ID

        Raises:
            KeyError: If project not found
            ValueError: If no agent available for the required capability
        """
        if project_id not in self.projects:
            raise KeyError(f"Project not found: {project_id}")

        # Find an agent with the required capability
        agent_id = None
        if capability_required:
            if not self.capability_registry[capability_required]:
                raise ValueError(
                    f"No agent available with capability: {capability_required.value}"
                )

            # Simple selection for now - could be more sophisticated
            agent_id = self.capability_registry[capability_required][0]

        task_id = str(uuid4())
        task = DesignTask(
            task_id=task_id,
            agent_id=agent_id,
            task_type=task_type,
            input_data=input_data,
            capability_required=capability_required,
        )

        self.tasks[task_id] = task
        self.projects[project_id]["tasks"].append(task_id)

        logger.info(f"Created task {task_id} for project {project_id}")
        return task_id

    def get_task(self, task_id: str) -> DesignTask:
        """
        Get a task by ID.

        Args:
            task_id: The task ID

        Returns:
            The task

        Raises:
            KeyError: If task not found
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task not found: {task_id}")

        return self.tasks[task_id]

    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """
        Execute a design task.

        Args:
            task_id: The task ID

        Returns:
            The task output data

        Raises:
            KeyError: If task not found
            ValueError: If task has no agent assigned
        """
        task = self.get_task(task_id)

        if not task.agent_id:
            raise ValueError(f"Task {task_id} has no agent assigned")

        if task.agent_id not in self.agents:
            raise KeyError(f"Agent not found: {task.agent_id}")

        agent = self.agents[task.agent_id]

        # Update task status
        task.update_status("in_progress")

        try:
            # Execute the task
            logger.info(f"Executing task {task_id} with agent {agent.name}")
            result = await agent.process_design_task(task.input_data)

            # Update task with result
            task.complete(result)

            return result
        except Exception as e:
            # Handle task failure
            logger.error(f"Task {task_id} failed: {str(e)}")
            task.fail(str(e))
            raise

    async def plan_design_project(self, project_id: str) -> Dict[str, Any]:
        """
        Plan a design project using a planner agent.

        Args:
            project_id: The project ID

        Returns:
            The planning result

        Raises:
            KeyError: If project not found
            ValueError: If no planner agent available
        """
        project = self.get_project(project_id)

        # Find a planner agent
        if not self.role_registry[DesignRoleType.PLANNER]:
            raise ValueError("No planner agent available")

        planner_id = self.role_registry[DesignRoleType.PLANNER][0]
        planner = self.agents[planner_id]

        # Update project status
        self.update_project_status(project_id, DesignProjectStatus.PLANNING)

        # Create planning task
        task_id = self.create_task(
            project_id=project_id,
            task_type="design_planning",
            input_data={
                "title": project["title"],
                "description": project["description"],
                "user_id": project["user_id"],
                "active_persona": project["active_persona"],
            },
            capability_required=DesignAgentCapabilities.UX_BRIEF,
        )

        # Execute planning task
        planning_result = await self.execute_task(task_id)

        # Update project with planning result
        project["design_brief"] = planning_result["brief"]
        project["tasks_plan"] = planning_result["tasks"]
        project["success_criteria"] = planning_result["success_criteria"]

        # Update project status
        self.update_project_status(project_id, DesignProjectStatus.EXECUTION)

        return planning_result

    async def execute_design_tasks(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Execute all planned design tasks for a project.

        Args:
            project_id: The project ID

        Returns:
            List of task results

        Raises:
            KeyError: If project not found
        """
        project = self.get_project(project_id)

        if "tasks_plan" not in project:
            raise ValueError("Project has no task plan - run planning first")

        # Create and execute tasks based on the plan
        results = []
        for task_plan in project["tasks_plan"]:
            # Create task
            task_id = self.create_task(
                project_id=project_id,
                task_type=task_plan["type"],
                input_data={
                    "design_brief": project["design_brief"],
                    "task_details": task_plan["details"],
                    "project_id": project_id,
                },
                capability_required=self._get_capability_for_task_type(
                    task_plan["type"]
                ),
            )

            # Execute task
            result = await self.execute_task(task_id)
            results.append(result)

            # Store artifacts in project
            if "artifacts" in result:
                artifact_type = task_plan["type"]
                project["artifacts"][artifact_type] = result["artifacts"]

        # Update project status
        self.update_project_status(project_id, DesignProjectStatus.REVIEW)

        return results

    async def review_design_artifacts(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Review all design artifacts for a project.

        Args:
            project_id: The project ID

        Returns:
            List of review results

        Raises:
            KeyError: If project not found
        """
        project = self.get_project(project_id)

        if not project["artifacts"]:
            raise ValueError("Project has no artifacts to review")

        # Update project status
        self.update_project_status(project_id, DesignProjectStatus.REVIEW)

        # Define review tasks based on artifacts and success criteria
        review_tasks = [
            {
                "type": "accessibility_audit",
                "capability": DesignAgentCapabilities.ACCESSIBILITY,
            },
            {
                "type": "heuristic_evaluation",
                "capability": DesignAgentCapabilities.HEURISTIC_CRITIQUE,
            },
            # Could add heatmap analysis if available
        ]

        # Create and execute review tasks
        results = []
        for review_task in review_tasks:
            # Check if we have an agent for this review type
            if not self.capability_registry[review_task["capability"]]:
                logger.warning(f"No agent available for {review_task['type']} review")
                continue

            # Create task
            task_id = self.create_task(
                project_id=project_id,
                task_type=review_task["type"],
                input_data={
                    "design_brief": project["design_brief"],
                    "artifacts": project["artifacts"],
                    "success_criteria": project["success_criteria"],
                    "project_id": project_id,
                },
                capability_required=review_task["capability"],
            )

            # Execute task
            result = await self.execute_task(task_id)
            results.append(result)

            # Store review results in project
            review_type = review_task["type"]
            if "reviews" not in project:
                project["reviews"] = {}
            project["reviews"][review_type] = result

        # Update project status
        self.update_project_status(project_id, DesignProjectStatus.CONSOLIDATION)

        return results

    async def consolidate_design_project(self, project_id: str) -> Dict[str, Any]:
        """
        Consolidate all design artifacts and reviews for a project.

        Args:
            project_id: The project ID

        Returns:
            The consolidated output

        Raises:
            KeyError: If project not found
            ValueError: If no meta-builder agent available
        """
        project = self.get_project(project_id)

        # Find a meta-builder agent
        if not self.role_registry[DesignRoleType.META_BUILDER]:
            raise ValueError("No meta-builder agent available")

        meta_builder_id = self.role_registry[DesignRoleType.META_BUILDER][0]
        meta_builder = self.agents[meta_builder_id]

        # Update project status
        self.update_project_status(project_id, DesignProjectStatus.CONSOLIDATION)

        # Create consolidation task
        task_id = self.create_task(
            project_id=project_id,
            task_type="design_consolidation",
            input_data={
                "project_title": project["title"],
                "design_brief": project["design_brief"],
                "artifacts": project["artifacts"],
                "reviews": project.get("reviews", {}),
                "project_id": project_id,
            },
            capability_required=DesignAgentCapabilities.DESIGN_SYSTEM,
        )

        # Execute consolidation task
        result = await self.execute_task(task_id)

        # Update project with consolidation result
        project["consolidated_output"] = result

        # Update project status
        self.update_project_status(project_id, DesignProjectStatus.COMPLETE)

        return result

    async def run_complete_workflow(self, project_id: str) -> Dict[str, Any]:
        """
        Run the complete design workflow for a project.

        Args:
            project_id: The project ID

        Returns:
            The final project state

        Raises:
            KeyError: If project not found
        """
        try:
            # Step 1: Plan the design project
            await self.plan_design_project(project_id)

            # Step 2: Execute all design tasks
            await self.execute_design_tasks(project_id)

            # Step 3: Review all design artifacts
            await self.review_design_artifacts(project_id)

            # Step 4: Consolidate all design work
            await self.consolidate_design_project(project_id)

            # Return the final project state
            return self.get_project(project_id)
        except Exception as e:
            # Mark project as failed
            self.update_project_status(project_id, DesignProjectStatus.FAILED)
            logger.error(f"Project {project_id} workflow failed: {str(e)}")
            raise

    def _get_capability_for_task_type(
        self, task_type: str
    ) -> Optional[DesignAgentCapabilities]:
        """Map task type to required capability."""
        task_capability_map = {
            "wireframe": DesignAgentCapabilities.WIREFRAMING,
            "moodboard": DesignAgentCapabilities.MOODBOARDING,
            "diagram": DesignAgentCapabilities.DIAGRAMS,
            "pixel_art": DesignAgentCapabilities.PIXEL_ART,
            "accessibility_audit": DesignAgentCapabilities.ACCESSIBILITY,
            "heuristic_evaluation": DesignAgentCapabilities.HEURISTIC_CRITIQUE,
            "heatmap_analysis": DesignAgentCapabilities.HEATMAP_ANALYSIS,
            "design_consolidation": DesignAgentCapabilities.DESIGN_SYSTEM,
        }

        return task_capability_map.get(task_type)


# Global orchestrator instance
_design_orchestrator = None


def get_design_orchestrator() -> DesignOrchestrator:
    """
    Get the global design orchestrator instance.

    Returns:
        The global DesignOrchestrator instance
    """
    global _design_orchestrator

    if _design_orchestrator is None:
        _design_orchestrator = DesignOrchestrator()

    return _design_orchestrator


def register_design_agents() -> None:
    """
    Register default design agents with the orchestrator.
    """
    from packages.agents.builder.design.base import (
        DesignPlannerAgent,
        DesignMetaBuilderAgent,
    )
    from packages.agents.builder.design.doer_agents import (
        WireframeGeneratorAgent,
        MoodboarderAgent,
        DiagramBotAgent,
        PixelArtistAgent,
    )
    from packages.agents.builder.design.reviewer_agents import (
        AccessibilityAuditorAgent,
        HeuristicCritiqueAgent,
        HeatmapAnalyzerAgent,
    )

    orchestrator = get_design_orchestrator()

    # Register planner
    planner = DesignPlannerAgent(agent_id="design-planner", name="Design Planner")
    orchestrator.register_agent(planner)

    # Register doer agents
    orchestrator.register_agent(WireframeGeneratorAgent())
    orchestrator.register_agent(MoodboarderAgent())
    orchestrator.register_agent(DiagramBotAgent())
    orchestrator.register_agent(PixelArtistAgent())

    # Register reviewer agents
    orchestrator.register_agent(AccessibilityAuditorAgent())
    orchestrator.register_agent(HeuristicCritiqueAgent())
    orchestrator.register_agent(HeatmapAnalyzerAgent())

    # Register meta-builder
    meta_builder = DesignMetaBuilderAgent(
        agent_id="design-meta-builder", name="Design Meta-Builder"
    )
    orchestrator.register_agent(meta_builder)

    logger.info("Registered all design agents with orchestrator")
