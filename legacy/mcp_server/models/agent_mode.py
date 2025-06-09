# TODO: Consider adding connection pooling configuration

"""
Cherry AI - Database Models
This module contains Pydantic models for database entities.
"""

from typing import List, Dict, Any, Optional
from typing_extensions import Optional, Union
from uuid import uuid4, UUID
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator

#!/usr/bin/env python3
"""
"""
    """Types of specialized agent modes."""
    CODER = "coder"
    DEBUGGER = "debugger"
    REFACTOR = "refactor"
    TESTER = "tester"
    SECURITY_ANALYST = "security_analyst"
    DOC_WRITER = "doc_writer"
    ARCHITECT = "architect"
    PLANNER = "planner"
    CONDUCTOR = "conductor"
    DEFAULT = "default"

class AgentModeConfig(BaseModel):
    """Configuration for an agent mode using Pydantic for validation."""
    name: str = Field(..., description="Display name of the agent mode")
    description: str = Field(..., description="Description of the agent mode's purpose")
    system_prompt: str = Field(..., description="System prompt for the agent mode")
    required_context: List[str] = Field(default_factory=list, description="Required context fields for this mode")
    suggested_tools: List[str] = Field(default_factory=list, description="Suggested tools for this mode")
    example_prompts: List[str] = Field(default_factory=list, description="Example prompts for this mode")
    token_multiplier: float = Field(default=1.0, description="Token budget multiplier for this mode")
    constraints: List[str] = Field(default_factory=list, description="Constraints for this mode")

    @validator("token_multiplier")
    def validate_token_multiplier(cls, v: float) -> float:
        """Validate that token_multiplier is positive."""
            raise ValueError("token_multiplier must be positive")
        return v

    class Config:
        """Pydantic configuration."""
        extra = "forbid"  # Forbid extra fields

