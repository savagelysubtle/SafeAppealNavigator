# src/ai_research_assistant/agents/orchestrator_agent/agent.py
import logging
import uuid
from typing import Any, Dict, List, Optional

from pydantic_ai.agent import AgentRunResult
from pydantic_ai.tools import Tool as PydanticAITool

from ai_research_assistant.agents.base_pydantic_agent import BasePydanticAgent
from ai_research_assistant.agents.orchestrator_agent.config import (
    OrchestratorAgentConfig,
)
from ai_research_assistant.core.models import Part, TaskResult

logger = logging.getLogger(__name__)


class OrchestratorAgent(BasePydanticAgent):
    """
    The Orchestrator Agent receives high-level tasks, breaks them down,
    and delegates sub-tasks to specialized agents.
    """

    def __init__(self, config: OrchestratorAgentConfig | None = None):
        # Ensure a default config is used if none is provided.
        config = config or OrchestratorAgentConfig()
        super().__init__(config=config)
        self.config: OrchestratorAgentConfig = config

    def _get_initial_tools(self) -> List[PydanticAITool]:
        """
        Defines the tools available to the Orchestrator, which correspond to
        the capabilities of the specialized agents it can command.
        """
        tools = [
            PydanticAITool(
                function=self.delegate_to_browser_agent,
                name="delegate_to_browser_agent",
                description="Delegate a web browsing task to the Browser Agent. Use this for searching the web, reading articles, or extracting information from websites.",
            ),
            PydanticAITool(
                function=self.delegate_to_document_agent,
                name="delegate_to_document_agent",
                description="Delegate a document analysis task to the Document Agent. Use this for reading, summarizing, or extracting information from local documents (PDF, DOCX, etc.).",
            ),
        ]
        return tools

    async def delegate_to_browser_agent(self, task_prompt: str) -> str:
        """
        A tool that instantiates and runs the BrowserAgent for a specific task.
        """
        logger.info(f"Orchestrator delegating to BrowserAgent: {task_prompt}")
        # In a real scenario, you would instantiate the agent and run it.
        # from ai_research_assistant.agents.specialized.browser_agent.agent import BrowserAgent
        # from ai_research_assistant.agents.specialized.browser_agent.config import BrowserAgentConfig
        # browser_agent = BrowserAgent(BrowserAgentConfig())
        # result = await browser_agent.run_skill(prompt=task_prompt)
        # return str(result.output)
        return f"Placeholder: BrowserAgent completed task: {task_prompt}"

    async def delegate_to_document_agent(self, task_prompt: str) -> str:
        """
        A tool that instantiates and runs the DocumentAgent for a specific task.
        """
        logger.info(f"Orchestrator delegating to DocumentAgent: {task_prompt}")
        # Placeholder implementation
        return f"Placeholder: DocumentAgent completed task: {task_prompt}"

    async def orchestrate(self, user_prompt: str) -> str:
        """
        Main method for the orchestrator to process a user request.
        It uses its LLM capabilities to decide which tool(s) to use.
        """
        logger.info(f"Orchestrator received task: {user_prompt}")
        result: AgentRunResult = await self.run_skill(prompt=user_prompt)

        # --- TEMPORARY DEBUGGING ---
        # Log the type and attributes of the result to understand its structure
        logger.info(f"DEBUG: Type of result is {type(result)}")
        logger.info(f"DEBUG: Attributes of result: {dir(result)}")
        try:
            # Try to log the result as a dict if possible
            logger.info(f"DEBUG: Result as dict: {vars(result)}")
        except TypeError:
            logger.info(
                f"DEBUG: Could not convert result to dict. Raw result: {result}"
            )
        # --- END TEMPORARY DEBUGGING ---

        # The logic below is likely incorrect and will be fixed after debugging.
        # For now, we return a simple output.

        # if hasattr(result, 'llm_response') and result.llm_response.message.tool_calls:
        #     tool_call = result.llm_response.message.tool_calls[0]
        #     tool_name = tool_call.function.name
        #     tool_args_str = tool_call.function.arguments
        #     tool_args = json.loads(tool_args_str)

        #     logger.info(f"Orchestrator is calling tool: {tool_name} with args: {tool_args}")

        #     return f"Orchestrator decided to use tool '{tool_name}' with arguments {tool_args_str}. The final result would be processed here."

        return str(result.output)

    async def handle_full_research_workflow(
        self,
        user_query: str,
        initial_document_mcp_paths: Optional[List[str]] = None,
        workflow_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Initiates and manages a full legal research workflow.
        This method will set up and run the pydantic-graph.
        """
        logger.info(
            f"Orchestrator: Starting full research workflow for query: '{user_query[:100]}...'"
        )
        workflow_id = str(uuid.uuid4())

        # Placeholder for pydantic-graph execution
        # initial_state = {
        #     "workflow_id": workflow_id,
        #     "user_query": user_query,
        #     "initial_document_mcp_paths": initial_document_mcp_paths or [],
        #     "workflow_options": workflow_options or {},
        #     "status": "pending_intake",
        #     "document_processing_summary": None,
        #     "research_findings_summary": None,
        #     "final_report_mcp_path": None,
        # }
        # graph_run_result = await self.workflow_graph.run(state=initial_state)
        # final_output = graph_run_result.output
        # final_state = graph_run_result.state

        # Mocked response
        mock_final_report_path = f"/mcp/reports/{workflow_id}/final_report.md"
        logger.warning(
            "Pydantic-graph execution is mocked for 'handle_full_research_workflow'."
        )

        # Simulate phases based on WORKFLOWS.MD
        # 1. Document Intake (Conceptual call to DocumentProcessingCoordinator)
        doc_processing_summary = {
            "case_id": workflow_id,
            "processed_documents_count": len(initial_document_mcp_paths or []),
            "overall_status": "Completed",
        }

        # 2. Research Phase (Conceptual call to LegalResearchCoordinator)
        research_findings_summary = {
            "research_query_summary": user_query,
            "findings_count": 5,
            "key_insights": ["Mock insight 1"],
        }

        # 3. Query & Synthesis (Conceptual call to DataQueryCoordinator)
        # report_artifact_mcp_path = mock_final_report_path

        # 4. Finalize (Conceptual reading of report)
        # final_report_content = f"Mock report for query: {user_query}"

        return {
            "workflow_id": workflow_id,
            "status": "completed_mock",  # graph_run_result.state.get("status", "unknown")
            "summary_report_mcp_path": mock_final_report_path,  # final_state.get("final_report_mcp_path")
            # "final_report_content": final_report_content # If returning content directly
        }

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Retrieves the current status and progress of a given workflow ID.
        """
        logger.info(f"Orchestrator: Getting status for workflow ID: {workflow_id}")
        # Placeholder: In a real system, this would query the pydantic-graph persistence layer.
        # state = await self.workflow_graph.persistence.load_state(workflow_id)
        mock_state = {
            "workflow_id": workflow_id,
            "status": "in_progress_mock",
            "current_phase": "ResearchPhase",
            "progress_percentage": 66,
            "details": {
                "message": "Currently conducting web searches and WCAT scraping."
            },
        }
        logger.warning(
            "Pydantic-graph status retrieval is mocked for 'get_workflow_status'."
        )
        return mock_state

    async def handle_user_request(
        self, user_prompt: str, ag_ui_tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Handles a generic user request, potentially for interactive chat or simpler tasks.
        This might involve a simpler pydantic-graph or direct LLM interaction.
        """
        logger.info(
            f"Orchestrator: Handling user request (chat/simple): '{user_prompt[:100]}...'"
        )

        # Use the orchestrator's Pydantic AI agent for a direct response or simple task.
        # This is where the `interactive chat with orchestrator` workflow would primarily hit.
        # If the orchestrator decides to delegate, it would use its tools (e.g., find_agent_for_task)
        # and then conceptually make an A2A call (which might be abstracted by a graph node).

        # For this example, let's assume it tries to answer directly or find a coordinator.
        # The `pydantic_ai_system_prompt` guides it to use tools for delegation.

        # The `deps` for the run method would include instances of clients if tools need them.
        # For example, if `find_coordinator_agent` tool needs `self.mcp_client`.
        # This depends on how tools are defined and if they expect dependencies via `deps`.
        # For simplicity, assuming tools can access `self.mcp_client` if they are methods of this class
        # or if `self.pydantic_agent` was initialized with `deps_type` and `deps`.

        # run_result: AgentRunResult = await self.pydantic_agent.run(prompt=user_prompt)
        # For now, a mocked response.
        mock_response_content = f"Orchestrator received: '{user_prompt}'. This would be an LLM-generated response, potentially after calling coordinator agents if needed."
        if "research" in user_prompt.lower():
            mock_response_content += (
                "\n(Decided to delegate to LegalResearchCoordinator - mock call)"
            )
        elif "document" in user_prompt.lower():
            mock_response_content += (
                "\n(Decided to delegate to DocumentProcessingCoordinator - mock call)"
            )

        # The response should be structured as a TaskResult for the A2A client
        task_result = TaskResult(
            status="completed",
            parts=[Part(content=mock_response_content, type="text/plain")],
        )
        return task_result.model_dump(exclude_none=True)
