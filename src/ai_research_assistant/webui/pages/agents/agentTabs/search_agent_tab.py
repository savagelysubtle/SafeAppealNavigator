"""
Search Agent WebUI Tab

Provides interface for advanced search operations across multiple data sources,
including legal databases, document collections, and web resources.
"""

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict

import gradio as gr
from gradio.components import Component

from src.ai_research_assistant.agent.core import AgentTask, TaskPriority
from src.ai_research_assistant.agent.search.search_agent import SearchAgent
from src.ai_research_assistant.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


async def run_search_operation(
    webui_manager: WebuiManager, components: Dict[Component, Any]
) -> AsyncGenerator[Dict[Component, Any], None]:
    """Execute the selected search operation."""

    # Get UI components
    search_type_comp = webui_manager.get_component_by_id("search_agent.search_type")
    search_query_comp = webui_manager.get_component_by_id("search_agent.search_query")
    search_scope_comp = webui_manager.get_component_by_id("search_agent.search_scope")
    max_results_comp = webui_manager.get_component_by_id("search_agent.max_results")
    start_button_comp = webui_manager.get_component_by_id("search_agent.start_button")
    stop_button_comp = webui_manager.get_component_by_id("search_agent.stop_button")
    progress_comp = webui_manager.get_component_by_id("search_agent.progress")
    status_comp = webui_manager.get_component_by_id("search_agent.status")
    results_comp = webui_manager.get_component_by_id("search_agent.results")

    # Get input values
    search_type = components.get(search_type_comp, "database_search")
    search_query = components.get(search_query_comp, "").strip()
    search_scope = components.get(search_scope_comp, ["legal_database"])
    max_results = int(components.get(max_results_comp, 50))

    # Validation
    if not search_query:
        gr.Warning("Please enter a search query.")
        yield {start_button_comp: gr.update(interactive=True)}
        return

    # Initial UI update
    yield {
        start_button_comp: gr.update(value="⏳ Starting Search...", interactive=False),
        stop_button_comp: gr.update(interactive=True),
        search_query_comp: gr.update(interactive=False),
        search_type_comp: gr.update(interactive=False),
        search_scope_comp: gr.update(interactive=False),
        max_results_comp: gr.update(interactive=False),
        progress_comp: gr.update(value=10, visible=True),
        status_comp: gr.update(value="🔍 Initializing search operation..."),
        results_comp: gr.update(
            value="**Search Starting...**\n\nInitializing search agent and preparing search parameters..."
        ),
    }

    try:
        # Initialize search agent
        agent = SearchAgent()
        logger.info("Search Agent initialized")

        yield {
            progress_comp: gr.update(value=20),
            status_comp: gr.update(value="🤖 Agent initialized, starting search..."),
        }

        # Create and execute task
        task = AgentTask(
            task_type=search_type,
            parameters={
                "query": search_query,
                "search_scope": search_scope,
                "max_results": max_results,
                "include_metadata": True,
            },
            priority=TaskPriority.HIGH,
        )

        # Store task for stop functionality
        webui_manager.search_current_task = asyncio.create_task(
            agent.execute_task(task)
        )

        yield {
            progress_comp: gr.update(value=30),
            status_comp: gr.update(value="🔍 Executing search..."),
        }

        # Monitor progress
        progress_value = 40
        while not webui_manager.search_current_task.done():
            # Simulate progress updates
            progress_value = min(progress_value + 10, 90)
            yield {
                progress_comp: gr.update(value=progress_value),
                status_comp: gr.update(value=f"📊 Searching... {progress_value}%"),
            }
            await asyncio.sleep(1.0)

        # Get results
        result = await webui_manager.search_current_task

        # Format results
        if result.get("success"):
            search_results = result.get("results", [])
            total_found = result.get("total_results", len(search_results))

            results_text = f"""# 🔍 Search Results

## ✅ Search Summary
- **Query**: "{search_query}"
- **Search Type**: {search_type.replace("_", " ").title()}
- **Results Found**: {len(search_results)} of {total_found} total
- **Search Scope**: {", ".join(search_scope)}

## 📊 Results

"""

            for i, search_result in enumerate(search_results[:20], 1):  # Show first 20
                title = search_result.get("title", f"Result {i}")
                url = search_result.get("url", "")
                snippet = search_result.get(
                    "snippet", search_result.get("content", "")
                )[:200]
                score = search_result.get(
                    "relevance_score", search_result.get("score", 0)
                )

                results_text += f"""### {i}. {title}
**Relevance Score**: {score:.2f}
**URL**: {url}
**Snippet**: {snippet}...

---

"""

            if len(search_results) > 20:
                results_text += (
                    f"\n*... and {len(search_results) - 20} more results not shown*\n"
                )

            results_text += """
## 🚀 Next Steps
1. Review the search results above
2. Use Cross Reference Agent to find related documents
3. Export results for further analysis
4. Refine search query if needed
"""
        else:
            # Error handling
            error_msg = result.get("error", "Unknown error occurred")
            results_text = f"""# ❌ Search Failed

**Error**: {error_msg}

## 💡 Suggestions
- Check your search query syntax
- Verify the selected search scope is available
- Try a simpler or more specific query
- Check network connectivity for web searches
"""

        yield {
            progress_comp: gr.update(value=100),
            status_comp: gr.update(value="✅ Search completed!"),
            results_comp: gr.update(value=results_text),
        }

    except Exception as e:
        logger.error(f"Error during search operation: {e}", exc_info=True)
        yield {
            status_comp: gr.update(value=f"❌ Search failed: {str(e)[:100]}..."),
            results_comp: gr.update(
                value=f"# ❌ Error\n\n**Error Details:**\n```\n{e}\n```"
            ),
            progress_comp: gr.update(value=0),
        }

    finally:
        # Reset UI
        webui_manager.search_current_task = None
        yield {
            start_button_comp: gr.update(value="🔍 Start Search", interactive=True),
            stop_button_comp: gr.update(interactive=False),
            search_query_comp: gr.update(interactive=True),
            search_type_comp: gr.update(interactive=True),
            search_scope_comp: gr.update(interactive=True),
            max_results_comp: gr.update(interactive=True),
            progress_comp: gr.update(visible=False),
        }


