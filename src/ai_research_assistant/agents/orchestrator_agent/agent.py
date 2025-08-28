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
    async def orchestrate(self, user_prompt: str, deps=None, usage=None) -> str:
        """
        Main orchestration method.
        """
        logger.info(f"Orchestrator received task: '{user_prompt[:100]}...'")

        try:
            # Enhanced orchestration prompt with ChromaDB tool awareness
            execution_prompt = (
                "You are the Orchestrator Agent responsible for coordinating complex workflows for SafeAppealNavigator, "
                "a specialized legal case management system for WorkSafe BC and WCAT appeals. "
                "Your primary goal is to fulfill the user's request using the most appropriate tools available.\n\n"
                "**SafeAppealNavigator Context:**\n"
                "This system helps injured workers, legal advocates, and families navigate Workers' Compensation appeals. "
                "You coordinate database operations, legal document processing, research, and case management workflows.\n\n"
                "**Available ChromaDB Tools (Legal Case Management Database):**\n"
                "• chroma_create_collection - Create specialized collections for legal case organization\n"
                "• chroma_list_collections - List existing case management collections\n"
                "• chroma_add_documents - Store legal documents, medical reports, WCAT decisions with embeddings\n"
                "• chroma_query_documents - Perform semantic search for case precedents and similar documents\n"
                "• chroma_get_documents - Retrieve case documents with legal metadata filtering\n"
                "• chroma_update_documents - Modify case documents and legal metadata\n"
                "• chroma_delete_documents - Remove outdated case documents\n"
                "• chroma_get_collection_info - Get legal collection statistics and health metrics\n"
                "• chroma_modify_collection - Optimize collections for legal document search performance\n"
                "• chroma_peek_collection - Preview legal collection contents and structure\n"
                "• chroma_delete_collection - Remove entire legal collections (use with extreme caution)\n\n"
                "**SafeAppealNavigator Database Collections Framework:**\n"
                "When creating databases for 'the app', establish these legal case management collections:\n"
                "• **case_files** - Primary case documents, correspondence, claim forms, decision letters\n"
                "• **medical_records** - Medical reports, assessments, treatment records, IME reports\n"
                "• **wcat_decisions** - WCAT precedent decisions, similar cases, appeal outcomes\n"
                "• **legal_policies** - WorkSafe BC policies, procedures, regulations, guidelines\n"
                "• **templates** - Appeal letter templates, legal document formats, form templates\n"
                "• **research_findings** - Legal research results, precedent analysis, case law summaries\n\n"
                "**Task Analysis Framework for Legal Cases:**\n"
                "1. **Simple Questions** → Provide direct response with legal context\n"
                "2. **Database Setup for App** → Create comprehensive legal case management database with all 6 collections\n"
                "3. **Document Processing** → Handle legal documents, medical reports, WCAT decisions\n"
                "4. **Legal Research** → Search for precedents, policies, similar cases\n"
                "5. **Case Management** → Organize evidence, timelines, appeal preparation\n\n"
                "**Database Creation Best Practices:**\n"
                "• Use descriptive collection names that reflect legal case organization\n"
                "• Configure optimal HNSW parameters for legal document similarity search\n"
                "• Set up metadata schemas appropriate for legal case management\n"
                "• Consider user's jurisdiction (primarily BC WorkSafe and WCAT)\n"
                "• Optimize for semantic search across legal and medical terminology\n\n"
                f"**Current User Request:** '{user_prompt}'\n\n"
                "**Analysis Required:**\n"
                "If this is a database setup request for SafeAppealNavigator, create the comprehensive 6-collection "
                "legal case management system. If it's document processing, research, or case management, use the "
                "appropriate tools and provide legal context in your response.\n\n"
                "Proceed with analyzing the request and using the most appropriate ChromaDB tools or other capabilities. "
                "Always provide clear explanations of what you're creating and why it's optimized for legal case management."
            )

            # --- ADDED LOGGING as requested ---
            print("\n" + "=" * 20 + " PROMPT SENT TO LLM " + "=" * 20)
            print(execution_prompt)
            print("=" * 62 + "\n")
            # --- END LOGGING ---

            # Pass deps and usage if provided for proper context delegation
            if deps is not None and usage is not None:
                result = await self.pydantic_agent.run(
                    execution_prompt, deps=deps, usage=usage
                )
            else:
                result = await self.pydantic_agent.run(execution_prompt)

            final_answer = result.output

            return final_answer

        except Exception as e:
            logger.error(f"Error during orchestration: {e}", exc_info=True)
            return f"I'm sorry, I encountered an error while trying to process your request: {e}"
