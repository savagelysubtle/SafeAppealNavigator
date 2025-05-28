"""
Base Agent Architecture for AI Research Assistant

This module provides the foundational agent architecture that all specialized agents inherit from.
It includes task management, resource allocation, configuration management, and observability.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ...utils.llm_provider import get_llm_model
from ...utils.unified_llm_factory import UnifiedLLMFactory

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task priority levels for resource allocation"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentTask:
    """Represents a task to be executed by an agent"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parent_workflow_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def start(self) -> None:
        """Mark task as started"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self, result: Dict[str, Any]) -> None:
        """Mark task as completed with result"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result

    def fail(self, error_message: str) -> None:
        """Mark task as failed with error message"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message

    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return self.retry_count < self.max_retries and self.status == TaskStatus.FAILED


class AgentConfig(BaseModel):
    """Dynamic configuration for individual agents"""

    # Model preferences
    preferred_llm_provider: str = Field(
        default="google", description="Preferred LLM provider"
    )
    model_temperature: float = Field(default=0.7, description="Model creativity level")
    max_tokens: int = Field(default=2048, description="Maximum response tokens")

    # Agent-specific prompts
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    specialized_prompts: Dict[str, str] = Field(
        default_factory=dict, description="Task-specific prompts"
    )

    # Performance tuning
    batch_size: int = Field(default=10, description="Processing batch size")
    timeout_seconds: int = Field(default=300, description="Task timeout")
    retry_attempts: int = Field(default=3, description="Max retry attempts")

    # Specialized settings (per agent type)
    custom_settings: Dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific settings"
    )


class BaseAgent(ABC):
    """
    Base class for all specialized agents in the AI Research Assistant.

    Provides core functionality including:
    - Task management and execution
    - Configuration management
    - LLM integration
    - Error handling and retry logic
    - Observability and metrics
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        config: Optional[AgentConfig] = None,
        llm_provider: Optional[str] = None,
        global_settings_manager=None,
        **kwargs,
    ):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.config = config or AgentConfig()
        self.llm_provider = llm_provider or self.config.preferred_llm_provider
        self.global_settings_manager = global_settings_manager

        # Initialize LLM using unified factory
        self.llm = self._initialize_llm()

        # Task management
        self.active_tasks: Dict[str, AgentTask] = {}
        self.task_history: List[AgentTask] = []

        # State management
        self.is_running = False
        self.is_paused = False
        self.stop_requested = False

        # Performance metrics
        self.start_time: Optional[datetime] = None
        self.total_tasks_completed = 0
        self.total_tasks_failed = 0

        logger.info(f"Initialized {self.__class__.__name__} with ID: {self.agent_id}")

    def _initialize_llm(self):
        """Initialize the LLM using unified factory with global settings support"""
        try:
            factory = UnifiedLLMFactory()

            # Try global settings first if available
            if self.global_settings_manager:
                try:
                    llm = factory.create_llm_from_global_settings(
                        self.global_settings_manager, "primary"
                    )
                    if llm:
                        logger.info(
                            f"✅ Using global settings for {self.__class__.__name__} LLM"
                        )
                        return llm
                except Exception as e:
                    logger.warning(f"Failed to use global settings for LLM: {e}")

            # Fallback to agent-specific configuration
            logger.info(
                f"Using agent-specific LLM configuration for {self.__class__.__name__}"
            )

            config = {
                "provider": self.llm_provider,
                "model_name": None,  # Will use default for provider
                "temperature": self.config.model_temperature,
                "max_tokens": self.config.max_tokens,
            }

            return factory.create_llm_from_config(config)

        except Exception as e:
            logger.error(f"Failed to initialize LLM using unified factory: {e}")
            # Final fallback to legacy method
            return self._legacy_initialize_llm()

    def _legacy_initialize_llm(self):
        """Legacy LLM initialization for backward compatibility"""
        try:
            logger.info("Using legacy LLM initialization as final fallback")
            return get_llm_model(
                provider=self.llm_provider,
                temperature=self.config.model_temperature,
                max_tokens=self.config.max_tokens,
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider {self.llm_provider}: {e}")
            # Fallback to first available provider
            try:
                from ...utils.llm_provider import get_configured_providers

                available_providers = get_configured_providers()
                if available_providers:
                    fallback_provider = available_providers[0]
                    logger.info(f"Falling back to provider: {fallback_provider}")
                    return get_llm_model(
                        provider=fallback_provider,
                        temperature=self.config.model_temperature,
                        max_tokens=self.config.max_tokens,
                    )
                else:
                    raise RuntimeError("No configured LLM providers available")
            except Exception as fallback_error:
                logger.error(f"Fallback LLM initialization failed: {fallback_error}")
                raise

    @abstractmethod
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Execute a specific task. Must be implemented by subclasses.

        Args:
            task: The task to execute

        Returns:
            Dict containing the task result
        """
        pass

    @abstractmethod
    def get_supported_task_types(self) -> List[str]:
        """
        Return list of task types this agent can handle.

        Returns:
            List of supported task type strings
        """
        pass

    async def run_task(
        self,
        task_type: str,
        parameters: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        parent_workflow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run a single task with proper error handling and metrics.

        Args:
            task_type: Type of task to execute
            parameters: Task parameters
            priority: Task priority level
            parent_workflow_id: Optional parent workflow ID

        Returns:
            Dict containing task result and metadata
        """
        # Validate task type
        if task_type not in self.get_supported_task_types():
            raise ValueError(f"Unsupported task type: {task_type}")

        # Create task
        task = AgentTask(
            task_type=task_type,
            parameters=parameters,
            priority=priority,
            parent_workflow_id=parent_workflow_id,
            max_retries=self.config.retry_attempts,
        )

        return await self._execute_task_with_retries(task)

    async def _execute_task_with_retries(self, task: AgentTask) -> Dict[str, Any]:
        """Execute task with retry logic and error handling"""
        self.active_tasks[task.id] = task

        try:
            while task.can_retry() or task.status == TaskStatus.PENDING:
                try:
                    task.start()

                    # Execute with timeout
                    result = await asyncio.wait_for(
                        self.execute_task(task), timeout=self.config.timeout_seconds
                    )

                    task.complete(result)
                    self.total_tasks_completed += 1

                    return {
                        "success": True,
                        "task_id": task.id,
                        "result": result,
                        "execution_time_ms": self._get_execution_time_ms(task),
                        "retry_count": task.retry_count,
                    }

                except asyncio.TimeoutError:
                    error_msg = (
                        f"Task {task.id} timed out after {self.config.timeout_seconds}s"
                    )
                    logger.warning(error_msg)
                    task.retry_count += 1
                    if not task.can_retry():
                        task.fail(error_msg)
                        self.total_tasks_failed += 1
                        break
                    await asyncio.sleep(1)  # Brief delay before retry

                except Exception as e:
                    error_msg = f"Task {task.id} failed: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    task.retry_count += 1
                    if not task.can_retry():
                        task.fail(error_msg)
                        self.total_tasks_failed += 1
                        break
                    await asyncio.sleep(1)  # Brief delay before retry

            # Task failed after all retries
            return {
                "success": False,
                "task_id": task.id,
                "error": task.error_message,
                "execution_time_ms": self._get_execution_time_ms(task),
                "retry_count": task.retry_count,
            }

        finally:
            # Clean up
            self.active_tasks.pop(task.id, None)
            self.task_history.append(task)

    def _get_execution_time_ms(self, task: AgentTask) -> float:
        """Get task execution time in milliseconds"""
        if task.started_at and task.completed_at:
            return (task.completed_at - task.started_at).total_seconds() * 1000
        return 0.0

    async def start(self) -> None:
        """Start the agent"""
        if self.is_running:
            logger.warning(f"Agent {self.agent_id} is already running")
            return

        self.is_running = True
        self.stop_requested = False
        self.start_time = datetime.now()

        logger.info(f"Agent {self.agent_id} started")

    async def stop(self) -> None:
        """Stop the agent gracefully"""
        if not self.is_running:
            logger.warning(f"Agent {self.agent_id} is not running")
            return

        logger.info(f"Stopping agent {self.agent_id}...")
        self.stop_requested = True

        # Wait for active tasks to complete (with timeout)
        timeout = 30  # 30 seconds
        start_time = time.time()

        while self.active_tasks and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.5)

        # Force stop if tasks don't complete
        if self.active_tasks:
            logger.warning(
                f"Force stopping agent {self.agent_id} with {len(self.active_tasks)} active tasks"
            )
            for task in self.active_tasks.values():
                task.fail("Agent stopped forcefully")

        self.is_running = False
        logger.info(f"Agent {self.agent_id} stopped")

    async def pause(self) -> None:
        """Pause the agent"""
        self.is_paused = True
        logger.info(f"Agent {self.agent_id} paused")

    async def resume(self) -> None:
        """Resume the agent"""
        self.is_paused = False
        logger.info(f"Agent {self.agent_id} resumed")

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics"""
        runtime_seconds = 0
        if self.start_time:
            runtime_seconds = (datetime.now() - self.start_time).total_seconds()

        return {
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "active_tasks": len(self.active_tasks),
            "total_tasks_completed": self.total_tasks_completed,
            "total_tasks_failed": self.total_tasks_failed,
            "runtime_seconds": runtime_seconds,
            "supported_task_types": self.get_supported_task_types(),
            "config": self.config.dict(),
        }

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update agent configuration"""
        # Create new config with updates
        config_dict = self.config.dict()
        config_dict.update(updates)
        self.config = AgentConfig(**config_dict)

        # Reinitialize LLM if provider changed
        if "preferred_llm_provider" in updates:
            self.llm_provider = updates["preferred_llm_provider"]
            self.llm = self._initialize_llm()

        logger.info(f"Updated configuration for agent {self.agent_id}")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the agent"""
        try:
            # Test LLM connectivity
            llm_status = "healthy"
            try:
                # Simple test query
                test_response = await self.llm.ainvoke("Test")
                if not test_response:
                    llm_status = "unhealthy"
            except Exception as e:
                llm_status = f"unhealthy: {str(e)}"

            return {
                "agent_id": self.agent_id,
                "status": "healthy" if llm_status == "healthy" else "degraded",
                "llm_status": llm_status,
                "active_tasks": len(self.active_tasks),
                "is_running": self.is_running,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "agent_id": self.agent_id,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
