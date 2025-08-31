# File: src/ai_research_assistant/agents/base_pydantic_agent_config.py

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class BasePydanticAgentConfig(BaseModel):
    """
    Configuration for BasePydanticAgent following PydanticAI native patterns.
    """

    agent_id: str = Field(description="Unique identifier for the agent.")
    agent_name: str = Field(description="Human-readable name for the agent.")

    # --- PydanticAI NATIVE MODEL SPECIFICATION ---
    # Use model name that PydanticAI recognizes (without provider prefix)
    llm_model: str = Field(
        default="gemini-2.5-pro",
        description="Model name in PydanticAI format (e.g., 'gemini-2.5-pro', 'gpt-4')",
    )

    llm_temperature: float = Field(
        default=0.7, description="LLM temperature for generation."
    )
    llm_max_tokens: int = Field(
        default=4096, description="LLM maximum tokens for generation."
    )

    # --- PydanticAI AGENT CONFIGURATION ---
    # Use 'instructions' as the primary field (PydanticAI standard)
    instructions: Optional[str] = Field(
        default=None, description="Primary instructions for the PydanticAI Agent."
    )

    # Keep system_prompt for backward compatibility, but instructions takes precedence
    system_prompt: Optional[str] = Field(
        default=None,
        description="Alternative system prompt (use instructions instead).",
    )

    retries: int = Field(
        default=1,
        description="Number of retries PydanticAI should attempt for recoverable errors.",
    )

    # Agent metadata for A2A protocol
    version: str = Field(default="1.0.0", description="Agent version for A2A protocol")
    description: str = Field(
        default="AI Research Agent", description="Agent description for A2A"
    )

    custom_settings: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"
