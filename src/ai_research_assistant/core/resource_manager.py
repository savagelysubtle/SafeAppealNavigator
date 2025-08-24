# src/ai_research_assistant/core/resource_manager.py
import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

# --- CORRECTED IMPORTS ---
# Import the correct base agent class and the AgentTask model from core.models
from ai_research_assistant.agents.base_pydantic_agent import BasePydanticAgent
from ai_research_assistant.core.models import AgentTask

logger = logging.getLogger(__name__)


class ResourceState(Enum):
    """Resource availability states."""

    AVAILABLE = "available"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    MAINTENANCE = "maintenance"


@dataclass
class PriorityTask:
    """Task wrapper for a priority queue."""

    priority: int
    task: AgentTask
    submitted_at: float = field(default_factory=time.time)

    def __lt__(self, other: "PriorityTask") -> bool:
        # Higher priority value means higher priority.
        if self.priority != other.priority:
            return self.priority > other.priority
        # FIFO for tasks with the same priority.
        return self.submitted_at < other.submitted_at


class ResourceManager:
    """
    Intelligent resource allocation for agent tasks.
    This is a placeholder implementation for future expansion.
    """

    def __init__(self, max_concurrent_tasks: int = 10, memory_limit_mb: int = 2048):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.memory_limit_mb = memory_limit_mb
        self.priority_queue: List[PriorityTask] = []
        self.running_tasks: Dict[str, AgentTask] = {}
        self.resource_semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.current_memory_mb = 0.0
        logger.info(
            f"Initialized ResourceManager: {max_concurrent_tasks} concurrent tasks, "
            f"{memory_limit_mb}MB memory limit"
        )

    async def submit_task(
        self, task: AgentTask, agent: BasePydanticAgent
    ) -> Dict[str, Any]:
        """
        Submits a task for execution, respecting concurrency limits.
        NOTE: Memory and priority logic is placeholder for future implementation.
        """
        logger.info(f"Submitting task {task.id} with priority {task.priority}")
        async with self.resource_semaphore:
            task_id_str = str(task.id)
            self.running_tasks[task_id_str] = task
            try:
                # The BasePydanticAgent has a `run_skill` method, not `run_task`.
                # This simulates calling that skill with a generic prompt.
                logger.info(
                    f"Executing task '{task.task_type}' for agent {agent.agent_name}"
                )

                # Create a prompt from the task parameters for the agent to run.
                prompt = f"Execute task '{task.task_type}' with parameters: {task.parameters}"
                result = await agent.run_skill(prompt=prompt)

                return {"status": "success", "task_id": task_id_str, "result": result}
            except Exception as e:
                logger.error(f"Error executing task {task.id}: {e}", exc_info=True)
                return {"status": "error", "task_id": task_id_str, "error": str(e)}
            finally:
                self.running_tasks.pop(task_id_str, None)

    def get_resource_status(self) -> Dict[str, Any]:
        """Gets the current resource utilization status."""
        return {
            "running_tasks": len(self.running_tasks),
            "queued_tasks": len(self.priority_queue),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "memory_usage_mb": self.current_memory_mb,  # Placeholder value
            "memory_limit_mb": self.memory_limit_mb,
        }
