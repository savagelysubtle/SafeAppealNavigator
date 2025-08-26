"""
Test suite for core.resource_manager module.

This module contains comprehensive tests for resource allocation and management,
including task submission, concurrency control, priority queues, and agent
integration functionality.
"""

import asyncio
import logging
import time
from unittest.mock import AsyncMock, Mock

import pytest

from ai_research_assistant.core.models import AgentTask
from ai_research_assistant.core.resource_manager import (
    PriorityTask,
    ResourceManager,
    ResourceState,
)


class TestResourceState:
    """Test cases for ResourceState enum."""

    def test_resource_state_values(self):
        """Test that all expected resource states exist."""
        expected_states = {
            "AVAILABLE": "available",
            "BUSY": "busy",
            "OVERLOADED": "overloaded",
            "MAINTENANCE": "maintenance",
        }

        for enum_name, enum_value in expected_states.items():
            state_enum = getattr(ResourceState, enum_name)
            assert state_enum.value == enum_value

    def test_resource_state_string_representation(self):
        """Test string representation of resource states."""
        assert str(ResourceState.AVAILABLE) == "ResourceState.AVAILABLE"
        assert ResourceState.AVAILABLE.value == "available"


class TestPriorityTask:
    """Test cases for PriorityTask dataclass."""

    def test_priority_task_creation(self):
        """Test PriorityTask creation with AgentTask."""
        agent_task = AgentTask(
            task_type="test_task", parameters={"param": "value"}, priority=5
        )

        priority_task = PriorityTask(priority=5, task=agent_task)

        assert priority_task.priority == 5
        assert priority_task.task == agent_task
        assert isinstance(priority_task.submitted_at, float)
        assert priority_task.submitted_at <= time.time()

    def test_priority_task_default_timestamp(self):
        """Test that PriorityTask generates default timestamp."""
        agent_task = AgentTask(task_type="test", parameters={})

        start_time = time.time()
        priority_task = PriorityTask(priority=1, task=agent_task)
        end_time = time.time()

        assert start_time <= priority_task.submitted_at <= end_time

    def test_priority_task_custom_timestamp(self):
        """Test PriorityTask with custom timestamp."""
        agent_task = AgentTask(task_type="test", parameters={})
        custom_timestamp = 1234567890.0

        priority_task = PriorityTask(
            priority=1, task=agent_task, submitted_at=custom_timestamp
        )

        assert priority_task.submitted_at == custom_timestamp

    def test_priority_task_comparison_by_priority(self):
        """Test PriorityTask comparison by priority (higher priority first)."""
        agent_task1 = AgentTask(task_type="task1", parameters={})
        agent_task2 = AgentTask(task_type="task2", parameters={})

        high_priority = PriorityTask(priority=10, task=agent_task1)
        low_priority = PriorityTask(priority=5, task=agent_task2)

        # Higher priority should be "less than" (comes first in queue)
        assert high_priority < low_priority
        assert not (low_priority < high_priority)

    def test_priority_task_comparison_by_timestamp_when_equal_priority(self):
        """Test PriorityTask comparison by timestamp for equal priority (FIFO)."""
        agent_task1 = AgentTask(task_type="task1", parameters={})
        agent_task2 = AgentTask(task_type="task2", parameters={})

        earlier_task = PriorityTask(priority=5, task=agent_task1, submitted_at=1000.0)
        later_task = PriorityTask(priority=5, task=agent_task2, submitted_at=2000.0)

        # Earlier submission should come first
        assert earlier_task < later_task
        assert not (later_task < earlier_task)

    def test_priority_task_comparison_edge_cases(self):
        """Test PriorityTask comparison edge cases."""
        agent_task = AgentTask(task_type="test", parameters={})

        # Same priority and timestamp
        task1 = PriorityTask(priority=5, task=agent_task, submitted_at=1000.0)
        task2 = PriorityTask(priority=5, task=agent_task, submitted_at=1000.0)

        # Should not be less than each other (equal)
        assert not (task1 < task2)
        assert not (task2 < task1)


