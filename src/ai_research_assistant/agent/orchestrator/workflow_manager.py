"""
Workflow Manager for Legal Research Orchestrator

Manages workflow states, transitions, and persistence for the legal research system.
Handles state management, transitions between workflow stages, and data persistence.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class WorkflowState(Enum):
    """Workflow states for legal research process"""

    CREATED = "created"
    INTAKE_PROCESSING = "intake_processing"
    INTAKE_COMPLETE = "intake_complete"
    MANAGER_REVIEW = "manager_review"
    CHAT_INTERACTIVE = "chat_interactive"
    RESEARCH_INITIATED = "research_initiated"
    RESEARCH_COMPLETE = "research_complete"
    ANALYSIS_COMPLETE = "analysis_complete"
    REPORT_GENERATION = "report_generation"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowTransition(Enum):
    """Valid transitions between workflow states"""

    START_INTAKE = "start_intake"
    COMPLETE_INTAKE = "complete_intake"
    START_MANAGER_REVIEW = "start_manager_review"
    ENTER_CHAT = "enter_chat"
    EXIT_CHAT = "exit_chat"
    START_RESEARCH = "start_research"
    COMPLETE_RESEARCH = "complete_research"
    START_ANALYSIS = "start_analysis"
    COMPLETE_ANALYSIS = "complete_analysis"
    GENERATE_REPORT = "generate_report"
    COMPLETE_WORKFLOW = "complete_workflow"
    FAIL_WORKFLOW = "fail_workflow"
    CANCEL_WORKFLOW = "cancel_workflow"


@dataclass
class WorkflowData:
    """Data structure for workflow information"""

    workflow_id: str
    state: WorkflowState
    created_at: datetime
    updated_at: datetime
    client_info: Dict[str, Any] = field(default_factory=dict)
    case_type: str = "wcat_appeal"
    documents: List[str] = field(default_factory=list)
    research_queries: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    transitions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowManager:
    """
    Manages legal research workflow states and transitions.

    Features:
    - State management and transitions
    - Workflow data persistence
    - Audit trail tracking
    - Error handling and recovery
    """

    def __init__(
        self, config=None, work_dir: Optional[Path] = None, agent_coordinator=None
    ):
        self.config = config
        self.work_dir = work_dir or Path("./tmp/workflows")
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.agent_coordinator = agent_coordinator

        # Active workflows
        self.workflows: Dict[str, WorkflowData] = {}

        # State transition rules
        self.valid_transitions = {
            WorkflowState.CREATED: [
                WorkflowState.INTAKE_PROCESSING,
                WorkflowState.CANCELLED,
            ],
            WorkflowState.INTAKE_PROCESSING: [
                WorkflowState.INTAKE_COMPLETE,
                WorkflowState.FAILED,
            ],
            WorkflowState.INTAKE_COMPLETE: [
                WorkflowState.MANAGER_REVIEW,
                WorkflowState.CHAT_INTERACTIVE,
                WorkflowState.RESEARCH_INITIATED,
            ],
            WorkflowState.MANAGER_REVIEW: [
                WorkflowState.RESEARCH_INITIATED,
                WorkflowState.CHAT_INTERACTIVE,
                WorkflowState.FAILED,
            ],
            WorkflowState.CHAT_INTERACTIVE: [
                WorkflowState.RESEARCH_INITIATED,
                WorkflowState.MANAGER_REVIEW,
            ],
            WorkflowState.RESEARCH_INITIATED: [
                WorkflowState.RESEARCH_COMPLETE,
                WorkflowState.FAILED,
            ],
            WorkflowState.RESEARCH_COMPLETE: [
                WorkflowState.ANALYSIS_COMPLETE,
                WorkflowState.REPORT_GENERATION,
            ],
            WorkflowState.ANALYSIS_COMPLETE: [
                WorkflowState.REPORT_GENERATION,
                WorkflowState.COMPLETED,
            ],
            WorkflowState.REPORT_GENERATION: [
                WorkflowState.COMPLETED,
                WorkflowState.FAILED,
            ],
            WorkflowState.COMPLETED: [],
            WorkflowState.FAILED: [WorkflowState.CREATED],  # Allow restart from failed
            WorkflowState.CANCELLED: [],
        }

        logger.info(f"Initialized WorkflowManager with work_dir: {self.work_dir}")

    async def create_workflow(
        self,
        workflow_id: str,
        client_info: Dict[str, Any],
        case_type: str = "wcat_appeal",
        initial_documents: Optional[List[str]] = None,
        research_queries: Optional[List[str]] = None,
    ) -> WorkflowData:
        """Create a new workflow"""

        if workflow_id in self.workflows:
            raise ValueError(f"Workflow {workflow_id} already exists")

        workflow = WorkflowData(
            workflow_id=workflow_id,
            state=WorkflowState.CREATED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            client_info=client_info,
            case_type=case_type,
            documents=initial_documents or [],
            research_queries=research_queries or [],
        )

        self.workflows[workflow_id] = workflow

        # Save to disk
        await self.save_workflow_state(workflow_id)

        logger.info(f"Created workflow {workflow_id} with case type: {case_type}")
        return workflow

    async def update_workflow_state(
        self,
        workflow_id: str,
        new_state: WorkflowState,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update workflow state with validation"""

        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.workflows[workflow_id]
        old_state = workflow.state

        # Validate transition
        if new_state not in self.valid_transitions.get(old_state, []):
            logger.warning(
                f"Invalid transition from {old_state} to {new_state} for workflow {workflow_id}"
            )
            return False

        # Update workflow
        workflow.state = new_state
        workflow.updated_at = datetime.now()

        if data:
            workflow.data.update(data)

        # Record transition
        transition_record = {
            "from_state": old_state.value,
            "to_state": new_state.value,
            "timestamp": datetime.now().isoformat(),
            "data_keys": list(data.keys()) if data else [],
        }
        workflow.transitions.append(transition_record)

        # Save to disk
        await self.save_workflow_state(workflow_id)

        logger.info(
            f"Updated workflow {workflow_id}: {old_state.value} → {new_state.value}"
        )
        return True

    async def get_workflow_state(self, workflow_id: str) -> Dict[str, Any]:
        """Get current workflow state and data"""

        if workflow_id not in self.workflows:
            # Try to load from disk
            await self.load_workflow_state(workflow_id)

        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.workflows[workflow_id]

        return {
            "workflow_id": workflow.workflow_id,
            "state": workflow.state.value,
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat(),
            "client_info": workflow.client_info,
            "case_type": workflow.case_type,
            "documents": workflow.documents,
            "research_queries": workflow.research_queries,
            "transitions": workflow.transitions,
            "metadata": workflow.metadata,
            **workflow.data,
        }

    async def save_workflow_state(self, workflow_id: str) -> bool:
        """Save workflow state to disk"""

        if workflow_id not in self.workflows:
            return False

        workflow = self.workflows[workflow_id]
        workflow_file_path = self.work_dir / f"workflow_{workflow_id}.json"

        try:
            workflow_data_str = json.dumps(
                {
                    "workflow_id": workflow.workflow_id,
                    "state": workflow.state.value,
                    "created_at": workflow.created_at.isoformat(),
                    "updated_at": workflow.updated_at.isoformat(),
                    "client_info": workflow.client_info,
                    "case_type": workflow.case_type,
                    "documents": workflow.documents,
                    "research_queries": workflow.research_queries,
                    "data": workflow.data,
                    "transitions": workflow.transitions,
                    "metadata": workflow.metadata,
                },
                indent=2,
            )

            if self.agent_coordinator:
                # Use MCP to write file
                mcp_result = await self.agent_coordinator.execute_agent_task(
                    agent_type="filesystem_server",
                    task_type="write_file",
                    parameters={
                        "file_path": str(workflow_file_path),
                        "content": workflow_data_str,
                        "overwrite": True,
                    },
                )
                if not mcp_result.get("success"):
                    logger.error(
                        f"MCP Error saving workflow {workflow_id}: {mcp_result.get('error')}"
                    )
                    return False
            else:
                # Fallback to standard python I/O if no coordinator
                with open(workflow_file_path, "w") as f:
                    f.write(workflow_data_str)

            logger.debug(f"Saved workflow {workflow_id} to {workflow_file_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving workflow {workflow_id}: {e}")
            return False

    async def load_workflow_state(self, workflow_id: str) -> bool:
        """Load workflow state from disk"""

        workflow_file_path = self.work_dir / f"workflow_{workflow_id}.json"

        try:
            content_data_str: Optional[str] = None
            if self.agent_coordinator:
                if not await self.agent_coordinator.execute_agent_task(
                    agent_type="filesystem_server",
                    task_type="get_file_info",
                    parameters={"file_path": str(workflow_file_path)},
                ).get("success", False):
                    return False

                mcp_result = await self.agent_coordinator.execute_agent_task(
                    agent_type="filesystem_server",
                    task_type="read_file",
                    parameters={"file_path": str(workflow_file_path)},
                )
                if mcp_result.get("success"):
                    content_data_str = mcp_result.get("content")
                else:
                    logger.error(
                        f"MCP Error loading workflow {workflow_id}: {mcp_result.get('error')}"
                    )
                    return False
            else:
                if not workflow_file_path.exists():
                    return False
                with open(workflow_file_path, "r") as f:
                    content_data_str = f.read()

            if content_data_str is None:
                logger.error(f"Failed to read content for workflow {workflow_id}")
                return False

            data = json.loads(content_data_str)

            workflow = WorkflowData(
                workflow_id=data["workflow_id"],
                state=WorkflowState(data["state"]),
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
                client_info=data.get("client_info", {}),
                case_type=data.get("case_type", "wcat_appeal"),
                documents=data.get("documents", []),
                research_queries=data.get("research_queries", []),
                data=data.get("data", {}),
                transitions=data.get("transitions", []),
                metadata=data.get("metadata", {}),
            )

            self.workflows[workflow_id] = workflow

            logger.debug(f"Loaded workflow {workflow_id} from {workflow_file_path}")
            return True

        except Exception as e:
            logger.error(f"Error loading workflow {workflow_id}: {e}")
            return False

    async def list_workflows(
        self, state_filter: Optional[WorkflowState] = None
    ) -> List[Dict[str, Any]]:
        """List all workflows, optionally filtered by state"""

        # Load all workflow files
        workflow_files = list(self.work_dir.glob("workflow_*.json"))

        workflows = []
        for workflow_file in workflow_files:
            workflow_id = workflow_file.stem.replace("workflow_", "")
            if workflow_id not in self.workflows:
                await self.load_workflow_state(workflow_id)

            if workflow_id in self.workflows:
                workflow = self.workflows[workflow_id]
                if state_filter is None or workflow.state == state_filter:
                    workflows.append(
                        {
                            "workflow_id": workflow.workflow_id,
                            "state": workflow.state.value,
                            "case_type": workflow.case_type,
                            "created_at": workflow.created_at.isoformat(),
                            "updated_at": workflow.updated_at.isoformat(),
                        }
                    )

        return workflows

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow and its data"""

        try:
            # Remove from memory
            if workflow_id in self.workflows:
                del self.workflows[workflow_id]

            # Remove from disk
            workflow_file_path = self.work_dir / f"workflow_{workflow_id}.json"

            if self.agent_coordinator:
                mcp_result_info = await self.agent_coordinator.execute_agent_task(
                    agent_type="filesystem_server",
                    task_type="get_file_info",
                    parameters={"file_path": str(workflow_file_path)},
                )
                if mcp_result_info.get("success"):  # File exists
                    mcp_result_delete = await self.agent_coordinator.execute_agent_task(
                        agent_type="filesystem_server",
                        task_type="delete_file",
                        parameters={"file_path": str(workflow_file_path)},
                    )
                    if not mcp_result_delete.get("success"):
                        logger.error(
                            f"MCP Error deleting workflow {workflow_id}: {mcp_result_delete.get('error')}"
                        )
                        # Potentially return False or raise an error, depending on desired strictness
            else:
                if workflow_file_path.exists():
                    workflow_file_path.unlink()

            logger.info(f"Deleted workflow {workflow_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting workflow {workflow_id}: {e}")
            return False

    def get_valid_transitions(self, workflow_id: str) -> List[WorkflowState]:
        """Get valid next states for a workflow"""

        if workflow_id not in self.workflows:
            return []

        current_state = self.workflows[workflow_id].state
        return self.valid_transitions.get(current_state, [])

    def is_workflow_complete(self, workflow_id: str) -> bool:
        """Check if workflow is in a terminal state"""

        if workflow_id not in self.workflows:
            return False

        terminal_states = [
            WorkflowState.COMPLETED,
            WorkflowState.FAILED,
            WorkflowState.CANCELLED,
        ]
        return self.workflows[workflow_id].state in terminal_states

    def get_workflow_progress(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow progress information"""

        if workflow_id not in self.workflows:
            return {"error": "Workflow not found"}

        workflow = self.workflows[workflow_id]

        # Define progress stages
        stages = [
            WorkflowState.CREATED,
            WorkflowState.INTAKE_PROCESSING,
            WorkflowState.INTAKE_COMPLETE,
            WorkflowState.RESEARCH_INITIATED,
            WorkflowState.RESEARCH_COMPLETE,
            WorkflowState.ANALYSIS_COMPLETE,
            WorkflowState.COMPLETED,
        ]

        current_index = -1
        for i, stage in enumerate(stages):
            if workflow.state == stage:
                current_index = i
                break

        progress_percentage = (
            (current_index + 1) / len(stages) * 100 if current_index >= 0 else 0
        )

        return {
            "workflow_id": workflow_id,
            "current_state": workflow.state.value,
            "progress_percentage": progress_percentage,
            "stages_completed": current_index + 1,
            "total_stages": len(stages),
            "is_complete": self.is_workflow_complete(workflow_id),
            "transitions_count": len(workflow.transitions),
        }

    def get_status(self) -> Dict[str, Any]:
        """Get workflow manager status"""

        return {
            "active_workflows": len(self.workflows),
            "work_dir": str(self.work_dir),
            "workflow_ids": list(self.workflows.keys()),
        }
