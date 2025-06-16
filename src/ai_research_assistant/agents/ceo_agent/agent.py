# File: src/ai_research_assistant/agents/ceo_agent/agent.py
import logging

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
    It understands the user's high-level goals and delegates the work
    to the Orchestrator Agent.
    """

    def __init__(self, config: CEOAgentConfig | None = None):
        config = config or CEOAgentConfig()
        super().__init__(config=config)
        self.config: CEOAgentConfig = config
        self.orchestrator = OrchestratorAgent(OrchestratorAgentConfig())

    async def handle_user_request(self, user_prompt: str) -> str:
        """
        Takes a raw user request, formulates a task for the orchestrator,
        and returns the final result.
        """
        logger.info(f"CEO Agent received user request: {user_prompt}")

        # For this refactoring, we will pass the user's request directly to the orchestrator.
        # In a more complex implementation, the CEO might first use its own LLM
        # to refine or clarify the prompt before delegation.
        orchestrator_task_prompt = user_prompt

        logger.info(
            f"CEO Agent delegating to Orchestrator with prompt: '{orchestrator_task_prompt}'"
        )

        # Delegate the task to the Orchestrator Agent
        final_result = await self.orchestrator.orchestrate(orchestrator_task_prompt)

        logger.info("CEO Agent received result from Orchestrator.")
        return final_result