class TestResourceManager:
    """Test cases for ResourceManager class."""

    def test_resource_manager_initialization(self):
        """Test ResourceManager initialization with default values."""
        manager = ResourceManager()

        assert manager.max_concurrent_tasks == 10
        assert manager.memory_limit_mb == 2048
        assert isinstance(manager.priority_queue, list)
        assert len(manager.priority_queue) == 0
        assert isinstance(manager.running_tasks, dict)
        assert len(manager.running_tasks) == 0
        assert isinstance(manager.resource_semaphore, asyncio.Semaphore)
        assert manager.current_memory_mb == 0.0

    def test_resource_manager_custom_initialization(self):
        """Test ResourceManager initialization with custom values."""
        manager = ResourceManager(max_concurrent_tasks=5, memory_limit_mb=1024)

        assert manager.max_concurrent_tasks == 5
        assert manager.memory_limit_mb == 1024
        assert manager.resource_semaphore._value == 5  # Semaphore initial value

    def test_resource_manager_initialization_logging(self, caplog):
        """Test that ResourceManager logs initialization parameters."""
        # Ensure the logger level captures INFO messages
        with caplog.at_level(
            logging.INFO, logger="ai_research_assistant.core.resource_manager"
        ):
            ResourceManager(max_concurrent_tasks=15, memory_limit_mb=4096)

            log_messages = [record.message for record in caplog.records]
            assert any(
                "Initialized ResourceManager: 15 concurrent tasks, 4096MB memory limit"
                in msg
                for msg in log_messages
            )

    @pytest.mark.asyncio
    async def test_submit_task_successful_execution(self):
        """Test successful task submission and execution."""
        manager = ResourceManager()

        # Create mock agent
        mock_agent = AsyncMock()
        mock_agent.agent_name = "TestAgent"
        mock_agent.run_skill.return_value = "Task completed successfully"

        # Create test task
        task = AgentTask(
            task_type="document_analysis", parameters={"document_id": "doc123"}
        )

        # Submit task
        result = await manager.submit_task(task, mock_agent)

        # Verify result
        assert result["status"] == "success"
        assert result["task_id"] == str(task.id)
        assert result["result"] == "Task completed successfully"

        # Verify agent was called correctly
        expected_prompt = (
            f"Execute task 'document_analysis' with parameters: {task.parameters}"
        )
        mock_agent.run_skill.assert_called_once_with(prompt=expected_prompt)

        # Task should not be in running_tasks anymore
        assert str(task.id) not in manager.running_tasks

    @pytest.mark.asyncio
    async def test_submit_task_execution_error(self):
        """Test task submission when agent execution fails."""
        manager = ResourceManager()

        # Create mock agent that raises exception
        mock_agent = AsyncMock()
        mock_agent.agent_name = "TestAgent"
        mock_agent.run_skill.side_effect = Exception("Agent execution failed")

        # Create test task
        task = AgentTask(task_type="failing_task", parameters={"param": "value"})

        # Submit task
        result = await manager.submit_task(task, mock_agent)

        # Verify error result
        assert result["status"] == "error"
        assert result["task_id"] == str(task.id)
        assert "Agent execution failed" in result["error"]

        # Task should not be in running_tasks anymore
        assert str(task.id) not in manager.running_tasks

    @pytest.mark.asyncio
    async def test_submit_task_adds_to_running_tasks(self):
        """Test that submitted tasks are tracked in running_tasks."""
        manager = ResourceManager()

        # Create slow mock agent to test tracking
        mock_agent = AsyncMock()
        mock_agent.agent_name = "SlowAgent"

        async def slow_run_skill(prompt):
            # Check that task is in running_tasks during execution
            task_id = prompt.split("'")[1]  # Extract task type as identifier
            # We can't check the exact ID easily, but we can check that there's a running task
            assert len(manager.running_tasks) > 0
            await asyncio.sleep(0.1)  # Small delay
            return "Slow task completed"

        mock_agent.run_skill.side_effect = slow_run_skill

        # Create test task
        task = AgentTask(task_type="slow_task", parameters={"delay": 0.1})

        # Submit task
        result = await manager.submit_task(task, mock_agent)

        # Verify successful completion
        assert result["status"] == "success"
        assert result["result"] == "Slow task completed"

    @pytest.mark.asyncio
    async def test_submit_task_concurrency_control(self):
        """Test that ResourceManager respects concurrency limits."""
        # Create manager with low concurrency limit
        manager = ResourceManager(max_concurrent_tasks=2)

        # Create mock agent with controlled delay
        mock_agent = AsyncMock()
        mock_agent.agent_name = "ConcurrentAgent"

        task_start_times = []

        async def delayed_run_skill(prompt):
            task_start_times.append(time.time())
            await asyncio.sleep(0.1)  # Small delay to test concurrency
            return "Concurrent task completed"

        mock_agent.run_skill.side_effect = delayed_run_skill

        # Create multiple tasks
        tasks = [
            AgentTask(task_type=f"task_{i}", parameters={"id": i}) for i in range(4)
        ]

        # Submit all tasks concurrently
        start_time = time.time()
        results = await asyncio.gather(
            *[manager.submit_task(task, mock_agent) for task in tasks]
        )
        end_time = time.time()

        # All tasks should complete successfully
        assert all(result["status"] == "success" for result in results)

        # Due to concurrency limit of 2, execution should take at least 2 * 0.1 seconds
        # (2 batches of 2 concurrent tasks)
        assert end_time - start_time >= 0.15  # Allow some tolerance

    def test_get_resource_status_empty(self):
        """Test resource status when no tasks are running."""
        manager = ResourceManager(max_concurrent_tasks=5, memory_limit_mb=1024)

        status = manager.get_resource_status()

        expected_status = {
            "running_tasks": 0,
            "queued_tasks": 0,
            "max_concurrent_tasks": 5,
            "memory_usage_mb": 0.0,
            "memory_limit_mb": 1024,
        }

        assert status == expected_status

    def test_get_resource_status_with_queued_tasks(self):
        """Test resource status with queued tasks."""
        manager = ResourceManager()

        # Manually add tasks to priority queue for testing
        task1 = AgentTask(task_type="task1", parameters={})
        task2 = AgentTask(task_type="task2", parameters={})

        manager.priority_queue.append(PriorityTask(priority=1, task=task1))
        manager.priority_queue.append(PriorityTask(priority=2, task=task2))

        status = manager.get_resource_status()

        assert status["queued_tasks"] == 2
        assert status["running_tasks"] == 0

    def test_get_resource_status_with_running_tasks(self):
        """Test resource status with running tasks."""
        manager = ResourceManager()

        # Manually add tasks to running_tasks for testing
        task1 = AgentTask(task_type="task1", parameters={})
        task2 = AgentTask(task_type="task2", parameters={})

        manager.running_tasks[str(task1.id)] = task1
        manager.running_tasks[str(task2.id)] = task2

        status = manager.get_resource_status()

        assert status["running_tasks"] == 2
        assert status["queued_tasks"] == 0

    @pytest.mark.asyncio
    async def test_resource_manager_logging_behavior(self, caplog):
        """Test logging behavior during task submission."""
        # Ensure the logger level captures INFO messages
        with caplog.at_level(
            logging.INFO, logger="ai_research_assistant.core.resource_manager"
        ):
            manager = ResourceManager()

            # Create mock agent
            mock_agent = AsyncMock()
            mock_agent.agent_name = "LoggingTestAgent"
            mock_agent.run_skill.return_value = "Success"

            # Create and submit task
            task = AgentTask(task_type="logging_test", parameters={"test": True})
            await manager.submit_task(task, mock_agent)

            # Verify logging occurred
            log_messages = [record.message for record in caplog.records]
            assert any(
                f"Submitting task {task.id} with priority {task.priority}" in msg
                for msg in log_messages
            )
        assert any("LoggingTestAgent" in msg for msg in log_messages)

    @pytest.mark.asyncio
    async def test_resource_manager_error_logging(self, caplog):
        """Test error logging when task execution fails."""
        manager = ResourceManager()

        # Create mock agent that fails
        mock_agent = AsyncMock()
        mock_agent.agent_name = "FailingAgent"
        mock_agent.run_skill.side_effect = ValueError("Test error for logging")

        # Create and submit task
        task = AgentTask(task_type="error_test", parameters={})
        await manager.submit_task(task, mock_agent)

        # Verify error logging
        log_messages = [record.message for record in caplog.records]
        assert any(f"Error executing task {task.id}" in msg for msg in log_messages)


