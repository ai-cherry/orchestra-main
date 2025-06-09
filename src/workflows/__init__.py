"""
Workflow Automation Integration for Orchestra AI

This package implements a workflow automation system that enables Orchestra AI to automate
multi-step workflows across different systems.
"""

from .workflow_automation import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStep,
    WorkflowStatus,
    StepStatus,
    StepType,
    ConnectorType,
    WorkflowAction
)

__all__ = [
    'WorkflowEngine',
    'WorkflowDefinition',
    'WorkflowExecution',
    'WorkflowStep',
    'WorkflowStatus',
    'StepStatus',
    'StepType',
    'ConnectorType',
    'WorkflowAction'
]
