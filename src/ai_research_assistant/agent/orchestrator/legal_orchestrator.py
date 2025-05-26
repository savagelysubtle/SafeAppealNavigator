"""
Legal Research Orchestrator Agent

This agent serves as the central coordinator for the legal research system,
orchestrating workflows between intake, analysis, research, and cross-reference agents
while maintaining WCAT specialization and document source tracking.

Workflow: Intake → Manager → Optional Chat → Research/Database/Cross-reference
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.base_agent import AgentConfig, AgentTask, BaseAgent
from .agent_coordinator import AgentCoordinator
from .workflow_manager import WorkflowManager, WorkflowState

logger = logging.getLogger(__name__)


class OrchestratorMode(Enum):
    """Operating modes for the orchestrator"""

    INTAKE_PROCESSING = "intake_processing"
    RESEARCH_COORDINATION = "research_coordination"
    CHAT_INTERACTIVE = "chat_interactive"
    ANALYSIS_REVIEW = "analysis_review"
    AUTONOMOUS = "autonomous"


@dataclass
class LegalWorkflowConfig:
    """Configuration for legal workflow orchestration"""

    # Workflow settings
    enable_chat_interface: bool = True
    auto_proceed_after_intake: bool = False
    require_human_approval: bool = True

    # Agent coordination settings
    max_concurrent_agents: int = 3
    timeout_seconds: int = 1800  # 30 minutes
    retry_failed_tasks: bool = True

    # WCAT specialization settings
    wcat_database_path: Optional[str] = None
    document_source_tracking: bool = True
    insurance_company_detection: bool = True

    # Output settings
    generate_comprehensive_report: bool = True
    maintain_audit_trail: bool = True


class LegalOrchestratorAgent(BaseAgent):
    """
    Central orchestrator for legal research workflows.

    Coordinates multiple specialized agents to provide comprehensive legal analysis
    while maintaining WCAT specialization and document source tracking.

    Key Features:
    - Unified workflow management
    - Intelligent agent coordination
    - Document source tracking
    - WCAT specialization
    - Optional chat interface
    - Comprehensive reporting
    """

    def __init__(
        self,
        orchestrator_config: Optional[LegalWorkflowConfig] = None,
        agent_config: Optional[AgentConfig] = None,
        global_settings_manager=None,
        work_dir: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(
            agent_id=kwargs.get("agent_id")
            or f"legal_orchestrator_{uuid.uuid4().hex[:8]}",
            config=agent_config or AgentConfig(system_prompt=None),
            global_settings_manager=global_settings_manager,
            **kwargs,
        )

        self.orchestrator_config = orchestrator_config or LegalWorkflowConfig()
        self.work_dir = Path(work_dir or "./tmp/orchestrator")
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # Initialize core components
        self.agent_coordinator = AgentCoordinator(
            max_concurrent=self.orchestrator_config.max_concurrent_agents,
            timeout_seconds=self.orchestrator_config.timeout_seconds,
            global_settings_manager=global_settings_manager,
        )

        self.workflow_manager = WorkflowManager(
            config=self.orchestrator_config,
            work_dir=self.work_dir,
            agent_coordinator=self.agent_coordinator,
        )

        # Workflow state
        self.current_mode = OrchestratorMode.INTAKE_PROCESSING
        self.active_workflow_id: Optional[str] = None
        self.workflow_context: Dict[str, Any] = {}

        logger.info(f"Initialized LegalOrchestratorAgent {self.agent_id}")

    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute orchestrator tasks based on task type"""

        try:
            task_type = task.task_type.lower()
            parameters = task.parameters

            if task_type == "start_legal_workflow":
                return await self._start_legal_workflow(parameters)
            elif task_type == "process_intake_documents":
                return await self._process_intake_documents(parameters)
            elif task_type == "coordinate_research":
                return await self._coordinate_research(parameters)
            elif task_type == "interactive_chat":
                return await self._handle_interactive_chat(parameters)
            elif task_type == "generate_final_report":
                return await self._generate_final_report(parameters)
            elif task_type == "get_workflow_status":
                return await self._get_workflow_status(parameters)
            else:
                raise ValueError(f"Unknown task type: {task_type}")

        except Exception as e:
            logger.error(f"Error executing task {task.task_type}: {e}")
            raise

    def get_supported_task_types(self) -> List[str]:
        """Return list of supported task types"""
        return [
            "start_legal_workflow",
            "process_intake_documents",
            "coordinate_research",
            "interactive_chat",
            "generate_final_report",
            "get_workflow_status",
        ]

    async def _start_legal_workflow(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new legal research workflow"""

        workflow_id = str(uuid.uuid4())
        self.active_workflow_id = workflow_id

        # Extract workflow parameters
        client_info = parameters.get("client_info", {})
        case_type = parameters.get("case_type", "wcat_appeal")
        documents = parameters.get("documents", [])
        research_queries = parameters.get("research_queries", [])

        # Initialize workflow
        await self.workflow_manager.create_workflow(
            workflow_id=workflow_id,
            client_info=client_info,
            case_type=case_type,
            initial_documents=documents,
            research_queries=research_queries,
        )

        self.workflow_context = {
            "workflow_id": workflow_id,
            "client_info": client_info,
            "case_type": case_type,
            "documents": documents,
            "research_queries": research_queries,
            "created_at": datetime.now().isoformat(),
        }

        logger.info(f"Started legal workflow {workflow_id} for case type: {case_type}")

        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": "Legal workflow started successfully",
            "next_step": "process_intake_documents",
            "context": self.workflow_context,
        }

    async def _process_intake_documents(
        self, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process documents through the intake agent"""

        if not self.active_workflow_id:
            raise ValueError("No active workflow. Start workflow first.")

        documents = parameters.get("documents", [])
        if not documents:
            documents = self.workflow_context.get("documents", [])

        logger.info(f"Processing {len(documents)} documents through intake agent")

        # Coordinate with intake agent
        intake_result = await self.agent_coordinator.execute_agent_task(
            agent_type="intake",
            task_type="process_documents_with_ocr",
            parameters={
                "documents": documents,
                "enable_source_tracking": True,
                "enable_insurance_detection": True,
                "workflow_id": self.active_workflow_id,
            },
        )

        # Update workflow state
        await self.workflow_manager.update_workflow_state(
            self.active_workflow_id,
            WorkflowState.INTAKE_COMPLETE,
            {
                "intake_results": intake_result,
                "processed_documents": intake_result.get("processed_documents", []),
                "document_sources": intake_result.get("document_sources", {}),
                "insurance_companies": intake_result.get("insurance_companies", []),
            },
        )

        # Decide next step
        next_step = "coordinate_research"
        if (
            self.orchestrator_config.enable_chat_interface
            and not self.orchestrator_config.auto_proceed_after_intake
        ):
            next_step = "interactive_chat"

        return {
            "success": True,
            "intake_results": intake_result,
            "documents_processed": len(intake_result.get("processed_documents", [])),
            "sources_identified": len(intake_result.get("document_sources", {})),
            "insurance_companies": intake_result.get("insurance_companies", []),
            "next_step": next_step,
            "workflow_id": self.active_workflow_id,
        }

    async def _coordinate_research(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate research across multiple specialized agents"""

        if not self.active_workflow_id:
            raise ValueError("No active workflow. Start workflow first.")

        # Get current workflow state
        workflow_state = await self.workflow_manager.get_workflow_state(
            self.active_workflow_id
        )
        intake_results = workflow_state.get("intake_results", {})

        research_tasks = []

        # 1. Legal Research Agent - Find similar WCAT cases
        research_tasks.append(
            {
                "agent_type": "legal_research",
                "task_type": "run_legal_research",
                "parameters": {
                    "search_queries": self._generate_search_queries(intake_results),
                    "user_case_summary": self._create_case_summary(intake_results),
                    "workflow_id": self.active_workflow_id,
                    "use_database_search": True,
                },
            }
        )

        # 2. Cross Reference Agent - Cross-reference with existing database
        research_tasks.append(
            {
                "agent_type": "cross_reference",
                "task_type": "cross_reference_analysis",
                "parameters": {
                    "case_details": intake_results,
                    "workflow_id": self.active_workflow_id,
                },
            }
        )

        # 3. Database Maintenance Agent - Update database with new findings
        research_tasks.append(
            {
                "agent_type": "database_maintenance",
                "task_type": "update_case_database",
                "parameters": {
                    "case_data": intake_results,
                    "workflow_id": self.active_workflow_id,
                },
            }
        )

        # Execute research tasks concurrently
        logger.info(f"Executing {len(research_tasks)} research tasks concurrently")
        research_results = await self.agent_coordinator.execute_concurrent_tasks(
            research_tasks
        )

        # Update workflow state
        await self.workflow_manager.update_workflow_state(
            self.active_workflow_id,
            WorkflowState.RESEARCH_COMPLETE,
            {
                "research_results": research_results,
                "legal_research": research_results.get("legal_research", {}),
                "cross_reference": research_results.get("cross_reference", {}),
                "database_updates": research_results.get("database_maintenance", {}),
            },
        )

        return {
            "success": True,
            "research_results": research_results,
            "tasks_completed": len(research_tasks),
            "next_step": "generate_final_report",
            "workflow_id": self.active_workflow_id,
        }

    async def _handle_interactive_chat(
        self, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle interactive chat interface"""

        user_message = parameters.get("message", "")
        if not user_message:
            return {"success": False, "error": "No message provided for chat interface"}

        # Get current workflow context
        workflow_state = await self.workflow_manager.get_workflow_state(
            self.active_workflow_id  # type: ignore
        )

        # Process chat message with context
        chat_response = await self._process_chat_message(user_message, workflow_state)

        return {
            "success": True,
            "response": chat_response,
            "workflow_id": self.active_workflow_id,
        }

    async def _generate_final_report(
        self, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive final report"""

        if not self.active_workflow_id:
            raise ValueError("No active workflow. Start workflow first.")

        # Get complete workflow state
        workflow_state = await self.workflow_manager.get_workflow_state(
            self.active_workflow_id
        )

        # Generate comprehensive report
        report = await self._compile_comprehensive_report(workflow_state)

        # Save report
        report_path = self.work_dir / f"final_report_{self.active_workflow_id}.json"
        with open(report_path, "w") as f:
            import json

            json.dump(report, f, indent=2, default=str)

        # Update workflow state
        await self.workflow_manager.update_workflow_state(
            self.active_workflow_id,
            WorkflowState.COMPLETED,
            {
                "final_report": report,
                "report_path": str(report_path),
                "completed_at": datetime.now().isoformat(),
            },
        )

        return {
            "success": True,
            "report": report,
            "report_path": str(report_path),
            "workflow_id": self.active_workflow_id,
            "status": "completed",
        }

    async def _get_workflow_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get current workflow status"""

        current_workflow_id = parameters.get("workflow_id", self.active_workflow_id)
        if not current_workflow_id:
            return {
                "success": False,
                "error": "No workflow ID provided or active workflow",
            }

        assert current_workflow_id is not None, (
            "Workflow ID cannot be None here after the check"
        )
        workflow_state = await self.workflow_manager.get_workflow_state(
            current_workflow_id
        )

        return {
            "success": True,
            "workflow_id": current_workflow_id,
            "state": workflow_state,
            "current_mode": self.current_mode.value,
        }

    def _generate_search_queries(self, intake_results: Dict[str, Any]) -> List[str]:
        """Generate search queries based on intake results"""

        queries = []

        # Extract key information from intake
        case_type = intake_results.get("case_type", "workers compensation")
        injury_types = intake_results.get("injury_types", [])
        employers = intake_results.get("employers", [])

        # Generate targeted queries
        queries.append(f"{case_type} appeal tribunal")

        for injury in injury_types:
            queries.append(f"{injury} workers compensation")

        for employer in employers:
            queries.append(f"{employer} workers compensation case")

        return queries

    def _create_case_summary(self, intake_results: Dict[str, Any]) -> str:
        """Create case summary from intake results"""

        summary_parts = []

        # Add case type
        case_type = intake_results.get("case_type", "Workers' Compensation Appeal")
        summary_parts.append(f"Case Type: {case_type}")

        # Add injury information
        injuries = intake_results.get("injury_types", [])
        if injuries:
            summary_parts.append(f"Injuries: {', '.join(injuries)}")

        # Add employer information
        employers = intake_results.get("employers", [])
        if employers:
            summary_parts.append(f"Employers: {', '.join(employers)}")

        # Add insurance information
        insurance_companies = intake_results.get("insurance_companies", [])
        if insurance_companies:
            summary_parts.append(
                f"Insurance Companies: {', '.join(insurance_companies)}"
            )

        return "\n".join(summary_parts)

    async def _process_chat_message(
        self, message: str, workflow_state: Dict[str, Any]
    ) -> str:
        """Process chat message with workflow context"""

        # Create context-aware prompt
        context_prompt = f"""
        You are a legal research assistant specializing in Workers' Compensation Appeal Tribunal (WCAT) cases.

        Current case context:
        {self._format_workflow_context(workflow_state)}

        User question: {message}

        Please provide a helpful response based on the case context and your legal knowledge.
        """

        # Use LLM to generate response
        response = await self.llm.ainvoke(context_prompt)

        return response.content if hasattr(response, "content") else str(response)

    def _format_workflow_context(self, workflow_state: Dict[str, Any]) -> str:
        """Format workflow context for chat"""

        context_parts = []

        # Add basic case information
        if "client_info" in workflow_state:
            context_parts.append(f"Client: {workflow_state['client_info']}")

        # Add intake results
        if "intake_results" in workflow_state:
            intake = workflow_state["intake_results"]
            context_parts.append(
                f"Documents processed: {len(intake.get('processed_documents', []))}"
            )
            context_parts.append(
                f"Insurance companies: {intake.get('insurance_companies', [])}"
            )

        # Add research results
        if "research_results" in workflow_state:
            research = workflow_state["research_results"]
            context_parts.append(
                f"Similar cases found: {len(research.get('legal_research', {}).get('similar_cases', []))}"
            )

        return "\n".join(context_parts)

    async def _compile_comprehensive_report(
        self, workflow_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compile comprehensive final report"""

        report = {
            "workflow_id": self.active_workflow_id,
            "generated_at": datetime.now().isoformat(),
            "case_summary": workflow_state.get("client_info", {}),
            "document_analysis": {},
            "research_findings": {},
            "recommendations": [],
            "next_steps": [],
        }

        # Add intake analysis
        if "intake_results" in workflow_state:
            intake = workflow_state["intake_results"]
            report["document_analysis"] = {
                "total_documents": len(intake.get("processed_documents", [])),
                "document_sources": intake.get("document_sources", {}),
                "insurance_companies": intake.get("insurance_companies", []),
                "key_dates": intake.get("key_dates", []),
                "medical_providers": intake.get("medical_providers", []),
            }

        # Add research findings
        if "research_results" in workflow_state:
            research = workflow_state["research_results"]
            legal_research = research.get("legal_research", {})

            report["research_findings"] = {
                "similar_cases": legal_research.get("similar_cases", []),
                "legal_arguments": legal_research.get("legal_arguments", {}),
                "precedent_analysis": legal_research.get("precedent_analysis", {}),
                "cross_reference_results": research.get("cross_reference", {}),
            }

        # Generate recommendations using LLM
        recommendations_prompt = f"""
        Based on the following legal research findings, generate actionable recommendations:

        {report}

        Please provide specific, actionable recommendations for this WCAT case.
        """

        recommendations_response = await self.llm.ainvoke(recommendations_prompt)
        report["recommendations"] = [
            recommendations_response.content
            if hasattr(recommendations_response, "content")
            else str(recommendations_response)
        ]

        return report

    async def stop(self):
        """Stop the orchestrator and clean up resources"""

        logger.info(f"Stopping LegalOrchestratorAgent {self.agent_id}")

        # Stop all managed agents
        await self.agent_coordinator.stop_all_agents()

        # Save workflow state if active
        if self.active_workflow_id:
            await self.workflow_manager.save_workflow_state(self.active_workflow_id)

        # Call parent stop
        await super().stop()

    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""

        base_status = super().get_status()

        orchestrator_status = {
            "current_mode": self.current_mode.value,
            "active_workflow_id": self.active_workflow_id,
            "workflow_context": self.workflow_context,
            "agent_coordinator_status": self.agent_coordinator.get_status(),
            "workflow_manager_status": self.workflow_manager.get_status(),
        }

        base_status.update(orchestrator_status)
        return base_status
