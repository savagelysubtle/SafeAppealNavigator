# src/ai_research_assistant/core/state_manager.py
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

logger = logging.getLogger(__name__)


class AgentStateManager:
    """
    Centralized state management for the agent ecosystem using aiosqlite.
    Handles agent configurations, task history, and metrics.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initializes the state manager."""
        self.db_path = db_path or "tmp/agent_state.db"
        self._connection_pool: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """Initializes the database connection and creates the schema."""
        self._ensure_db_directory()
        if not self._connection_pool:
            self._connection_pool = await aiosqlite.connect(self.db_path)
            self._connection_pool.row_factory = aiosqlite.Row
            await self._create_schema()
            logger.info(f"Initialized AgentStateManager with {self.db_path}")

    def _ensure_db_directory(self) -> None:
        """Ensures the database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    async def _create_schema(self) -> None:
        """Creates the necessary database tables and indexes."""
        if not self._connection_pool:
            raise RuntimeError("Database connection not initialized.")

        schema_sql = """
        CREATE TABLE IF NOT EXISTS agent_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            metric_type TEXT NOT NULL,
            tags TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            agent_id TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON agent_metrics(timestamp);
        """
        await self._connection_pool.executescript(schema_sql)
        await self._connection_pool.commit()

    async def store_metric(self, metric_data: Dict[str, Any]) -> None:
        """Stores an agent metric in the database."""
        if not self._connection_pool:
            raise RuntimeError(
                "Database connection not initialized. Call initialize() first."
            )

        await self._connection_pool.execute(
            """
            INSERT INTO agent_metrics (metric_name, metric_value, metric_type, tags, agent_id)
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
        """Retrieves metrics with optional filtering."""
        if not self._connection_pool:
            raise RuntimeError(
                "Database connection not initialized. Call initialize() first."
            )

        # Handle days_back=0 case - return empty results immediately
        if days_back <= 0:
            return []

        query = "SELECT * FROM agent_metrics WHERE timestamp > ?"
        params: List[Any] = [datetime.now() - timedelta(days=days_back)]

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

    async def close(self) -> None:
        """Closes the database connection."""
        if self._connection_pool:
            await self._connection_pool.close()
            self._connection_pool = None
            # Add a small delay on Windows to ensure file handle is released
            import asyncio
            import platform

            if platform.system() == "Windows":
                await asyncio.sleep(0.01)
            logger.info("database connection closed")
