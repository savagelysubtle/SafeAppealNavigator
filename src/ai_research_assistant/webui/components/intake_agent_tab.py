"""
Intake Agent WebUI Tab

Provides interface for document intake and organization workflows,
including the Enhanced Legal Intake Agent for WCB case processing.
"""

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict

import gradio as gr
from gradio.components import Component

from src.ai_research_assistant.agent.core import AgentTask, TaskPriority
from src.ai_research_assistant.agent.intake.enhanced_legal_intake import (
    EnhancedLegalIntakeAgent,
)
from src.ai_research_assistant.agent.intake.intake_agent import IntakeAgent
from src.ai_research_assistant.utils.path_utils import (
    ensure_directory_exists,
    find_valid_path,
    validate_windows_path,
)
from src.ai_research_assistant.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


async def run_intake_workflow(
    webui_manager: WebuiManager, components: Dict[Component, Any]
) -> AsyncGenerator[Dict[Component, Any], None]:
    """Execute the selected intake workflow."""

    logger.info("🚀 Starting intake workflow execution...")

    # Get UI components with enhanced error handling
    try:
        workflow_type_comp = webui_manager.get_component_by_id(
            "intake_agent.workflow_type"
        )
        source_directory_comp = webui_manager.get_component_by_id(
            "intake_agent.source_directory"
        )
        case_id_comp = webui_manager.get_component_by_id("intake_agent.case_id")
        output_directory_comp = webui_manager.get_component_by_id(
            "intake_agent.output_directory"
        )
        start_button_comp = webui_manager.get_component_by_id(
            "intake_agent.start_button"
        )
        stop_button_comp = webui_manager.get_component_by_id("intake_agent.stop_button")
        progress_comp = webui_manager.get_component_by_id("intake_agent.progress")
        status_comp = webui_manager.get_component_by_id("intake_agent.status")
        results_comp = webui_manager.get_component_by_id("intake_agent.results")

        logger.info("✅ Successfully retrieved all UI components")
    except Exception as e:
        logger.error(f"❌ Failed to retrieve UI components: {e}")
        return

    # Get input values with enhanced logging
    workflow_type = components.get(workflow_type_comp, "basic_intake")
    source_directory = components.get(source_directory_comp, "").strip()
    case_id = components.get(case_id_comp, "").strip()
    output_directory = components.get(output_directory_comp, "./tmp/intake_output")

    logger.info("📋 Workflow inputs received:")
    logger.info(f"  - Workflow Type: {workflow_type}")
    logger.info(f"  - Source Directory: '{source_directory}'")
    logger.info(f"  - Case ID: '{case_id}'")
    logger.info(f"  - Output Directory: '{output_directory}'")

    # Enhanced source directory validation
    if not source_directory:
        logger.warning("❌ Source directory is empty or missing")
        gr.Warning("Please provide a source directory.")
        yield {
            start_button_comp: gr.update(value="🚀 Start Processing", interactive=True),
            status_comp: gr.update(
                value="❌ Missing source directory - please enter a valid path"
            ),
        }
        return

    logger.info(f"🔍 Validating source directory: '{source_directory}'")

    # Try to find a valid path variant (handles F:\WCBCLAIM vs F:\!WCBCLAIM)
    valid_source_path = find_valid_path(source_directory)
    if not valid_source_path:
        # Get detailed error message
        is_valid, error_msg = validate_windows_path(source_directory)
        logger.error(f"❌ Path validation failed: {error_msg}")
        gr.Warning(f"Invalid source directory: {error_msg}")
        yield {
            start_button_comp: gr.update(value="🚀 Start Processing", interactive=True),
            status_comp: gr.update(value=f"❌ Invalid source directory: {error_msg}"),
        }
        return

    # Use the valid path variant
    source_directory = valid_source_path
    logger.info(f"✅ Using valid source path: '{source_directory}'")

    # Ensure output directory exists with enhanced logging
    logger.info(f"🔧 Ensuring output directory exists: '{output_directory}'")
    success, output_path_or_error = ensure_directory_exists(
        output_directory, create_if_missing=True
    )
    if not success:
        logger.error(f"❌ Output directory error: {output_path_or_error}")
        gr.Warning(f"Output directory error: {output_path_or_error}")
        yield {
            start_button_comp: gr.update(value="🚀 Start Processing", interactive=True),
            status_comp: gr.update(
                value=f"❌ Output directory error: {output_path_or_error}"
            ),
        }
        return

    output_directory = output_path_or_error
    logger.info(f"✅ Output directory ready: '{output_directory}'")

    # Initial UI update with enhanced logging
    logger.info("🎯 Updating UI for workflow start...")
    yield {
        start_button_comp: gr.update(value="⏳ Starting...", interactive=False),
        stop_button_comp: gr.update(interactive=True),
        source_directory_comp: gr.update(interactive=False),
        case_id_comp: gr.update(interactive=False),
        output_directory_comp: gr.update(interactive=False),
        workflow_type_comp: gr.update(interactive=False),
        progress_comp: gr.update(value=10, visible=True),
        status_comp: gr.update(value="🚀 Initializing intake workflow..."),
        results_comp: gr.update(
            value="**Workflow Starting...**\n\nInitializing agent and preparing for document processing..."
        ),
    }

    try:
        # Initialize appropriate agent based on workflow type with enhanced logging
        logger.info(f"🤖 Initializing {workflow_type} agent...")

        if workflow_type == "enhanced_legal":
            agent = EnhancedLegalIntakeAgent(
                case_organization_directory=output_directory,
            )
            logger.info("✅ Enhanced Legal Intake Agent initialized successfully")
        else:
            agent = IntakeAgent(
                intake_directory=source_directory,
                processed_directory=output_directory,
            )
            logger.info("✅ Basic Intake Agent initialized successfully")

        yield {
            progress_comp: gr.update(value=20),
            status_comp: gr.update(
                value="🤖 Agent initialized, starting processing..."
            ),
        }

        # Create and execute task with enhanced logging
        logger.info("📝 Creating task for agent execution...")

        if workflow_type == "enhanced_legal":
            task = AgentTask(
                task_type="process_legal_dump",
                parameters={
                    "dump_directory": source_directory,
                    "case_id": case_id or None,
                },
                priority=TaskPriority.HIGH,
            )
            logger.info(
                f"✅ Enhanced legal task created with dump_directory: '{source_directory}'"
            )
        else:
            task = AgentTask(
                task_type="batch_process_documents",
                parameters={
                    "source_directory": source_directory,
                    "case_id": case_id or None,
                },
                priority=TaskPriority.NORMAL,
            )
            logger.info(
                f"✅ Basic intake task created with source_directory: '{source_directory}'"
            )

        # Store task for stop functionality
        logger.info("🚀 Starting agent task execution...")
        webui_manager.intake_current_task = asyncio.create_task(
            agent.execute_task(task)
        )

        yield {
            progress_comp: gr.update(value=30),
            status_comp: gr.update(value="📊 Processing documents..."),
        }

        # Monitor progress with enhanced logging
        progress_value = 40
        iteration_count = 0
        while not webui_manager.intake_current_task.done():
            iteration_count += 1
            # Simulate progress updates
            progress_value = min(progress_value + 5, 90)

            if iteration_count % 10 == 0:  # Log every 10th iteration to avoid spam
                logger.info(
                    f"📊 Processing progress: {progress_value}% (iteration {iteration_count})"
                )

            yield {
                progress_comp: gr.update(value=progress_value),
                status_comp: gr.update(value=f"📄 Processing... {progress_value}%"),
            }
            await asyncio.sleep(2.0)

        # Get results with enhanced logging
        logger.info("🔍 Retrieving task results...")
        result = await webui_manager.intake_current_task
        logger.info(
            f"📊 Task completed. Result keys: {list(result.keys()) if isinstance(result, dict) else 'Non-dict result'}"
        )

        # Format results based on workflow type
        if workflow_type == "enhanced_legal" and result.get("success"):
            logger.info("📋 Formatting enhanced legal results...")
            results_text = f"""# 📊 Enhanced Legal Intake Results

## ✅ Processing Summary
- **Case ID**: {result.get("case_id", "N/A")}
- **Total Files Processed**: {result.get("total_files_processed", 0)}
- **Documents Organized**: {result.get("documents_organized", 0)}
- **Search Points Generated**: {result.get("search_points_generated", 0)}
- **Timeline Events**: {result.get("timeline_events", 0)}

## 📁 Output Structure
**Case Directory**: `{result.get("case_directory", output_directory)}`

The case has been organized into the following structure:
- 📋 **Decisions**: Tribunal/board/appeal decisions
- 📧 **Letters**: Correspondence and notifications
- 🏥 **Medical Reports**: Medical assessments and reports
- 📄 **Case Files**: Main case documentation
- 📝 **Review Files**: Case review documents
- 💼 **Employment Records**: Employment history
- 📝 **Forms**: Application and claim forms
- 💬 **Correspondence**: General correspondence
- ⏱️ **Timeline**: Chronological case events
- 🔍 **Search Points**: Generated research strategies

## 🔍 Search Points Ready
{result.get("search_points_generated", 0)} search points have been generated for the Legal Research Agent.

## 🚀 Next Steps
1. Review organized documents in the case directory
2. Use Legal Research Agent with generated search points
3. Analyze case timeline for key events
4. Prepare legal arguments based on categorized evidence
"""
        else:
            # Basic intake results with enhanced logging
            files_processed = (
                result.get("files_processed", 0) if result.get("success") else 0
            )
            logger.info(
                f"📋 Formatting basic intake results - {files_processed} files processed"
            )
            results_text = f"""# 📊 Basic Intake Results

## ✅ Processing Summary
- **Files Processed**: {files_processed}
- **Output Directory**: `{output_directory}`
- **Case ID**: {case_id or "Auto-generated"}

## 📁 Organization
Documents have been processed and organized in the output directory.

## 🚀 Next Steps
1. Review processed documents
2. Continue with specialized agent workflows as needed
"""

        logger.info("✅ Workflow completed successfully!")
        yield {
            progress_comp: gr.update(value=100),
            status_comp: gr.update(value="✅ Processing completed successfully!"),
            results_comp: gr.update(value=results_text),
        }

    except Exception as e:
        logger.error(f"❌ Error during intake processing: {e}", exc_info=True)
        error_message = f"Processing failed: {str(e)[:100]}..."
        logger.error(f"❌ Full error details: {str(e)}")

        yield {
            status_comp: gr.update(value=f"❌ {error_message}"),
            results_comp: gr.update(
                value=f"""# ❌ Processing Error

**Error Details:**
```
{e}
```

**What to try:**
1. Check that the source directory path is correct and accessible
2. Ensure you have proper permissions to the directories
3. Verify the directory contains the expected documents
4. Check the logs for more detailed error information

**Need help?** Check the status messages above for specific guidance.
"""
            ),
            progress_comp: gr.update(value=0),
        }

    finally:
        # Reset UI with enhanced logging
        logger.info("🔄 Resetting UI components to initial state...")
        webui_manager.intake_current_task = None
        yield {
            start_button_comp: gr.update(value="🚀 Start Processing", interactive=True),
            stop_button_comp: gr.update(interactive=False),
            source_directory_comp: gr.update(interactive=True),
            case_id_comp: gr.update(interactive=True),
            output_directory_comp: gr.update(interactive=True),
            workflow_type_comp: gr.update(interactive=True),
            progress_comp: gr.update(visible=False),
        }
        logger.info("✅ UI reset completed")