class TestResourceManagerIntegration:
    """Integration tests for ResourceManager with realistic scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_agents_multiple_tasks(self):
        """Test ResourceManager with multiple agents and tasks."""
        manager = ResourceManager(max_concurrent_tasks=3)

        # Create multiple mock agents
        agents = []
        for i in range(3):
            agent = AsyncMock()
            agent.agent_name = f"Agent_{i}"
            agent.run_skill.return_value = f"Result from Agent_{i}"
            agents.append(agent)

        # Create tasks for different agents
        tasks = []
        for i in range(6):  # More tasks than agents
            task = AgentTask(task_type=f"task_{i}", parameters={"agent_id": i % 3})
            tasks.append(task)

        # Submit tasks with corresponding agents
        results = []
        for i, task in enumerate(tasks):
            agent = agents[i % 3]
            result = await manager.submit_task(task, agent)
            results.append(result)

        # All tasks should complete successfully
        assert len(results) == 6
        assert all(result["status"] == "success" for result in results)

        # Verify agents were called
        for agent in agents:
            assert agent.run_skill.call_count >= 1

    @pytest.mark.asyncio
    async def test_resource_manager_with_different_task_priorities(self):
        """Test ResourceManager behavior with different task priorities."""
        manager = ResourceManager()

        # Create tasks with different priorities
        high_priority_task = AgentTask(
            task_type="urgent_task", parameters={"urgent": True}, priority=10
        )

        low_priority_task = AgentTask(
            task_type="routine_task", parameters={"routine": True}, priority=1
        )

        # Create mock agent
        mock_agent = AsyncMock()
        mock_agent.agent_name = "PriorityAgent"
        mock_agent.run_skill.return_value = "Priority task completed"

        # Submit both tasks
        results = await asyncio.gather(
            manager.submit_task(high_priority_task, mock_agent),
            manager.submit_task(low_priority_task, mock_agent),
        )

        # Both should complete successfully
        assert all(result["status"] == "success" for result in results)

    @pytest.mark.asyncio
    async def test_resource_manager_memory_tracking_placeholder(self):
        """Test memory tracking placeholder functionality."""
        manager = ResourceManager(memory_limit_mb=512)

        # Create mock agent
        mock_agent = AsyncMock()
        mock_agent.agent_name = "MemoryAgent"
        mock_agent.run_skill.return_value = "Memory task completed"

        # Create task
        task = AgentTask(task_type="memory_intensive", parameters={"size": "large"})

        # Submit task
        result = await manager.submit_task(task, mock_agent)

        # Should complete successfully
        assert result["status"] == "success"

        # Memory usage should still be placeholder value (0.0)
        status = manager.get_resource_status()
        assert status["memory_usage_mb"] == 0.0
        assert status["memory_limit_mb"] == 512


class TestResourceManagerEdgeCases:
    """Test cases for edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_submit_task_with_invalid_agent(self):
        """Test submitting task with invalid agent."""
        manager = ResourceManager()

        # Create task
        task = AgentTask(task_type="test", parameters={})

        # Submit with None agent should return error result
        result = await manager.submit_task(task, None)

        assert result["status"] == "error"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_submit_task_with_agent_missing_run_skill(self):
        """Test submitting task with agent missing run_skill method."""
        manager = ResourceManager()

        # Create mock agent without run_skill method
        mock_agent = Mock()
        mock_agent.agent_name = "IncompleteAgent"
        # Don't add run_skill method

        # Create task
        task = AgentTask(task_type="test", parameters={})

        # Should handle missing method gracefully
        result = await manager.submit_task(task, mock_agent)

        assert result["status"] == "error"
        assert "error" in result

    def test_resource_manager_zero_concurrency_limit(self):
        """Test ResourceManager with zero concurrency limit."""
        # asyncio.Semaphore actually allows 0, though it's not practical
        manager = ResourceManager(max_concurrent_tasks=0)

        # Should work but no tasks can run concurrently
        assert manager.max_concurrent_tasks == 0
        assert manager.resource_semaphore._value == 0

    def test_resource_manager_negative_memory_limit(self):
        """Test ResourceManager with negative memory limit."""
        # Should work but with unusual value
        manager = ResourceManager(memory_limit_mb=-100)

        status = manager.get_resource_status()
        assert status["memory_limit_mb"] == -100

    @pytest.mark.asyncio
    async def test_task_cleanup_after_exception(self):
        """Test that tasks are properly cleaned up after exceptions."""
        manager = ResourceManager()

        # Create agent that raises exception
        mock_agent = AsyncMock()
        mock_agent.agent_name = "ExceptionAgent"
        mock_agent.run_skill.side_effect = RuntimeError("Cleanup test error")

        # Create task
        task = AgentTask(task_type="cleanup_test", parameters={})
        task_id = str(task.id)

        # Submit task (should handle exception)
        result = await manager.submit_task(task, mock_agent)

        # Verify error handling
        assert result["status"] == "error"

        # Task should be cleaned up from running_tasks
        assert task_id not in manager.running_tasks

    def test_priority_task_comparison_with_none_values(self):
        """Test PriorityTask comparison edge cases with unusual values."""
        agent_task = AgentTask(task_type="test", parameters={})

        # Test with very high and very low priorities
        max_priority = PriorityTask(priority=float("inf"), task=agent_task)
        min_priority = PriorityTask(priority=float("-inf"), task=agent_task)

        assert max_priority < min_priority  # inf > -inf, so max comes first

    def test_resource_status_data_types(self):
        """Test that resource status returns correct data types."""
        manager = ResourceManager()
        status = manager.get_resource_status()

        # Verify all values are correct types
        assert isinstance(status["running_tasks"], int)
        assert isinstance(status["queued_tasks"], int)
        assert isinstance(status["max_concurrent_tasks"], int)
        assert isinstance(status["memory_usage_mb"], float)
        assert isinstance(status["memory_limit_mb"], int)
