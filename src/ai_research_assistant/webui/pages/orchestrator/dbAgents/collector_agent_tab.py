import asyncio
import logging
import os
from typing import Any, AsyncGenerator, Dict

import gradio as gr
from gradio.components import Component

from src.ai_research_assistant.agent.collector.collector_agent import (
    run_parallel_pdf_research_agents,
    stop_pdf_research_agents,
)
from src.ai_research_assistant.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


async def run_collector_agent(
    webui_manager: WebuiManager, components: Dict[Component, Any]
) -> AsyncGenerator[Dict[Component, Any], None]:
    """Handles initializing and running the PDF Research Agent."""

    # --- Get Components ---
    search_queries_comp = webui_manager.get_component_by_id(
        "collector_agent.search_queries"
    )
    sheets_url_comp = webui_manager.get_component_by_id("collector_agent.sheets_url")
    parallel_num_comp = webui_manager.get_component_by_id(
        "collector_agent.parallel_num"
    )
    download_dir_comp = webui_manager.get_component_by_id(
        "collector_agent.download_dir"
    )
    start_button_comp = webui_manager.get_component_by_id(
        "collector_agent.start_button"
    )
    stop_button_comp = webui_manager.get_component_by_id("collector_agent.stop_button")
    status_display_comp = webui_manager.get_component_by_id(
        "collector_agent.status_display"
    )
    results_display_comp = webui_manager.get_component_by_id(
        "collector_agent.results_display"
    )
    progress_bar_comp = webui_manager.get_component_by_id(
        "collector_agent.progress_bar"
    )

    # --- 1. Get Task and Settings ---
    search_queries_text = components.get(search_queries_comp, "").strip()
    sheets_url = components.get(sheets_url_comp, "").strip()
    max_parallel_agents = int(components.get(parallel_num_comp, 2))
    download_dir = components.get(download_dir_comp, "./tmp/collector_downloads")

    if not search_queries_text:
        gr.Warning("Please enter search queries (one per line).")
        yield {start_button_comp: gr.update(interactive=True)}
        return

    if not sheets_url:
        gr.Warning("Please enter a Google Sheets URL.")
        yield {start_button_comp: gr.update(interactive=True)}
        return

    # Parse search queries (one per line)
    search_queries = [q.strip() for q in search_queries_text.split("\n") if q.strip()]

    if not search_queries:
        gr.Warning("No valid search queries found.")
        yield {start_button_comp: gr.update(interactive=True)}
        return

    # Store settings for stop handler
    webui_manager.collector_download_dir = download_dir
    os.makedirs(download_dir, exist_ok=True)

    # --- 2. Initial UI Update ---
    yield {
        start_button_comp: gr.update(value="⏳ Starting...", interactive=False),
        stop_button_comp: gr.update(interactive=True),
        search_queries_comp: gr.update(interactive=False),
        sheets_url_comp: gr.update(interactive=False),
        parallel_num_comp: gr.update(interactive=False),
        download_dir_comp: gr.update(interactive=False),
        status_display_comp: gr.update(value="🔄 Initializing PDF research..."),
        results_display_comp: gr.update(value=""),
        progress_bar_comp: gr.update(value=0, visible=True),
    }

    main_task_id = None

    try:
        # --- 3. Get Browser Config from browser_settings tab ---
        def get_browser_setting(key: str, default: Any = None):
            comp = webui_manager.id_to_component.get(f"browser_settings.{key}")
            return components.get(comp, default) if comp else default

        # Browser Config
        browser_config_dict = {
            "headless": get_browser_setting("headless", False),
            "disable_security": get_browser_setting("disable_security", False),
            "browser_binary_path": get_browser_setting("browser_binary_path"),
            "user_data_dir": get_browser_setting("browser_user_data_dir"),
            "window_width": int(get_browser_setting("window_w", 1280)),
            "window_height": int(get_browser_setting("window_h", 1100)),
        }

        # --- 4. Start Agent Run ---
        status_text = f"🚀 Starting {len(search_queries)} PDF research tasks in parallel (max {max_parallel_agents} at once)..."
        yield {
            status_display_comp: gr.update(value=status_text),
            progress_bar_comp: gr.update(value=10),
        }

        import uuid

        main_task_id = str(uuid.uuid4())
        webui_manager.collector_task_id = main_task_id

        # Run the parallel agents
        agent_run_coro = run_parallel_pdf_research_agents(
            search_queries=search_queries,
            sheets_url=sheets_url,
            browser_config=browser_config_dict,
            max_parallel=max_parallel_agents,
            download_dir=download_dir,
            main_task_id=main_task_id,
        )
        agent_task = asyncio.create_task(agent_run_coro)
        webui_manager.collector_current_task = agent_task

        # --- 5. Monitor Progress ---
        last_status = ""
        progress_step = 0
        while not agent_task.done():
            # Update status and progress periodically
            progress_step = min(progress_step + 5, 90)
            current_status = f"📊 Processing {len(search_queries)} queries... (Task ID: {main_task_id[:8]}) - Step {progress_step // 10}/9"
            if current_status != last_status:
                yield {
                    status_display_comp: gr.update(value=current_status),
                    progress_bar_comp: gr.update(value=progress_step),
                }
                last_status = current_status

            await asyncio.sleep(2.0)  # Check every 2 seconds

        # --- 6. Task Finalization ---
        logger.info("PDF research agent processing finished. Awaiting final result...")
        results = await agent_task
        logger.info(f"PDF research completed. Results count: {len(results)}")

        # Format results for display
        results_text = "# 📊 PDF Research Results\n\n"
        completed_count = 0
        failed_count = 0
        stopped_count = 0

        for i, result in enumerate(results, 1):
            status = result.get("status", "unknown")
            query = result.get("query", f"Query {i}")

            # Status emoji mapping
            status_emoji = {
                "completed": "✅",
                "failed": "❌",
                "stopped": "⏹️",
                "cancelled": "🚫",
            }

            results_text += f"## {status_emoji.get(status, '❓')} {i}. {query}\n"
            results_text += f"**Status:** {status.title()}\n"

            if status == "completed":
                completed_count += 1
                task_results = result.get("results", [])
                results_text += f"**Records found:** {len(task_results)}\n"
                if task_results:
                    results_text += "**Sample Records:**\n"
                    for j, record in enumerate(
                        task_results[:3]
                    ):  # Show first 3 records
                        results_text += (
                            f"- 📄 Record {j + 1}: {record.get('result_url', 'N/A')}\n"
                        )
                    if len(task_results) > 3:
                        results_text += (
                            f"- ... and {len(task_results) - 3} more records\n"
                        )
            elif status == "failed":
                failed_count += 1
                error = result.get("error", "Unknown error")
                results_text += f"**Error:** `{error}`\n"
            elif status == "stopped":
                stopped_count += 1

            results_text += "\n---\n\n"

        # Enhanced Summary
        summary_text = "# 📈 Research Summary\n\n"
        summary_text += "| Metric | Count | Percentage |\n"
        summary_text += "|--------|-------|------------|\n"
        summary_text += f"| 📝 Total Queries | {len(search_queries)} | 100% |\n"
        summary_text += f"| ✅ Completed | {completed_count} | {(completed_count / len(search_queries) * 100):.1f}% |\n"
        summary_text += f"| ❌ Failed | {failed_count} | {(failed_count / len(search_queries) * 100):.1f}% |\n"
        summary_text += f"| ⏹️ Stopped | {stopped_count} | {(stopped_count / len(search_queries) * 100):.1f}% |\n"
        summary_text += f"\n**📁 Download Directory:** `{download_dir}`\n\n"

        if completed_count > 0:
            summary_text += "🎉 **Research completed successfully!** Check the download directory for PDF files.\n\n"
        elif failed_count == len(search_queries):
            summary_text += "⚠️ **All queries failed.** Please check your configuration and try again.\n\n"
        else:
            summary_text += "⚠️ **Partial completion.** Some queries were processed successfully.\n\n"

        final_display = summary_text + results_text

        yield {
            status_display_comp: gr.update(value="✅ PDF research completed!"),
            results_display_comp: gr.update(value=final_display),
            progress_bar_comp: gr.update(value=100),
        }

    except Exception as e:
        logger.error(f"Error during PDF Research Agent execution: {e}", exc_info=True)
        gr.Error(f"PDF research failed: {e}")
        yield {
            status_display_comp: gr.update(value=f"❌ Research failed: {e}"),
            results_display_comp: gr.update(value=f"# ❌ Error\n\n```\n{e}\n```"),
            progress_bar_comp: gr.update(value=0),
        }

    finally:
        # --- 7. Final UI Reset ---
        webui_manager.collector_current_task = None
        webui_manager.collector_task_id = None

        yield {
            start_button_comp: gr.update(value="🚀 Start Research", interactive=True),
            stop_button_comp: gr.update(interactive=False),
            search_queries_comp: gr.update(interactive=True),
            sheets_url_comp: gr.update(interactive=True),
            parallel_num_comp: gr.update(interactive=True),
            download_dir_comp: gr.update(interactive=True),
            progress_bar_comp: gr.update(visible=False),
        }


