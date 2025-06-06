# src/ai_research_assistant/agents/legal_research_coordinator/agent.py
import logging
from typing import List, Dict, Any, Optional

from pydantic_ai.tool import Tool as PydanticAITool

from savagelysubtle_airesearchagent.agents.base_pydantic_agent import BasePydanticAgent
from savagelysubtle_airesearchagent.agents.base_pydantic_agent_config import BasePydanticAgentConfig
from savagelysubtle_airesearchagent.core.models import (
    ConductComprehensiveResearchInput,
    LegalResearchFindingsSummary,
    ResearchFinding
)
# from savagelysubtle_airesearchagent.mcp_integration.shared_tools.web_tools import WebSearchTool, WCATScrapingTool # Example
# from savagelysubtle_airesearchagent.mcp_integration.shared_tools.db_tools import QueryVectorDatabaseTool # Example

from ai_research_assistant.core.mcp_client import fetch_and_wrap_mcp_tools
from ai_research_assistant.config.global_settings import settings

import asyncio

logger = logging.getLogger(__name__)

class LegalResearchCoordinatorConfig(BasePydanticAgentConfig):
    agent_name: str = "LegalResearchCoordinator"
    agent_id: str = "legal_research_coordinator_instance_001"
    default_web_search_engine: str = "google_mcp_tool" # Example
    default_wcat_endpoint: str = "wcat_official_site_mcp_tool" # Example
    pydantic_ai_system_prompt: str = (
        "You are a Legal Research Coordinator. Your role is to conduct comprehensive legal research based on provided keywords and case context. "
        "This involves performing web searches, scraping WCAT (Workers' Compensation Appeal Tribunal) decisions, and matching findings against relevant policies. "
        "You will use available tools for web searching, WCAT data access, and potentially vector database lookups for policy matching. "
        "Summarize your findings and provide key insights."
    )

class LegalResearchCoordinator(BasePydanticAgent):
    def __init__(self, config: Optional[LegalResearchCoordinatorConfig] = None):
        super().__init__(config=config or LegalResearchCoordinatorConfig())
        self.coordinator_config: LegalResearchCoordinatorConfig = self.config # type: ignore
        logger.info(f"LegalResearchCoordinator '{self.agent_name}' initialized.")

    def _get_initial_tools(self) -> List[PydanticAITool]:
        base_tools = super()._get_initial_tools()
        coordinator_tools: List[PydanticAITool] = []
        # ...add any in-house tools here...

        try:
            mcp_tools = asyncio.run(fetch_and_wrap_mcp_tools(settings.MCP_SERVER_URL))
        except Exception as e:
            logger.error(f"Failed to fetch MCP tools: {e}")
            mcp_tools = []

        logger.warning("LegalResearchCoordinator tools are placeholders. Implement actual MCP tools.")
        return base_tools + coordinator_tools + mcp_tools

    async def conduct_comprehensive_research(
        self,
        search_keywords: List[str],
        case_context: str,
        research_depth: str = "moderate",
        sources_to_include: Optional[List[str]] = None,
        max_results_per_source: int = 10
    ) -> Dict[str, Any]: # Should match LegalResearchFindingsSummary schema
        """
        Conducts comprehensive legal research and policy analysis.
        Input should match ConductComprehensiveResearchInput schema.
        Output should match LegalResearchFindingsSummary schema.
        """
        try:
            input_data = ConductComprehensiveResearchInput(
                search_keywords=search_keywords,
                case_context=case_context,
                research_depth=research_depth,
                sources_to_include=sources_to_include,
                max_results_per_source=max_results_per_source
            )
        except Exception as e:
            logger.error(f"Invalid input for conduct_comprehensive_research: {e}")
            # Return an error structure that matches the expected output schema if possible
            error_summary = LegalResearchFindingsSummary(
                research_query_summary=f"Invalid input: {str(e)}",
                findings=[],
                overall_summary="Failed due to invalid input.",
                key_insights=[],
                mcp_path_to_full_report=None
            )
            return error_summary.model_dump(exclude_none=True)

        logger.info(f"Conducting research for context: '{input_data.case_context[:100]}...' with keywords: {input_data.search_keywords}")

        all_findings: List[ResearchFinding] = []

        # 1. Web Search (via MCP tool) - Conceptual
        #    - web_search_results = await self.pydantic_agent.run_tool("web_search_tool", query=" ".join(input_data.search_keywords), num_results=input_data.max_results_per_source)
        #    - for res in web_search_results.get("results", []):
        #    -    all_findings.append(ResearchFinding(source_name="WebSearch", title=res.get("title"), url=res.get("url"), summary=res.get("snippet")))
        logger.warning("Mocked Web Search for LegalResearchCoordinator.")
        all_findings.append(ResearchFinding(source_name="MockWebSearch", title="Mock Web Result 1", url="http://example.com/web1", summary="Relevant finding from web."))

        # 2. WCAT Scraping (via MCP tool or internal) - Conceptual
        #    - wcat_results = await self.pydantic_agent.run_tool("wcat_scraping_tool", keywords=input_data.search_keywords, max_decisions=input_data.max_results_per_source)
        #    - for dec in wcat_results.get("decisions", []):
        #    -    all_findings.append(ResearchFinding(source_name="WCATSearch", title=dec.get("decision_id"), url=dec.get("url"), summary=dec.get("summary")))
        logger.warning("Mocked WCAT Scraping for LegalResearchCoordinator.")
        all_findings.append(ResearchFinding(source_name="MockWCATSearch", title="WCAT Decision XYZ", url="http://wcat.example/xyz", summary="Key WCAT decision summary."))

        # 3. Policy Matching (internal LLM + data tools via MCP) - Conceptual
        #    - relevant_policies = await self.pydantic_agent.run(prompt=f"Find relevant policies for: {input_data.case_context} and keywords {input_data.search_keywords}")
        #    - for policy in relevant_policies.result.get("policies", []):
        #    -    all_findings.append(ResearchFinding(source_name="PolicyDB", title=policy.get("name"), summary=policy.get("description")))
        logger.warning("Mocked Policy Matching for LegalResearchCoordinator.")
        all_findings.append(ResearchFinding(source_name="MockPolicyDB", title="Policy 123: Relevant Conduct", summary="This policy applies to the case context."))

        # Synthesize overall summary
        # synthesized_summary_text = await self.pydantic_agent.run(prompt=f"Summarize these findings: {json.dumps([f.dict() for f in all_findings])}")
        mock_overall_summary = f"Comprehensive research for '{input_data.case_context[:50]}...' yielded {len(all_findings)} findings. Key themes include..."
        mock_key_insights = ["Insight A based on findings.", "Insight B regarding policy."]

        summary_output = LegalResearchFindingsSummary(
            research_query_summary=f"Keywords: {input_data.search_keywords}, Context: {input_data.case_context[:100]}...",
            findings=all_findings,
            overall_summary=mock_overall_summary, # synthesized_summary_text.result.get("summary", "Could not synthesize summary.")
            key_insights=mock_key_insights,
            research_time_seconds=25.5, # Mock time
            mcp_path_to_full_report=f"/mcp/reports/{uuid.uuid4()}/legal_research_report.json"
        )

        return summary_output.model_dump(exclude_none=True)