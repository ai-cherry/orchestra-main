"""
Vertex AI Agent integration for Orchestra.

This package provides integration with Vertex AI Agents for automation
of infrastructure tasks, embeddings management, and other operations.
"""

from .vertex_agent_manager import VertexAgentManager, trigger_vertex_task

__all__ = ['VertexAgentManager', 'trigger_vertex_task']
