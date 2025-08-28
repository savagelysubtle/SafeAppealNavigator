# FILE: src/ai_research_assistant/agents/base_pydantic_agent.py
# (Corrected and Complete Version)

import logging
from typing import Any, List, Optional

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServer

from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)
from ai_research_assistant.core.unified_llm_factory import get_llm_factory

logger = logging.getLogger(__name__)


# --- CRITICAL FIX: Define the @agent_skill decorator ---
def agent_skill(func):
    """
    Decorator to mark agent methods as A2A skills.
    This allows the fasta2a_wrapper to discover them.
    """
    func._is_agent_skill = True
    func._skill_name = func.__name__
    return func


class BasePydanticAgent:
    """
    A base class for all agents in the system, providing common
    initialization for LLM, MCP tools, and the underlying PydanticAIAgent.
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

        if llm_instance:
            self.llm = llm_instance
        else:
            llm_factory = get_llm_factory()
            self.llm = llm_factory.create_llm_from_config(
                {
                    "provider": self.config.llm_provider,
                    "model_name": self.config.llm_model_name,
                }
            )

        # Initialize the underlying Agent with model and toolsets
        self.pydantic_agent = Agent(  # type: ignore
            self.llm,
            system_prompt=(
                self.config.pydantic_ai_instructions
                or self.config.pydantic_ai_system_prompt
                or ""
            ),
            toolsets=self.toolsets
            if self.toolsets
            else [],  # Pass toolsets directly to Agent
        )
        logger.info(f"Agent '{self.agent_name}' initialized successfully.")

    async def initialize_mcp_tools(self):
        """
        MCP tools are already initialized when toolsets are passed to the Agent constructor.
        This method is kept for compatibility but doesn't need to do anything.
        """
        logger.debug(
            f"MCP tools already initialized for {self.agent_name} via toolsets parameter"
        )
        if self.toolsets:
            logger.info(
                f"Agent {self.agent_name} has {len(self.toolsets)} MCP toolsets available."
            )

    async def run_skill(self, prompt: str, **kwargs) -> Any:
        """A generic method to run the underlying PydanticAIAgent."""
        logger.debug(
            f"Running skill for {self.agent_name} with prompt: {prompt[:100]}..."
        )
        result = await self.pydantic_agent.run(prompt, **kwargs)
        return result.output

    def to_a2a(self, *args, **kwargs):
        """
        Convert this agent to A2A format by delegating to the underlying pydantic_agent.
        This ensures that registered tools are properly available in the A2A interface.
        """
        logger.info(f"Converting {self.agent_name} to A2A format with registered tools")
        return self.pydantic_agent.to_a2a(*args, **kwargs)
