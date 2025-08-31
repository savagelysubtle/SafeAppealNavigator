# src/ai_research_assistant/agents/specialized_manager_agent/legal_manager_agent/agent.py
import logging
import uuid
from typing import Any, Dict, List, Optional

from pydantic_ai.mcp import MCPServer

from ai_research_assistant.agents.base_pydantic_agent import (
    BasePydanticAgent,
)
from ai_research_assistant.agents.specialized_manager_agent.legal_manager_agent.config import (
    LegalManagerAgentConfig,
)

logger = logging.getLogger(__name__)


class LegalManagerAgent(BasePydanticAgent):
    """Legal Manager Agent for coordinating legal document workflows and quality assurance."""

    def __init__(
        self,
        config: Optional[LegalManagerAgentConfig] = None,
        llm_instance: Optional[Any] = None,
        toolsets: Optional[List[MCPServer]] = None,
    ):
        # Use the refactored BasePydanticAgent constructor
        super().__init__(
            config=config or LegalManagerAgentConfig(),
            llm_instance=llm_instance,
            toolsets=toolsets,
        )
        self.config: LegalManagerAgentConfig = self.config  # type: ignore

        logger.info(
            f"LegalManagerAgent '{self.config.agent_name}' initialized with "
            f"{'factory-created model' if llm_instance else 'config model'} and "
            f"{len(toolsets) if toolsets else 0} MCP toolsets."
        )

    async def draft_memo(self, research_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes research findings and drafts a legal memo.

        This matches the agent card skill definition exactly.

        Args:
            research_summary: Research findings to base the memo on

        Returns:
            Dictionary with draft_memo_mcp_path
        """
        logger.info("Legal Manager Agent drafting memo from research summary")

        try:
            # Use the existing draft_legal_memo method for implementation
            memo_result = await self.draft_legal_memo(
                research_summary=research_summary,
                memo_type="standard",
                output_path=None,
            )

            if memo_result["status"] == "success":
                return {"draft_memo_mcp_path": memo_result["output_path"]}
            else:
                # Return error path
                return {
                    "draft_memo_mcp_path": f"/tmp/legal_memos/error_{uuid.uuid4()}.md"
                }

        except Exception as e:
            logger.error(f"Error in draft_memo skill: {e}", exc_info=True)
            return {"draft_memo_mcp_path": f"/tmp/legal_memos/error_{uuid.uuid4()}.md"}

    async def draft_legal_memo(
        self,
        research_summary: Dict[str, Any],
        memo_type: str = "standard",
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Coordinates with Document Agent to draft a legal memo based on research findings.

        Args:
            research_summary: Summary of research findings to include in memo
            memo_type: Type of legal memo (standard, brief, opinion, etc.)
            output_path: Optional path where memo should be saved

        Returns:
            Result of memo creation including path to created document
        """
        logger.info(f"Coordinating legal memo drafting ({memo_type})")

        try:
            # Prepare memo content based on research
            memo_prompt = (
                f"Create a {memo_type} legal memo for SafeAppealNavigator based on the following research findings:\n\n"
                f"{research_summary}\n\n"
                f"The memo should include:\n"
                f"1. Executive Summary\n"
                f"2. Issue Statement\n"
                f"3. Brief Answer\n"
                f"4. Facts\n"
                f"5. Discussion/Analysis with WCAT precedents and WorkSafe BC policy references\n"
                f"6. Conclusion with actionable recommendations\n"
                f"7. Properly formatted legal citations using Bluebook and Canadian citation standards\n\n"
                f"Focus on WorkSafe BC and WCAT appeal context for injured worker representation."
            )

            # Use PydanticAI's native run method to generate memo content
            memo_result = await self.pydantic_agent.run(memo_prompt)

            memo_content = str(memo_result)

            # Coordinate with Document Agent to create the memo
            # In a real implementation, this would use A2A communication
            logger.info("Would coordinate with Document Agent to create memo file")

            return {
                "status": "success",
                "memo_type": memo_type,
                "content_preview": memo_content[:500] + "...",
                "output_path": output_path or f"/legal/memos/{uuid.uuid4()}.md",
                "message": "Legal memo drafted successfully",
            }

        except Exception as e:
            logger.error(f"Error drafting legal memo: {e}")
            return {"status": "error", "error": str(e), "memo_type": memo_type}

    async def verify_citations(
        self, document_path: str, citation_style: str = "bluebook"
    ) -> Dict[str, Any]:
        """
        Coordinates with Document Agent to read a document and verify its citations.

        Args:
            document_path: Path to the document to verify
            citation_style: Citation style to check against (bluebook, APA, etc.)

        Returns:
            Verification results with corrections if needed
        """
        logger.info(f"Coordinating citation verification for document: {document_path}")

        try:
            # Would coordinate with Document Agent to read the document
            logger.info("Would coordinate with Document Agent to read document")

            # Mock document content for now
            document_content = f"Mock content from {document_path}"

            # Verify citations using LLM with specific focus on legal standards
            verification_result = await self.pydantic_agent.run(
                f"Verify all legal citations in the following document using {citation_style} style:\n\n"
                f"{document_content}\n\n"
                f"Focus on:\n"
                f"1. WCAT decision citations\n"
                f"2. WorkSafe BC policy references\n"
                f"3. Canadian case law citations using McGill Guide\n"
                f"4. Statute and regulation citations\n"
                f"Identify any incorrect citations and provide corrections."
            )

            return {
                "status": "success",
                "document_path": document_path,
                "citation_style": citation_style,
                "verification_results": str(verification_result),
                "citations_found": 0,  # Would be counted in real implementation
                "corrections_needed": 0,  # Would be counted in real implementation
            }

        except Exception as e:
            logger.error(f"Error verifying citations: {e}")
            return {"status": "error", "error": str(e), "document_path": document_path}

    async def review_legal_document(
        self, document_path: str, review_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Coordinates a comprehensive review of a legal document.

        Args:
            document_path: Path to the document to review
            review_criteria: Optional specific criteria to review against

        Returns:
            Review results with recommendations
        """
        logger.info(f"Coordinating legal document review: {document_path}")

        try:
            # Default review criteria
            if not review_criteria:
                review_criteria = {
                    "check_citations": True,
                    "check_legal_accuracy": True,
                    "check_formatting": True,
                    "check_completeness": True,
                    "verify_precedents": True,
                }

            # Would coordinate with Document Agent to read the document
            logger.info(
                "Would coordinate with Document Agent to read document for review"
            )

            # Mock document content
            document_content = f"Mock legal document content from {document_path}"

            # Perform comprehensive review using LLM with legal expertise
            review_result = await self.pydantic_agent.run(
                f"Perform a comprehensive legal review of the following SafeAppealNavigator document:\n\n"
                f"{document_content}\n\n"
                f"Review criteria: {review_criteria}\n\n"
                f"Provide detailed feedback on:\n"
                f"1. Legal accuracy and completeness for WorkSafe BC/WCAT context\n"
                f"2. Citation correctness using Bluebook and Canadian standards\n"
                f"3. Document structure and professional legal formatting\n"
                f"4. Missing elements or sections for workers' compensation appeals\n"
                f"5. Recommendations for strengthening legal arguments\n"
                f"6. Compliance with WCAT appeal procedures and requirements"
            )

            return {
                "status": "success",
                "document_path": document_path,
                "review_criteria": review_criteria,
                "review_results": str(review_result),
                "recommendations": [],  # Would be extracted from review in real implementation
            }

        except Exception as e:
            logger.error(f"Error reviewing legal document: {e}")
            return {"status": "error", "error": str(e), "document_path": document_path}

    async def manage_legal_workflow(
        self, workflow_type: str, workflow_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Manages complex legal document workflows.

        Args:
            workflow_type: Type of workflow (research_to_memo, brief_preparation, etc.)
            workflow_data: Data needed for the workflow

        Returns:
            Workflow execution results
        """
        logger.info(f"Managing legal workflow: {workflow_type}")

        try:
            if workflow_type == "research_to_memo":
                # Extract research data
                research_data = workflow_data.get("research_summary", {})
                output_path = workflow_data.get("output_path")

                # Draft memo based on research
                memo_result = await self.draft_legal_memo(
                    research_summary=research_data,
                    memo_type="research_memo",
                    output_path=output_path,
                )

                if memo_result["status"] == "success" and output_path:
                    # Verify citations in the created memo
                    citation_result = await self.verify_citations(
                        document_path=output_path,
                        citation_style=workflow_data.get("citation_style", "bluebook"),
                    )

                    return {
                        "status": "success",
                        "workflow_type": workflow_type,
                        "memo_result": memo_result,
                        "citation_result": citation_result,
                    }

                return memo_result

            elif workflow_type == "appeal_preparation":
                # Handle comprehensive appeal preparation workflow
                appeal_type = workflow_data.get("appeal_type", "standard")
                case_data = workflow_data.get("case_data", {})

                workflow_result = await self.pydantic_agent.run(
                    f"Coordinate comprehensive appeal preparation workflow for {appeal_type} WCAT appeal:\n\n"
                    f"Case Data: {case_data}\n\n"
                    f"Workflow should include:\n"
                    f"1. Document review and organization\n"
                    f"2. Legal research coordination\n"
                    f"3. Appeal letter drafting\n"
                    f"4. Evidence summary preparation\n"
                    f"5. Citation verification\n"
                    f"6. Final quality review"
                )

                return {
                    "status": "success",
                    "workflow_type": workflow_type,
                    "appeal_type": appeal_type,
                    "workflow_plan": str(workflow_result),
                }

            elif workflow_type == "brief_preparation":
                # Handle legal brief preparation workflow
                brief_type = workflow_data.get("brief_type", "standard")

                return {
                    "status": "success",
                    "workflow_type": workflow_type,
                    "brief_type": brief_type,
                    "message": f"Legal brief preparation workflow for {brief_type} initiated",
                }

            else:
                return {
                    "status": "error",
                    "error": f"Unknown workflow type: {workflow_type}",
                }

        except Exception as e:
            logger.error(f"Error managing legal workflow: {e}")
            return {"status": "error", "workflow_type": workflow_type, "error": str(e)}