async def stop_collector_agent(webui_manager: WebuiManager) -> Dict[Component, Any]:
    """Handles the Stop button click."""
    logger.info("Stop button clicked for PDF Research Agent.")
    task = webui_manager.collector_current_task
    task_id = webui_manager.collector_task_id

    stop_button_comp = webui_manager.get_component_by_id("collector_agent.stop_button")
    start_button_comp = webui_manager.get_component_by_id(
        "collector_agent.start_button"
    )
    status_display_comp = webui_manager.get_component_by_id(
        "collector_agent.status_display"
    )

    if task and task_id and not task.done():
        logger.info("Signaling PDF Research Agent to stop.")
        try:
            await stop_pdf_research_agents(task_id)
            return {
                stop_button_comp: gr.update(interactive=False, value="⏹️ Stopping..."),
                status_display_comp: gr.update(
                    value="⏹️ Stopping PDF research agents..."
                ),
            }
        except Exception as e:
            logger.error(f"Error calling stop_pdf_research_agents(): {e}")
            return {
                stop_button_comp: gr.update(interactive=False),
                status_display_comp: gr.update(value=f"❌ Error stopping agents: {e}"),
            }
    else:
        logger.warning("Stop clicked but no active PDF research task found.")
        return {
            start_button_comp: gr.update(interactive=True),
            stop_button_comp: gr.update(interactive=False),
            status_display_comp: gr.update(value="ℹ️ No active task to stop."),
        }


