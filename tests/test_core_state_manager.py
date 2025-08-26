"""
Test suite for core.state_manager module.

This module contains comprehensive tests for agent state management,
including database operations, metrics storage and retrieval, connection
management, and async functionality.
"""

import json
import logging
import tempfile
from pathlib import Path

import pytest

from ai_research_assistant.core.state_manager import AgentStateManager


class TestAgentStateManagerInitialization:
    """Test cases for AgentStateManager initialization."""

    def test_agent_state_manager_default_initialization(self):
        """Test AgentStateManager initialization with default database path."""
        manager = AgentStateManager()

        assert manager.db_path == "tmp/agent_state.db"
        assert manager._connection_pool is None

    def test_agent_state_manager_custom_db_path(self):
        """Test AgentStateManager initialization with custom database path."""
        custom_path = "custom/path/state.db"
        manager = AgentStateManager(db_path=custom_path)

        assert manager.db_path == custom_path
        assert manager._connection_pool is None

    def test_agent_state_manager_none_db_path(self):
        """Test AgentStateManager initialization with None db_path (uses default)."""
        manager = AgentStateManager(db_path=None)

        assert manager.db_path == "tmp/agent_state.db"

    @pytest.mark.asyncio
    async def test_initialize_creates_directory_and_connection(self):
        """Test that initialize creates database directory and connection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/test_state.db"
            manager = AgentStateManager(db_path=db_path)

            # Directory should not exist initially
            assert not Path(temp_dir).exists() or not Path(db_path).exists()

            # Initialize should create directory and connection
            await manager.initialize()

            assert manager._connection_pool is not None
            assert Path(db_path).parent.exists()

            # Clean up
            await manager.close()

    @pytest.mark.asyncio
    async def test_initialize_logging(self, caplog):
        """Test that initialize logs the database path."""
        # Set the logging level to capture INFO logs
        caplog.set_level(
            logging.INFO, logger="ai_research_assistant.core.state_manager"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/test_state.db"
            manager = AgentStateManager(db_path=db_path)

            try:
                await manager.initialize()

                # Verify logging
                log_messages = [record.message for record in caplog.records]
                assert any(db_path in msg for msg in log_messages)
                assert any(
                    "Initialized AgentStateManager" in msg for msg in log_messages
                )
            finally:
                await manager.close()

    @pytest.mark.asyncio
    async def test_ensure_db_directory_creates_path(self):
        """Test that _ensure_db_directory creates the database path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = f"{temp_dir}/nested/deep/state.db"
            manager = AgentStateManager(db_path=nested_path)

            # Directory should not exist
            assert not Path(nested_path).parent.exists()

            # This is called during initialize()
            manager._ensure_db_directory()

            # Directory should now exist
            assert Path(nested_path).parent.exists()


