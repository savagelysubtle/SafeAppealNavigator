# File: src/ai_research_assistant/agents/ceo_agent/config.py
from typing import Any, Dict

from pydantic import Field

from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)


class CEOAgentConfig(BasePydanticAgentConfig):
    """
    Configuration for the CEO Agent.
    """

    agent_name: str = "CEOAgent"
    agent_id: str = "ceo_agent_001"

    # --- ADDED DEFAULT MODEL ---
    # This ensures the agent can initialize its LLM factory.
    llm_model_name: str = "gemini-1.5-flash"
    # --- END CORRECTION ---

    pydantic_ai_system_prompt: str = (
        "You are the CEO Agent. Your role is to understand the user's request, "
        "clarify it if necessary, and then delegate the task to your direct report, the Orchestrator Agent. "
        "Formulate a clear, actionable instruction for the Orchestrator."
    )

    # Custom settings for the CEO agent
    custom_settings: Dict[str, Any] = Field(default_factory=dict)