class AgentMode(BaseModel):
    """Agent mode with configuration and state."""
    active: bool = Field(default=False, description="Whether this mode is currently active")
    context: Dict[str, Any] = Field(default_factory=dict, description="Current context for this mode")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
            "mode_type": self.mode_type,
            "name": self.config.name,
            "description": self.config.description,
            "active": self.active,
            "context": self.context,
        }

    def get_prompt_template(self) -> str:
        """Get the prompt template for this mode."""
        template = f"""
"""
            template += "Constraints:\n"
            for i, constraint in enumerate(self.config.constraints, 1):
                template += f"{i}. {constraint}\n"

        return template

    def get_constraints_text(self) -> str:
        """Get the constraints text for this mode."""
            return "Adhere to best practices and provide clear explanations."

        return "\n".join([f"- {constraint}" for constraint in self.config.constraints])

    def has_required_context(self, provided_context: Dict[str, Any]) -> bool:
        """Check if all required context is provided."""
        """Get list of missing required context keys."""
        """Format the prompt template with task and context."""
            context_str = "No additional context provided."

        return template.format(context=context_str, task=task)

    class Config:
        """Pydantic configuration."""
        name="CoderAgent",
        description="Specialized in generating, completing, and explaining code",
        system_prompt="""
frameworks, and best practices. Your task is to write clean, efficient, and well-documented code."""
        required_context=["language", "requirements"],
        suggested_tools=["code_completion", "code_explanation", "code_generation"],
        example_prompts=[
            "Generate a Python function that sorts a list of dictionaries by a specific key",
            "Complete this JavaScript function to handle API errors",
        ],
        constraints=[
            "Write code that is efficient and follows best practices",
            "Include appropriate error handling",
            "Add clear comments and documentation",
        ],
    ),
    AgentModeType.DEBUGGER: AgentModeConfig(
        name="DebuggerAgent",
        description="Specialized in identifying and fixing bugs",
        system_prompt="""
Your task is to analyze code, error messages, and logs to diagnose and fix issues."""
        required_context=["error_message", "code_context"],
        suggested_tools=["error_analysis", "code_fix_suggestion"],
        example_prompts=[
            "Debug this Python KeyError in the data processing function",
            "Fix the null reference exception in this JavaScript code",
        ],
        constraints=[
            "Suggest minimal changes to fix the problem",
            "Explain why the error occurred",
        ],
    ),
    AgentModeType.REFACTOR: AgentModeConfig(
        name="RefactorAgent",
        description="Specialized in improving code structure and quality",
        system_prompt="""
Your task is to improve code quality, readability, and maintainability without changing its external behavior."""
        required_context=["code", "refactoring_goals"],
        suggested_tools=["code_analysis", "refactoring_suggestion"],
        example_prompts=[
            "Refactor this function to reduce complexity",
            "Apply the Strategy pattern to this code",
        ],
        constraints=[
            "Preserve the original functionality",
            "Improve readability and maintainability",
            "Follow SOLID principles and design patterns",
        ],
    ),
    AgentModeType.TESTER: AgentModeConfig(
        name="TesterAgent",
        description="Specialized in creating tests and test strategies",
        system_prompt="""
Your task is to create comprehensive tests that verify code correctness and catch potential issues."""
        required_context=["code_to_test", "testing_framework"],
        suggested_tools=["test_generation", "test_analysis"],
        example_prompts=[
            "Write unit tests for this Python class",
            "Create integration tests for this API endpoint",
        ],
        constraints=[
            "Cover edge cases and error conditions",
            "Ensure high test coverage",
            "Write maintainable and readable tests",
        ],
    ),
    AgentModeType.SECURITY_ANALYST: AgentModeConfig(
        name="SecurityAnalystAgent",
        description="Specialized in identifying security vulnerabilities",
        system_prompt="""
Your task is to identify potential security vulnerabilities and suggest improvements."""
        required_context=["code", "security_requirements"],
        suggested_tools=["vulnerability_scan", "security_recommendation"],
        example_prompts=[
            "Check this code for SQL injection vulnerabilities",
            "Review this authentication implementation for security issues",
        ],
        constraints=[
            "Focus on OWASP Top 10 vulnerabilities",
            "Suggest practical mitigations",
            "Consider both security and usability",
        ],
    ),
    AgentModeType.DOC_WRITER: AgentModeConfig(
        name="DocWriterAgent",
        description="Specialized in creating documentation",
        system_prompt="""
Your task is to create documentation that helps users understand and use the code effectively."""
        required_context=["code", "audience"],
        suggested_tools=["docstring_generation", "readme_generation"],
        example_prompts=[
            "Write docstrings for this Python module",
            "Create a README for this project",
        ],
        constraints=[
            "Be clear and concise",
            "Include examples where appropriate",
            "Target the documentation to the specified audience",
        ],
    ),
    AgentModeType.ARCHITECT: AgentModeConfig(
        name="ArchitectAgent",
        description="Specialized in system design and architecture",
        system_prompt="""
patterns, and best practices. Your task is to design robust, scalable, and maintainable systems."""
        required_context=["requirements", "constraints"],
        suggested_tools=["architecture_diagram", "design_recommendation"],
        example_prompts=[
            "Design a microservice architecture for this e-commerce system",
            "Suggest a data storage strategy for this analytics platform",
        ],
        constraints=[
            "Consider scalability, reliability, and performance",
            "Follow architectural best practices",
            "Balance technical excellence with practical constraints",
        ],
    ),
    AgentModeType.PLANNER: AgentModeConfig(
        name="PlannerAgent",
        description="Specialized in breaking down complex tasks",
        system_prompt="""
Your task is to break down complex problems into manageable steps."""
        required_context=["goal", "constraints"],
        suggested_tools=["task_decomposition", "timeline_generation"],
        example_prompts=[
            "Create a plan for implementing this feature",
            "Break down this project into phases and tasks",
        ],
        constraints=[
            "Create clear, actionable steps",
            "Consider dependencies between tasks",
            "Provide realistic time estimates",
        ],
    ),
    AgentModeType.CONDUCTOR: AgentModeConfig(
        name="conductorAgent",
        description="Specialized in coordinating multiple agents",
        system_prompt="""
Your task is to cherry_aite the work of multiple specialized agents to solve complex problems."""
        required_context=["goal", "available_agents"],
        suggested_tools=["agent_delegation", "workflow_management"],
        example_prompts=[
            "Coordinate the development of this feature using multiple agents",
            "Manage the debugging and fixing of these issues",
        ],
        constraints=[
            "Effectively delegate tasks to appropriate agents",
            "Maintain context across agent transitions",
            "Synthesize results into a coherent solution",
        ],
        token_multiplier=1.5,  # conductor needs more context
    ),
    AgentModeType.DEFAULT: AgentModeConfig(
        name="DefaultAgent",
        description="General-purpose assistant",
        system_prompt="""
helpful responses to user queries."""
            "Explain how to use this API",
            "Help me understand this concept",
        ],
        constraints=["Be helpful and accurate", "Provide clear explanations"],
    ),
}
