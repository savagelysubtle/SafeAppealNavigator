# File: src/ai_research_assistant/agents/base_pydantic_agent.py

import asyncio
import logging
import uuid
from typing import Any, List, Optional, Type

from pydantic_ai.agent import Agent as PydanticAIAgent
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.messages import ModelMessage
from pydantic_ai.tools import Tool as PydanticAITool

# Assuming your project structure is something like:
# src/
#   ai_research_assistant/
#     agents/
#       base_pydantic_agent.py
#       base_pydantic_agent_config.py
#     core/
#       unified_llm_factory.py
#       mcp_client.py
#       env_manager.py (used by llm_factory)
#       rate_limiter.py (used by llm_factory)
from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)
from ai_research_assistant.core.mcp_client import (
    MCPClient,
)  # Assuming a basic client for now
from ai_research_assistant.core.unified_llm_factory import (
    UnifiedLLMFactory,
    get_llm_factory,
)

# from savagelysubtle_airesearchagent.core.state_manager import AgentStateManager # For skills to use

logger = logging.getLogger(__name__)


class BasePydanticAgent:
    """
    Base class for all Pydantic AI-centric agents in the ai_research_assistant project.
    It encapsulates a pydantic_ai.Agent instance and provides common setup for
    LLM, MCP client, and basic configuration.
    """

    def __init__(
        self,
        config: BasePydanticAgentConfig,
        # mcp_client: Optional[MCPClient] = None, # MCP client could be passed or initialized here
        # state_manager: Optional[AgentStateManager] = None # For skills to use
    ):
        self.config = config
        self.agent_id = config.agent_id or str(uuid.uuid4())
        self.agent_name = config.agent_name

        self.llm_factory: UnifiedLLMFactory = get_llm_factory()
        self.llm = self._initialize_llm()
        self.tools = self._get_initial_tools()

        # Initialize MCP Client - this might be more complex depending on mcp_client.py
        # For now, assuming it's instantiated simply or passed in.
        # If mcp_client is intended to be a shared dependency for tools,
        # it should be part of the `deps` for pydantic_ai.Agent.run() calls.
        self.mcp_client = MCPClient()  # Placeholder initialization

        # Initialize the core Pydantic AI agent
        # The API for pydantic_ai.Agent is different from pydantic.Agent
        self.pydantic_agent = PydanticAIAgent(
            self.llm,
            # 'instructions' might map to 'system_prompt' in pydantic_ai
            system_prompt=(
                self.config.pydantic_ai_instructions
                or self.config.pydantic_ai_system_prompt
                or ""
            ),
            tools=self.tools,
            # retries is not a direct parameter, might be part of llm config
        )

        # self.state_manager = state_manager or AgentStateManager() # For skills to use

        logger.info(
            f"Initialized {self.agent_name} (ID: {self.agent_id}) with Pydantic AI."
        )

    def _initialize_llm(self) -> Any:
        """
        Initializes the LLM instance using the UnifiedLLMFactory.
        """
        llm_config = {
            "provider": self.config.llm_provider,
            "model_name": self.config.llm_model_name,
            "temperature": self.config.llm_temperature,
            "max_tokens": self.config.llm_max_tokens,
            # Potentially other params like api_key, base_url if not handled by env_manager in factory
        }
        try:
            # Assuming create_llm_from_config exists and works as expected
            return self.llm_factory.create_llm_from_config(llm_config)
        except Exception as e:
            logger.error(f"Failed to initialize LLM for {self.agent_name}: {e}")
            raise

    def _get_initial_tools(self) -> List[PydanticAITool]:
        """
        Provides a list of initial PydanticAITool instances.
        Fetches MCP tools from the MCP client manager based on agent type.
        Derived agents can override this to add their specific tools.
        """
        mcp_tools = []

        try:
            # Import here to avoid circular imports
            from ai_research_assistant.mcp_intergration import get_mcp_client_manager

            # Get MCP tools for this agent synchronously
            # We'll use asyncio.run to call the async function
            async def fetch_tools():
                mcp_manager = await get_mcp_client_manager()
                return mcp_manager.get_tools_for_agent(self.agent_name)

            mcp_tools = asyncio.run(fetch_tools())
            logger.info(f"Fetched {len(mcp_tools)} MCP tools for {self.agent_name}")

        except Exception as e:
            logger.warning(f"Failed to fetch MCP tools for {self.agent_name}: {e}")
            # Continue without MCP tools if there's an error

        return mcp_tools

    # Example of how tools wrapping MCP client could be created
    # This would live in a more specific place or be called by _get_initial_tools
    # def _create_mcp_tools(self) -> List[PydanticAITool]:
    #     """
    #     Creates Pydantic AI tools that wrap MCP client functionalities.
    #     This is a placeholder and needs actual MCP tool definitions.
    #     """
    #     mcp_tools = []
    #     # Example:
    #     # if hasattr(self.mcp_client, 'query_sql_database_tool_def'):
    #     #     tool_def = self.mcp_client.query_sql_database_tool_def() # Assuming this returns a PydanticAITool
    #     #     mcp_tools.append(tool_def)
    #     logger.info(f"Created {len(mcp_tools)} MCP tools for {self.agent_name}.")
    #     return mcp_tools

    async def run_skill(
        self,
        prompt: str,
        message_history: Optional[List[ModelMessage]] = None,
        output_type: Optional[Type[Any]] = None,
        skill_dependencies: Optional[
            Any
        ] = None,  # Dependencies for this specific skill run
        **kwargs,
    ) -> AgentRunResult:
        """
        A generic way to run a skill using the encapsulated Pydantic AI agent.
        Specific agents (Coordinators) will have more descriptively named methods
        that call this or directly use self.pydantic_agent.run().

        Args:
            prompt: The user prompt or task description for the skill.
            message_history: Optional conversation history.
            output_type: Optional Pydantic model for structured output for this specific run.
            skill_dependencies: Dependencies to pass to `pydantic_ai.Agent.run(deps=...)`.
                               This could be self.mcp_client if tools need it.

        Returns:
            AgentRunResult from pydantic_ai.Agent.
        """
        logger.debug(
            f"Running skill for {self.agent_name} with prompt: {prompt[:100]}..."
        )

        return await self.pydantic_agent.run(
            user_prompt=prompt,
            message_history=message_history,
            output_type=output_type,
            deps=skill_dependencies,
            **kwargs,
        )

    async def run_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """
        Explicitly finds and runs a tool by name with the given arguments.

        Note: This is a simplified implementation. For proper tool execution
        with context, use self.pydantic_agent.run() with appropriate prompts.

        Args:
            tool_name: The name of the tool to run.
            **kwargs: The arguments to pass to the tool's function.

        Returns:
            The result of the tool's execution.

        Raises:
            ValueError: If the tool is not found.
        """
        logger.debug(f"Attempting to run tool '{tool_name}' for {self.agent_name}.")

        tool_to_run = next((t for t in self.tools if t.name == tool_name), None)

        if not tool_to_run:
            logger.error(
                f"Tool '{tool_name}' not found in {self.agent_name}'s tool list."
            )
            raise ValueError(f"Tool '{tool_name}' not found.")

        # For direct tool execution, we would need to create a proper RunContext
        # For now, we recommend using self.pydantic_agent.run() for tool execution
        logger.warning(
            f"Direct tool execution for '{tool_name}' is not fully implemented. "
            "Use self.pydantic_agent.run() with appropriate prompts for proper tool execution."
        )

        # Return a placeholder response
        return {
            "warning": "Direct tool execution not implemented",
            "tool_name": tool_name,
            "suggestion": "Use pydantic_agent.run() for proper tool execution with context",
        }

    async def health_check(self) -> dict:
        """
        Performs a basic health check.
        For Pydantic AI, this might involve a simple LLM call.
        """
        status = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "status": "unknown",
            "llm_status": "unknown",
        }
        try:
            # A simple test prompt
            await self.pydantic_agent.run(user_prompt="Hello, are you there?")
            status["llm_status"] = "healthy"
            status["status"] = "healthy"
        except Exception as e:
            logger.error(f"Health check failed for {self.agent_name}: {e}")
            status["llm_status"] = f"unhealthy: {str(e)}"
            status["status"] = "degraded"
        return status

    def get_status(self) -> dict:
        """
        Returns basic status information about the agent.
        """
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "llm_provider": self.config.llm_provider,
            "llm_model_name": self.config.llm_model_name,
            "pydantic_ai_instructions": self.config.pydantic_ai_instructions
            is not None,
            "pydantic_ai_system_prompt": self.config.pydantic_ai_system_prompt
            is not None,
            "tools_count": len(self.tools or []),
        }
