# src/ai_research_assistant/agents/specialized_manager_agent/browser_agent/agent.py
import logging
from typing import Any, Dict, List, Optional

from pydantic_ai.mcp import MCPServer

from ai_research_assistant.agents.base_pydantic_agent import (
    BasePydanticAgent,
    agent_skill,
)
from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)
from ai_research_assistant.core.models import (
    ConductComprehensiveResearchInput,
)

logger = logging.getLogger(__name__)


class BrowserAgentConfig(BasePydanticAgentConfig):
    """Configuration for the BrowserAgent."""

    agent_name: str = "BrowserAgent"
    agent_id: str = "browser_agent_instance_001"

    # This prompt is crucial. It tells the agent what its purpose is and hints at the tools it should use.
    pydantic_ai_system_prompt: str = (
        "You are a specialized Browser Agent. Your role is to conduct comprehensive research on the internet. "
        "You must use the available tools, such as 'brave-search_search' for web searches and 'playwright' tools for navigating web pages, "
        "to gather information based on the user's request. Synthesize the findings into a clear summary."
    )


class BrowserAgent(BasePydanticAgent):
    """
    A specialized agent for browsing the web and conducting research using MCP tools.
    """

    def __init__(
        self,
        config: Optional[BrowserAgentConfig] = None,
        toolsets: Optional[List[MCPServer]] = None,
    ) -> None:
        """Initializes the BrowserAgent, passing toolsets to the base class."""
        super().__init__(config=config or BrowserAgentConfig(), toolsets=toolsets)
        self.config: BrowserAgentConfig = self.config  # type: ignore
        logger.info(f"BrowserAgent '{self.agent_name}' initialized.")

    # The obsolete `_get_initial_tools` method has been removed.

    @agent_skill
    async def conduct_comprehensive_research(
        self,
        search_keywords: List[str],
        case_context: str,
        research_depth: str = "moderate",
        sources_to_include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Conducts comprehensive research using web search and scraping tools
        by invoking the internal pydantic-ai agent.
        """
        try:
            # Validate input using our Pydantic model
            input_data = ConductComprehensiveResearchInput(
                search_keywords=search_keywords,
                case_context=case_context,
                research_depth=research_depth,
                sources_to_include=sources_to_include or [],
            )
        except Exception as e:
            logger.error(f"Invalid input for research skill: {e}")
            return {"error": f"Invalid input provided: {e}"}

        logger.info(
            f"Conducting research for context: '{input_data.case_context[:100]}...' with keywords: {input_data.search_keywords}"
        )

        # Construct a detailed prompt for the LLM, instructing it on how to use its tools.
        # The tools will be automatically available to the agent (e.g., brave-search_search).
        prompt_for_llm = (
            f"Perform a {input_data.research_depth} research task. "
            f"The case context is: '{input_data.case_context}'. "
            f"Start by using the 'brave-search_search' tool with the following keywords: {', '.join(input_data.search_keywords)}. "
            f"If you find relevant URLs, use the 'playwright_navigate' and 'playwright_get_content' tools to read their content. "
            "Synthesize all the information you find into a comprehensive summary and identify key insights."
        )

        try:
            # Run the task using the internal pydantic_agent
            result = await self.pydantic_agent.run(user_prompt=prompt_for_llm)

            # For now, we return the direct output. In a more advanced implementation,
            # you would parse this output into the LegalResearchFindingsSummary model.
            return {
                "status": "success",
                "summary": result.output,
                "ran_tools": result.ran_tools,
            }

        except Exception as e:
            logger.error(f"Error during browser agent research: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