async def stop_search_operation(webui_manager: WebuiManager) -> Dict[Component, Any]:
    """Stop the current search operation."""
    logger.info("Stop button clicked for Search Agent.")

    task = webui_manager.search_current_task
    if task and not task.done():
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=2.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass

    webui_manager.search_current_task = None

    return {
        webui_manager.get_component_by_id("search_agent.start_button"): gr.update(
            value="🔍 Start Search", interactive=True
        ),
        webui_manager.get_component_by_id("search_agent.stop_button"): gr.update(
            interactive=False
        ),
        webui_manager.get_component_by_id("search_agent.status"): gr.update(
            value="⏹️ Search stopped by user"
        ),
    }


def create_search_agent_tab(webui_manager: WebuiManager):
    """Create the Search Agent tab for advanced search operations."""

    input_components = list(webui_manager.get_components())
    tab_components = {}

    with gr.Column():
        # Header
        gr.Markdown("""
        # 🔍 Advanced Search Agent
        *Intelligent search across legal databases, documents, and web resources*
        """)

        with gr.Group():
            gr.Markdown("## 🎯 Search Configuration")

            search_type = gr.Radio(
                choices=[
                    ("Database Search", "database_search"),
                    ("Document Search", "document_search"),
                    ("Web Search", "web_search"),
                    ("Semantic Search", "semantic_search"),
                    ("Legal Precedent Search", "legal_precedent_search"),
                ],
                value="database_search",
                label="🔍 Search Type",
                info="Choose the type of search operation to perform",
                interactive=True,
            )

            search_query = gr.Textbox(
                label="📝 Search Query",
                placeholder="Enter your search terms, legal concepts, or natural language question...",
                lines=3,
                interactive=True,
                info="Be specific for better results. You can use keywords, phrases, or questions.",
            )

        with gr.Group():
            gr.Markdown("## 🎛️ Search Parameters")

            with gr.Row():
                search_scope = gr.CheckboxGroup(
                    choices=[
                        "legal_database",
                        "case_files",
                        "medical_reports",
                        "employment_records",
                        "web_resources",
                        "document_archives",
                    ],
                    value=["legal_database"],
                    label="📂 Search Scope",
                    info="Select which data sources to search",
                    interactive=True,
                )

                max_results = gr.Number(
                    label="📊 Max Results",
                    value=50,
                    minimum=5,
                    maximum=500,
                    precision=0,
                    interactive=True,
                    info="Maximum number of results to return",
                )

            with gr.Accordion("💡 Search Tips & Examples", open=False):
                gr.Markdown("""
                **Database Search Examples:**
                - "chronic pain workplace injury"
                - "WCB decision appeal process"
                - "medical evidence requirements"

                **Legal Precedent Search Examples:**
                - "similar case: back injury office worker"
                - "precedent: repetitive strain injury"
                - "comparable decision: denied claim appeal"

                **Semantic Search Examples:**
                - "What are the requirements for proving work-related injury?"
                - "How to appeal a WCB decision?"
                - "Medical evidence needed for chronic pain claims"

                **Tips for Better Results:**
                - Use specific medical terminology when applicable
                - Include relevant case details (injury type, workplace, etc.)
                - Try different phrasings if initial results aren't relevant
                - Use quotation marks for exact phrase matching
                """)

        # Control buttons
        with gr.Row():
            stop_button = gr.Button(
                "⏹️ Stop Search", variant="stop", scale=2, interactive=False, size="lg"
            )
            start_button = gr.Button(
                "🔍 Start Search", variant="primary", scale=3, size="lg"
            )

        # Progress and results section
        with gr.Group():
            gr.Markdown("## 📊 Search Progress & Results")

            progress = gr.Slider(
                label="🔄 Search Progress",
                minimum=0,
                maximum=100,
                value=0,
                interactive=False,
                visible=False,
                info="Current search progress",
            )

            status = gr.Textbox(
                label="📈 Current Status",
                value="🎯 Ready to start search operation...",
                lines=2,
                interactive=False,
                container=True,
            )

            results = gr.Markdown(
                label="📋 Search Results",
                value="""# 🔍 Advanced Search Agent

**Welcome to the Advanced Search System!**

This tool provides comprehensive search capabilities across multiple data sources:

## 🔍 Available Search Types:

### **1. Database Search**
- Search through structured legal databases
- Fast, indexed searches with relevance scoring
- Perfect for finding specific cases or precedents

### **2. Document Search**
- Full-text search through document collections
- Searches through PDFs, Word docs, and text files
- Ideal for finding specific information in large document sets

### **3. Web Search**
- Search across web resources and online databases
- Access to up-to-date legal information and precedents
- Useful for research and current legal developments

### **4. Semantic Search**
- AI-powered search that understands meaning and context
- Natural language queries supported
- Great for exploratory research and finding related concepts

### **5. Legal Precedent Search**
- Specialized search for legal precedents and similar cases
- Finds cases with similar facts, outcomes, or legal principles
- Essential for legal argument preparation

## 🚀 Getting Started:

1. **Choose your search type** based on what you're looking for
2. **Enter your search query** - be as specific as possible
3. **Select search scope** - choose which data sources to include
4. **Set max results** - control how many results to return
5. **Start search** and review the results

*Configure your search parameters above and click Start Search!*
""",
                container=True,
                height=500,
            )

    # Store components
    tab_components.update(
        {
            "search_type": search_type,
            "search_query": search_query,
            "search_scope": search_scope,
            "max_results": max_results,
            "start_button": start_button,
            "stop_button": stop_button,
            "progress": progress,
            "status": status,
            "results": results,
        }
    )

    webui_manager.add_components("search_agent", tab_components)
    webui_manager.init_search_agent()

    # Event handlers
    async def start_wrapper(*comps: Any) -> AsyncGenerator[Dict[Component, Any], None]:
        components_dict = dict(zip(input_components, comps))
        async for update in run_search_operation(webui_manager, components_dict):
            yield update

    async def stop_wrapper() -> AsyncGenerator[Dict[Component, Any], None]:
        update_dict = await stop_search_operation(webui_manager)
        yield update_dict

    # Connect handlers
    start_button.click(
        fn=start_wrapper, inputs=input_components, outputs=list(tab_components.values())
    )

    stop_button.click(
        fn=stop_wrapper, inputs=None, outputs=list(tab_components.values())
    )