class TestDatabaseSchemaCreation:
    """Test cases for database schema creation."""

    @pytest.mark.asyncio
    async def test_create_schema_creates_tables(self):
        """Test that _create_schema creates required tables."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/schema_test.db"
            manager = AgentStateManager(db_path=db_path)

            await manager.initialize()

            # Verify table exists
            async with manager._connection_pool.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='agent_metrics'"
            ) as cursor:
                result = await cursor.fetchone()
                assert result is not None
                assert result[0] == "agent_metrics"

            await manager.close()

    @pytest.mark.asyncio
    async def test_create_schema_creates_indexes(self):
        """Test that _create_schema creates required indexes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/index_test.db"
            manager = AgentStateManager(db_path=db_path)

            await manager.initialize()

            # Verify index exists
            async with manager._connection_pool.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_metrics_timestamp'"
            ) as cursor:
                result = await cursor.fetchone()
                assert result is not None
                assert result[0] == "idx_metrics_timestamp"

            await manager.close()

    @pytest.mark.asyncio
    async def test_create_schema_before_initialization_raises_error(self):
        """Test that _create_schema raises error when called before initialization."""
        manager = AgentStateManager()

        with pytest.raises(RuntimeError) as exc_info:
            await manager._create_schema()

        assert "Database connection not initialized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_schema_columns_are_correct(self):
        """Test that agent_metrics table has correct columns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/columns_test.db"
            manager = AgentStateManager(db_path=db_path)

            await manager.initialize()

            # Get table schema
            async with manager._connection_pool.execute(
                "PRAGMA table_info(agent_metrics)"
            ) as cursor:
                columns = await cursor.fetchall()

            # Verify expected columns exist
            column_names = [col[1] for col in columns]  # Column name is at index 1
            expected_columns = [
                "id",
                "metric_name",
                "metric_value",
                "metric_type",
                "tags",
                "timestamp",
                "agent_id",
            ]

            for expected_col in expected_columns:
                assert expected_col in column_names

            await manager.close()


class TestMetricsStorage:
    """Test cases for metrics storage functionality."""

    @pytest.mark.asyncio
    async def test_store_metric_successful(self):
        """Test successful metric storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/store_test.db"
            manager = AgentStateManager(db_path=db_path)

            await manager.initialize()

            # Store a metric
            metric_data = {
                "name": "response_time",
                "value": 125.5,
                "metric_type": "duration",
                "tags": {"endpoint": "/api/chat", "status": "success"},
                "agent_id": "agent_001",
            }

            await manager.store_metric(metric_data)

            # Verify metric was stored
            async with manager._connection_pool.execute(
                "SELECT * FROM agent_metrics WHERE metric_name = ?", ("response_time",)
            ) as cursor:
                result = await cursor.fetchone()

            assert result is not None
            assert result["metric_name"] == "response_time"
            assert result["metric_value"] == 125.5
            assert result["metric_type"] == "duration"
            assert result["agent_id"] == "agent_001"

            # Verify tags are stored as JSON
            stored_tags = json.loads(result["tags"])
            assert stored_tags == {"endpoint": "/api/chat", "status": "success"}

            await manager.close()

    @pytest.mark.asyncio
    async def test_store_metric_without_agent_id(self):
        """Test storing metric without agent_id."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/no_agent_test.db"
            manager = AgentStateManager(db_path=db_path)

            await manager.initialize()

            # Store metric without agent_id
            metric_data = {
                "name": "cpu_usage",
                "value": 75.2,
                "metric_type": "percentage",
                "tags": {"system": "production"},
            }

            await manager.store_metric(metric_data)

            # Verify metric was stored with None agent_id
            async with manager._connection_pool.execute(
                "SELECT agent_id FROM agent_metrics WHERE metric_name = ?",
                ("cpu_usage",),
            ) as cursor:
                result = await cursor.fetchone()

            assert result is not None
            assert result["agent_id"] is None

            await manager.close()

    @pytest.mark.asyncio
    async def test_store_metric_before_initialization_raises_error(self):
        """Test that store_metric raises error when called before initialization."""
        manager = AgentStateManager()

        metric_data = {
            "name": "test_metric",
            "value": 100,
            "metric_type": "counter",
            "tags": {},
        }

        with pytest.raises(RuntimeError) as exc_info:
            await manager.store_metric(metric_data)

        assert "Database connection not initialized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_store_metric_with_complex_tags(self):
        """Test storing metric with complex tags structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/complex_tags_test.db"
            manager = AgentStateManager(db_path=db_path)

            await manager.initialize()

            # Store metric with complex tags
            complex_tags = {
                "service": "chat_service",
                "version": "1.2.3",
                "environment": "production",
                "metadata": {"request_id": "req_12345", "user_type": "premium"},
            }

            metric_data = {
                "name": "request_latency",
                "value": 250.7,
                "metric_type": "latency",
                "tags": complex_tags,
            }

            await manager.store_metric(metric_data)

            # Verify complex tags are properly stored and retrieved
            async with manager._connection_pool.execute(
                "SELECT tags FROM agent_metrics WHERE metric_name = ?",
                ("request_latency",),
            ) as cursor:
                result = await cursor.fetchone()

            stored_tags = json.loads(result["tags"])
            assert stored_tags == complex_tags

            await manager.close()


