# src/ai_research_assistant/agents/base_pydantic_agent.py
import logging
import uuid
from typing import Any, List

from pydantic_ai.agent import Agent as PydanticAIAgent
from pydantic_ai.tools import Tool as PydanticAITool

from .base_pydantic_agent_config import BasePydanticAgentConfig
from ..core.unified_llm_factory import UnifiedLLMFactory, get_llm_factory

logger = logging.getLogger(__name__)


def agent_skill(func):
    """
    Decorator to mark agent methods as A2A skills.

    This allows the FastA2A wrapper to discover and expose them as part of the
    agent's public capabilities.

    Usage:
        @agent_skill
        async def handle_user_request(self, prompt: str) -> TaskResult:
            ...
    """
    func._is_agent_skill = True
    func._skill_name = func.__name__
    return func


class BasePydanticAgent:
    """
    Base class for all agents, encapsulating a PydanticAIAgent instance.

    This class handles the core setup for an agent, including LLM initialization.
    It uses an asynchronous pattern for loading MCP tools to prevent blocking
    during instantiation, which is a critical best practice for async applications.
    """

    def __init__(self, config: BasePydanticAgentConfig) -> None:
        """
        Initializes the agent's core components synchronously.

        Note: MCP tools are not loaded in the constructor. They must be loaded
        by calling the `async def initialize_mcp_tools()` method after the
        agent instance has been created.

        Args:
            config: The configuration object for the agent.
        """
        self.config: BasePydanticAgentConfig = config
        self.agent_id: str = config.agent_id or str(uuid.uuid4())
        self.agent_name: str = config.agent_name

        self.llm_factory: UnifiedLLMFactory = get_llm_factory()
        self.llm: Any = self._initialize_llm()

        # Initialize the underlying PydanticAIAgent with an EMPTY tool list.
        # Tools will be added later via the async initialize_mcp_tools method.
        self.pydantic_agent = PydanticAIAgent(
            llm=self.llm,
            system_prompt=(
                self.config.pydantic_ai_instructions
                or self.config.pydantic_ai_system_prompt
                or ""
            ),
            tools=[],
        )
        logger.info(
            f"Initialized {self.agent_name} (ID: {self.agent_id}). "
            "Call `initialize_mcp_tools()` to load its tools."
        )

    def _initialize_llm(self) -> Any:
        """
        Sets up the LLM instance for the agent using the central factory.

        Returns:
            An initialized LLM client instance.
        """
        llm_config = {
            "provider": self.config.llm_provider,
            "model_name": self.config.llm_model_name,
            "temperature": self.config.llm_temperature,
            "max_tokens": self.config.llm_max_tokens,
        }
        try:
            return self.llm_factory.create_llm_from_config(llm_config)
        except Exception as e:
            logger.error(f"Failed to initialize LLM for {self.agent_name}: {e}")
            raise

    async def initialize_mcp_tools(self) -> None:
        """
        Asynchronously loads MCP tools and adds them to the agent.

        This method is the second half of the agent's setup and must be
        called after instantiation to make the agent fully operational.
        """
        logger.info(f"Asynchronously loading MCP tools for {self.agent_name}...")
        mcp_tools = await self._get_mcp_tools()

        # --- CORRECTED LOGIC ---
        # The `tools` attribute on a PydanticAIAgent is a property that expects
        # a full list. You cannot append to it directly. The correct way is
        # to assign a new list containing both old and new tools.
        existing_tools = self.pydantic_agent.tools or []
        self.pydantic_agent.tools = existing_tools + mcp_tools
        # --- END CORRECTION ---

        logger.info(
            f"Successfully loaded {len(mcp_tools)} MCP tools for {self.agent_name}."
        )

    async def _get_mcp_tools(self) -> List[PydanticAITool]:
        """
        Asynchronously fetches MCP tools for this agent from the central manager.

        Returns:
            A list of PydanticAITool instances configured for this agent.
        """
        try:
            from ai_research_assistant.mcp.client import get_mcp_client_manager

            mcp_manager = await get_mcp_client_manager()
            tools = mcp_manager.get_tools_for_agent(self.agent_name)
            logger.info(f"Fetched {len(tools)} MCP tools for {self.agent_name}")
            return tools
        except Exception as e:
            logger.warning(
                f"Failed to fetch MCP tools for {self.agent_name}: {e}", exc_info=True
            )
            return []

    async def run_skill(self, prompt: str, **kwargs: Any) -> Any:
        """
        A generic way to run a skill using the encapsulated Pydantic AI agent.

        Args:
            prompt: The user prompt or task description for the skill.
            **kwargs: Additional arguments to pass to the pydantic_agent.run method.

        Returns:
            The output from the Pydantic AI agent's execution.
        """
        logger.debug(
            f"Running skill for {self.agent_name} with prompt: {prompt[:100]}..."
        )
        result = await self.pydantic_agent.run(user_prompt=prompt, **kwargs)
        return result.output
