# File: src/ai_research_assistant/agents/orchestrator_agent/config.py
from typing import Any, Dict

from pydantic import Field

from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)


class OrchestratorAgentConfig(BasePydanticAgentConfig):
    """
    Configuration for the Orchestrator Agent.
    """

    agent_name: str = "OrchestratorAgent"
    agent_id: str = "orchestrator_agent_001"

    pydantic_ai_system_prompt: str = (
        "You are the Orchestrator Agent. Your role is to receive tasks from the CEO agent, "
        "break them down into smaller, executable steps, and then delegate each step to the "
        "appropriate specialized agent by calling the correct tool."
    )

    # Custom settings for the Orchestrator agent
    custom_settings: Dict[str, Any] = Field(default_factory=dict)
