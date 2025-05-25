"""
Database Maintenance Agent WebUI Tab

Provides interface for database maintenance operations including optimization,
cleanup, health monitoring, and performance analytics.
"""

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict

import gradio as gr
from gradio.components import Component

from src.ai_research_assistant.agent.core import AgentTask, TaskPriority
from src.ai_research_assistant.agent.database_maintenance.database_maintenance_agent import (
    DatabaseMaintenanceAgent,
)
from src.ai_research_assistant.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


async def run_maintenance_operation(
    webui_manager: WebuiManager, components: Dict[Component, Any]
) -> AsyncGenerator[Dict[Component, Any], None]:
    """Execute the selected database maintenance operation."""

    # Get UI components
    operation_type_comp = webui_manager.get_component_by_id(
        "database_maintenance_agent.operation_type"
    )
    target_databases_comp = webui_manager.get_component_by_id(
        "database_maintenance_agent.target_databases"
    )
    maintenance_level_comp = webui_manager.get_component_by_id(
        "database_maintenance_agent.maintenance_level"
    )
    cleanup_options_comp = webui_manager.get_component_by_id(
        "database_maintenance_agent.cleanup_options"
    )
    start_button_comp = webui_manager.get_component_by_id(
        "database_maintenance_agent.start_button"
    )
    stop_button_comp = webui_manager.get_component_by_id(
        "database_maintenance_agent.stop_button"
    )
    progress_comp = webui_manager.get_component_by_id(
        "database_maintenance_agent.progress"
    )
    status_comp = webui_manager.get_component_by_id("database_maintenance_agent.status")
    results_comp = webui_manager.get_component_by_id(
        "database_maintenance_agent.results"
    )

    # Get input values
    operation_type = components.get(operation_type_comp, "health_check")
    target_databases = components.get(target_databases_comp, ["legal_database"])
    maintenance_level = components.get(maintenance_level_comp, "standard")
    cleanup_options = components.get(cleanup_options_comp, [])

    # Validation
    if not target_databases:
        gr.Warning("Please select at least one database to maintain.")
        yield {start_button_comp: gr.update(interactive=True)}
        return

    # Initial UI update
    yield {
        start_button_comp: gr.update(
            value="⏳ Starting Maintenance...", interactive=False
        ),
        stop_button_comp: gr.update(interactive=True),
        operation_type_comp: gr.update(interactive=False),
        target_databases_comp: gr.update(interactive=False),
        maintenance_level_comp: gr.update(interactive=False),
        cleanup_options_comp: gr.update(interactive=False),
        progress_comp: gr.update(value=10, visible=True),
        status_comp: gr.update(value="🔧 Initializing database maintenance..."),
        results_comp: gr.update(
            value="**Maintenance Starting...**\n\nInitializing Database Maintenance Agent and preparing maintenance operations..."
        ),
    }

    try:
        # Initialize database maintenance agent
        agent = DatabaseMaintenanceAgent()
        logger.info("Database Maintenance Agent initialized")

        yield {
            progress_comp: gr.update(value=20),
            status_comp: gr.update(
                value="🤖 Agent initialized, starting maintenance operations..."
            ),
        }

        # Create and execute task
        task = AgentTask(
            task_type=operation_type,
            parameters={
                "target_databases": target_databases,
                "maintenance_level": maintenance_level,
                "cleanup_options": cleanup_options,
                "generate_report": True,
            },
            priority=TaskPriority.HIGH,
        )

        # Store task for stop functionality
        webui_manager.dm_current_task = asyncio.create_task(agent.execute_task(task))

        yield {
            progress_comp: gr.update(value=30),
            status_comp: gr.update(value="🔧 Executing maintenance operations..."),
        }

        # Monitor progress
        progress_value = 40
        while not webui_manager.dm_current_task.done():
            # Simulate progress updates based on operation type
            if operation_type == "health_check":
                progress_value = min(progress_value + 15, 90)
            elif operation_type == "optimization":
                progress_value = min(progress_value + 8, 90)
            elif operation_type == "cleanup":
                progress_value = min(progress_value + 10, 90)
            else:
                progress_value = min(progress_value + 5, 90)

            yield {
                progress_comp: gr.update(value=progress_value),
                status_comp: gr.update(
                    value=f"⚙️ Maintaining databases... {progress_value}%"
                ),
            }
            await asyncio.sleep(1.5)

        # Get results
        result = await webui_manager.dm_current_task

        # Format results
        if result.get("success"):
            maintenance_data = result.get("maintenance_results", {})
            health_scores = maintenance_data.get("health_scores", {})
            optimizations = maintenance_data.get("optimizations_performed", [])
            cleanup_results = maintenance_data.get("cleanup_results", {})

            results_text = f"""# 🔧 Database Maintenance Results

## ✅ Maintenance Summary
- **Operation Type**: {operation_type.replace("_", " ").title()}
- **Maintenance Level**: {maintenance_level.title()}
- **Databases Processed**: {", ".join(target_databases)}
- **Completion Time**: {maintenance_data.get("execution_time", "N/A")}

## 🏥 Database Health Scores
"""

            for db_name, score in health_scores.items():
                status_emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
                results_text += f"- **{db_name}**: {status_emoji} {score}/100\n"

            if operation_type in ["optimization", "full_maintenance"]:
                results_text += f"""

## ⚡ Optimizations Performed: {len(optimizations)}
"""
                for i, opt in enumerate(optimizations[:10], 1):  # Show first 10
                    opt_type = opt.get("type", "Unknown")
                    improvement = opt.get("improvement_percent", 0)
                    description = opt.get("description", "No description")

                    results_text += f"""
**{i}. {opt_type.title()}**
- **Performance Improvement**: {improvement:.1f}%
- **Details**: {description}
"""

            if operation_type in ["cleanup", "full_maintenance"]:
                results_text += f"""

## 🧹 Cleanup Results
- **Records Removed**: {cleanup_results.get("records_removed", 0):,}
- **Space Freed**: {cleanup_results.get("space_freed_mb", 0):.1f} MB
- **Orphaned Files Cleaned**: {cleanup_results.get("files_cleaned", 0)}
"""

            # Performance metrics
            performance_metrics = maintenance_data.get("performance_metrics", {})
            if performance_metrics:
                results_text += f"""

## 📊 Performance Metrics
- **Query Response Time**: {performance_metrics.get("avg_query_time_ms", 0):.1f}ms
- **Index Efficiency**: {performance_metrics.get("index_efficiency", 0):.1f}%
- **Storage Utilization**: {performance_metrics.get("storage_utilization", 0):.1f}%
- **Fragmentation Level**: {performance_metrics.get("fragmentation_percent", 0):.1f}%
"""

            # Recommendations
            recommendations = maintenance_data.get("recommendations", [])
            if recommendations:
                results_text += """

## 💡 Maintenance Recommendations
"""
                for i, rec in enumerate(recommendations[:5], 1):
                    priority = rec.get("priority", "medium")
                    priority_emoji = (
                        "🔴"
                        if priority == "high"
                        else "🟡"
                        if priority == "medium"
                        else "🟢"
                    )
                    results_text += f"{i}. {priority_emoji} **{rec.get('title', 'Recommendation')}**\n   {rec.get('description', 'No description')}\n\n"

            results_text += """

## 🚀 Next Steps
1. **Review Health Scores**: Address any databases with scores below 80
2. **Monitor Performance**: Check if optimizations improved query times
3. **Schedule Regular Maintenance**: Set up automated maintenance schedules
4. **Review Recommendations**: Implement high-priority recommendations

## ⏰ Maintenance Schedule Suggestions
- **Daily**: Light cleanup and health checks
- **Weekly**: Index optimization and statistics updates
- **Monthly**: Comprehensive analysis and space reclamation
- **Quarterly**: Full maintenance with deep optimization
"""

        else:
            # Error handling
            error_msg = result.get("error", "Unknown error occurred")
            results_text = f"""# ❌ Maintenance Failed

**Error**: {error_msg}

## 💡 Troubleshooting
- Verify database connections are active
- Check that the agent has sufficient permissions
- Ensure no other maintenance operations are running
- Try a lighter maintenance level if issues persist
- Review database logs for specific error details
"""

        yield {
            progress_comp: gr.update(value=100),
            status_comp: gr.update(value="✅ Database maintenance completed!"),
            results_comp: gr.update(value=results_text),
        }

    except Exception as e:
        logger.error(f"Error during database maintenance: {e}", exc_info=True)
        yield {
            status_comp: gr.update(value=f"❌ Maintenance failed: {str(e)[:100]}..."),
            results_comp: gr.update(
                value=f"# ❌ Error\n\n**Error Details:**\n```\n{e}\n```"
            ),
            progress_comp: gr.update(value=0),
        }

    finally:
        # Reset UI
        webui_manager.dm_current_task = None
        yield {
            start_button_comp: gr.update(
                value="🔧 Start Maintenance", interactive=True
            ),
            stop_button_comp: gr.update(interactive=False),
            operation_type_comp: gr.update(interactive=True),
            target_databases_comp: gr.update(interactive=True),
            maintenance_level_comp: gr.update(interactive=True),
            cleanup_options_comp: gr.update(interactive=True),
            progress_comp: gr.update(visible=False),
        }


