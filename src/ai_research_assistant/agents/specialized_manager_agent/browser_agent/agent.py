# src/ai_research_assistant/agents/specialized_manager_agent/browser_agent/agent.py
import logging
from typing import Any, Dict, List, Optional

from pydantic_ai.mcp import MCPServer

from ai_research_assistant.agents.base_pydantic_agent import (
    BasePydanticAgent,
)
from ai_research_assistant.agents.specialized_manager_agent.browser_agent.config import (
    BrowserAgentConfig,
)
from ai_research_assistant.core.models import (
    ConductComprehensiveResearchInput,
)

logger = logging.getLogger(__name__)


class BrowserAgent(BasePydanticAgent):
    """
    A specialized agent for browsing the web and conducting research using MCP tools.
    """

    def __init__(
        self,
        config: Optional[BrowserAgentConfig] = None,
        llm_instance: Optional[Any] = None,
        toolsets: Optional[List[MCPServer]] = None,
    ) -> None:
        """Initializes the BrowserAgent, passing toolsets to the base class."""
        # Use the refactored BasePydanticAgent constructor
        super().__init__(
            config=config or BrowserAgentConfig(),
            llm_instance=llm_instance,
            toolsets=toolsets,
        )
        self.config: BrowserAgentConfig = self.config  # type: ignore

        logger.info(
            f"BrowserAgent '{self.config.agent_name}' initialized with "
            f"{'factory-created model' if llm_instance else 'config model'} and "
            f"{len(toolsets) if toolsets else 0} MCP toolsets."
        )

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
            f"Perform a {input_data.research_depth} research task for SafeAppealNavigator legal case management. "
            f"The case context is: '{input_data.case_context}'. "
            f"Start by using the 'brave-search_search' tool with the following keywords: {', '.join(input_data.search_keywords)}. "
            f"Focus on WorkSafe BC and WCAT legal matters, precedents, and policies. "
            f"If you find relevant URLs from authoritative sources (wcat.bc.ca, worksafebc.com, bclaws.ca, canlii.org), "
            f"use the 'playwright_navigate' and 'playwright_get_content' tools to read their content. "
            "Synthesize all the information you find into a comprehensive legal summary with proper citations and identify key insights "
            "that could support or challenge legal arguments in this workers' compensation case."
        )

        try:
            # Use PydanticAI's native run method
            result = await self.pydantic_agent.run(prompt_for_llm)

            # For now, we return the direct output. In a more advanced implementation,
            # you would parse this output into the LegalResearchFindingsSummary model.
            return {
                "status": "success",
                "summary": str(result),  # Convert result to string
                "research_context": input_data.case_context,
                "keywords_used": input_data.search_keywords,
                "research_depth": input_data.research_depth,
            }

        except Exception as e:
            logger.error(f"Error during browser agent research: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
