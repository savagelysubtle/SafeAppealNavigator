# src/ai_research_assistant/agents/specialized_manager_agent/browser_agent/agent.py
import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional

from pydantic_ai.tools import Tool as PydanticAITool

from ai_research_assistant.agents.base_pydantic_agent import BasePydanticAgent
from ai_research_assistant.agents.base_pydantic_agent_config import (
    BasePydanticAgentConfig,
)
from ai_research_assistant.config.global_settings import settings
from ai_research_assistant.core.mcp_client import fetch_and_wrap_mcp_tools
from ai_research_assistant.core.models import (
    ConductComprehensiveResearchInput,
    LegalResearchFindingsSummary,
    ResearchFinding,
)

logger = logging.getLogger(__name__)


class BrowserAgentConfig(BasePydanticAgentConfig):
    agent_name: str = "BrowserAgent"
    agent_id: str = "browser_agent_instance_001"
    default_web_search_engine: str = "google_mcp_tool"
    default_wcat_endpoint: str = "wcat_official_site_mcp_tool"
    pydantic_ai_system_prompt: str = (
        "You are a Browser Agent. Your role is to conduct comprehensive research based on provided keywords and case context. "
        "This involves performing web searches, and scraping websites like WCAT (Workers' Compensation Appeal Tribunal) decisions. "
        "You will use available tools for web searching and data access. "
        "Summarize your findings and provide key insights."
    )


class BrowserAgent(BasePydanticAgent):
    def __init__(self, config: Optional[BrowserAgentConfig] = None):
        super().__init__(config=config or BrowserAgentConfig())
        self.agent_config: BrowserAgentConfig = self.config  # type: ignore
        logger.info(f"BrowserAgent '{self.agent_name}' initialized.")

    def _get_initial_tools(self) -> List[PydanticAITool]:
        base_tools = super()._get_initial_tools()
        coordinator_tools: List[PydanticAITool] = []

        try:
            mcp_tools = asyncio.run(fetch_and_wrap_mcp_tools(settings.MCP_SERVER_URL))
        except Exception as e:
            logger.error(f"Failed to fetch MCP tools: {e}")
            mcp_tools = []

        logger.warning(
            "BrowserAgent tools are placeholders. Implement actual MCP tools."
        )
        return base_tools + coordinator_tools + mcp_tools

    async def conduct_comprehensive_research(
        self,
        search_keywords: List[str],
        case_context: str,
        research_depth: str = "moderate",
        sources_to_include: Optional[List[str]] = None,
        max_results_per_source: int = 10,
    ) -> Dict[str, Any]:
        """
        Conducts comprehensive research using web search and scraping tools.
        """
        try:
            input_data = ConductComprehensiveResearchInput(
                search_keywords=search_keywords,
                case_context=case_context,
                research_depth=research_depth,
                sources_to_include=sources_to_include,
                max_results_per_source=max_results_per_source,
            )
        except Exception as e:
            logger.error(f"Invalid input for conduct_comprehensive_research: {e}")
            error_summary = LegalResearchFindingsSummary(
                research_query_summary=f"Invalid input: {str(e)}",
                findings=[],
                overall_summary="Failed due to invalid input.",
                key_insights=[],
                mcp_path_to_full_report=None,
            )
            return error_summary.model_dump(exclude_none=True)

        logger.info(
            f"Conducting research for context: '{input_data.case_context[:100]}...' with keywords: {input_data.search_keywords}"
        )

        all_findings: List[ResearchFinding] = []

        logger.warning("Mocked Web Search for BrowserAgent.")
        all_findings.append(
            ResearchFinding(
                source_name="MockWebSearch",
                title="Mock Web Result 1",
                url="http://example.com/web1",
                summary="Relevant finding from web.",
            )
        )

        logger.warning("Mocked WCAT Scraping for BrowserAgent.")
        all_findings.append(
            ResearchFinding(
                source_name="MockWCATSearch",
                title="WCAT Decision XYZ",
                url="http://wcat.example/xyz",
                summary="Key WCAT decision summary.",
            )
        )

        mock_overall_summary = f"Comprehensive research for '{input_data.case_context[:50]}...' yielded {len(all_findings)} findings. Key themes include..."
        mock_key_insights = [
            "Insight A based on findings.",
            "Insight B regarding policy.",
        ]

        summary_output = LegalResearchFindingsSummary(
            research_query_summary=f"Keywords: {input_data.search_keywords}, Context: {input_data.case_context[:100]}...",
            findings=all_findings,
            overall_summary=mock_overall_summary,
            key_insights=mock_key_insights,
            research_time_seconds=25.5,
            mcp_path_to_full_report=f"/mcp/reports/{uuid.uuid4()}/legal_research_report.json",
        )

        return summary_output.model_dump(exclude_none=True)
