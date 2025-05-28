"""
Legal Research Orchestrator Agent

This module provides orchestration capabilities for coordinating multiple specialized agents
in a unified legal research workflow.

Main Components:
- LegalOrchestratorAgent: Main orchestrator that coordinates all agents
- WorkflowManager: Manages workflow states and transitions
- AgentCoordinator: Handles agent communication and task delegation
"""

from .agent_coordinator import AgentCoordinator
from .legal_orchestrator import LegalOrchestratorAgent
from .workflow_manager import WorkflowManager

__all__ = ["LegalOrchestratorAgent", "WorkflowManager", "AgentCoordinator"]