def create_collector_agent_tab(webui_manager: WebuiManager):
    """
    Creates an enhanced PDF research (collector) agent tab with improved UI
    """
    input_components = list(
        webui_manager.get_components()
    )  # Convert to list for Gradio
    tab_components = {}

    with gr.Column():
        # Header with info
        gr.Markdown(
            "# 📚 PDF Research Collector\n*Automated PDF research, download, and data collection to Google Sheets*"
        )

        with gr.Group():
            gr.Markdown("## 🔍 Search Configuration")

            # Enhanced search queries input with examples
            search_queries = gr.Textbox(
                label="Search Queries (one per line)",
                lines=6,
                value="artificial intelligence research papers\nmachine learning datasets\ndeep learning tutorials\nneural network architectures\ncomputer vision algorithms",
                interactive=True,
                placeholder="Enter search queries, one per line...\nExample:\n- machine learning research\n- deep learning papers\n- AI algorithms",
                info="💡 Tip: Use specific, targeted queries for better results",
            )

            # Google Sheets URL with validation info
            sheets_url = gr.Textbox(
                label="📊 Google Sheets URL",
                lines=1,
                value="https://docs.google.com/spreadsheets/d/your-sheet-id/edit",
                interactive=True,
                placeholder="Paste your Google Sheets URL here...",
                info="⚠️ Make sure the sheet is accessible and you have edit permissions",
            )

        with gr.Group():
            gr.Markdown("## ⚙️ Research Settings")
            with gr.Row():
                parallel_num = gr.Number(
                    label="🔄 Max Parallel Agents",
                    value=2,
                    precision=0,
                    interactive=True,
                    minimum=1,
                    maximum=10,
                    info="Number of concurrent research agents (1-10)",
                )
                download_dir = gr.Textbox(
                    label="📁 Download Directory",
                    value="./tmp/collector_downloads",
                    interactive=True,
                    placeholder="./downloads",
                    info="Where to save downloaded PDFs",
                )

        # Control buttons with better styling
        with gr.Row():
            stop_button = gr.Button(
                "⏹️ Stop", variant="stop", scale=2, interactive=False, size="lg"
            )
            start_button = gr.Button(
                "🚀 Start Research", variant="primary", scale=3, size="lg"
            )

        # Enhanced status and progress section
        with gr.Group():
            gr.Markdown("## 📊 Research Progress")

            progress_bar = gr.Slider(
                label="📊 Progress",
                minimum=0,
                maximum=100,
                value=0,
                interactive=False,
                visible=False,
                info="Research progress indicator",
            )

            status_display = gr.Textbox(
                label="🔄 Current Status",
                lines=2,
                interactive=False,
                value="🎯 Ready to start PDF research...",
                container=True,
            )

            results_display = gr.Markdown(
                label="📋 Research Results",
                value="📝 Results will appear here after the research is complete.\n\n💡 **Tips for better results:**\n- Use specific, academic search terms\n- Ensure your Google Sheets URL is correct\n- Start with fewer queries to test the setup",
                container=True,
                height=400,
            )

    tab_components.update(
        dict(
            search_queries=search_queries,
            sheets_url=sheets_url,
            parallel_num=parallel_num,
            download_dir=download_dir,
            start_button=start_button,
            stop_button=stop_button,
            status_display=status_display,
            results_display=results_display,
            progress_bar=progress_bar,
        )
    )
    webui_manager.add_components("collector_agent", tab_components)
    webui_manager.init_collector_agent()

    # --- Define Event Handler Wrappers ---
    async def start_wrapper(
        *comps: Any,
    ) -> AsyncGenerator[Dict[Component, Any], None]:
        # Convert gradio inputs to component dict
        components_dict = dict(zip(input_components, comps))
        async for update in run_collector_agent(webui_manager, components_dict):
            yield update

    async def stop_wrapper() -> AsyncGenerator[Dict[Component, Any], None]:
        update_dict = await stop_collector_agent(webui_manager)
        yield update_dict

    # --- Connect Handlers ---
    start_button.click(
        fn=start_wrapper, inputs=input_components, outputs=list(tab_components.values())
    )

    stop_button.click(
        fn=stop_wrapper, inputs=None, outputs=list(tab_components.values())
    )
