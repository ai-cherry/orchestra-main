"""
Agent Team Coordination for AI Orchestration System.

This module provides classes for coordinating teams of specialized agents,
enabling them to work together to solve complex tasks.
"""

import logging
import asyncio
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from pydantic import BaseModel, Field

from core.orchestrator.src.agents.agent_base import Agent, AgentContext, AgentResponse
from core.orchestrator.src.agents.memory.layered_memory import get_memory_manager
from core.orchestrator.src.agents.stateful_agent import StatefulAgent
from core.orchestrator.src.config.models import TeamMode

# Configure logging
logger = logging.getLogger(__name__)


class ExecutionStep(BaseModel):
    """
    Step in an execution plan.

    This class represents a step in an execution plan, specifying which
    agent should execute the step and what the step involves.
    """

    agent_name: str
    description: str
    input_context: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    step_id: str = ""
    is_parallel: bool = False


class ExecutionPlan(BaseModel):
    """
    Plan for executing a task with multiple agents.

    This class represents a plan for executing a task, including the steps
    to be taken and the agents involved.
    """

    steps: List[ExecutionStep]
    coordinator_notes: str = ""
    max_iterations: int = 5
    team_mode: TeamMode = TeamMode.COORDINATE


class StepResult(BaseModel):
    """
    Result of executing a step.

    This class represents the result of executing a step in an execution plan,
    including the agent's response and any additional metadata.
    """

    step_id: str
    agent_name: str
    response: Dict[str, Any]
    success: bool = True
    error: Optional[str] = None
    execution_time_ms: float = 0


