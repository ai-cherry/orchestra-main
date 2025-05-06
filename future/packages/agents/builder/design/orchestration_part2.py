"""
DEPRECATED: This file is deprecated and will be removed in a future release.

This legacy file has been replaced by a newer implementation with improved architecture 
and error handling. Please consult the project documentation for the recommended 
replacement module.

Example migration:
from orchestration_part2 import * # Old
# Change to:
# Import the appropriate replacement module
"""

"""
Design Guild Orchestration - Part 2.

This module contains the remaining implementation for the orchestration layer, including
methods for reviewing design artifacts, consolidating results, and running the complete workflow.
"""

import logging
from typing import Dict, List, Optional, Any, Union

from packages.agents.builder.design.base import (
    DesignAgentCapabilities,
    DesignRoleType,
    DesignBaseAgent,
)
from packages.agents.builder.design.orchestration import (
    DesignProjectStatus,
    DesignOrchestrator,
)

logger = logging.getLogger(__name__)


# Continuation of DesignOrchestrator class methods
async def review_design_artifacts_continued(
    self: DesignOrchestrator, project_id: str
) -> List[Dict[str, Any]]:
    """
    Implementation continuation for the review_design_artifacts method.

    Args:
        project_id: The project ID

    Returns:
        List of review results
    """
    project = self.get_project(project_id)

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


async def consolidate_design_project(
    self: DesignOrchestrator, project_id: str
) -> Dict[str, Any]:
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


async def run_complete_workflow(
    self: DesignOrchestrator, project_id: str
) -> Dict[str, Any]:
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
        await review_design_artifacts_continued(self, project_id)

        # Step 4: Consolidate all design work
        await consolidate_design_project(self, project_id)

        # Return the final project state
        return self.get_project(project_id)
    except Exception as e:
        # Mark project as failed
        self.update_project_status(project_id, DesignProjectStatus.FAILED)
        logger.error(f"Project {project_id} workflow failed: {str(e)}")
        raise


def _get_capability_for_task_type(task_type: str) -> Optional[DesignAgentCapabilities]:
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


# Add capability to DesignOrchestrator class
DesignOrchestrator._get_capability_for_task_type = _get_capability_for_task_type
