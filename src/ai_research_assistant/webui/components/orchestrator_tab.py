"""
Legal Research Orchestrator Tab Component

Provides a unified interface for managing and controlling the legal research orchestrator,
which coordinates multiple specialized agents in a streamlined workflow.
"""

import logging
from datetime import datetime

import gradio as gr

logger = logging.getLogger(__name__)


def create_orchestrator_tab(webui_manager):
    """Create the Legal Research Orchestrator tab interface"""

    # Orchestrator state
    current_workflow_id = gr.State(None)
    workflow_status = gr.State({})
    orchestrator_instance = gr.State(None)

    with gr.Column():
        # Header section
        gr.Markdown("""
        ## 🎯 Legal Research Orchestrator

        **Unified Workflow Management for WCAT Cases**

        This orchestrator coordinates multiple specialized agents to provide comprehensive legal analysis:
        - **Intake Agent** → Process and analyze documents with OCR
        - **Manager Agent** → Review and organize findings
        - **Research Agents** → Find similar cases and precedents
        - **Cross-Reference** → Identify relationships and patterns
        - **Optional Chat Interface** → Interactive legal consultation
        """)

        # Status display
        with gr.Row():
            with gr.Column(scale=2):
                workflow_status_display = gr.Markdown(
                    "**Status:** Ready to start new workflow",
                    elem_classes="status-indicator",
                )
            with gr.Column(scale=1):
                workflow_progress = gr.Progress()

        # Configuration section
        with gr.Accordion("⚙️ Orchestrator Configuration", open=True):
            with gr.Row():
                with gr.Column():
                    enable_chat = gr.Checkbox(
                        label="Enable Interactive Chat Interface",
                        value=True,
                        info="Allow interactive consultation during workflow",
                    )
                    auto_proceed = gr.Checkbox(
                        label="Auto-proceed after Intake",
                        value=False,
                        info="Automatically start research after document processing",
                    )
                    require_approval = gr.Checkbox(
                        label="Require Human Approval",
                        value=True,
                        info="Require approval for major workflow transitions",
                    )

                with gr.Column():
                    max_concurrent = gr.Slider(
                        minimum=1,
                        maximum=5,
                        value=3,
                        step=1,
                        label="Max Concurrent Agents",
                        info="Maximum number of agents running simultaneously",
                    )
                    timeout_minutes = gr.Slider(
                        minimum=5,
                        maximum=60,
                        value=30,
                        step=5,
                        label="Timeout (minutes)",
                        info="Maximum time for each workflow stage",
                    )

        # Workflow initiation section
        with gr.Accordion("🚀 Start New Legal Workflow", open=True):
            with gr.Row():
                with gr.Column():
                    client_name = gr.Textbox(
                        label="Client Name",
                        placeholder="Enter client name",
                        info="Name of the client or case reference",
                    )
                    case_type = gr.Dropdown(
                        choices=[
                            "wcat_appeal",
                            "workers_compensation",
                            "injury_claim",
                            "other",
                        ],
                        value="wcat_appeal",
                        label="Case Type",
                        info="Type of legal case",
                    )
                    case_description = gr.Textbox(
                        label="Case Description",
                        placeholder="Brief description of the case...",
                        lines=3,
                        info="Summary of the legal issue",
                    )

                with gr.Column():
                    # Document input options
                    gr.Markdown("### 📄 Document Input Options")

                    # Option 1: Directory path (like intake agent)
                    source_directory = gr.Textbox(
                        label="📂 Source Directory",
                        placeholder="Path to directory containing documents to process...",
                        lines=1,
                        interactive=True,
                        info="Directory containing the documents you want to process (alternative to file upload)",
                    )

                    gr.Markdown("**— OR —**", elem_classes="or-separator")

                    # Option 2: Direct file upload (existing)
                    document_files = gr.File(
                        label="📎 Upload Documents",
                        file_count="multiple",
                        file_types=[
                            ".pdf",
                            ".doc",
                            ".docx",
                            ".txt",
                            ".png",
                            ".jpg",
                            ".jpeg",
                        ],
                    )

                    research_queries = gr.Textbox(
                        label="Research Queries (one per line)",
                        placeholder="Workers compensation back injury\nWCAT appeal precedents\n...",
                        lines=4,
                        info="Specific legal research queries",
                    )

            with gr.Row():
                start_workflow_btn = gr.Button(
                    "🚀 Start Legal Research Workflow", variant="primary", size="lg"
                )
                stop_workflow_btn = gr.Button(
                    "⛔ Stop Workflow", variant="stop", size="lg"
                )

        # Workflow control and monitoring
        with gr.Accordion("📊 Workflow Monitoring & Control", open=True):
            with gr.Tabs():
                # Workflow steps tab
                with gr.TabItem("🔄 Workflow Steps"):
                    workflow_steps_display = gr.JSON(
                        label="Current Workflow State", value={}, container=True
                    )

                    with gr.Row():
                        refresh_status_btn = gr.Button("🔄 Refresh Status")
                        next_step_btn = gr.Button("➡️ Proceed to Next Step")

                # Agent status tab
                with gr.TabItem("🤖 Agent Status"):
                    agent_status_display = gr.JSON(
                        label="Agent Coordinator Status", value={}, container=True
                    )

                    refresh_agents_btn = gr.Button("🔄 Refresh Agent Status")

        # Interactive Chat Reference - Link to dedicated chat tab
        with gr.Accordion("💬 Interactive Chat Reference", open=False):
            gr.Markdown("""
            ### 🚀 Dedicated Chat Interface Available

            For comprehensive legal consultation and document analysis, visit the **💬 Interactive Chat** tab.

            The dedicated chat interface provides:
            - **Document Analysis** - Upload and analyze case documents
            - **Legal Research** - Find precedents and similar cases
            - **Strategy Discussion** - Develop case arguments and approaches
            - **Workflow Assistance** - Get guidance on orchestrator processes

            **🔗 Integration**: The chat system can access and reference all workflow data from this orchestrator
            including processed documents, research findings, and case timeline information.

            **💡 Tip**: Start your workflow here first, then use the Interactive Chat tab for detailed analysis and consultation.
            """)

        # Results section
        with gr.Accordion("📋 Workflow Results", open=False):
            with gr.Tabs():
                # Summary tab
                with gr.TabItem("📄 Executive Summary"):
                    summary_display = gr.Markdown("No workflow results yet.")

                # Detailed results tab
                with gr.TabItem("📊 Detailed Analysis"):
                    detailed_results = gr.JSON(
                        label="Complete Workflow Results", value={}, container=True
                    )

                # Export tab
                with gr.TabItem("💾 Export Results"):
                    with gr.Row():
                        export_format = gr.Dropdown(
                            choices=["JSON", "PDF Report", "Word Document"],
                            value="JSON",
                            label="Export Format",
                        )
                        export_btn = gr.Button("📥 Export Results")

                    export_status = gr.Textbox(label="Export Status", interactive=False)

    # Event handlers
    async def start_workflow(
        client_name_val,
        case_type_val,
        case_description_val,
        source_directory_val,
        documents,
        queries,
        enable_chat_val,
        auto_proceed_val,
        require_approval_val,
        max_concurrent_val,
        timeout_minutes_val,
    ):
        """Start a new legal research workflow"""
        try:
            # Initialize orchestrator if needed
            if orchestrator_instance.value is None:
                from ...agent.orchestrator.legal_orchestrator import (
                    LegalOrchestratorAgent,
                    LegalWorkflowConfig,
                )

                config = LegalWorkflowConfig(
                    enable_chat_interface=enable_chat_val,
                    auto_proceed_after_intake=auto_proceed_val,
                    require_human_approval=require_approval_val,
                    max_concurrent_agents=int(max_concurrent_val),
                    timeout_seconds=int(timeout_minutes_val * 60),
                )

                orchestrator = LegalOrchestratorAgent(
                    orchestrator_config=config,
                    global_settings_manager=webui_manager.global_settings_manager,
                )

                orchestrator_instance.value = orchestrator

            # Prepare workflow parameters
            client_info = {
                "name": client_name_val,
                "case_description": case_description_val,
                "created_at": datetime.now().isoformat(),
            }

            # Handle document input - either from directory or uploaded files
            document_paths = []

            logger.info("📋 Document input options:")
            logger.info(f"  - Source Directory: '{source_directory_val}'")
            logger.info(
                f"  - Uploaded Files: {len(documents) if documents else 0} files"
            )

            # Check if source directory is provided
            if source_directory_val and source_directory_val.strip():
                # Use source directory path
                from pathlib import Path

                logger.info(f"🔍 Using source directory: '{source_directory_val}'")

                source_path = Path(source_directory_val.strip())
                if source_path.exists() and source_path.is_dir():
                    # Get all relevant files from the directory
                    supported_extensions = [
                        ".pdf",
                        ".doc",
                        ".docx",
                        ".txt",
                        ".png",
                        ".jpg",
                        ".jpeg",
                    ]
                    for ext in supported_extensions:
                        document_paths.extend(
                            [str(f) for f in source_path.glob(f"*{ext}")]
                        )
                        document_paths.extend(
                            [str(f) for f in source_path.glob(f"**/*{ext}")]
                        )  # Include subdirectories

                    # Remove duplicates while preserving order
                    document_paths = list(dict.fromkeys(document_paths))

                    logger.info(
                        f"📁 Found {len(document_paths)} documents in directory"
                    )

                    if not document_paths:
                        logger.warning(
                            f"❌ No supported documents found in directory: {source_directory_val}"
                        )
                        return (
                            f"⚠️ **No supported documents found in directory**\n\nDirectory: `{source_directory_val}`\n\nSupported formats: {', '.join(supported_extensions)}",
                            {},
                            gr.update(interactive=True),
                            gr.update(interactive=False),
                        )
                else:
                    logger.error(f"❌ Invalid source directory: {source_directory_val}")
                    return (
                        f"❌ **Invalid source directory**\n\nPath does not exist or is not a directory: `{source_directory_val}`",
                        {},
                        gr.update(interactive=True),
                        gr.update(interactive=False),
                    )
            elif documents:
                # Use uploaded files
                logger.info("📎 Using uploaded files")
                for doc in documents:
                    if hasattr(doc, "name"):
                        document_paths.append(doc.name)
                logger.info(f"📁 Processing {len(document_paths)} uploaded files")
            else:
                # No documents provided
                logger.warning(
                    "❌ No documents provided - neither directory nor uploads"
                )
                return (
                    "⚠️ **No documents provided**\n\nPlease either specify a source directory or upload files.",
                    {},
                    gr.update(interactive=True),
                    gr.update(interactive=False),
                )

            research_queries_list = []
            if queries:
                research_queries_list = [
                    q.strip() for q in queries.split("\n") if q.strip()
                ]

            # Start the workflow
            result = await orchestrator_instance.value.run_task(
                task_type="start_legal_workflow",
                parameters={
                    "client_info": client_info,
                    "case_type": case_type_val,
                    "documents": document_paths,
                    "research_queries": research_queries_list,
                },
            )

            if result.get("success"):
                workflow_id = result.get("workflow_id")
                current_workflow_id.value = workflow_id

                return (
                    f"✅ **Workflow Started Successfully**\n\nWorkflow ID: `{workflow_id}`\n\nNext Step: {result.get('next_step', 'Unknown')}",
                    result.get("context", {}),
                    gr.update(interactive=False),  # Disable start button
                    gr.update(interactive=True),  # Enable stop button
                )
            else:
                return (
                    f"❌ **Failed to start workflow**\n\nError: {result.get('error', 'Unknown error')}",
                    {},
                    gr.update(interactive=True),
                    gr.update(interactive=False),
                )

        except Exception as e:
            logger.error(f"Error starting workflow: {e}")
            return (
                f"❌ **Error starting workflow**\n\n{str(e)}",
                {},
                gr.update(interactive=True),
                gr.update(interactive=False),
            )

    async def stop_workflow():
        """Stop the current workflow"""
        try:
            if orchestrator_instance.value and current_workflow_id.value:
                await orchestrator_instance.value.stop()

                return (
                    "⛔ **Workflow Stopped**\n\nAll agents have been stopped.",
                    {},
                    gr.update(interactive=True),  # Enable start button
                    gr.update(interactive=False),  # Disable stop button
                )
            else:
                return (
                    "⚠️ **No active workflow to stop**",
                    {},
                    gr.update(interactive=True),
                    gr.update(interactive=False),
                )

        except Exception as e:
            logger.error(f"Error stopping workflow: {e}")
            return (
                f"❌ **Error stopping workflow**\n\n{str(e)}",
                {},
                gr.update(interactive=True),
                gr.update(interactive=False),
            )

    async def refresh_workflow_status():
        """Refresh workflow status"""
        try:
            if orchestrator_instance.value and current_workflow_id.value:
                result = await orchestrator_instance.value.run_task(
                    task_type="get_workflow_status",
                    parameters={"workflow_id": current_workflow_id.value},
                )

                if result.get("success"):
                    return result.get("state", {})
                else:
                    return {"error": result.get("error", "Failed to get status")}
            else:
                return {"message": "No active workflow"}

        except Exception as e:
            logger.error(f"Error refreshing status: {e}")
            return {"error": str(e)}

    # Wire up event handlers
    start_workflow_btn.click(
        fn=start_workflow,
        inputs=[
            client_name,
            case_type,
            case_description,
            source_directory,
            document_files,
            research_queries,
            enable_chat,
            auto_proceed,
            require_approval,
            max_concurrent,
            timeout_minutes,
        ],
        outputs=[
            workflow_status_display,
            workflow_steps_display,
            start_workflow_btn,
            stop_workflow_btn,
        ],
    )

    stop_workflow_btn.click(
        fn=stop_workflow,
        outputs=[
            workflow_status_display,
            workflow_steps_display,
            start_workflow_btn,
            stop_workflow_btn,
        ],
    )

    refresh_status_btn.click(
        fn=refresh_workflow_status, outputs=[workflow_steps_display]
    )

    return {
        "workflow_status": workflow_status_display,
        "workflow_steps": workflow_steps_display,
        "agent_status": agent_status_display,
    }