async def stop_intake_workflow(webui_manager: WebuiManager) -> Dict[Component, Any]:
    """Stop the current intake workflow."""
    logger.info(
        "⏹️ Stop button clicked for Intake Agent - attempting to cancel current task..."
    )

    task = webui_manager.intake_current_task
    if task and not task.done():
        logger.info("🛑 Cancelling running task...")
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=2.0)
            logger.info("✅ Task cancelled successfully")
        except (asyncio.CancelledError, asyncio.TimeoutError):
            logger.warning("⚠️ Task cancellation timed out or was already cancelled")
    else:
        logger.info("ℹ️ No active task to cancel")

    webui_manager.intake_current_task = None

    return {
        webui_manager.get_component_by_id("intake_agent.start_button"): gr.update(
            value="🚀 Start Processing", interactive=True
        ),
        webui_manager.get_component_by_id("intake_agent.stop_button"): gr.update(
            interactive=False
        ),
        webui_manager.get_component_by_id("intake_agent.status"): gr.update(
            value="⏹️ Processing stopped by user"
        ),
    }


def create_intake_agent_tab(webui_manager: WebuiManager):
    """Create the Intake Agent tab with both basic and enhanced workflows."""

    # Don't get all components - we'll define our own input list
    tab_components = {}

    with gr.Column():
        # Header with workflow selection
        gr.Markdown("""
        # 📥 Document Intake & Organization
        *Automated document processing, organization, and legal case preparation*
        """)

        with gr.Group():
            gr.Markdown("## 🔄 Workflow Selection")

            workflow_type = gr.Radio(
                choices=[
                    ("Basic Document Intake", "basic_intake"),
                    ("Enhanced Legal Intake (WCB)", "enhanced_legal"),
                ],
                value="enhanced_legal",
                label="📋 Intake Workflow Type",
                info="Choose the appropriate workflow for your documents",
                interactive=True,
            )

            with gr.Accordion("💡 Workflow Information", open=False):
                gr.Markdown("""
                **Basic Document Intake:**
                - General document processing and organization
                - File type identification and sorting
                - Metadata extraction
                - Simple directory structure creation

                **Enhanced Legal Intake (WCB):**
                - Specialized WCB/Workers' Compensation case processing
                - Advanced document classification (decisions, letters, medical reports)
                - Legal entity extraction (claim numbers, dates, conditions)
                - Timeline reconstruction
                - Search point generation for Legal Research Agent
                - Comprehensive case organization structure
                """)

        with gr.Group():
            gr.Markdown("## 📁 Source Configuration")

            source_directory = gr.Textbox(
                label="📂 Source Directory",
                placeholder="Path to directory containing documents to process...",
                lines=1,
                interactive=True,
                info="Directory containing the documents you want to process and organize",
            )

            with gr.Row():
                case_id = gr.Textbox(
                    label="🏷️ Case ID (Optional)",
                    placeholder="Enter case identifier...",
                    lines=1,
                    interactive=True,
                    info="Optional: Specify case ID, otherwise auto-generated",
                )
                output_directory = gr.Textbox(
                    label="📁 Output Directory",
                    value="./tmp/intake_output",
                    lines=1,
                    interactive=True,
                    info="Where to save organized documents",
                )

        # Control buttons
        with gr.Row():
            stop_button = gr.Button(
                "⏹️ Stop Processing",
                variant="stop",
                scale=2,
                interactive=False,
                size="lg",
            )
            start_button = gr.Button(
                "🚀 Start Processing", variant="primary", scale=3, size="lg"
            )

        # Progress and results section
        with gr.Group():
            gr.Markdown("## 📊 Processing Status & Results")

            progress = gr.Slider(
                label="📈 Processing Progress",
                minimum=0,
                maximum=100,
                value=0,
                interactive=False,
                visible=False,
                info="Current processing progress",
            )

            status = gr.Textbox(
                label="🔄 Current Status",
                value="🎯 Ready to start document intake...",
                lines=2,
                interactive=False,
                container=True,
            )

            results = gr.Markdown(
                label="📋 Processing Results",
                value="""# 📥 Document Intake Agent

**Welcome to the Document Intake System!**

This tool provides two powerful workflows for document processing:

## 🔄 Available Workflows:

### **1. Basic Document Intake**
- General-purpose document processing
- File organization and metadata extraction
- Suitable for any document collection

### **2. Enhanced Legal Intake (WCB)**
- Specialized for Workers' Compensation Board cases
- Advanced document classification and legal entity extraction
- Timeline reconstruction and search point generation
- Seamless integration with Legal Research Agent

## 🚀 Getting Started:

1. **Select your workflow type** above
2. **Choose source directory** containing your documents
3. **Set output directory** for organized results
4. **Optionally specify case ID** for better organization
5. **Start processing** and monitor progress

*Choose your workflow type and configure the directories to begin!*
""",
                container=True,
                height=400,
            )

    # Store components
    tab_components.update(
        {
            "workflow_type": workflow_type,
            "source_directory": source_directory,
            "case_id": case_id,
            "output_directory": output_directory,
            "start_button": start_button,
            "stop_button": stop_button,
            "progress": progress,
            "status": status,
            "results": results,
        }
    )

    webui_manager.add_components("intake_agent", tab_components)
    webui_manager.init_intake_agent()
    logger.info("✅ Intake agent tab components initialized successfully")

    # Define ONLY the intake tab input components in the correct order
    intake_input_components = [
        workflow_type,  # Index 0
        source_directory,  # Index 1
        case_id,  # Index 2
        output_directory,  # Index 3
    ]

    # Event handlers with enhanced logging and error handling
    async def start_wrapper(*comps: Any) -> AsyncGenerator[Dict[Component, Any], None]:
        """Enhanced wrapper for start button with better error handling and logging."""
        try:
            logger.info("🎯 Start button clicked - preparing to launch workflow...")
            logger.info(f"📊 Received {len(comps)} input components")

            # Debug: Log the actual component values we received
            if len(comps) >= 4:
                try:
                    workflow_val = comps[0] if len(comps) > 0 else "N/A"
                    source_dir_val = comps[1] if len(comps) > 1 else "N/A"
                    case_id_val = comps[2] if len(comps) > 2 else "N/A"
                    output_dir_val = comps[3] if len(comps) > 3 else "N/A"

                    logger.info("🔍 Component values received:")
                    logger.info(f"  - Workflow: '{workflow_val}'")
                    logger.info(f"  - Source Directory: '{source_dir_val}'")
                    logger.info(f"  - Case ID: '{case_id_val}'")
                    logger.info(f"  - Output Directory: '{output_dir_val}'")
                except Exception as e:
                    logger.warning(f"⚠️ Could not preview component values: {e}")

            # Create component mapping using only intake components
            components_dict = dict(zip(intake_input_components, comps))
            logger.info("📋 Component mapping created successfully")

            async for update in run_intake_workflow(webui_manager, components_dict):
                yield update

        except Exception as e:
            logger.error(f"❌ Critical error in start_wrapper: {e}", exc_info=True)
            # Provide fallback error UI update
            try:
                yield {
                    webui_manager.get_component_by_id("intake_agent.status"): gr.update(
                        value=f"❌ System error: {str(e)[:100]}..."
                    ),
                    webui_manager.get_component_by_id(
                        "intake_agent.start_button"
                    ): gr.update(value="🚀 Start Processing", interactive=True),
                }
            except Exception as fallback_error:
                logger.error(
                    f"❌ Even fallback error handling failed: {fallback_error}"
                )

    async def stop_wrapper() -> AsyncGenerator[Dict[Component, Any], None]:
        """Enhanced wrapper for stop button with better error handling and logging."""
        try:
            logger.info("🛑 Stop button clicked - attempting to halt workflow...")
            update_dict = await stop_intake_workflow(webui_manager)
            logger.info("✅ Stop workflow completed successfully")
            yield update_dict
        except Exception as e:
            logger.error(f"❌ Error in stop_wrapper: {e}", exc_info=True)
            # Provide fallback error UI update
            try:
                yield {
                    webui_manager.get_component_by_id("intake_agent.status"): gr.update(
                        value=f"⚠️ Stop error: {str(e)[:100]}..."
                    ),
                    webui_manager.get_component_by_id(
                        "intake_agent.start_button"
                    ): gr.update(value="🚀 Start Processing", interactive=True),
                    webui_manager.get_component_by_id(
                        "intake_agent.stop_button"
                    ): gr.update(interactive=False),
                }
            except Exception as fallback_error:
                logger.error(
                    f"❌ Stop fallback error handling failed: {fallback_error}"
                )

    # Connect handlers with logging - Use only intake input components
    logger.info("🔗 Connecting event handlers...")

    try:
        start_button.click(
            fn=start_wrapper,
            inputs=intake_input_components,  # Use only intake components
            outputs=list(tab_components.values()),
        )
        logger.info("✅ Start button handler connected")

        stop_button.click(
            fn=stop_wrapper, inputs=None, outputs=list(tab_components.values())
        )
        logger.info("✅ Stop button handler connected")

    except Exception as e:
        logger.error(f"❌ Failed to connect event handlers: {e}", exc_info=True)
