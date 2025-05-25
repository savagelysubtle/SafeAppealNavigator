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
                    document_files = gr.File(
                        label="Upload Documents",
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

                # Chat interface tab
                with gr.TabItem("💬 Interactive Chat"):
                    gr.Markdown("**Chat with the Legal Research System**")

                    chat_history = gr.Chatbot(
                        label="Legal Consultation Chat", height=300, show_label=True
                    )

                    with gr.Row():
                        chat_input = gr.Textbox(
                            label="Ask a question about your case",
                            placeholder="What are the key precedents for my case?",
                            scale=4,
                        )
                        chat_send_btn = gr.Button("Send", scale=1)

                # Agent status tab
                with gr.TabItem("🤖 Agent Status"):
                    agent_status_display = gr.JSON(
                        label="Agent Coordinator Status", value={}, container=True
                    )

                    refresh_agents_btn = gr.Button("🔄 Refresh Agent Status")

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

            document_paths = []
            if documents:
                for doc in documents:
                    if hasattr(doc, "name"):
                        document_paths.append(doc.name)

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

    async def send_chat_message(message, history):
        """Send chat message to orchestrator"""
        try:
            if orchestrator_instance.value and current_workflow_id.value:
                result = await orchestrator_instance.value.run_task(
                    task_type="interactive_chat", parameters={"message": message}
                )

                if result.get("success"):
                    response = result.get("response", "No response received")
                    history.append([message, response])
                    return history, ""
                else:
                    error_msg = result.get("error", "Failed to process message")
                    history.append([message, f"❌ Error: {error_msg}"])
                    return history, ""
            else:
                history.append(
                    [message, "❌ No active workflow. Please start a workflow first."]
                )
                return history, ""

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            history.append([message, f"❌ Error: {str(e)}"])
            return history, ""

    # Wire up event handlers
    start_workflow_btn.click(
        fn=start_workflow,
        inputs=[
            client_name,
            case_type,
            case_description,
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

    chat_send_btn.click(
        fn=send_chat_message,
        inputs=[chat_input, chat_history],
        outputs=[chat_history, chat_input],
    )

    chat_input.submit(
        fn=send_chat_message,
        inputs=[chat_input, chat_history],
        outputs=[chat_history, chat_input],
    )

    return {
        "workflow_status": workflow_status_display,
        "workflow_steps": workflow_steps_display,
        "chat_history": chat_history,
        "agent_status": agent_status_display,
    }
