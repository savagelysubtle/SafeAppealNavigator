"""
Resource Management for AI Research Assistant

This module provides intelligent resource allocation and task prioritization
for the agent ecosystem, handling concurrency limits and memory management.
"""

import asyncio
import heapq
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from ...base_agent import AgentTask

logger = logging.getLogger(__name__)


class ResourceState(Enum):
    """Resource availability states"""

    AVAILABLE = "available"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    MAINTENANCE = "maintenance"


@dataclass
class PriorityTask:
    """Task wrapper for priority queue"""

    priority: int
    task: AgentTask
    submitted_at: float = field(default_factory=time.time)

    def __lt__(self, other):
        # Higher priority first, then FIFO for same priority
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.submitted_at < other.submitted_at


class ResourceManager:
    """Intelligent resource allocation for agent tasks"""

    def __init__(self, max_concurrent_tasks: int = 10, memory_limit_mb: int = 2048):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.memory_limit_mb = memory_limit_mb

        # Task management
        self.priority_queue: List[PriorityTask] = []
        self.running_tasks: Dict[str, AgentTask] = {}
        self.resource_semaphore = asyncio.Semaphore(max_concurrent_tasks)

        # Resource monitoring
        self.current_memory_mb = 0.0
        self.task_memory_estimates: Dict[str, float] = {}

        # Performance tracking
        self.total_tasks_processed = 0
        self.queue_wait_times: List[float] = []

        logger.info(
            f"Initialized ResourceManager: {max_concurrent_tasks} concurrent tasks, "
            f"{memory_limit_mb}MB memory limit"
        )

    async def submit_task(self, task: AgentTask, agent: "BaseAgent") -> Dict[str, Any]:
        """Submit task with intelligent scheduling"""

        # Estimate resource requirements
        memory_estimate = await self._estimate_task_memory(task, agent)

        # Check if we can run immediately
        if await self._can_run_immediately(task, memory_estimate):
            return await self._execute_task_with_resources(task, agent, memory_estimate)

        # Queue for later execution
        priority_task = PriorityTask(priority=task.priority.value, task=task)
        heapq.heappush(self.priority_queue, priority_task)

        logger.info(
            f"Task {task.id} queued with priority {task.priority.name}, "
            f"estimated memory: {memory_estimate:.1f}MB"
        )

        # Wait for slot or timeout
        return await self._wait_for_execution(priority_task, agent, memory_estimate)

    async def _can_run_immediately(
        self, task: AgentTask, memory_estimate: float
    ) -> bool:
        """Check if task can run without queueing"""

        # Check concurrency limit
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            return False

        # Check memory availability
        if self.current_memory_mb + memory_estimate > self.memory_limit_mb:
            return False

        # Check if higher priority tasks are queued
        if (
            self.priority_queue
            and self.priority_queue[0].priority > task.priority.value
        ):
            return False

        return True

    async def _execute_task_with_resources(
        self, task: AgentTask, agent: "BaseAgent", memory_estimate: float
    ) -> Dict[str, Any]:
        """Execute task with resource tracking"""

        async with self.resource_semaphore:
            self.running_tasks[task.id] = task
            self.current_memory_mb += memory_estimate

            try:
                logger.debug(
                    f"Executing task {task.id}, "
                    f"memory usage: {self.current_memory_mb:.1f}/{self.memory_limit_mb}MB"
                )

                # Execute with resource monitoring
                result = await agent.run_task(
                    task.task_type,
                    task.parameters,
                    task.priority,
                    task.parent_workflow_id,
                )

                self.total_tasks_processed += 1
                return result

            finally:
                # Clean up resources
                self.running_tasks.pop(task.id, None)
                self.current_memory_mb -= memory_estimate

                # Process next queued task
                await self._process_next_queued_task()

    async def _wait_for_execution(
        self, priority_task: PriorityTask, agent: "BaseAgent", memory_estimate: float
    ) -> Dict[str, Any]:
        """Wait for task execution slot with timeout"""

        start_wait_time = time.time()
        timeout_seconds = 300  # 5 minutes default timeout

        while time.time() - start_wait_time < timeout_seconds:
            # Check if we can run now
            if await self._can_run_immediately(priority_task.task, memory_estimate):
                # Remove from queue
                try:
                    self.priority_queue.remove(priority_task)
                    heapq.heapify(self.priority_queue)
                except ValueError:
                    pass  # Already removed

                wait_time = time.time() - start_wait_time
                self.queue_wait_times.append(wait_time)

                return await self._execute_task_with_resources(
                    priority_task.task, agent, memory_estimate
                )

            # Brief wait before checking again
            await asyncio.sleep(0.1)

        # Timeout reached
        try:
            self.priority_queue.remove(priority_task)
            heapq.heapify(self.priority_queue)
        except ValueError:
            pass

        return {
            "success": False,
            "task_id": priority_task.task.id,
            "error": f"Task timed out waiting for resources after {timeout_seconds}s",
            "execution_time_ms": 0,
            "retry_count": 0,
        }

    async def _process_next_queued_task(self):
        """Process next task in priority queue if resources available"""

        if not self.priority_queue:
            return

        # Find next executable task
        for i, priority_task in enumerate(self.priority_queue):
            memory_estimate = await self._estimate_task_memory(
                priority_task.task,
                None,  # Agent context not available here
            )

            if await self._can_run_immediately(priority_task.task, memory_estimate):
                # Remove from queue
                del self.priority_queue[i]
                heapq.heapify(self.priority_queue)

                # Note: In practice, we'd need to store agent reference with task
                # or use a different execution pattern
                logger.debug(f"Would process queued task {priority_task.task.id}")
                break

    async def _estimate_task_memory(
        self, task: AgentTask, agent: Optional["BaseAgent"]
    ) -> float:
        """Estimate memory requirements for task"""

        # Check cache first
        cache_key = f"{task.task_type}:{hash(str(task.parameters))}"
        if cache_key in self.task_memory_estimates:
            return self.task_memory_estimates[cache_key]

        # Base memory per agent type
        base_memory = {
            "LegalAnalysisAgent": 200.0,  # MB
            "SearchAgent": 100.0,
            "IntakeAgent": 150.0,
            "CrossReferenceAgent": 120.0,
            "BrowserUseAgent": 180.0,
            "DeepResearchAgent": 250.0,
            "CollectorAgent": 130.0,
        }

        agent_memory = 100.0  # Default
        if agent:
            agent_memory = base_memory.get(agent.__class__.__name__, 100.0)

        # Task-specific adjustments
        task_memory = agent_memory

        if task.task_type == "analyze_large_document":
            doc_size_mb = task.parameters.get("document_size_mb", 0)
            task_memory += doc_size_mb * 1.5  # Processing overhead

        elif task.task_type == "browser_search":
            search_depth = task.parameters.get("search_depth", 1)
            task_memory += search_depth * 50  # Memory per search level

        elif task.task_type == "legal_research":
            num_cases = task.parameters.get("max_cases", 10)
            task_memory += num_cases * 5  # Memory per legal case

        # Cache the estimate
        self.task_memory_estimates[cache_key] = task_memory
        return task_memory

    def get_resource_status(self) -> Dict[str, Any]:
        """Get current resource utilization status"""

        avg_wait_time = (
            sum(self.queue_wait_times[-100:]) / len(self.queue_wait_times[-100:])
            if self.queue_wait_times
            else 0
        )

        return {
            "running_tasks": len(self.running_tasks),
            "queued_tasks": len(self.priority_queue),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "memory_usage_mb": self.current_memory_mb,
            "memory_limit_mb": self.memory_limit_mb,
            "memory_utilization_percent": (
                self.current_memory_mb / self.memory_limit_mb
            )
            * 100,
            "state": self._get_resource_state(),
            "total_tasks_processed": self.total_tasks_processed,
            "avg_queue_wait_time_seconds": avg_wait_time,
        }

    def _get_resource_state(self) -> ResourceState:
        """Determine current resource state"""

        memory_util = (self.current_memory_mb / self.memory_limit_mb) * 100
        task_util = (len(self.running_tasks) / self.max_concurrent_tasks) * 100

        if memory_util > 90 or task_util > 90:
            return ResourceState.OVERLOADED
        elif memory_util > 70 or task_util > 70:
            return ResourceState.BUSY
        else:
            return ResourceState.AVAILABLE

    async def adjust_limits(
        self,
        max_concurrent_tasks: Optional[int] = None,
        memory_limit_mb: Optional[int] = None,
    ):
        """Dynamically adjust resource limits"""

        if max_concurrent_tasks is not None:
            old_limit = self.max_concurrent_tasks
            self.max_concurrent_tasks = max_concurrent_tasks

            # Adjust semaphore
            if max_concurrent_tasks > old_limit:
                # Release additional permits
                for _ in range(max_concurrent_tasks - old_limit):
                    self.resource_semaphore.release()

            logger.info(
                f"Adjusted concurrent task limit: {old_limit} -> {max_concurrent_tasks}"
            )

        if memory_limit_mb is not None:
            old_limit = self.memory_limit_mb
            self.memory_limit_mb = memory_limit_mb
            logger.info(f"Adjusted memory limit: {old_limit}MB -> {memory_limit_mb}MB")

    async def cleanup(self):
        """Clean up resources and cancel pending tasks"""

        # Cancel all queued tasks
        cancelled_count = len(self.priority_queue)
        self.priority_queue.clear()

        # Wait for running tasks to complete
        while self.running_tasks:
            await asyncio.sleep(0.1)

        logger.info(
            f"ResourceManager cleanup complete. Cancelled {cancelled_count} queued tasks."
        )
