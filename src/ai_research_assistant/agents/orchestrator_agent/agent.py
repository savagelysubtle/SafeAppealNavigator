# src/ai_research_assistant/agents/orchestrator_agent/agent.py
import json
import logging
from typing import List, Optional

from pydantic_ai.tools import Tool as PydanticAITool

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
    An intelligent, dynamic orchestrator that uses MCP for agent discovery
    and A2A for task delegation. It does not follow a rigid, predefined graph.
    """

    def __init__(self, config: Optional[OrchestratorAgentConfig] = None) -> None:
        """
        Initializes the OrchestratorAgent.

        Args:
            config: The configuration object for the agent. If None, a default
                    OrchestratorAgentConfig will be instantiated.
        """
        # The base class __init__ handles all necessary setup, including
        # preparing the agent to load its tools.
        super().__init__(config=config or OrchestratorAgentConfig())
        self.config: OrchestratorAgentConfig = self.config  # type: ignore

        # In a real implementation, an A2A client would be initialized here
        # self.a2a_client = A2AClient()

    def _get_initial_tools(self) -> List[PydanticAITool]:
        """
        Retrieves the tools for this agent.

        For the Orchestrator, its primary tool is the ability to find other agents.
        This is loaded from the MCP client via the base class method.
        Ensure `agent_mcp_mapping.json` grants this agent access to the `find_agent` tool.
        """
        return super()._get_initial_tools()

    @agent_skill
    async def orchestrate(self, user_prompt: str) -> str:
        """
        Main orchestration method. It uses its LLM and the `find_agent` tool
        to dynamically discover and delegate tasks to the best specialist agent.

        Args:
            user_prompt: The high-level task description from the user or CEO agent.

        Returns:
            A string containing the synthesized final answer after delegation.
        """
        logger.info(f"Orchestrator received task: '{user_prompt[:100]}...'")

        try:
            # Step 1: Use the LLM and the `find_agent` tool to decide who to talk to.
            # The PydanticAI agent will automatically see the `find_agent` tool in its
            # tool list and call it if the prompt instructs it to.
            discovery_prompt = (
                f"Based on the user's request, determine the best specialized agent to handle this task "
                f"by using the `find_agent` tool. User request: '{user_prompt}'"
            )

            # The .run() method executes the LLM call, which in turn calls the find_agent tool.
            # The result will contain the agent card of the best agent.
            discovery_result = await self.pydantic_agent.run(
                user_prompt=discovery_prompt
            )

            # The output of the tool call is a stringified JSON, so we parse it.
            agent_card = json.loads(discovery_result.output)
            agent_name = agent_card.get("agent_name")

            if not agent_name:
                raise ValueError("Could not identify a suitable agent for the task.")

            logger.info(
                f"Orchestrator discovered that '{agent_name}' is the best agent for the job."
            )

            # Step 2: Formulate a task and (simulate) delegating via A2A.
            logger.info(f"Simulating A2A delegation of task to '{agent_name}'...")

            # In a real implementation, you would use self.a2a_client here.
            # specialist_response = await self.a2a_client.send_to_agent(...)
            specialist_response_content = f"Mock response from {agent_name}: I have successfully handled the task: '{user_prompt}'"

            # Step 3: Synthesize the final response.
            final_answer = (
                f"I consulted with the {agent_name}, our specialist in this area.\n\n"
                f"Here is the result:\n{specialist_response_content}"
            )

            return final_answer

        except Exception as e:
            logger.error(f"Error during orchestration: {e}", exc_info=True)
            return f"I'm sorry, I encountered an error while trying to process your request: {e}"
