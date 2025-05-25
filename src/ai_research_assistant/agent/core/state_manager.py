"""
Agent State Management for AI Research Assistant

This module provides centralized state management for all agents, including
configuration persistence, task history, and shared data storage.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

logger = logging.getLogger(__name__)


class AgentStateManager:
    """
    Centralized state management for agent ecosystem.

    Handles:
    - Agent configuration persistence
    - Task history and metrics
    - Shared data storage
    - Workflow trace storage
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or "tmp/agent_state.db"
        self._ensure_db_directory()
        self._connection_pool: Optional[aiosqlite.Connection] = None

    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Initialize the state manager and create database schema"""
        await self._create_connection_pool()
        await self._create_schema()
        logger.info(f"Initialized AgentStateManager with database: {self.db_path}")

    async def _create_connection_pool(self):
        """Create database connection pool"""
        self._connection_pool = await aiosqlite.connect(self.db_path)
        if self._connection_pool:
            self._connection_pool.row_factory = aiosqlite.Row

    async def _create_schema(self):
        """Create database schema for agent state management"""
        if not self._connection_pool:
            raise RuntimeError("Database connection not initialized")

        schema_sql = """
        -- Agent configurations
        CREATE TABLE IF NOT EXISTS agent_configs (
            agent_id TEXT PRIMARY KEY,
            agent_type TEXT NOT NULL,
            config_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Task history
        CREATE TABLE IF NOT EXISTS task_history (
            task_id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            task_type TEXT NOT NULL,
            parameters TEXT NOT NULL,
            priority INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            result TEXT,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            execution_time_ms REAL,
            parent_workflow_id TEXT
        );

        -- Workflow traces
        CREATE TABLE IF NOT EXISTS workflow_traces (
            workflow_id TEXT PRIMARY KEY,
            workflow_type TEXT NOT NULL,
            trace_data TEXT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            total_duration_ms REAL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Idempotent operations
        CREATE TABLE IF NOT EXISTS idempotent_operations (
            operation_id TEXT PRIMARY KEY,
            result TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        );

        -- Classified data storage
        CREATE TABLE IF NOT EXISTS classified_data (
            data_key TEXT PRIMARY KEY,
            data_value TEXT NOT NULL,
            classification TEXT NOT NULL,
            created_by TEXT NOT NULL,
            access_log TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Agent metrics
        CREATE TABLE IF NOT EXISTS agent_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            metric_type TEXT NOT NULL,
            tags TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            agent_id TEXT
        );

        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_task_history_agent_id ON task_history(agent_id);
        CREATE INDEX IF NOT EXISTS idx_task_history_status ON task_history(status);
        CREATE INDEX IF NOT EXISTS idx_task_history_created_at ON task_history(created_at);
        CREATE INDEX IF NOT EXISTS idx_workflow_traces_status ON workflow_traces(status);
        CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON agent_metrics(timestamp);
        CREATE INDEX IF NOT EXISTS idx_idempotent_expires ON idempotent_operations(expires_at);
        """

        await self._connection_pool.executescript(schema_sql)
        await self._connection_pool.commit()

    # Agent Configuration Management
    async def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get stored configuration for an agent"""
        if not self._connection_pool:
            raise RuntimeError("Database connection not initialized")

        async with self._connection_pool.execute(
            "SELECT config_data FROM agent_configs WHERE agent_id = ?", (agent_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row["config_data"])
            return None

    async def store_agent_config(
        self, agent_id: str, agent_type: str, config: Dict[str, Any]
    ):
        """Store agent configuration"""
        if not self._connection_pool:
            raise RuntimeError("Database connection not initialized")

        config_json = json.dumps(config)
        await self._connection_pool.execute(
            """
            INSERT OR REPLACE INTO agent_configs
            (agent_id, agent_type, config_data, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (agent_id, agent_type, config_json),
        )
        await self._connection_pool.commit()

    # Task History Management
    async def store_task_history(self, task_data: Dict[str, Any]):
        """Store completed task in history"""
        if not self._connection_pool:
            raise RuntimeError("Database connection not initialized")

        await self._connection_pool.execute(
            """
            INSERT OR REPLACE INTO task_history
            (task_id, agent_id, task_type, parameters, priority, status,
             created_at, started_at, completed_at, result, error_message,
             retry_count, execution_time_ms, parent_workflow_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_data["task_id"],
                task_data["agent_id"],
                task_data["task_type"],
                json.dumps(task_data["parameters"]),
                task_data["priority"],
                task_data["status"],
                task_data["created_at"],
                task_data.get("started_at"),
                task_data.get("completed_at"),
                json.dumps(task_data.get("result"))
                if task_data.get("result")
                else None,
                task_data.get("error_message"),
                task_data.get("retry_count", 0),
                task_data.get("execution_time_ms"),
                task_data.get("parent_workflow_id"),
            ),
        )
        await self._connection_pool.commit()

    async def get_task_history(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get task history with optional filtering"""
        query = "SELECT * FROM task_history"
        params = []
        conditions = []

        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)

        if status:
            conditions.append("status = ?")
            params.append(status)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        async with self._connection_pool.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # Workflow Trace Management
    async def store_workflow_trace(self, trace_data: Dict[str, Any]):
        """Store workflow trace for analysis"""
        await self._connection_pool.execute(
            """
            INSERT OR REPLACE INTO workflow_traces
            (workflow_id, workflow_type, trace_data, start_time, end_time,
             total_duration_ms, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trace_data["workflow_id"],
                trace_data["workflow_type"],
                json.dumps(trace_data),
                trace_data["start_time"],
                trace_data.get("end_time"),
                trace_data.get("total_duration_ms"),
                trace_data["status"],
            ),
        )
        await self._connection_pool.commit()

    # Classified Data Management
    async def store_classified_record(self, key: str, record: Dict[str, Any]):
        """Store classified data with access controls"""
        await self._connection_pool.execute(
            """
            INSERT OR REPLACE INTO classified_data
            (data_key, data_value, classification, created_by, access_log, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                key,
                json.dumps(record["data"]),
                record["classification"],
                record["created_by"],
                json.dumps(record.get("access_log", [])),
            ),
        )
        await self._connection_pool.commit()

    async def get_classified_record(self, key: str) -> Optional[Dict[str, Any]]:
        """Get classified data record"""
        async with self._connection_pool.execute(
            "SELECT data_value, classification, created_by, access_log FROM classified_data WHERE data_key = ?",
            (key,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "data": json.loads(row["data_value"]),
                    "classification": row["classification"],
                    "created_by": row["created_by"],
                    "access_log": json.loads(row["access_log"]),
                }
            return None

    # Metrics Management
    async def store_metric(self, metric_data: Dict[str, Any]):
        """Store agent metric"""
        await self._connection_pool.execute(
            """
            INSERT INTO agent_metrics
            (metric_name, metric_value, metric_type, tags, agent_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                metric_data["name"],
                metric_data["value"],
                metric_data["metric_type"],
                json.dumps(metric_data["tags"]),
                metric_data.get("agent_id"),
            ),
        )
        await self._connection_pool.commit()

    async def get_metrics(
        self,
        metric_name: Optional[str] = None,
        agent_id: Optional[str] = None,
        days_back: int = 7,
    ) -> List[Dict[str, Any]]:
        """Get metrics with optional filtering"""
        query = "SELECT * FROM agent_metrics WHERE timestamp > ?"
        params = [datetime.now() - timedelta(days=days_back)]

        if metric_name:
            query += " AND metric_name = ?"
            params.append(metric_name)

        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)

        query += " ORDER BY timestamp DESC"

        async with self._connection_pool.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # Cleanup operations
    async def cleanup_expired_operations(self):
        """Remove expired idempotent operations"""
        await self._connection_pool.execute(
            "DELETE FROM idempotent_operations WHERE expires_at < ?", (datetime.now(),)
        )
        await self._connection_pool.commit()

    async def cleanup_old_metrics(self, days_to_keep: int = 30):
        """Remove old metrics to manage database size"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        await self._connection_pool.execute(
            "DELETE FROM agent_metrics WHERE timestamp < ?", (cutoff_date,)
        )
        await self._connection_pool.commit()

    async def close(self):
        """Close database connections"""
        if self._connection_pool:
            await self._connection_pool.close()
            logger.info("AgentStateManager database connections closed")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
