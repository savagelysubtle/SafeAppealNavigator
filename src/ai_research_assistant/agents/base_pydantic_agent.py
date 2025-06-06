# File: src/savagelysubtle_airesearchagent/agents/base_pydantic_agent.py

import logging
import uuid
from typing import Any, List, Optional, Type

from pydantic import Agent as PydanticAIAgent
from pydantic import AgentRunResult, ModelMessage
from pydantic import Tool as PydanticAITool

# Assuming your project structure is something like:
# src/
#   savagelysubtle_airesearchagent/
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
    Base class for all Pydantic AI-centric agents in the savagelysubtle-airesearchagent project.
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

        # Initialize MCP Client - this might be more complex depending on mcp_client.py
        # For now, assuming it's instantiated simply or passed in.
        # If mcp_client is intended to be a shared dependency for tools,
        # it should be part of the `deps` for pydantic_ai.Agent.run() calls.
        self.mcp_client = MCPClient()  # Placeholder initialization

        # Initialize the core Pydantic AI agent
        # Tools will be collected and passed by derived classes or specific skill setups.
        self.pydantic_agent = PydanticAIAgent(
            model=self.llm,
            instructions=self.config.pydantic_ai_instructions,
            system_prompt=self.config.pydantic_ai_system_prompt,
            tools=self._get_initial_tools(),  # Derived classes should override or extend this
            retries=self.config.pydantic_ai_retries,
            # deps_type can be set if there's a common dependency structure for tools
            # For example, if all tools need the MCPClient:
            # deps_type=MCPClient,
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
        Derived agents should override this to add their specific tools,
        often by wrapping MCP client functionalities.

        Example:
        mcp_tools = self._create_mcp_tools()
        return mcp_tools + other_specific_tools
        """
        return []

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

        # If an output_type is provided for this specific skill,
        # we might need to run with a temporarily reconfigured agent or handle it.
        # For simplicity, PydanticAIAgent can take output_type directly in run if supported,
        # or one might create a temporary agent instance if the base `self.pydantic_agent`
        # has a conflicting default output_type.
        # However, pydantic_ai.Agent.run does not take output_type directly.
        # The output_type is part of the Agent's constructor.
        # So, if a skill needs a *different* output_type than the agent's default,
        # this approach needs refinement. Often, skills will be methods with Pydantic
        # input/output types, and the A2A wrapper handles invoking them.
        # The internal call to self.pydantic_agent.run() might use the agent's default output_type.

        if output_type and output_type != self.pydantic_agent.output_type:
            # This is a simplification. In reality, if a skill needs a *different*
            # output_type than the agent's default, you might:
            # 1. Have the agent's default output_type be a Union of all possible skill outputs.
            # 2. Create a temporary, specialized PydanticAIAgent instance for this run.
            # 3. Rely on the skill method itself being typed and FastA2A handling the output.
            logger.warning(
                f"Skill-specific output_type ({output_type}) differs from agent's default ({self.pydantic_agent.output_type}). This run will use the agent's default output handling unless the skill method is directly called by A2A."
            )

        # If tools need access to MCPClient, pass it as deps
        current_deps = skill_dependencies
        # Example: if self.pydantic_agent was initialized with deps_type=MCPClient
        # current_deps = self.mcp_client

        return await self.pydantic_agent.run(
            prompt=prompt, messages=message_history, deps=current_deps, **kwargs
        )

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
            await self.pydantic_agent.run("Hello, are you there?")
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
            "tools_count": len(self.pydantic_agent.tools or []),
        }
