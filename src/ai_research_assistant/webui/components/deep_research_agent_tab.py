import asyncio
import logging
import os
from typing import Any, AsyncGenerator, Dict, Optional

import gradio as gr
from gradio.components import Component
from langchain_core.language_models.chat_models import BaseChatModel

from src.ai_research_assistant.agent.deep_research.deep_research_agent import (
    DeepResearchAgent,
)
from src.ai_research_assistant.utils import llm_provider
from src.ai_research_assistant.utils.unified_llm_factory import (
    UnifiedLLMFactory,
    create_llm_from_settings,
)
from src.ai_research_assistant.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


async def _initialize_llm(
    provider: Optional[str],
    model_name: Optional[str],
    temperature: float,
    base_url: Optional[str],
    api_key: Optional[str],
    num_ctx: Optional[int] = None,
):
    """Initializes the LLM based on settings. Returns None if provider/model is missing."""
    if not provider or not model_name:
        logger.info("LLM Provider or Model Name not specified, LLM will be None.")
        return None
    try:
        logger.info(
            f"Initializing LLM: Provider={provider}, Model={model_name}, Temp={temperature}"
        )
        # Use your actual LLM provider logic here
        llm = llm_provider.get_llm_model(
            provider=provider,
            model_name=model_name,
            temperature=temperature,
            base_url=base_url or None,
            api_key=api_key or None,
            num_ctx=num_ctx if provider == "ollama" else None,
        )
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}", exc_info=True)
        gr.Warning(
            f"Failed to initialize LLM '{model_name}' for provider '{provider}'. Please check settings. Error: {e}"
        )
        return None


