# File: src/ai_research_assistant/agents/base_pydantic_agent_config.py

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class BasePydanticAgentConfig(BaseModel):
    """
    Configuration for BasePydanticAgent.
    """

    agent_id: str = Field(description="Unique identifier for the agent.")
    agent_name: str = Field(description="Human-readable name for the agent.")

    # The pydantic-ai library expects the string format "google:<model_name>"
    llm_provider: str = Field(
        default="google",
        description="LLM provider key (e.g., 'openai', 'google', 'anthropic').",
    )

    # --- DEFINITIVE FIX: Use the stable and highly compatible gemini-1.5-flash model ---
    # This avoids the "UNEXPECTED_TOOL_CALL" edge case from the pro model.
    llm_model_name: Optional[str] = Field(
        default="gemini-1.5-flash", description="Specific model name for the provider."
    )
    llm_temperature: float = Field(
        default=0.7, description="LLM temperature for generation."
    )
    llm_max_tokens: int = Field(
        default=4096, description="LLM maximum tokens for generation."
    )

    pydantic_ai_instructions: Optional[str] = Field(
        default=None, description="Default instructions for the pydantic_ai.Agent."
    )
    pydantic_ai_system_prompt: Optional[str] = Field(
        default=None, description="Default system prompt for the pydantic_ai.Agent."
    )
    pydantic_ai_retries: int = Field(
        default=1,
        description="Number of retries Pydantic AI should attempt for recoverable errors.",
    )

    custom_settings: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"
