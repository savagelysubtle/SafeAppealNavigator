# File: src/savagelysubtle_airesearchagent/agents/base_pydantic_agent_config.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class BasePydanticAgentConfig(BaseModel):
    """
    Configuration for BasePydanticAgent.
    """
    agent_id: str = Field(description="Unique identifier for the agent.")
    agent_name: str = Field(description="Human-readable name for the agent.")

    # LLM Configuration (to be used by UnifiedLLMFactory)
    llm_provider: str = Field(default="google", description="Default LLM provider (e.g., 'openai', 'google', 'anthropic').")
    llm_model_name: Optional[str] = Field(default=None, description="Specific model name for the provider (e.g., 'gpt-4o', 'gemini-1.5-pro'). If None, factory default is used.")
    llm_temperature: float = Field(default=0.7, description="LLM temperature for generation.")
    llm_max_tokens: int = Field(default=2048, description="LLM maximum tokens for generation.")

    # Pydantic AI Agent specific settings
    pydantic_ai_instructions: Optional[str] = Field(default=None, description="Default instructions for the pydantic_ai.Agent.")
    pydantic_ai_system_prompt: Optional[str] = Field(default=None, description="Default system prompt for the pydantic_ai.Agent.")
    # Retries for Pydantic AI's internal retry mechanism (e.g., for tool validation errors)
    pydantic_ai_retries: int = Field(default=1, description="Number of retries Pydantic AI should attempt for recoverable errors.")

    # MCP Client Configuration (if any specific needed at base level)
    # mcp_server_url: Optional[str] = Field(default=None, description="URL of the MCP server if directly configured.")

    # Custom settings that can be passed down to specific agent implementations
    custom_settings: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow" # Allow additional fields for derived agent configs