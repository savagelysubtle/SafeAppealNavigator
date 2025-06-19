# src/ai_research_assistant/agents/orchestrator_agent/agent.py
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from pydantic import TypeAdapter, ValidationError
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.tools import Tool as PydanticAITool

from ai_research_assistant.agents.base_pydantic_agent import (
    BasePydanticAgent,
    agent_skill,
)
from ai_research_assistant.agents.orchestrator_agent.config import (
    OrchestratorAgentConfig,
)
from ai_research_assistant.core.models import (
    AnalyzeDocumentRequest,
    ApprovePlanRequest,
    ChatRequest,
    CreateFileRequest,
    InlineEditRequest,
    Part,
    StatusPart,
    TaskResult,
    UserPrompt,
)
from src.ai_research_assistant.ag_ui_backend.a2a_client import A2AClient

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
        self.a2a_client = A2AClient()

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

    async def _handle_chat(
        self, prompt: str, history: List[Dict[str, Any]]
    ) -> TaskResult:
        """Handles a standard chat request by calling the main generator."""
        return await self.generate_response(prompt, history)

    async def _handle_inline_edit(
        self, request: InlineEditRequest, history: List[Dict[str, Any]]
    ) -> TaskResult:
        """Handles an inline edit request."""
        status_part = StatusPart(
            message=f"Received inline edit request for {request.uri}"
        ).model_dump()
        return TaskResult(
            parts=[
                Part(type="application/vnd.agent-status.v1+json", content=status_part)
            ]
        )

    async def _handle_create_file(
        self, request: CreateFileRequest, history: List[Dict[str, Any]]
    ) -> TaskResult:
        """Handles a create file request."""
        status_part = StatusPart(
            message=f"Received request to create file at {request.uri}"
        ).model_dump()
        return TaskResult(
            parts=[
                Part(type="application/vnd.agent-status.v1+json", content=status_part)
            ]
        )

    async def _handle_analyze_document(
        self, request: AnalyzeDocumentRequest, history: List[Dict[str, Any]]
    ) -> TaskResult:
        """Handles an analyze document request."""
        status_part = StatusPart(
            message=f"Received request to analyze document {request.uri}"
        ).model_dump()
        return TaskResult(
            parts=[
                Part(type="application/vnd.agent-status.v1+json", content=status_part)
            ]
        )

    async def _handle_approve_plan(
        self, request: ApprovePlanRequest, history: List[Dict[str, Any]]
    ) -> TaskResult:
        """Handles a plan approval request."""
        status_part = StatusPart(
            message=f"Received approval for plan {request.plan_id}"
        ).model_dump()
        return TaskResult(
            parts=[
                Part(type="application/vnd.agent-status.v1+json", content=status_part)
            ]
        )

    @agent_skill
    async def handle_user_request(
        self, user_prompt: str, history: List[Dict[str, Any]]
    ) -> TaskResult:
        """
        Handles a user request, which can be a simple string
        or a JSON string representing a structured command from the Void IDE.
        """
        # Try to parse the user_prompt as a structured request
        try:
            prompt_data = json.loads(user_prompt)
            # Use TypeAdapter to parse and validate the structured request against the Union
            adapter = TypeAdapter(UserPrompt)
            request_model = adapter.validate_python(prompt_data)

            if isinstance(request_model, InlineEditRequest):
                return await self._handle_inline_edit(request_model, history)
            elif isinstance(request_model, CreateFileRequest):
                return await self._handle_create_file(request_model, history)
            elif isinstance(request_model, AnalyzeDocumentRequest):
                return await self._handle_analyze_document(request_model, history)
            elif isinstance(request_model, ApprovePlanRequest):
                return await self._handle_approve_plan(request_model, history)
            elif isinstance(request_model, ChatRequest):
                # Even a structured request can be a chat message
                return await self._handle_chat(request_model.prompt, history)

        except (json.JSONDecodeError, ValidationError):
            # If it's not a valid structured prompt, treat it as a simple chat message
            return await self._handle_chat(user_prompt, history)

        # Fallback in case something unexpected happens
        return TaskResult(
            status="error",
            error_message="Could not process the request.",
            parts=[Part(content="An unexpected error occurred.")],
        )

    async def generate_response(
        self, prompt: str, history: List[Dict[str, Any]]
    ) -> TaskResult:
        """
        Generates a response using the underlying Pydantic AI agent.
        This is the core logic for handling chat-like interactions.
        """
        logger.info(f"Orchestrator generating response for: '{prompt[:100]}...'")

        # For now, a mocked response.
        # In the future, this will involve the Pydantic AI agent and tool calls.
        mock_response_content = f"Orchestrator received: '{prompt}'. This would be an LLM-generated response."
        if "research" in prompt.lower():
            mock_response_content += (
                "\n(Decided to delegate to LegalResearchCoordinator - mock call)"
            )
        elif "document" in prompt.lower():
            mock_response_content += (
                "\n(Decided to delegate to DocumentProcessingCoordinator - mock call)"
            )

        return TaskResult(
            parts=[Part(content=mock_response_content, type="text/plain")],
        )

    async def run_task(
        self, task_description: str, context: Optional[Dict[str, Any]] = None
    ) -> TaskResult:
        """
        Runs a specific, complex task by leveraging the full capabilities of the
        pydantic-ai agent, including tools and graph-based execution.
        """
        logger.info(f"Orchestrator running task: '{task_description[:100]}...'")
        # This is where the original complex logic for running a task would go.
        # For now, returning a placeholder result.
        return TaskResult(
            parts=[Part(content=f"Task '{task_description}' is being processed.")]
        )

    async def _delegate_task_to_agent(
        self, agent_id: str, task_description: str, context: Dict[str, Any]
    ) -> TaskResult:
        """Delegates a task to another agent via A2A communication."""
        logger.info(f"Delegating task '{task_description}' to agent '{agent_id}'")
        # This would involve using self.a2a_client to send the request
        # For now, return a placeholder.
        return TaskResult(parts=[Part(content=f"Task delegated to {agent_id}.")])
