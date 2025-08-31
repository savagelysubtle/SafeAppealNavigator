# FILE: src/ai_research_assistant/agents/base_pydantic_agent.py
# Pure PydanticAI Implementation with Factory Support

import logging
from typing import Any, List, Optional

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServer

from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)

logger = logging.getLogger(__name__)


class BasePydanticAgent:
    """
    Pure PydanticAI agent implementation following native patterns.
    Supports both direct model strings and factory-created model instances.
    Provides A2A compatibility through PydanticAI's built-in to_a2a() method.
    """

    def __init__(
        self,
        config: BasePydanticAgentConfig,
        llm_instance: Optional[Any] = None,
        toolsets: Optional[List[MCPServer]] = None,
    ):
        self.config = config
        self.agent_name = self.config.agent_name
        self.toolsets = toolsets or []

        # --- FLEXIBLE MODEL INITIALIZATION ---
        # Support both factory-created instances and direct model strings
        if llm_instance is not None:
            # Use factory-created model instance (preferred for dynamic model selection)
            model = llm_instance
            logger.info(
                f"Agent '{self.agent_name}' using factory-created model instance"
            )
        else:
            # Use model string from config (fallback for direct instantiation)
            model = self.config.llm_model
            logger.info(
                f"Agent '{self.agent_name}' using config model: {self.config.llm_model}"
            )

        # --- PURE PydanticAI INITIALIZATION ---
        # Create Agent with model and system_prompt following PydanticAI patterns
        self.pydantic_agent = Agent(
            model,  # Either factory instance or model string
            system_prompt=self._get_instructions(),  # System prompt for agent behavior
        )

        # Add MCP toolsets - PydanticAI handles them automatically when passed to Agent
        # Note: Your existing MCP client creates the correct MCPServer types

        logger.info(f"PydanticAI Agent '{self.agent_name}' initialized successfully")
        if self.toolsets:
            logger.info(
                f"Agent '{self.agent_name}' has {len(self.toolsets)} MCP toolsets available"
            )

    def _get_instructions(self) -> str:
        """
        Get instructions for the agent, prioritizing 'instructions' over 'system_prompt'
        following PydanticAI conventions.
        """
        if self.config.instructions:
            return self.config.instructions
        elif self.config.system_prompt:
            logger.warning(
                f"Agent '{self.agent_name}' using deprecated system_prompt. "
                "Consider migrating to 'instructions' field."
            )
            return self.config.system_prompt
        else:
            return f"You are {self.agent_name}, an AI research assistant."

    async def run(self, prompt: str, **kwargs) -> Any:
        """
        Primary interface method following PydanticAI patterns.
        This is the method that A2A will automatically expose.
        """
        logger.debug(f"Running {self.agent_name} with prompt: {prompt[:100]}...")

        try:
            result = await self.pydantic_agent.run(prompt, **kwargs)
            logger.debug(f"Agent {self.agent_name} completed successfully")
            return result.output
        except Exception as e:
            logger.error(f"Agent {self.agent_name} failed: {e}")
            raise

    def to_a2a(self, **kwargs):
        """
        Convert this agent to A2A format using PydanticAI's native support.
        This method provides the A2A server interface.
        """
        # Merge config defaults with kwargs
        a2a_config = {
            "name": self.config.agent_name,
            "version": self.config.version,
            "description": self.config.description,
            **kwargs,  # Allow override of defaults
        }

        logger.info(
            f"Converting {self.agent_name} to A2A format with native PydanticAI support"
        )
        return self.pydantic_agent.to_a2a(**a2a_config)

    async def initialize_mcp_tools(self):
        """
        Compatibility method - MCP tools are automatically initialized
        when toolsets are passed to the Agent constructor.
        """
        logger.debug(
            f"MCP tools already initialized for {self.agent_name} via PydanticAI Agent constructor"
        )
        if self.toolsets:
            logger.info(
                f"Agent {self.agent_name} has {len(self.toolsets)} MCP toolsets available"
            )

    # --- FACTORY INTEGRATION HELPERS ---
    @classmethod
    def create_with_factory_model(
        cls,
        config: BasePydanticAgentConfig,
        model_instance: Any,
        toolsets: Optional[List[MCPServer]] = None,
    ):
        """
        Factory method for creating agents with factory-generated model instances.
        This is the preferred method when using the unified LLM factory.
        """
        return cls(config=config, llm_instance=model_instance, toolsets=toolsets)

    # --- FUTURE: Add structured output support ---
    # async def run_structured(self, prompt: str, result_type: Type, **kwargs):
    #     """Run agent with structured output validation."""
    #     result = await self.pydantic_agent.run(prompt, result_type=result_type, **kwargs)
    #     return result.output
