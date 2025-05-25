"""
Agent Coordinator for Legal Research Orchestrator

Handles agent communication, task delegation, and coordination between multiple specialized agents.
Manages concurrent task execution, agent lifecycle, and inter-agent communication.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Supported agent types"""

    INTAKE = "intake"
    LEGAL_RESEARCH = "legal_research"
    CROSS_REFERENCE = "cross_reference"
    DATABASE_MAINTENANCE = "database_maintenance"
    DEEP_RESEARCH = "deep_research"
    SEARCH = "search"
    BROWSER_USE = "browser_use"
    COLLECTOR = "collector"


@dataclass
class AgentTask:
    """Task for agent execution"""

    task_id: str
    agent_type: AgentType
    task_type: str
    parameters: Dict[str, Any]
    priority: int = 0
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 3
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class AgentInstance:
    """Represents an active agent instance"""

    agent_id: str
    agent_type: AgentType
    agent_instance: Any
    is_busy: bool = False
    last_used: Optional[datetime] = None
    task_count: int = 0

    def __post_init__(self):
        if self.last_used is None:
            self.last_used = datetime.now()


class AgentPlaceholder:
    """Placeholder agent for testing and development"""

    def __init__(self, agent_type: AgentType, global_settings_manager=None):
        self.agent_type = agent_type
        self.global_settings_manager = global_settings_manager

    async def run_task(
        self, task_type: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Placeholder task execution"""
        return {
            "success": True,
            "message": f"Placeholder execution of {task_type} on {self.agent_type.value}",
            "parameters": parameters,
            "agent_type": self.agent_type.value,
        }

    async def stop(self):
        """Placeholder stop method"""
        pass


class AgentCoordinator:
    """
    Coordinates multiple specialized agents for the legal research orchestrator.

    Features:
    - Agent lifecycle management
    - Concurrent task execution
    - Load balancing and resource management
    - Error handling and retry logic
    - Agent communication and data sharing
    """

    def __init__(
        self,
        max_concurrent: int = 3,
        timeout_seconds: int = 300,
        global_settings_manager=None,
    ):
        self.max_concurrent = max_concurrent
        self.timeout_seconds = timeout_seconds
        self.global_settings_manager = global_settings_manager

        # Agent management
        self.agent_instances: Dict[str, AgentInstance] = {}
        self.agent_pool: Dict[AgentType, List[str]] = {}

        # Task management
        self.pending_tasks: List[AgentTask] = []
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: Dict[str, AgentTask] = {}

        # Coordination state
        self.is_running = False
        self.task_executor: Optional[asyncio.Task] = None

        logger.info(
            f"Initialized AgentCoordinator with max_concurrent={max_concurrent}"
        )

    async def execute_agent_task(
        self,
        agent_type: str,
        task_type: str,
        parameters: Dict[str, Any],
        priority: int = 0,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute a single task on the specified agent type"""

        task_id = str(uuid.uuid4())
        agent_type_enum = AgentType(agent_type)

        task = AgentTask(
            task_id=task_id,
            agent_type=agent_type_enum,
            task_type=task_type,
            parameters=parameters,
            priority=priority,
            timeout_seconds=timeout_seconds or self.timeout_seconds,
        )

        # Execute task directly
        return await self._execute_single_task(task)

    async def execute_concurrent_tasks(
        self, task_specs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute multiple tasks concurrently"""

        tasks = []
        for spec in task_specs:
            task_id = str(uuid.uuid4())
            agent_type_enum = AgentType(spec["agent_type"])

            task = AgentTask(
                task_id=task_id,
                agent_type=agent_type_enum,
                task_type=spec["task_type"],
                parameters=spec["parameters"],
                priority=spec.get("priority", 0),
                timeout_seconds=spec.get("timeout_seconds", self.timeout_seconds),
            )
            tasks.append(task)

        # Execute tasks concurrently
        results = {}

        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def execute_with_semaphore(task: AgentTask):
            async with semaphore:
                return await self._execute_single_task(task)

        # Run tasks concurrently
        task_coroutines = [execute_with_semaphore(task) for task in tasks]
        task_results = await asyncio.gather(*task_coroutines, return_exceptions=True)

        # Collect results
        for task, result in zip(tasks, task_results):
            if isinstance(result, Exception):
                results[task.agent_type.value] = {
                    "success": False,
                    "error": str(result),
                    "task_id": task.task_id,
                }
            else:
                results[task.agent_type.value] = result

        return results

    async def _execute_single_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute a single task with proper error handling"""

        task.started_at = datetime.now()

        try:
            # Get or create agent instance
            agent_instance = await self._get_agent_instance(task.agent_type)

            # Mark agent as busy
            agent_instance.is_busy = True
            agent_instance.task_count += 1

            # Execute task with timeout
            result = await asyncio.wait_for(
                self._execute_task_on_agent(agent_instance.agent_instance, task),
                timeout=task.timeout_seconds,
            )

            task.completed_at = datetime.now()
            task.result = result

            # Mark agent as free
            agent_instance.is_busy = False
            agent_instance.last_used = datetime.now()

            logger.info(f"Completed task {task.task_id} on {task.agent_type.value}")

            return result

        except asyncio.TimeoutError:
            error_msg = (
                f"Task {task.task_id} timed out after {task.timeout_seconds} seconds"
            )
            logger.error(error_msg)
            task.error = error_msg

            # Free the agent
            if task.agent_type.value in self.agent_instances:
                agent_instance = self.agent_instances[task.agent_type.value]
                agent_instance.is_busy = False

            return {"success": False, "error": error_msg, "task_id": task.task_id}

        except Exception as e:
            error_msg = f"Error executing task {task.task_id}: {str(e)}"
            logger.error(error_msg)
            task.error = error_msg

            # Free the agent
            if task.agent_type.value in self.agent_instances:
                agent_instance = self.agent_instances[task.agent_type.value]
                agent_instance.is_busy = False

            # Retry if possible
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                logger.info(f"Retrying task {task.task_id}, attempt {task.retry_count}")
                await asyncio.sleep(1)  # Brief delay before retry
                return await self._execute_single_task(task)

            return {
                "success": False,
                "error": error_msg,
                "task_id": task.task_id,
                "retry_count": task.retry_count,
            }

    async def _get_agent_instance(self, agent_type: AgentType) -> AgentInstance:
        """Get or create an agent instance of the specified type"""

        agent_key = agent_type.value

        # Check if we have an available instance
        if agent_key in self.agent_instances:
            return self.agent_instances[agent_key]

        # Create new agent instance
        agent_instance = await self._create_agent_instance(agent_type)
        self.agent_instances[agent_key] = agent_instance

        return agent_instance

    async def _create_agent_instance(self, agent_type: AgentType) -> AgentInstance:
        """Create a new agent instance of the specified type"""

        try:
            # For now, create placeholder agents - these will be enhanced with proper implementations
            agent = AgentPlaceholder(
                agent_type=agent_type,
                global_settings_manager=self.global_settings_manager,
            )

            agent_instance = AgentInstance(
                agent_id=str(uuid.uuid4()), agent_type=agent_type, agent_instance=agent
            )

            logger.info(
                f"Created {agent_type.value} agent instance: {agent_instance.agent_id}"
            )
            return agent_instance

        except Exception as e:
            logger.error(f"Failed to create {agent_type.value} agent: {e}")
            raise

    async def _execute_task_on_agent(
        self, agent_instance, task: AgentTask
    ) -> Dict[str, Any]:
        """Execute a task on a specific agent instance"""

        try:
            # Check if agent has the required method
            if hasattr(agent_instance, "run_task"):
                # Use BaseAgent's run_task method
                result = await agent_instance.run_task(
                    task_type=task.task_type, parameters=task.parameters
                )
            elif hasattr(agent_instance, task.task_type):
                # Call the specific method directly
                method = getattr(agent_instance, task.task_type)
                if asyncio.iscoroutinefunction(method):
                    result = await method(**task.parameters)
                else:
                    result = method(**task.parameters)
            else:
                # Try to call a generic execute method
                if hasattr(agent_instance, "execute"):
                    result = await agent_instance.execute(
                        task.task_type, task.parameters
                    )
                else:
                    raise AttributeError(
                        f"Agent does not support task type: {task.task_type}"
                    )

            # Ensure result is a dictionary
            if not isinstance(result, dict):
                result = {"result": result, "success": True}
            elif "success" not in result:
                result["success"] = True

            return result

        except Exception as e:
            logger.error(
                f"Error executing {task.task_type} on {task.agent_type.value}: {e}"
            )
            raise

    async def stop_all_agents(self):
        """Stop all active agent instances"""

        logger.info("Stopping all agent instances")

        for agent_key, agent_instance in self.agent_instances.items():
            try:
                if hasattr(agent_instance.agent_instance, "stop"):
                    await agent_instance.agent_instance.stop()
                logger.info(f"Stopped {agent_key} agent")
            except Exception as e:
                logger.error(f"Error stopping {agent_key} agent: {e}")

        self.agent_instances.clear()

    def get_agent_status(
        self, agent_type: Optional[AgentType] = None
    ) -> Dict[str, Any]:
        """Get status of agents"""

        if agent_type:
            agent_key = agent_type.value
            if agent_key in self.agent_instances:
                instance = self.agent_instances[agent_key]
                return {
                    "agent_id": instance.agent_id,
                    "agent_type": instance.agent_type.value,
                    "is_busy": instance.is_busy,
                    "task_count": instance.task_count,
                    "last_used": instance.last_used.isoformat()
                    if instance.last_used
                    else None,
                }
            else:
                return {"error": f"No instance found for {agent_type.value}"}

        # Return status for all agents
        status = {}
        for agent_key, instance in self.agent_instances.items():
            status[agent_key] = {
                "agent_id": instance.agent_id,
                "is_busy": instance.is_busy,
                "task_count": instance.task_count,
                "last_used": instance.last_used.isoformat()
                if instance.last_used
                else None,
            }

        return status

    def get_task_status(self) -> Dict[str, Any]:
        """Get task execution status"""

        return {
            "pending_tasks": len(self.pending_tasks),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "agent_instances": len(self.agent_instances),
        }

    def get_status(self) -> Dict[str, Any]:
        """Get overall coordinator status"""

        return {
            "max_concurrent": self.max_concurrent,
            "timeout_seconds": self.timeout_seconds,
            "is_running": self.is_running,
            "agent_status": self.get_agent_status(),
            "task_status": self.get_task_status(),
        }
