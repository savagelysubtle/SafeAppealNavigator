# src/ai_research_assistant/agents/orchestrator_agent/agent.py
import logging
from typing import Any, List, Optional

from pydantic_ai.mcp import MCPServer

from ai_research_assistant.agents.base_pydantic_agent import (
    BasePydanticAgent,
    agent_skill,
)
from ai_research_assistant.agents.orchestrator_agent.config import (
    OrchestratorAgentConfig,
)

logger = logging.getLogger(__name__)


class OrchestratorAgent(BasePydanticAgent):
    """
    An intelligent, dynamic orchestrator that uses its tools (provided by MCP)
    to discover and delegate tasks.
    """

    def __init__(
        self,
        llm_instance: Any,
        config: Optional[OrchestratorAgentConfig] = None,
        toolsets: Optional[List[MCPServer]] = None,
    ) -> None:
        super().__init__(
            config=config or OrchestratorAgentConfig(),
            llm_instance=llm_instance,
            toolsets=toolsets,
        )
        self.config: OrchestratorAgentConfig = self.config  # type: ignore

    @agent_skill
    async def orchestrate(self, user_prompt: str) -> str:
        """
        Main orchestration method.
        """
        logger.info(f"Orchestrator received task: '{user_prompt[:100]}...'")

        try:
            # --- DEFINITIVE FIX: A more robust prompt to handle simple inputs ---
            execution_prompt = (
                "You are an orchestrator agent. Your primary goal is to answer the user's request. "
                "First, analyze the request. If it is a simple question or a greeting that can be answered directly without needing to perform an action, "
                "then provide a conversational response. "
                "If and only if the request requires an action (like searching, reading a file, or querying a database), "
                "then you must call the single most appropriate tool from your available tools to fulfill the request. "
                f"User request: '{user_prompt}'"
            )

            # --- ADDED LOGGING as requested ---
            print("\n" + "=" * 20 + " PROMPT SENT TO LLM " + "=" * 20)
            print(execution_prompt)
            print("=" * 62 + "\n")
            # --- END LOGGING ---

            result = await self.pydantic_agent.run(user_prompt=execution_prompt)

            final_answer = result.output

            return final_answer

        except Exception as e:
            logger.error(f"Error during orchestration: {e}", exc_info=True)
            return f"I'm sorry, I encountered an error while trying to process your request: {e}"
