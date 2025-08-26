# File: src/ai_research_assistant/agents/ceo_agent/agent.py
import logging
from typing import Any, List, Optional

from pydantic_ai.mcp import MCPServer

from ai_research_assistant.agents.base_pydantic_agent import BasePydanticAgent
from ai_research_assistant.agents.ceo_agent.config import CEOAgentConfig
from ai_research_assistant.agents.orchestrator_agent.agent import OrchestratorAgent
from ai_research_assistant.agents.orchestrator_agent.config import (
    OrchestratorAgentConfig,
)

logger = logging.getLogger(__name__)


class CEOAgent(BasePydanticAgent):
    """
    The CEO Agent is the main conversational interface with the user.
    """

    def __init__(
        self,
        llm_instance: Optional[Any] = None,
        config: Optional[CEOAgentConfig] = None,
        toolsets: Optional[List[MCPServer]] = None,
    ):
        # The base class now handles everything with just the config and toolsets.
        super().__init__(
            config=config or CEOAgentConfig(),
            llm_instance=llm_instance,
            toolsets=toolsets,
        )
        self.config: CEOAgentConfig = self.config  # type: ignore

        # Pass the same toolsets to the Orchestrator it creates
        self.orchestrator = OrchestratorAgent(
            llm_instance=llm_instance,
            config=OrchestratorAgentConfig(),
            toolsets=toolsets,
        )

    async def handle_user_request(self, user_prompt: str) -> str:
        """
        Takes a raw user request and delegates to the orchestrator.
        """
        logger.info(f"CEO Agent received user request: {user_prompt}")
        orchestrator_task_prompt = user_prompt

        logger.info(
            f"CEO Agent delegating to Orchestrator with prompt: '{orchestrator_task_prompt}'"
        )

        final_result = await self.orchestrator.orchestrate(orchestrator_task_prompt)

        logger.info("CEO Agent received result from Orchestrator.")
        return final_result