async def stop_maintenance_operation(
    webui_manager: WebuiManager,
) -> Dict[Component, Any]:
    """Stop the current maintenance operation."""
    logger.info("Stop button clicked for Database Maintenance Agent.")

    task = webui_manager.dm_current_task
    if task and not task.done():
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=3.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

    webui_manager.dm_current_task = None

    return {
        webui_manager.get_component_by_id(
            "database_maintenance_agent.start_button"
        ): gr.update(value="🔧 Start Maintenance", interactive=True),
        webui_manager.get_component_by_id(
            "database_maintenance_agent.stop_button"
        ): gr.update(interactive=False),
        webui_manager.get_component_by_id(
            "database_maintenance_agent.status"
        ): gr.update(value="⏹️ Maintenance stopped by user"),
    }


def create_database_maintenance_agent_tab(webui_manager: WebuiManager):
    """Create the Database Maintenance Agent tab for system maintenance."""

    input_components = list(webui_manager.get_components())
    tab_components = {}

    with gr.Column():
        # Header
        gr.Markdown(
            """
        # 🔧 Database Maintenance Agent
        *Automated database optimization, cleanup, and health monitoring for optimal system performance*
        """
        )

        with gr.Group():
            gr.Markdown("## 🎯 Maintenance Configuration")

            operation_type = gr.Radio(
                choices=[
                    ("Health Check", "health_check"),
                    ("Database Optimization", "optimization"),
                    ("Data Cleanup", "cleanup"),
                    ("Performance Analysis", "performance_analysis"),
                    ("Full Maintenance", "full_maintenance"),
                ],
                value="health_check",
                label="🔧 Operation Type",
                info="Choose the type of maintenance operation to perform",
                interactive=True,
            )

            target_databases = gr.CheckboxGroup(
                choices=[
                    "legal_database",
                    "case_files_db",
                    "document_index",
                    "search_cache",
                    "user_data",
                    "system_logs",
                    "all_databases",
                ],
                value=["legal_database"],
                label="🗄️ Target Databases",
                info="Select which databases to maintain",
                interactive=True,
            )

        with gr.Group():
            gr.Markdown("## 🎛️ Maintenance Parameters")

            with gr.Row():
                maintenance_level = gr.Radio(
                    choices=[
                        ("Light Maintenance", "light"),
                        ("Standard Maintenance", "standard"),
                        ("Deep Maintenance", "deep"),
                        ("Comprehensive Overhaul", "comprehensive"),
                    ],
                    value="standard",
                    label="🔬 Maintenance Level",
                    info="How thorough should the maintenance be?",
                    interactive=True,
                )

                cleanup_options = gr.CheckboxGroup(
                    choices=[
                        "remove_old_logs",
                        "clean_temp_files",
                        "optimize_indexes",
                        "update_statistics",
                        "defragment_tables",
                        "cleanup_orphaned_records",
                    ],
                    value=["remove_old_logs", "optimize_indexes"],
                    label="🧹 Cleanup Options",
                    info="Select specific cleanup operations",
                    interactive=True,
                )

            with gr.Accordion("💡 Maintenance Guide & Best Practices", open=False):
                gr.Markdown(
                    """
                ## 🔧 Operation Types:

                **Health Check** (Fast, 1-2 minutes)
                - Database connectivity and integrity checks
                - Performance metrics collection
                - Basic health scoring
                - No modifications made to data

                **Database Optimization** (Medium, 5-10 minutes)
                - Index optimization and rebuilding
                - Query plan analysis and improvement
                - Statistics updates for better performance
                - Storage space optimization

                **Data Cleanup** (Medium, 3-8 minutes)
                - Remove old logs and temporary files
                - Clean orphaned records and references
                - Archive old data based on retention policies
                - Free up storage space

                **Performance Analysis** (Medium, 5-15 minutes)
                - Comprehensive performance profiling
                - Query bottleneck identification
                - Resource usage analysis
                - Performance trend reporting

                **Full Maintenance** (Long, 15-30 minutes)
                - All of the above operations combined
                - Deep optimization and comprehensive cleanup
                - Complete system health assessment
                - Detailed recommendations report

                ## 🎯 Maintenance Levels:

                - **Light**: Quick checks and minimal optimizations
                - **Standard**: Balanced approach with moderate optimizations
                - **Deep**: Thorough analysis and comprehensive optimizations
                - **Comprehensive**: Maximum optimization with detailed analysis

                ## ⏰ Recommended Schedule:

                - **Daily**: Light health checks during off-peak hours
                - **Weekly**: Standard maintenance with basic cleanup
                - **Monthly**: Deep maintenance with comprehensive analysis
                - **Quarterly**: Full overhaul with complete optimization

                ## ⚠️ Important Notes:

                - Maintenance may temporarily slow database performance
                - Schedule intensive operations during low-usage periods
                - Always backup databases before comprehensive maintenance
                - Monitor health scores regularly to identify issues early
                """
                )

        # Control buttons
        with gr.Row():
            stop_button = gr.Button(
                "⏹️ Stop Maintenance",
                variant="stop",
                scale=2,
                interactive=False,
                size="lg",
            )
            start_button = gr.Button(
                "🔧 Start Maintenance", variant="primary", scale=3, size="lg"
            )

        # Progress and results section
        with gr.Group():
            gr.Markdown("## 📊 Maintenance Progress & Results")

            progress = gr.Slider(
                label="🔄 Maintenance Progress",
                minimum=0,
                maximum=100,
                value=0,
                interactive=False,
                visible=False,
                info="Current maintenance progress",
            )

            status = gr.Textbox(
                label="📈 Current Status",
                value="🎯 Ready to start database maintenance...",
                lines=2,
                interactive=False,
                container=True,
            )

            results = gr.Markdown(
                label="📋 Maintenance Results",
                value="""# 🔧 Database Maintenance Agent

**Welcome to the Database Maintenance System!**

This tool provides comprehensive database maintenance and optimization capabilities:

## 🔧 Available Operations:

### **1. Health Check**
- Quick system health assessment (1-2 minutes)
- Database connectivity verification
- Performance metrics collection
- Health scoring for all monitored databases
- No data modifications - safe for production use

### **2. Database Optimization**
- Index analysis and optimization
- Query performance improvements
- Statistics updates for better query planning
- Storage optimization and space reclamation
- Recommended for weekly maintenance

### **3. Data Cleanup**
- Remove old logs and temporary files
- Clean orphaned records and broken references
- Archive data based on retention policies
- Free up storage space and improve performance
- Essential for maintaining database health

### **4. Performance Analysis**
- Comprehensive performance profiling
- Query bottleneck identification and analysis
- Resource usage monitoring and reporting
- Performance trend analysis over time
- Detailed recommendations for optimization

### **5. Full Maintenance**
- Complete system maintenance combining all operations
- Deep optimization with comprehensive cleanup
- Detailed health assessment and reporting
- Maximum performance improvements
- Recommended for monthly deep maintenance

## 🗄️ Database Coverage:

- **Legal Database**: Primary legal case and decision storage
- **Case Files DB**: Document and file management system
- **Document Index**: Search and indexing system
- **Search Cache**: Query result caching system
- **User Data**: User preferences and session data
- **System Logs**: Application and error logs
- **All Databases**: Comprehensive system-wide maintenance

## 🚀 Getting Started:

1. **Choose operation type** based on your maintenance needs
2. **Select target databases** you want to maintain
3. **Set maintenance level** appropriate for your system load
4. **Configure cleanup options** for specific maintenance tasks
5. **Start maintenance** and monitor progress

## 💡 Best Practices:

- Run health checks daily to monitor system status
- Schedule heavy maintenance during low-usage periods
- Monitor health scores and address issues promptly
- Keep regular backups before intensive maintenance
- Review recommendations and implement improvements

*Configure your maintenance parameters above and click Start Maintenance!*
""",
                container=True,
                height=500,
            )

    # Store components
    tab_components.update(
        {
            "operation_type": operation_type,
            "target_databases": target_databases,
            "maintenance_level": maintenance_level,
            "cleanup_options": cleanup_options,
            "start_button": start_button,
            "stop_button": stop_button,
            "progress": progress,
            "status": status,
            "results": results,
        }
    )

    webui_manager.add_components("database_maintenance_agent", tab_components)
    webui_manager.init_database_maintenance_agent()

    # Event handlers
    async def start_wrapper(
        *comps: Any,
    ) -> AsyncGenerator[Dict[Component, Any], None]:
        components_dict = dict(zip(input_components, comps))
        async for update in run_maintenance_operation(webui_manager, components_dict):
            yield update

    async def stop_wrapper() -> AsyncGenerator[Dict[Component, Any], None]:
        update_dict = await stop_maintenance_operation(webui_manager)
        yield update_dict

    # Connect handlers
    start_button.click(
        fn=start_wrapper,
        inputs=input_components,
        outputs=list(tab_components.values()),
    )

    stop_button.click(
        fn=stop_wrapper, inputs=None, outputs=list(tab_components.values())
    )