def _read_file_safe(file_path: str) -> Optional[str]:
    """Safely read a file, returning None if it doesn't exist or on error."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None


# --- Deep Research Agent Specific Logic ---


async def run_deep_research(
    webui_manager: WebuiManager, components: Dict[Component, Any]
) -> AsyncGenerator[Dict[Component, Any], None]:
    """Handles initializing and running the DeepResearchAgent."""

    # --- Get Components ---
    research_task_comp = webui_manager.get_component_by_id(
        "deep_research_agent.research_task"
    )
    resume_task_id_comp = webui_manager.get_component_by_id(
        "deep_research_agent.resume_task_id"
    )
    parallel_num_comp = webui_manager.get_component_by_id(
        "deep_research_agent.parallel_num"
    )
    save_dir_comp = webui_manager.get_component_by_id("deep_research_agent.save_dir")
    start_button_comp = webui_manager.get_component_by_id(
        "deep_research_agent.start_button"
    )
    stop_button_comp = webui_manager.get_component_by_id(
        "deep_research_agent.stop_button"
    )
    markdown_display_comp = webui_manager.get_component_by_id(
        "deep_research_agent.markdown_display"
    )
    markdown_download_comp = webui_manager.get_component_by_id(
        "deep_research_agent.markdown_download"
    )
    progress_slider_comp = webui_manager.get_component_by_id(
        "deep_research_agent.progress_slider"
    )
    status_display_comp = webui_manager.get_component_by_id(
        "deep_research_agent.status_display"
    )

    # --- 1. Get Task and Settings ---
    task_topic = components.get(research_task_comp, "").strip()
    task_id_to_resume = components.get(resume_task_id_comp, "").strip() or None
    max_parallel_agents = int(components.get(parallel_num_comp, 1))
    base_save_dir = components.get(save_dir_comp, "./tmp/deep_research")
    mcp_config = webui_manager.mcp_server_config

    if not task_topic:
        gr.Warning("Please enter a research task.")
        yield {start_button_comp: gr.update(interactive=True)}
        return

    # Store base save dir for stop handler
    webui_manager.dr_save_dir = base_save_dir
    os.makedirs(base_save_dir, exist_ok=True)

    # --- 2. Initial UI Update ---
    yield {
        start_button_comp: gr.update(value="⏳ Initializing...", interactive=False),
        stop_button_comp: gr.update(interactive=True),
        research_task_comp: gr.update(interactive=False),
        resume_task_id_comp: gr.update(interactive=False),
        parallel_num_comp: gr.update(interactive=False),
        save_dir_comp: gr.update(interactive=False),
        markdown_display_comp: gr.update(
            value="🔄 **Initializing Deep Research Agent...**\n\nPreparing research environment and LLM connections..."
        ),
        markdown_download_comp: gr.update(value=None, interactive=False),
        progress_slider_comp: gr.update(value=5, visible=True),
        status_display_comp: gr.update(value="🚀 Starting research initialization..."),
    }

    agent_task = None
    running_task_id = None
    plan_file_path = None
    report_file_path = None
    last_plan_content = None
    last_plan_mtime = 0

    try:
        # --- 3. Get LLM and Browser Config from other tabs ---
        # Access settings values via components dict, getting IDs from webui_manager
        def get_setting(tab: str, key: str, default: Any = None):
            comp = webui_manager.id_to_component.get(f"{tab}.{key}")
            return components.get(comp, default) if comp else default

        # LLM Config (from agent_settings tab)
        llm_provider_name = get_setting("agent_settings", "llm_provider")
        llm_model_name = get_setting("agent_settings", "llm_model_name")
        llm_temperature = max(
            get_setting("agent_settings", "llm_temperature", 0.5), 0.5
        )
        llm_base_url = get_setting("agent_settings", "llm_base_url")
        llm_api_key = get_setting("agent_settings", "llm_api_key")
        ollama_num_ctx = get_setting("agent_settings", "ollama_num_ctx")

        # Try global settings first, then fallback to legacy component settings
        llm = _get_llm_from_global_settings(webui_manager, "primary")
        if not llm:
            llm = _get_llm_from_legacy_settings(
                webui_manager,
                components,
                llm_provider_name,
                llm_model_name,
                llm_temperature,
                llm_base_url,
                llm_api_key,
                ollama_num_ctx,
            )
        if not llm:
            raise ValueError("LLM Initialization failed. Please check Agent Settings.")

        # Browser Config (from browser_settings tab)
        browser_config_dict = {
            "headless": get_setting("browser_settings", "headless", False),
            "disable_security": get_setting(
                "browser_settings", "disable_security", False
            ),
            "browser_binary_path": get_setting(
                "browser_settings", "browser_binary_path"
            ),
            "user_data_dir": get_setting("browser_settings", "browser_user_data_dir"),
            "window_width": int(get_setting("browser_settings", "window_w", 1280)),
            "window_height": int(get_setting("browser_settings", "window_h", 1100)),
        }

        yield {
            progress_slider_comp: gr.update(value=15),
            status_display_comp: gr.update(
                value="🧠 LLM initialized, setting up agent..."
            ),
        }

        # --- 4. Initialize or Get Agent ---
        if not webui_manager.dr_agent:
            webui_manager.dr_agent = DeepResearchAgent(
                llm=llm,
                browser_config=browser_config_dict,
                mcp_server_config=mcp_config,
            )
            logger.info("DeepResearchAgent initialized.")

        yield {
            progress_slider_comp: gr.update(value=25),
            status_display_comp: gr.update(
                value="🔬 Agent initialized, starting research..."
            ),
        }

        # --- 5. Start Agent Run ---
        agent_run_coro = webui_manager.dr_agent.run(
            topic=task_topic,
            task_id=task_id_to_resume,
            save_dir=base_save_dir,
            max_parallel_browsers=max_parallel_agents,
        )
        agent_task = asyncio.create_task(agent_run_coro)
        webui_manager.dr_current_task = agent_task

        # Wait briefly for the agent to start and potentially create the task ID/folder
        await asyncio.sleep(1.0)

        # Determine the actual task ID being used (agent sets this)
        running_task_id = webui_manager.dr_agent.current_task_id
        if not running_task_id:
            running_task_id = task_id_to_resume
            if not running_task_id:
                logger.warning("Could not determine running task ID immediately.")
            else:
                logger.info(f"Assuming task ID based on resume ID: {running_task_id}")
        else:
            logger.info(f"Agent started with Task ID: {running_task_id}")

        webui_manager.dr_task_id = running_task_id

        # --- 6. Monitor Progress via research_plan.md ---
        if running_task_id:
            task_specific_dir = os.path.join(base_save_dir, str(running_task_id))
            plan_file_path = os.path.join(task_specific_dir, "research_plan.md")
            report_file_path = os.path.join(task_specific_dir, "report.md")
            logger.info(f"Monitoring plan file: {plan_file_path}")
        else:
            logger.warning("Cannot monitor plan file: Task ID unknown.")
            plan_file_path = None

        last_plan_content = None
        progress_value = 30

        while not agent_task.done():
            update_dict = {}
            update_dict[resume_task_id_comp] = gr.update(value=running_task_id)
            agent_stopped = getattr(webui_manager.dr_agent, "stopped", False)
            if agent_stopped:
                logger.info("Stop signal detected from agent state.")
                break

            # Simulate progress increment
            progress_value = min(progress_value + 1, 85)
            update_dict[progress_slider_comp] = gr.update(value=progress_value)
            update_dict[status_display_comp] = gr.update(
                value=f"🔍 Researching... Progress: {progress_value}% (Task: {running_task_id[:8] if running_task_id else 'Unknown'})"
            )

            # Check and update research plan display
            if plan_file_path:
                try:
                    current_mtime = (
                        os.path.getmtime(plan_file_path)
                        if os.path.exists(plan_file_path)
                        else 0
                    )
                    if current_mtime > last_plan_mtime:
                        logger.info(f"Detected change in {plan_file_path}")
                        plan_content = _read_file_safe(plan_file_path)
                        if last_plan_content is None or (
                            plan_content is not None
                            and plan_content != last_plan_content
                        ):
                            # Add header to plan content
                            display_content = f"# 📋 Research Plan - {running_task_id[:8] if running_task_id else 'Active'}\n\n"
                            display_content += (
                                plan_content
                                if plan_content
                                else "Loading research plan..."
                            )

                            update_dict[markdown_display_comp] = gr.update(
                                value=display_content
                            )
                            last_plan_content = plan_content
                            last_plan_mtime = current_mtime
                        elif plan_content is None:
                            last_plan_mtime = 0
                except Exception as e:
                    logger.warning(
                        f"Error checking/reading plan file {plan_file_path}: {e}"
                    )
                    await asyncio.sleep(2.0)

            # Yield updates if any
            if update_dict:
                yield update_dict

            await asyncio.sleep(1.0)

        # --- 7. Task Finalization ---
        logger.info("Agent task processing finished. Awaiting final result...")
        final_result_dict = await agent_task
        logger.info(
            f"Agent run completed. Result keys: {final_result_dict.keys() if final_result_dict else 'None'}"
        )

        # Try to get task ID from result if not known before
        if not running_task_id and final_result_dict and "task_id" in final_result_dict:
            running_task_id = final_result_dict["task_id"]
            webui_manager.dr_task_id = running_task_id
            task_specific_dir = os.path.join(base_save_dir, str(running_task_id))
            report_file_path = os.path.join(task_specific_dir, "report.md")
            logger.info(f"Task ID confirmed from result: {running_task_id}")

        final_ui_update = {}
        final_ui_update[progress_slider_comp] = gr.update(value=100)
        final_ui_update[status_display_comp] = gr.update(
            value="✅ Research completed successfully!"
        )

        if report_file_path and os.path.exists(report_file_path):
            logger.info(f"Loading final report from: {report_file_path}")
            report_content = _read_file_safe(report_file_path)
            if report_content:
                # Add completion header
                display_content = f"# 📊 Research Report - {running_task_id[:8] if running_task_id else 'Complete'}\n\n"
                display_content += "✅ **Status**: Research completed successfully!\n\n"
                display_content += "---\n\n"
                display_content += report_content

                final_ui_update[markdown_display_comp] = gr.update(
                    value=display_content
                )
                final_ui_update[markdown_download_comp] = gr.update(
                    value=report_file_path, interactive=True, visible=True
                )
            else:
                final_ui_update[markdown_display_comp] = gr.update(
                    value="# ❌ Research Complete\n\n*Error reading final report file.*"
                )
        elif final_result_dict and "report" in final_result_dict:
            logger.info("Using report content directly from agent result.")
            final_ui_update[markdown_display_comp] = gr.update(
                value=final_result_dict["report"]
            )
            final_ui_update[markdown_download_comp] = gr.update(
                value=None, interactive=False
            )
        else:
            logger.warning("Final report file not found and not in result dict.")
            final_ui_update[markdown_display_comp] = gr.update(
                value="# ⚠️ Research Complete\n\n*Final report not found.*"
            )

        yield final_ui_update

    except Exception as e:
        logger.error(f"Error during Deep Research Agent execution: {e}", exc_info=True)
        gr.Error(f"Research failed: {e}")
        yield {
            markdown_display_comp: gr.update(
                value=f"# ❌ Research Failed\n\n**Error:**\n```\n{e}\n```"
            ),
            progress_slider_comp: gr.update(value=0),
            status_display_comp: gr.update(
                value=f"❌ Research failed: {str(e)[:100]}..."
            ),
        }

    finally:
        # --- 8. Final UI Reset ---
        webui_manager.dr_current_task = None
        webui_manager.dr_task_id = None

        yield {
            start_button_comp: gr.update(value="🚀 Start Research", interactive=True),
            stop_button_comp: gr.update(interactive=False),
            research_task_comp: gr.update(interactive=True),
            resume_task_id_comp: gr.update(interactive=True),
            parallel_num_comp: gr.update(interactive=True),
            save_dir_comp: gr.update(interactive=True),
            progress_slider_comp: gr.update(visible=False),
        }


async def stop_deep_research(webui_manager: WebuiManager) -> Dict[Component, Any]:
    """Handles the Stop button click."""
    logger.info("Stop button clicked for Deep Research.")
    agent = webui_manager.dr_agent
    task = webui_manager.dr_current_task
    task_id = webui_manager.dr_task_id
    base_save_dir = webui_manager.dr_save_dir

    stop_button_comp = webui_manager.get_component_by_id(
        "deep_research_agent.stop_button"
    )
    start_button_comp = webui_manager.get_component_by_id(
        "deep_research_agent.start_button"
    )
    markdown_display_comp = webui_manager.get_component_by_id(
        "deep_research_agent.markdown_display"
    )
    markdown_download_comp = webui_manager.get_component_by_id(
        "deep_research_agent.markdown_download"
    )
    status_display_comp = webui_manager.get_component_by_id(
        "deep_research_agent.status_display"
    )

    final_update = {
        stop_button_comp: gr.update(interactive=False, value="⏹️ Stopping..."),
        status_display_comp: gr.update(value="⏹️ Stopping research agent..."),
    }

    if agent and task and not task.done():
        logger.info("Signalling DeepResearchAgent to stop.")
        try:
            await agent.stop()
        except Exception as e:
            logger.error(f"Error calling agent.stop(): {e}")

        # Try to show the final report if available after stopping
        await asyncio.sleep(1.5)
        report_file_path = None
        if task_id and base_save_dir:
            report_file_path = os.path.join(base_save_dir, str(task_id), "report.md")

        if report_file_path and os.path.exists(report_file_path):
            report_content = _read_file_safe(report_file_path)
            if report_content:
                display_content = f"# 📊 Research Report - {task_id[:8] if task_id else 'Unknown'}\n\n"
                display_content += "⏹️ **Status**: Research stopped by user\n\n"
                display_content += "---\n\n"
                display_content += report_content

                final_update[markdown_display_comp] = gr.update(value=display_content)
                final_update[markdown_download_comp] = gr.update(
                    value=report_file_path, interactive=True, visible=True
                )
            else:
                final_update[markdown_display_comp] = gr.update(
                    value="# ⏹️ Research Stopped\n\n*Error reading final report file after stop.*"
                )
        else:
            final_update[markdown_display_comp] = gr.update(
                value="# ⏹️ Research Stopped by User"
            )

        final_update[start_button_comp] = gr.update(interactive=False)

    else:
        logger.warning("Stop clicked but no active research task found.")
        final_update = {
            start_button_comp: gr.update(interactive=True),
            stop_button_comp: gr.update(interactive=False),
            status_display_comp: gr.update(value="ℹ️ No active research task to stop."),
        }

    return final_update


def create_deep_research_agent_tab(webui_manager: WebuiManager):
    """
    Creates an enhanced deep research agent tab with improved UI
    """
    input_components = list(
        webui_manager.get_components()
    )  # Convert to list for Gradio
    tab_components = {}

    with gr.Column():
        # Header
        gr.Markdown(
            "# 🔬 Deep Research Agent\n*AI-powered comprehensive research with autonomous browsing and analysis*"
        )

        with gr.Group():
            gr.Markdown("## 📝 Research Task Configuration")

            # Research task templates
            task_templates = [
                "Give me a detailed travel plan to Switzerland from June 1st to 10th.",
                "Research the latest developments in quantum computing and provide a comprehensive analysis.",
                "Analyze the current state of renewable energy technologies and their market adoption.",
                "Investigate the impact of AI on modern healthcare systems and future implications.",
                "Study the economic effects of remote work on different industries post-2020.",
                "Research sustainable urban planning strategies for smart cities.",
            ]

            with gr.Accordion("💡 Click to see research task templates", open=False):
                template_examples = "\n".join(
                    [f"• {template}" for template in task_templates]
                )
                gr.Markdown(f"**Example Research Tasks:**\n\n{template_examples}")

            research_task = gr.Textbox(
                label="🎯 Research Task",
                lines=6,
                value=task_templates[0],
                interactive=True,
                placeholder="Describe your research task in detail. Be specific about what you want to discover, analyze, or investigate...",
                info="💡 Tip: More detailed prompts lead to better research outcomes",
            )

        with gr.Group():
            gr.Markdown("## ⚙️ Research Settings")

            with gr.Row():
                resume_task_id = gr.Textbox(
                    label="🔄 Resume Task ID",
                    value="",
                    interactive=True,
                    placeholder="Enter task ID to resume previous research...",
                    info="Leave empty to start new research",
                )
                parallel_num = gr.Number(
                    label="🔗 Parallel Agents",
                    value=1,
                    precision=0,
                    interactive=True,
                    minimum=1,
                    maximum=5,
                    info="Number of concurrent research agents (1-5)",
                )
                save_dir = gr.Textbox(
                    label="📁 Research Directory",
                    value="./tmp/deep_research",
                    interactive=True,
                    placeholder="./research_output",
                    info="Directory to save research files",
                )

        # Control buttons
        with gr.Row():
            stop_button = gr.Button(
                "⏹️ Stop Research", variant="stop", scale=2, interactive=False, size="lg"
            )
            start_button = gr.Button(
                "🚀 Start Research", variant="primary", scale=3, size="lg"
            )

        # Enhanced progress and status section
        with gr.Group():
            gr.Markdown("## 📊 Research Progress & Results")

            progress_slider = gr.Slider(
                label="🔄 Research Progress",
                minimum=0,
                maximum=100,
                value=0,
                interactive=False,
                visible=False,
                info="Current research progress",
            )

            status_display = gr.Textbox(
                label="📈 Current Status",
                lines=2,
                interactive=False,
                value="🎯 Ready to start deep research...",
                container=True,
            )

            with gr.Row():
                with gr.Column(scale=4):
                    markdown_display = gr.Markdown(
                        label="📋 Research Report",
                        value="# 🔬 Deep Research Agent\n\n**Welcome to the Deep Research Agent!**\n\nThis tool will help you conduct comprehensive research on any topic using AI-powered browsing and analysis.\n\n## 🚀 Getting Started:\n\n1. **Enter your research task** - Be specific about what you want to research\n2. **Configure settings** - Adjust parallel agents and output directory\n3. **Start research** - The agent will autonomously browse, analyze, and compile results\n4. **Download report** - Get your comprehensive research report\n\n## 💡 Tips for Better Results:\n\n- Use specific, well-defined research questions\n- Include context about what type of analysis you need\n- Specify any particular focus areas or constraints\n\n*Ready when you are!*",
                        container=True,
                        height=500,
                    )

                with gr.Column(scale=1):
                    markdown_download = gr.File(
                        label="📥 Download Report",
                        interactive=False,
                        visible=True,
                        file_count="single",
                    )

    tab_components.update(
        dict(
            research_task=research_task,
            parallel_num=parallel_num,
            save_dir=save_dir,
            start_button=start_button,
            stop_button=stop_button,
            markdown_display=markdown_display,
            markdown_download=markdown_download,
            resume_task_id=resume_task_id,
            progress_slider=progress_slider,
            status_display=status_display,
        )
    )
    webui_manager.add_components("deep_research_agent", tab_components)
    webui_manager.init_deep_research_agent()

    # --- Define Event Handler Wrappers ---
    async def start_wrapper(
        *comps: Any,
    ) -> AsyncGenerator[Dict[Component, Any], None]:
        # Convert gradio inputs to component dict
        components_dict = dict(zip(input_components, comps))
        async for update in run_deep_research(webui_manager, components_dict):
            yield update

    async def stop_wrapper() -> AsyncGenerator[Dict[Component, Any], None]:
        update_dict = await stop_deep_research(webui_manager)
        yield update_dict

    # --- Connect Handlers ---
    start_button.click(
        fn=start_wrapper, inputs=input_components, outputs=list(tab_components.values())
    )

    stop_button.click(
        fn=stop_wrapper, inputs=None, outputs=list(tab_components.values())
    )


def _get_llm_from_global_settings(
    webui_manager: WebuiManager, llm_type: str = "primary"
) -> Optional[BaseChatModel]:
    """Get LLM instance from global settings manager"""
    if (
        not hasattr(webui_manager, "global_settings_manager")
        or not webui_manager.global_settings_manager
    ):
        logger.warning(
            "Global settings manager not available, falling back to legacy method"
        )
        return None

    try:
        llm = create_llm_from_settings(webui_manager.global_settings_manager, llm_type)
        logger.info(f"✅ Successfully created {llm_type} LLM from global settings")
        return llm
    except Exception as e:
        logger.error(f"Failed to create {llm_type} LLM from global settings: {e}")
        return None


def _get_llm_from_legacy_settings(
    webui_manager: WebuiManager,
    components: Dict[Component, Any],
    llm_provider_name: Optional[str],
    llm_model_name: Optional[str],
    llm_temperature: float,
    llm_base_url: Optional[str],
    llm_api_key: Optional[str],
    ollama_num_ctx: Optional[int] = None,
) -> Optional[BaseChatModel]:
    """Fallback method using legacy component-based settings"""
    if not llm_provider_name or not llm_model_name:
        logger.info("LLM Provider or Model Name not specified, LLM will be None.")
        return None

    try:
        factory = UnifiedLLMFactory()
        llm = factory.create_llm_for_research_agent(
            provider=llm_provider_name,
            model_name=llm_model_name,
            temperature=llm_temperature,
        )
        logger.info(
            f"✅ Successfully created LLM from legacy settings: {llm_provider_name}:{llm_model_name}"
        )
        return llm
    except Exception as e:
        logger.error(f"Failed to create LLM from legacy settings: {e}")
        gr.Warning(
            f"Failed to initialize LLM '{llm_model_name}' for provider '{llm_provider_name}'. Error: {e}"
        )
        return None