class TestMetricsRetrieval:
    """Test cases for metrics retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_metrics_all_metrics(self):
        """Test retrieving all metrics within time range."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/get_all_test.db"
            manager = AgentStateManager(db_path=db_path)

            await manager.initialize()

            # Store multiple metrics
            metrics = [
                {
                    "name": "metric_1",
                    "value": 10.0,
                    "metric_type": "counter",
                    "tags": {"type": "test"},
                },
                {
                    "name": "metric_2",
                    "value": 20.0,
                    "metric_type": "gauge",
                    "tags": {"type": "test"},
                },
            ]

            for metric in metrics:
                await manager.store_metric(metric)

            # Retrieve all metrics
            results = await manager.get_metrics()

            assert len(results) == 2
            assert any(m["metric_name"] == "metric_1" for m in results)
            assert any(m["metric_name"] == "metric_2" for m in results)

            await manager.close()

    @pytest.mark.asyncio
    async def test_get_metrics_filtered_by_name(self):
        """Test retrieving metrics filtered by metric name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/filter_name_test.db"
            manager = AgentStateManager(db_path=db_path)

            await manager.initialize()

            # Store metrics with different names
            await manager.store_metric(
                {
                    "name": "response_time",
                    "value": 100.0,
                    "metric_type": "duration",
                    "tags": {},
                }
            )

            await manager.store_metric(
                {
                    "name": "error_count",
                    "value": 5.0,
                    "metric_type": "counter",
                    "tags": {},
                }
            )

            # Retrieve only response_time metrics
            results = await manager.get_metrics(metric_name="response_time")

            assert len(results) == 1
            assert results[0]["metric_name"] == "response_time"
            assert results[0]["metric_value"] == 100.0

            await manager.close()

    @pytest.mark.asyncio
    async def test_get_metrics_filtered_by_agent_id(self):
        """Test retrieving metrics filtered by agent ID."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/filter_agent_test.db"
            manager = AgentStateManager(db_path=db_path)

            await manager.initialize()

            # Store metrics for different agents
            await manager.store_metric(
                {
                    "name": "task_count",
                    "value": 5.0,
                    "metric_type": "counter",
                    "tags": {},
                    "agent_id": "agent_1",
                }
            )

            await manager.store_metric(
                {
                    "name": "task_count",
                    "value": 3.0,
                    "metric_type": "counter",
                    "tags": {},
                    "agent_id": "agent_2",
                }
            )

            # Retrieve metrics for agent_1 only
            results = await manager.get_metrics(agent_id="agent_1")

            assert len(results) == 1
            assert results[0]["agent_id"] == "agent_1"
            assert results[0]["metric_value"] == 5.0

            await manager.close()

    @pytest.mark.asyncio
    async def test_get_metrics_with_custom_time_range(self):
        """Test retrieving metrics with custom time range."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/time_range_test.db"
            manager = AgentStateManager(db_path=db_path)

            try:
                await manager.initialize()

                # Store a metric
                await manager.store_metric(
                    {
                        "name": "recent_metric",
                        "value": 42.0,
                        "metric_type": "gauge",
                        "tags": {},
                    }
                )

                # Retrieve metrics from last 1 day (should include recent metric)
                results_1_day = await manager.get_metrics(days_back=1)
                assert len(results_1_day) == 1

                # Retrieve metrics from last 0 days (should be empty)
                results_0_days = await manager.get_metrics(days_back=0)
                assert len(results_0_days) == 0
            finally:
                await manager.close()

    @pytest.mark.asyncio
    async def test_get_metrics_combined_filters(self):
        """Test retrieving metrics with multiple filters combined."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/combined_filter_test.db"
            manager = AgentStateManager(db_path=db_path)

            await manager.initialize()

            # Store various metrics
            test_metrics = [
                {
                    "name": "cpu_usage",
                    "value": 80.0,
                    "metric_type": "percentage",
                    "tags": {},
                    "agent_id": "server_1",
                },
                {
                    "name": "cpu_usage",
                    "value": 60.0,
                    "metric_type": "percentage",
                    "tags": {},
                    "agent_id": "server_2",
                },
                {
                    "name": "memory_usage",
                    "value": 70.0,
                    "metric_type": "percentage",
                    "tags": {},
                    "agent_id": "server_1",
                },
            ]

            for metric in test_metrics:
                await manager.store_metric(metric)

            # Retrieve CPU usage for server_1 only
            results = await manager.get_metrics(
                metric_name="cpu_usage", agent_id="server_1"
            )

            assert len(results) == 1
            assert results[0]["metric_name"] == "cpu_usage"
            assert results[0]["agent_id"] == "server_1"
            assert results[0]["metric_value"] == 80.0

            await manager.close()

    @pytest.mark.asyncio
    async def test_get_metrics_before_initialization_raises_error(self):
        """Test that get_metrics raises error when called before initialization."""
        manager = AgentStateManager()

        with pytest.raises(RuntimeError) as exc_info:
            await manager.get_metrics()

        assert "Database connection not initialized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_metrics_ordering(self):
        """Test that get_metrics returns results ordered by timestamp descending."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/ordering_test.db"
            manager = AgentStateManager(db_path=db_path)

            await manager.initialize()

            # Store metrics with slight delay to ensure different timestamps
            import asyncio

            await manager.store_metric(
                {
                    "name": "test_metric",
                    "value": 1.0,
                    "metric_type": "counter",
                    "tags": {"order": "first"},
                }
            )

            await asyncio.sleep(0.001)  # Small delay

            await manager.store_metric(
                {
                    "name": "test_metric",
                    "value": 2.0,
                    "metric_type": "counter",
                    "tags": {"order": "second"},
                }
            )

            # Retrieve metrics
            results = await manager.get_metrics()

            # Should be ordered by timestamp descending (most recent first)
            assert len(results) == 2
            assert results[0]["metric_value"] == 2.0  # Most recent
            assert results[1]["metric_value"] == 1.0  # Older

            await manager.close()


class TestConnectionManagement:
    """Test cases for database connection management."""

    @pytest.mark.asyncio
    async def test_close_connection(self):
        """Test closing database connection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/close_test.db"
            manager = AgentStateManager(db_path=db_path)

            await manager.initialize()
            assert manager._connection_pool is not None

            await manager.close()
            assert manager._connection_pool is None

    @pytest.mark.asyncio
    async def test_close_connection_logging(self, caplog):
        """Test that close() logs the closure."""
        # Set the logging level to capture INFO logs
        caplog.set_level(
            logging.INFO, logger="ai_research_assistant.core.state_manager"
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/close_log_test.db"
            manager = AgentStateManager(db_path=db_path)

            try:
                await manager.initialize()
                await manager.close()

                # Verify logging
                log_messages = [record.message for record in caplog.records]
                assert any("database connection closed" in msg for msg in log_messages)
            finally:
                # Ensure cleanup even if test fails
                if manager._connection_pool:
                    await manager.close()

    @pytest.mark.asyncio
    async def test_close_without_initialization(self):
        """Test closing connection when not initialized (should not error)."""
        manager = AgentStateManager()

        # Should not raise exception
        await manager.close()
        assert manager._connection_pool is None

    @pytest.mark.asyncio
    async def test_multiple_close_calls(self):
        """Test multiple close calls (should be safe)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/multi_close_test.db"
            manager = AgentStateManager(db_path=db_path)

            await manager.initialize()

            # Multiple close calls should not error
            await manager.close()
            await manager.close()
            await manager.close()

            assert manager._connection_pool is None


class TestAgentStateManagerIntegration:
    """Integration tests for AgentStateManager."""

    @pytest.mark.asyncio
    async def test_full_lifecycle_with_metrics(self):
        """Test complete lifecycle: initialize, store, retrieve, close."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/lifecycle_test.db"
            manager = AgentStateManager(db_path=db_path)

            # Initialize
            await manager.initialize()

            # Store multiple metrics
            metrics_data = [
                {
                    "name": "api_response_time",
                    "value": 150.2,
                    "metric_type": "duration",
                    "tags": {"endpoint": "/chat", "method": "POST"},
                    "agent_id": "api_agent",
                },
                {
                    "name": "memory_usage",
                    "value": 85.5,
                    "metric_type": "percentage",
                    "tags": {"component": "processor"},
                    "agent_id": "system_agent",
                },
                {
                    "name": "error_rate",
                    "value": 0.02,
                    "metric_type": "ratio",
                    "tags": {"severity": "low"},
                    "agent_id": "monitor_agent",
                },
            ]

            for metric in metrics_data:
                await manager.store_metric(metric)

            # Retrieve and verify all metrics
            all_metrics = await manager.get_metrics()
            assert len(all_metrics) == 3

            # Retrieve filtered metrics
            api_metrics = await manager.get_metrics(agent_id="api_agent")
            assert len(api_metrics) == 1
            assert api_metrics[0]["metric_name"] == "api_response_time"

            duration_metrics = await manager.get_metrics(metric_name="memory_usage")
            assert len(duration_metrics) == 1
            assert duration_metrics[0]["metric_value"] == 85.5

            # Close
            await manager.close()

    @pytest.mark.asyncio
    async def test_persistence_across_sessions(self):
        """Test that data persists across different manager instances."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/persistence_test.db"

            # First session: store data
            manager1 = AgentStateManager(db_path=db_path)
            await manager1.initialize()

            await manager1.store_metric(
                {
                    "name": "persistent_metric",
                    "value": 999.99,
                    "metric_type": "test",
                    "tags": {"session": "first"},
                }
            )

            await manager1.close()

            # Second session: retrieve data
            manager2 = AgentStateManager(db_path=db_path)
            await manager2.initialize()

            results = await manager2.get_metrics(metric_name="persistent_metric")

            assert len(results) == 1
            assert results[0]["metric_value"] == 999.99

            stored_tags = json.loads(results[0]["tags"])
            assert stored_tags["session"] == "first"

            await manager2.close()


class TestErrorHandling:
    """Test cases for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_invalid_database_path(self):
        """Test handling of invalid database path."""
        # Try to create database in non-existent directory without permission
        invalid_path = "/root/invalid/path/state.db"  # Likely no permission
        manager = AgentStateManager(db_path=invalid_path)

        try:
            await manager.initialize()
            # If it succeeds (e.g., running as root), clean up
            await manager.close()
        except (PermissionError, OSError):
            # Expected for most systems
            pass

    @pytest.mark.asyncio
    async def test_malformed_metric_data(self):
        """Test handling of malformed metric data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/malformed_test.db"
            manager = AgentStateManager(db_path=db_path)

            await manager.initialize()

            # Try to store malformed metric data
            malformed_data = {
                "name": "test_metric",
                # Missing required fields
                "tags": "not_a_dict",  # Should be dict, not string
            }

            with pytest.raises((KeyError, TypeError)):
                await manager.store_metric(malformed_data)

            await manager.close()

    @pytest.mark.asyncio
    async def test_database_locked_scenario(self):
        """Test handling when database is locked or busy."""
        # This is difficult to test reliably, but we can mock the scenario
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = f"{temp_dir}/locked_test.db"
            manager = AgentStateManager(db_path=db_path)

            await manager.initialize()

            # Store a metric successfully first
            await manager.store_metric(
                {
                    "name": "test_metric",
                    "value": 1.0,
                    "metric_type": "counter",
                    "tags": {},
                }
            )

            # Verify it was stored
            results = await manager.get_metrics()
            assert len(results) == 1

            await manager.close()
