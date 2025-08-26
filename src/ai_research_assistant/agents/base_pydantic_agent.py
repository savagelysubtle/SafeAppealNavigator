# FILE: src/ai_research_assistant/agents/base_pydantic_agent.py
# (Corrected and Complete Version)

import logging
from typing import Any, List, Optional

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServer
from pydantic_ai.tools import Tool as PydanticAITool

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
        self.pydantic_agent = Agent(
            model=self.llm,
            system_prompt=(
                self.config.pydantic_ai_instructions
                or self.config.pydantic_ai_system_prompt
                or ""
            ),
            toolsets=self.toolsets,  # Pass toolsets directly to Agent
        )
        logger.info(f"Agent '{self.agent_name}' initialized successfully.")

    async def initialize_mcp_tools(self):
        """Asynchronously loads and assigns MCP tools."""
        logger.debug(f"Initializing MCP tools for {self.agent_name}...")
        mcp_tools = await self._get_mcp_tools()
        self.pydantic_agent.tools.extend(mcp_tools)
        logger.info(
            f"Asynchronously loaded {len(mcp_tools)} MCP tools for {self.agent_name}."
        )

    async def _get_mcp_tools(self) -> List[PydanticAITool]:
        """
        Retrieves tools from all configured MCP servers (toolsets).
        This method is now asynchronous.
        """
        all_tools: List[PydanticAITool] = []
        if not self.toolsets:
            return all_tools

        for toolset in self.toolsets:
            try:
                # The `tools` property of MCPServer is an async generator
                async for tool in toolset.tools:
                    all_tools.append(tool)
            except Exception as e:
                logger.error(
                    f"Failed to fetch tools from a toolset for agent {self.agent_name}: {e}"
                )
        return all_tools

    async def run_skill(self, prompt: str, **kwargs) -> Any:
        """A generic method to run the underlying PydanticAIAgent."""
        logger.debug(
            f"Running skill for {self.agent_name} with prompt: {prompt[:100]}..."
        )
        result = await self.pydantic_agent.run(prompt, **kwargs)
        return result.output
