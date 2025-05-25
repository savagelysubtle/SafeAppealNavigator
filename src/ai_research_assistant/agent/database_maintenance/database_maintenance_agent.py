"""
Database Maintenance Agent for AI Research Assistant

This agent handles system-wide database maintenance operations:
- Automated data cleanup and optimization
- Index management and performance monitoring
- Schema management and migrations
- Cross-database analytics and reporting
- Database health monitoring
"""

import logging
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from ..core import AgentTask, BaseAgent

logger = logging.getLogger(__name__)


class DatabaseMaintenanceAgent(BaseAgent):
    """
    Agent responsible for system-wide database maintenance and optimization.

    This agent can work with any SQLite database in the system, including:
    - Legal case databases
    - Agent state databases
    - Search history databases
    - User data databases

    Key Responsibilities:
    - Database optimization (VACUUM, ANALYZE, index management)
    - Data cleanup (expired records, orphaned data)
    - Performance monitoring and reporting
    - Schema migrations and updates
    - Database health checks
    """

    def __init__(self, **kwargs):
        """Initialize the Database Maintenance Agent"""
        super().__init__(**kwargs)

        # Configure agent-specific settings
        self.agent_type = "DatabaseMaintenanceAgent"
        self.description = "System-wide database maintenance and optimization"

        # Database paths to monitor (can be configured)
        self.monitored_databases = [
            "./tmp/legal_research/cases.db",
            "./tmp/agent_history/agent_state.db",
            "./tmp/search_cache.db",
        ]

        # Maintenance schedules
        self.maintenance_intervals = {
            "daily_cleanup": timedelta(days=1),
            "weekly_optimization": timedelta(weeks=1),
            "monthly_analytics": timedelta(days=30),
        }

        self.last_maintenance = {}

    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """Execute database maintenance tasks"""
        try:
            task_type = task.task_type
            params = task.parameters

            if task_type == "optimize_database":
                return await self._optimize_database(
                    params.get("database_path"),
                    params.get("optimization_level", "standard"),
                )
            elif task_type == "cleanup_expired_data":
                return await self._cleanup_expired_data(
                    params.get("database_path"), params.get("retention_days", 30)
                )
            elif task_type == "database_health_check":
                return await self._database_health_check(params.get("database_path"))
            elif task_type == "scheduled_maintenance":
                return await self._run_scheduled_maintenance()
            elif task_type == "database_analytics":
                return await self._generate_database_analytics(
                    params.get("database_path"), params.get("report_type", "summary")
                )
            elif task_type == "migrate_schema":
                database_path = params.get("database_path")
                migration_script = params.get("migration_script")

                if not database_path or not migration_script:
                    return {
                        "success": False,
                        "error": "Both database_path and migration_script are required for schema migration",
                        "task_id": task.id,
                    }

                return await self._migrate_schema(database_path, migration_script)
            else:
                return {
                    "success": False,
                    "error": f"Unknown task type: {task_type}",
                    "task_id": task.id,
                }

        except Exception as e:
            logger.error(f"Database maintenance task failed: {e}")
            return {"success": False, "error": str(e), "task_id": task.id}

    async def _optimize_database(
        self, database_path: Optional[str], optimization_level: str = "standard"
    ) -> Dict[str, Any]:
        """Optimize database performance"""
        if not database_path:
            # Optimize all monitored databases
            results = []
            for db_path in self.monitored_databases:
                if Path(db_path).exists():
                    result = await self._optimize_single_database(
                        db_path, optimization_level
                    )
                    results.append(result)

            return {
                "success": True,
                "optimization_results": results,
                "total_databases": len(results),
                "timestamp": datetime.now().isoformat(),
            }
        else:
            # Optimize specific database
            result = await self._optimize_single_database(
                database_path, optimization_level
            )
            return {
                "success": True,
                "optimization_result": result,
                "timestamp": datetime.now().isoformat(),
            }

    async def _optimize_single_database(
        self, database_path: str, optimization_level: str
    ) -> Dict[str, Any]:
        """Optimize a single database"""
        start_time = time.time()
        db_path = Path(database_path)

        if not db_path.exists():
            return {
                "database_path": database_path,
                "success": False,
                "error": "Database file not found",
            }

        # Get initial database stats
        initial_size = db_path.stat().st_size

        try:
            with sqlite3.connect(database_path) as conn:
                # Update statistics
                conn.execute("ANALYZE")

                if optimization_level in ["aggressive", "full"]:
                    # Full vacuum to reclaim space
                    conn.execute("VACUUM")

                    # Optimize indexes
                    await self._optimize_indexes(conn)

                # Update query planner statistics
                conn.execute("PRAGMA optimize")

                # Get database info
                table_count = conn.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                ).fetchone()[0]

                index_count = conn.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='index'"
                ).fetchone()[0]

                conn.commit()

        except Exception as e:
            return {"database_path": database_path, "success": False, "error": str(e)}

        # Get final stats
        final_size = db_path.stat().st_size
        duration = time.time() - start_time
        space_saved = initial_size - final_size

        return {
            "database_path": database_path,
            "success": True,
            "initial_size_mb": round(initial_size / 1024 / 1024, 2),
            "final_size_mb": round(final_size / 1024 / 1024, 2),
            "space_saved_mb": round(space_saved / 1024 / 1024, 2),
            "optimization_time_seconds": round(duration, 2),
            "table_count": table_count,
            "index_count": index_count,
            "optimization_level": optimization_level,
        }

    async def _optimize_indexes(self, conn: sqlite3.Connection):
        """Optimize database indexes"""
        # Get all indexes
        indexes = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND sql IS NOT NULL
        """).fetchall()

        for (index_name,) in indexes:
            try:
                # Reindex to optimize
                conn.execute(f"REINDEX {index_name}")
            except sqlite3.Error as e:
                logger.warning(f"Could not reindex {index_name}: {e}")

    async def _cleanup_expired_data(
        self, database_path: Optional[str], retention_days: int = 30
    ) -> Dict[str, Any]:
        """Clean up expired data across databases"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        if not database_path:
            # Clean all monitored databases
            results = []
            for db_path in self.monitored_databases:
                if Path(db_path).exists():
                    result = await self._cleanup_single_database(db_path, cutoff_date)
                    results.append(result)

            return {
                "success": True,
                "cleanup_results": results,
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat(),
            }
        else:
            # Clean specific database
            result = await self._cleanup_single_database(database_path, cutoff_date)
            return {
                "success": True,
                "cleanup_result": result,
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat(),
            }

    async def _cleanup_single_database(
        self, database_path: str, cutoff_date: datetime
    ) -> Dict[str, Any]:
        """Clean up expired data from a single database"""
        if not Path(database_path).exists():
            return {
                "database_path": database_path,
                "success": False,
                "error": "Database file not found",
            }

        deleted_records = 0

        try:
            with sqlite3.connect(database_path) as conn:
                # Get all tables
                tables = conn.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """).fetchall()

                # Look for timestamp columns and clean old data
                for (table_name,) in tables:
                    # Check for common timestamp column names
                    timestamp_columns = [
                        "created_at",
                        "timestamp",
                        "date",
                        "updated_at",
                    ]

                    for col_name in timestamp_columns:
                        try:
                            # Check if column exists
                            cursor = conn.execute(f"PRAGMA table_info({table_name})")
                            columns = [row[1] for row in cursor.fetchall()]

                            if col_name in columns:
                                # Delete old records
                                cursor = conn.execute(
                                    f"""
                                    DELETE FROM {table_name}
                                    WHERE {col_name} < ?
                                """,
                                    (cutoff_date.isoformat(),),
                                )

                                deleted_records += cursor.rowcount
                                break

                        except sqlite3.Error:
                            # Column doesn't exist or other error, continue
                            continue

                conn.commit()

        except Exception as e:
            return {"database_path": database_path, "success": False, "error": str(e)}

        return {
            "database_path": database_path,
            "success": True,
            "deleted_records": deleted_records,
        }

    async def _database_health_check(
        self, database_path: Optional[str]
    ) -> Dict[str, Any]:
        """Perform comprehensive database health check"""
        if not database_path:
            # Check all monitored databases
            results = []
            for db_path in self.monitored_databases:
                if Path(db_path).exists():
                    result = await self._check_single_database_health(db_path)
                    results.append(result)

            # Calculate overall health score
            if results:
                avg_health = sum(r.get("health_score", 0) for r in results) / len(
                    results
                )
                overall_status = (
                    "healthy"
                    if avg_health >= 80
                    else "needs_attention"
                    if avg_health >= 60
                    else "critical"
                )
            else:
                avg_health = 0
                overall_status = "no_databases"

            return {
                "success": True,
                "overall_health_score": round(avg_health, 1),
                "overall_status": overall_status,
                "database_health_checks": results,
                "total_databases": len(results),
                "timestamp": datetime.now().isoformat(),
            }
        else:
            # Check specific database
            result = await self._check_single_database_health(database_path)
            return {
                "success": True,
                "health_check": result,
                "timestamp": datetime.now().isoformat(),
            }

    async def _check_single_database_health(self, database_path: str) -> Dict[str, Any]:
        """Check health of a single database"""
        db_path = Path(database_path)

        if not db_path.exists():
            return {
                "database_path": database_path,
                "success": False,
                "error": "Database file not found",
                "health_score": 0,
            }

        health_metrics = {}

        try:
            with sqlite3.connect(database_path) as conn:
                # Database integrity check
                integrity_result = conn.execute("PRAGMA integrity_check").fetchone()[0]
                health_metrics["integrity"] = integrity_result == "ok"

                # Get database statistics
                page_count = conn.execute("PRAGMA page_count").fetchone()[0]
                page_size = conn.execute("PRAGMA page_size").fetchone()[0]
                freelist_count = conn.execute("PRAGMA freelist_count").fetchone()[0]

                health_metrics["size_mb"] = round(
                    (page_count * page_size) / 1024 / 1024, 2
                )
                health_metrics["unused_space_percent"] = round(
                    (freelist_count / max(page_count, 1)) * 100, 1
                )

                # Check for indexes
                index_count = conn.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='index'"
                ).fetchone()[0]
                table_count = conn.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchone()[0]

                health_metrics["index_to_table_ratio"] = round(
                    index_count / max(table_count, 1), 2
                )

                # Performance test - simple query timing
                start_time = time.time()
                conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
                query_time_ms = (time.time() - start_time) * 1000
                health_metrics["query_performance_ms"] = round(query_time_ms, 2)

        except Exception as e:
            return {
                "database_path": database_path,
                "success": False,
                "error": str(e),
                "health_score": 0,
            }

        # Calculate health score (0-100)
        health_score = 100

        # Deduct points for issues
        if not health_metrics["integrity"]:
            health_score -= 50  # Critical issue

        if health_metrics["unused_space_percent"] > 20:
            health_score -= 20  # Needs optimization
        elif health_metrics["unused_space_percent"] > 10:
            health_score -= 10

        if health_metrics["query_performance_ms"] > 100:
            health_score -= 15  # Slow queries
        elif health_metrics["query_performance_ms"] > 50:
            health_score -= 5

        if health_metrics["index_to_table_ratio"] < 0.5:
            health_score -= 10  # Possibly under-indexed

        health_score = max(0, health_score)

        status = (
            "healthy"
            if health_score >= 80
            else "needs_attention"
            if health_score >= 60
            else "critical"
        )

        return {
            "database_path": database_path,
            "success": True,
            "health_score": health_score,
            "status": status,
            "metrics": health_metrics,
        }

    async def _run_scheduled_maintenance(self) -> Dict[str, Any]:
        """Run scheduled maintenance tasks"""
        current_time = datetime.now()
        tasks_performed = []

        # Check if daily cleanup is needed
        if self._should_run_maintenance("daily_cleanup", current_time):
            cleanup_result = await self._cleanup_expired_data(None, 30)
            tasks_performed.append({"task": "daily_cleanup", "result": cleanup_result})
            self.last_maintenance["daily_cleanup"] = current_time

        # Check if weekly optimization is needed
        if self._should_run_maintenance("weekly_optimization", current_time):
            optimization_result = await self._optimize_database(None, "standard")
            tasks_performed.append(
                {"task": "weekly_optimization", "result": optimization_result}
            )
            self.last_maintenance["weekly_optimization"] = current_time

        # Check if monthly analytics is needed
        if self._should_run_maintenance("monthly_analytics", current_time):
            analytics_result = await self._generate_database_analytics(None, "full")
            tasks_performed.append(
                {"task": "monthly_analytics", "result": analytics_result}
            )
            self.last_maintenance["monthly_analytics"] = current_time

        return {
            "success": True,
            "scheduled_maintenance_completed": True,
            "tasks_performed": tasks_performed,
            "timestamp": current_time.isoformat(),
        }

    def _should_run_maintenance(self, task_name: str, current_time: datetime) -> bool:
        """Check if maintenance task should run"""
        if task_name not in self.last_maintenance:
            return True

        last_run = self.last_maintenance[task_name]
        interval = self.maintenance_intervals[task_name]

        return current_time - last_run >= interval

    async def _generate_database_analytics(
        self, database_path: Optional[str], report_type: str = "summary"
    ) -> Dict[str, Any]:
        """Generate database analytics and reports"""
        if not database_path:
            # Generate analytics for all databases
            analytics = []
            for db_path in self.monitored_databases:
                if Path(db_path).exists():
                    db_analytics = await self._analyze_single_database(
                        db_path, report_type
                    )
                    analytics.append(db_analytics)

            return {
                "success": True,
                "analytics_type": report_type,
                "database_analytics": analytics,
                "total_databases": len(analytics),
                "timestamp": datetime.now().isoformat(),
            }
        else:
            # Generate analytics for specific database
            analytics = await self._analyze_single_database(database_path, report_type)
            return {
                "success": True,
                "analytics_type": report_type,
                "database_analytics": analytics,
                "timestamp": datetime.now().isoformat(),
            }

    async def _analyze_single_database(
        self, database_path: str, report_type: str
    ) -> Dict[str, Any]:
        """Analyze a single database"""
        if not Path(database_path).exists():
            return {
                "database_path": database_path,
                "success": False,
                "error": "Database file not found",
            }

        analytics = {"database_path": database_path, "success": True}

        try:
            with sqlite3.connect(database_path) as conn:
                # Basic stats
                tables = conn.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """).fetchall()

                analytics["table_count"] = len(tables)

                # Table statistics
                table_stats = []
                for (table_name,) in tables:
                    try:
                        row_count = conn.execute(
                            f"SELECT COUNT(*) FROM {table_name}"
                        ).fetchone()[0]
                        table_stats.append(
                            {"table_name": table_name, "row_count": row_count}
                        )
                    except sqlite3.Error:
                        continue

                analytics["table_statistics"] = table_stats
                analytics["total_rows"] = sum(t["row_count"] for t in table_stats)

                if report_type == "full":
                    # Additional detailed analytics
                    analytics["index_count"] = conn.execute(
                        "SELECT COUNT(*) FROM sqlite_master WHERE type='index'"
                    ).fetchone()[0]

                    # Database size analysis
                    page_count = conn.execute("PRAGMA page_count").fetchone()[0]
                    page_size = conn.execute("PRAGMA page_size").fetchone()[0]
                    analytics["total_size_mb"] = round(
                        (page_count * page_size) / 1024 / 1024, 2
                    )

        except Exception as e:
            analytics["success"] = False
            analytics["error"] = str(e)

        return analytics

    async def _migrate_schema(
        self, database_path: str, migration_script: str
    ) -> Dict[str, Any]:
        """Execute schema migration"""
        if not Path(database_path).exists():
            return {"success": False, "error": "Database file not found"}

        try:
            with sqlite3.connect(database_path) as conn:
                # Execute migration script
                conn.executescript(migration_script)
                conn.commit()

                return {
                    "success": True,
                    "database_path": database_path,
                    "migration_completed": True,
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            return {"success": False, "error": str(e), "database_path": database_path}

    async def get_database_overview(self) -> Dict[str, Any]:
        """Get overview of all databases managed by this agent"""
        overview = {
            "monitored_databases": len(self.monitored_databases),
            "databases": [],
        }

        for db_path in self.monitored_databases:
            db_info = {"path": db_path, "exists": Path(db_path).exists()}

            if db_info["exists"]:
                db_info["size_mb"] = round(
                    Path(db_path).stat().st_size / 1024 / 1024, 2
                )
                health_check = await self._check_single_database_health(db_path)
                db_info["health_score"] = health_check.get("health_score", 0)
                db_info["status"] = health_check.get("status", "unknown")

            overview["databases"].append(db_info)

        return overview