class AgentTeam:
    """
    Coordinates a team of specialized agents.

    This class provides a unified interface for managing a team of agents,
    coordinating their execution to solve complex tasks.
    """

    def __init__(
        self,
        coordinator: Agent,
        agents: Dict[str, Agent],
        team_mode: TeamMode = TeamMode.COORDINATE,
        team_name: str = "default_team",
    ):
        """
        Initialize the agent team.

        Args:
            coordinator: The agent that coordinates the team
            agents: Dictionary of agent name to agent instance
            team_mode: The mode of team coordination
            team_name: The name of the team
        """
        self.coordinator = coordinator
        self.agents = agents
        self.team_mode = team_mode
        self.team_name = team_name
        self._results_cache: Dict[str, StepResult] = {}

    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process a request using the appropriate agent(s).

        Args:
            context: The context for this interaction

        Returns:
            The team's response
        """
        # Create execution plan using coordinator
        plan = await self._create_execution_plan(context)

        # Execute the plan
        if self.team_mode == TeamMode.COORDINATE:
            results = await self._execute_coordinated_plan(plan, context)
        elif self.team_mode == TeamMode.COLLABORATE:
            results = await self._execute_collaborative_plan(plan, context)
        elif self.team_mode == TeamMode.COMPETE:
            results = await self._execute_competitive_plan(plan, context)
        elif self.team_mode == TeamMode.DEBATE:
            results = await self._execute_debate_plan(plan, context)
        else:
            # Default to coordinated execution
            results = await self._execute_coordinated_plan(plan, context)

        # Synthesize final response
        return await self._synthesize_response(results, context)

    async def _create_execution_plan(self, context: AgentContext) -> ExecutionPlan:
        """
        Create an execution plan using the coordinator.

        Args:
            context: The context for this interaction

        Returns:
            An execution plan
        """
        # Add team info to context
        if context.metadata is None:
            context.metadata = {}

        context.metadata["team_info"] = {
            "team_name": self.team_name,
            "team_mode": self.team_mode.value,
            "available_agents": list(self.agents.keys()),
        }

        # Ask coordinator to create a plan
        coordinator_context = AgentContext(
            user_input=f"Create an execution plan for: {context.user_input}",
            user_id=context.user_id,
            persona=context.persona,
            conversation_history=context.conversation_history,
            session_id=context.session_id,
            interaction_id=context.interaction_id,
            metadata=context.metadata,
        )

        # Get response from coordinator
        response = await self.coordinator.process(coordinator_context)

        # Parse plan from response
        # In a real implementation, the coordinator would return a structured plan
        # For now, we'll create a simple plan based on the coordinator's response

        # Create a simple plan with one step per agent
        steps = []
        for i, (agent_name, _) in enumerate(self.agents.items()):
            step = ExecutionStep(
                agent_name=agent_name,
                description=f"Process the request using {agent_name}",
                step_id=f"step_{i+1}",
            )
            steps.append(step)

        return ExecutionPlan(
            steps=steps, coordinator_notes=response.text, team_mode=self.team_mode
        )

    async def _execute_coordinated_plan(
        self, plan: ExecutionPlan, context: AgentContext
    ) -> List[StepResult]:
        """
        Execute a plan in coordinated mode.

        In coordinated mode, steps are executed sequentially based on dependencies.

        Args:
            plan: The execution plan
            context: The context for this interaction

        Returns:
            List of step results
        """
        results = []
        executed_steps = set()

        # Execute steps in order, respecting dependencies
        for iteration in range(plan.max_iterations):
            executed_any = False

            for step in plan.steps:
                # Skip already executed steps
                if step.step_id in executed_steps:
                    continue

                # Check if dependencies are satisfied
                dependencies_met = all(dep in executed_steps for dep in step.depends_on)
                if not dependencies_met:
                    continue

                # Execute step
                result = await self._execute_step(step, context, results)
                results.append(result)
                executed_steps.add(step.step_id)
                executed_any = True

            # If no steps were executed in this iteration, we're done
            if not executed_any:
                break

        return results

    async def _execute_collaborative_plan(
        self, plan: ExecutionPlan, context: AgentContext
    ) -> List[StepResult]:
        """
        Execute a plan in collaborative mode.

        In collaborative mode, agents work together, building on each other's outputs.

        Args:
            plan: The execution plan
            context: The context for this interaction

        Returns:
            List of step results
        """
        results = []
        current_context = context

        # Execute steps sequentially, passing output from one to the next
        for step in plan.steps:
            # Update context with previous results
            if results:
                if current_context.metadata is None:
                    current_context.metadata = {}

                current_context.metadata["previous_result"] = results[-1].response

            # Execute step
            result = await self._execute_step(step, current_context, results)
            results.append(result)

            # Update context for next step
            current_context = AgentContext(
                user_input=f"{context.user_input}\n\nPrevious agent said: {result.response.get('text', '')}",
                user_id=context.user_id,
                persona=context.persona,
                conversation_history=context.conversation_history,
                session_id=context.session_id,
                interaction_id=context.interaction_id,
                metadata=context.metadata,
            )

        return results

    async def _execute_competitive_plan(
        self, plan: ExecutionPlan, context: AgentContext
    ) -> List[StepResult]:
        """
        Execute a plan in competitive mode.

        In competitive mode, all agents process the request independently,
        and the best response is selected.

        Args:
            plan: The execution plan
            context: The context for this interaction

        Returns:
            List of step results
        """
        # Execute all steps in parallel
        tasks = []
        for step in plan.steps:
            task = asyncio.create_task(self._execute_step(step, context, []))
            tasks.append((step, task))

        # Wait for all tasks to complete
        results = []
        for step, task in tasks:
            try:
                result = await task
                results.append(result)
            except Exception as e:
                logger.error(f"Error executing step {step.step_id}: {e}")
                results.append(
                    StepResult(
                        step_id=step.step_id,
                        agent_name=step.agent_name,
                        response={"text": f"Error: {str(e)}"},
                        success=False,
                        error=str(e),
                    )
                )

        return results

    async def _execute_debate_plan(
        self, plan: ExecutionPlan, context: AgentContext
    ) -> List[StepResult]:
        """
        Execute a plan in debate mode.

        In debate mode, agents engage in a multi-turn debate to refine their answers.

        Args:
            plan: The execution plan
            context: The context for this interaction

        Returns:
            List of step results
        """
        results = []
        debate_history = []

        # Initial round: all agents respond to the original query
        initial_results = await self._execute_competitive_plan(plan, context)
        results.extend(initial_results)

        # Add initial responses to debate history
        for result in initial_results:
            debate_history.append(
                {"agent": result.agent_name, "text": result.response.get("text", "")}
            )

        # Debate rounds
        for round_num in range(1, plan.max_iterations):
            round_results = []

            # Each agent responds to the debate so far
            for step in plan.steps:
                # Create debate context
                debate_context = AgentContext(
                    user_input=f"{context.user_input}\n\nDebate history:\n"
                    + "\n".join([f"{d['agent']}: {d['text']}" for d in debate_history]),
                    user_id=context.user_id,
                    persona=context.persona,
                    conversation_history=context.conversation_history,
                    session_id=context.session_id,
                    interaction_id=context.interaction_id,
                    metadata={
                        **(context.metadata or {}),
                        "debate_round": round_num,
                        "debate_history": debate_history,
                    },
                )

                # Execute step
                result = await self._execute_step(step, debate_context, results)
                round_results.append(result)

                # Add to debate history
                debate_history.append(
                    {
                        "agent": result.agent_name,
                        "text": result.response.get("text", ""),
                    }
                )

            # Add round results to overall results
            results.extend(round_results)

        return results

    async def _execute_step(
        self,
        step: ExecutionStep,
        context: AgentContext,
        previous_results: List[StepResult],
    ) -> StepResult:
        """
        Execute a single step in the plan.

        Args:
            step: The step to execute
            context: The context for this interaction
            previous_results: Results from previous steps

        Returns:
            The result of executing the step
        """
        # Check if agent exists
        if step.agent_name not in self.agents:
            return StepResult(
                step_id=step.step_id,
                agent_name=step.agent_name,
                response={"text": f"Agent {step.agent_name} not found"},
                success=False,
                error=f"Agent {step.agent_name} not found",
            )

        # Get agent
        agent = self.agents[step.agent_name]

        # Prepare context for this step
        step_context = AgentContext(
            user_input=context.user_input,
            user_id=context.user_id,
            persona=context.persona,
            conversation_history=context.conversation_history,
            session_id=context.session_id,
            interaction_id=context.interaction_id,
            metadata={
                **(context.metadata or {}),
                "step": {
                    "id": step.step_id,
                    "description": step.description,
                    "agent": step.agent_name,
                    "input_context": step.input_context,
                },
                "previous_results": [r.dict() for r in previous_results],
            },
        )

        # Execute agent
        start_time = asyncio.get_event_loop().time()

        try:
            response = await agent.process(step_context)
            success = True
            error = None
        except Exception as e:
            logger.error(f"Error executing agent {step.agent_name}: {e}")
            response = AgentResponse(
                text=f"Error executing agent {step.agent_name}: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)},
            )
            success = False
            error = str(e)

        # Calculate execution time
        execution_time = (asyncio.get_event_loop().time() - start_time) * 1000

        # Create result
        result = StepResult(
            step_id=step.step_id,
            agent_name=step.agent_name,
            response=response.to_dict(),
            success=success,
            error=error,
            execution_time_ms=execution_time,
        )

        # Cache result
        self._results_cache[step.step_id] = result

        return result

    async def _synthesize_response(
        self, results: List[StepResult], context: AgentContext
    ) -> AgentResponse:
        """
        Synthesize a final response from the results.

        Args:
            results: The results of executing the plan
            context: The context for this interaction

        Returns:
            The final response
        """
        # If no results, return an error
        if not results:
            return AgentResponse(
                text="No agents were able to process your request.",
                confidence=0.0,
                metadata={"error": "No results"},
            )

        # In coordinated and collaborative modes, use the last result
        if self.team_mode in [TeamMode.COORDINATE, TeamMode.COLLABORATE]:
            last_result = results[-1]
            if not last_result.success:
                return AgentResponse(
                    text=f"Error in final step: {last_result.error}",
                    confidence=0.0,
                    metadata={"error": last_result.error},
                )

            return AgentResponse(
                text=last_result.response.get("text", ""),
                confidence=last_result.response.get("confidence", 0.5),
                metadata={
                    "team_mode": self.team_mode.value,
                    "team_name": self.team_name,
                    "agent": last_result.agent_name,
                    "step_id": last_result.step_id,
                    "execution_time_ms": last_result.execution_time_ms,
                },
            )

        # In competitive mode, select the best response based on confidence
        elif self.team_mode == TeamMode.COMPETE:
            # Filter out failed results
            successful_results = [r for r in results if r.success]

            if not successful_results:
                return AgentResponse(
                    text="All agents failed to process your request.",
                    confidence=0.0,
                    metadata={"error": "All agents failed"},
                )

            # Select result with highest confidence
            best_result = max(
                successful_results, key=lambda r: r.response.get("confidence", 0.0)
            )

            return AgentResponse(
                text=best_result.response.get("text", ""),
                confidence=best_result.response.get("confidence", 0.5),
                metadata={
                    "team_mode": self.team_mode.value,
                    "team_name": self.team_name,
                    "agent": best_result.agent_name,
                    "step_id": best_result.step_id,
                    "execution_time_ms": best_result.execution_time_ms,
                    "selection_method": "highest_confidence",
                },
            )

        # In debate mode, ask coordinator to synthesize a final answer
        elif self.team_mode == TeamMode.DEBATE:
            # Create context for coordinator
            coordinator_context = AgentContext(
                user_input=f"Synthesize a final answer for: {context.user_input}",
                user_id=context.user_id,
                persona=context.persona,
                conversation_history=context.conversation_history,
                session_id=context.session_id,
                interaction_id=context.interaction_id,
                metadata={
                    **(context.metadata or {}),
                    "debate_results": [r.dict() for r in results],
                },
            )

            # Get response from coordinator
            response = await self.coordinator.process(coordinator_context)

            # Add metadata about the debate
            response.metadata = {
                **(response.metadata or {}),
                "team_mode": self.team_mode.value,
                "team_name": self.team_name,
                "debate_agents": [r.agent_name for r in results],
                "debate_rounds": len(results) // len(self.agents) if self.agents else 0,
            }

            return response

        # Default case
        return AgentResponse(
            text="The team processed your request.",
            confidence=0.5,
            metadata={
                "team_mode": self.team_mode.value,
                "team_name": self.team_name,
                "results_count": len(results),
            },
        )


class TeamCoordinator(StatefulAgent):
    """
    Agent that coordinates a team of specialized agents.

    This class extends StatefulAgent to provide coordination capabilities
    for agent teams, including execution planning and result synthesis.
    """

    async def process_with_state(
        self, context: AgentContext
    ) -> Tuple[AgentResponse, Any]:
        """
        Process user input with team coordination.

        Args:
            context: The context for this interaction

        Returns:
            A tuple of (response, state)
        """
        # Get state
        state = self.get_state(context)

        # Increment step counter
        state.increment_step()

        # Create execution plan
        plan = await self._create_execution_plan(context)

        # Store plan in state
        state.add_context_variable("execution_plan", plan.dict())

        # Return plan as response
        response = AgentResponse(
            text=f"Execution plan created with {len(plan.steps)} steps:\n"
            + "\n".join([f"- {s.agent_name}: {s.description}" for s in plan.steps]),
            confidence=0.9,
            metadata={"execution_plan": plan.dict(), "step": state.current_step},
        )

        return response, state

    async def _create_execution_plan(self, context: AgentContext) -> ExecutionPlan:
        """
        Create an execution plan for the team.

        Args:
            context: The context for this interaction

        Returns:
            An execution plan
        """
        # Get available agents from context
        available_agents = []
        if context.metadata and "team_info" in context.metadata:
            available_agents = context.metadata["team_info"].get("available_agents", [])

        # Get team mode from context
        team_mode = TeamMode.COORDINATE
        if context.metadata and "team_info" in context.metadata:
            mode_str = context.metadata["team_info"].get("team_mode", "coordinate")
            try:
                team_mode = TeamMode(mode_str)
            except ValueError:
                pass

        # Create a simple plan based on available agents
        steps = []
        for i, agent_name in enumerate(available_agents):
            step = ExecutionStep(
                agent_name=agent_name,
                description=f"Process the request using {agent_name}",
                step_id=f"step_{i+1}",
            )
            steps.append(step)

        # In a real implementation, the coordinator would use an LLM to create
        # a more sophisticated plan based on the task and available agents

        return ExecutionPlan(
            steps=steps,
            coordinator_notes=f"Simple plan using {len(available_agents)} agents in {team_mode.value} mode",
            team_mode=team_mode,
        )

    async def synthesize_response(
        self, results: List[Dict[str, Any]], context: AgentContext
    ) -> AgentResponse:
        """
        Synthesize a final response from the results.

        Args:
            results: The results of executing the plan
            context: The context for this interaction

        Returns:
            The final response
        """
        # In a real implementation, the coordinator would use an LLM to synthesize
        # a coherent response from the individual agent responses

        # For now, just combine the responses
        combined_text = "Team response:\n\n"
        for i, result in enumerate(results):
            agent_name = result.get("agent_name", f"Agent {i+1}")
            response_text = result.get("response", {}).get("text", "No response")
            combined_text += f"{agent_name}: {response_text}\n\n"

        return AgentResponse(
            text=combined_text,
            confidence=0.8,
            metadata={
                "synthesized_from": len(results),
                "coordinator": self.__class__.__name__,
            },
        )
