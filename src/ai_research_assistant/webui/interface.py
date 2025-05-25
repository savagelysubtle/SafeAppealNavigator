"""
Main WebUI Interface for AI Research Assistant

Updated to include unified global settings panel that consolidates
all LLM configurations previously scattered across multiple tabs.
"""

import gradio as gr
import gradio.themes as themes

from .components.agent_settings_tab import create_agent_settings_tab
from .components.browser_launch_tab import create_browser_launch_tab
from .components.browser_settings_tab import create_browser_settings_tab
from .components.browser_use_agent_tab import create_browser_use_agent_tab
from .components.collector_agent_tab import create_collector_agent_tab
from .components.cross_reference_agent_tab import create_cross_reference_agent_tab
from .components.database_maintenance_agent_tab import (
    create_database_maintenance_agent_tab,
)
from .components.deep_research_agent_tab import create_deep_research_agent_tab
from .components.global_settings_panel import create_global_settings_panel
from .components.intake_agent_tab import create_intake_agent_tab
from .components.legal_research_tab import create_legal_research_tab
from .components.load_save_config_tab import create_load_save_config_tab
from .components.mcp_server_tab import create_mcp_server_tab
from .components.orchestrator_tab import create_orchestrator_tab
from .components.search_agent_tab import create_search_agent_tab
from .webui_manager import WebuiManager

theme_map = {
    "Default": themes.Default(),
    "Soft": themes.Soft(),
    "Monochrome": themes.Monochrome(),
    "Glass": themes.Glass(),
    "Origin": themes.Origin(),
    "Citrus": themes.Citrus(),
    "Ocean": themes.Ocean(),
    "Base": themes.Base(),
}


def create_ui(theme_name="Ocean"):
    """
    Create the main WebUI interface with unified global settings.

    The interface now features:
    1. Global Settings Panel (collapsible) - at the top for easy access
    2. All agent tabs below - simplified without duplicate LLM settings
    """
    # Initialize WebUI Manager
    webui_manager = WebuiManager()

    # Create the main interface
    with gr.Blocks(
        theme=theme_name,
        title="🧠 AI Research Assistant - Unified Settings",
        css="""
        .global-settings-panel {
            border: 2px solid #4a90e2;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        .agent-tabs {
            margin-top: 10px;
        }
        .status-indicator {
            font-weight: bold;
            padding: 8px;
            border-radius: 4px;
        }
        .status-success {
            background-color: #d4edda;
            color: #155724;
        }
        .status-warning {
            background-color: #fff3cd;
            color: #856404;
        }
        .status-error {
            background-color: #f8d7da;
            color: #721c24;
        }
        """,
    ) as demo:
        # Header
        gr.Markdown("""
        # 🧠 AI Research Assistant
        ### Advanced WC-AT case research with AI-powered analysis and document generation

        **🎯 NEW: Legal Research Orchestrator** - Unified workflow management for complete case processing
        **🌟 Phase 4 Complete:** All specialized agents now available - Intake, Search, Cross Reference, and Database Maintenance
        **🌟 Unified Settings:** All LLM and system configurations are managed in the Global Settings panel below.
        """)

        # Global Settings Panel (always visible at top)
        with gr.Group(elem_classes="global-settings-panel"):
            gr.Markdown("## 🌐 Unified Configuration Center")
            global_settings_components, settings_manager = create_global_settings_panel(
                webui_manager
            )

        # Agent Tabs (simplified without duplicate settings)
        with gr.Tabs(elem_classes="agent-tabs") as main_tabs:
            # Legal Research Orchestrator - PRIMARY WORKFLOW MANAGER
            with gr.TabItem("🎯 Legal Orchestrator"):
                gr.Markdown("""
                **🌟 UNIFIED LEGAL WORKFLOW MANAGER**
                *Complete case management from intake → research → analysis*
                """)
                create_orchestrator_tab(webui_manager)

            # Browser Use Agent Tab
            with gr.TabItem("🌐 Browser Agent"):
                gr.Markdown("""
                **Browser automation with AI guidance**
                *LLM settings managed in Global Settings panel above*
                """)
                create_browser_use_agent_tab(webui_manager)

            # Deep Research Agent Tab
            with gr.TabItem("🔍 Deep Research"):
                gr.Markdown("""
                **Comprehensive research with parallel processing**
                *LLM settings managed in Global Settings panel above*
                """)
                create_deep_research_agent_tab(webui_manager)

            # Legal Research Tab
            with gr.TabItem("⚖️ Legal Research"):
                gr.Markdown("""
                **WC-AT case research and legal analysis**
                *LLM settings managed in Global Settings panel above*
                """)
                create_legal_research_tab(webui_manager)

            # Collector Agent Tab
            with gr.TabItem("📊 Data Collector"):
                gr.Markdown("""
                **Automated data collection and organization**
                *LLM settings managed in Global Settings panel above*
                """)
                create_collector_agent_tab(webui_manager)

            # Phase 4 Agents - New Specialized Workflow Agents
            with gr.TabItem("📥 Intake Agent"):
                gr.Markdown("""
                **Document intake and organization workflows**
                *Enhanced Legal Intake for WCB case processing*
                """)
                create_intake_agent_tab(webui_manager)

            with gr.TabItem("🔍 Search Agent"):
                gr.Markdown("""
                **Advanced search across multiple data sources**
                *Semantic search and legal precedent discovery*
                """)
                create_search_agent_tab(webui_manager)

            with gr.TabItem("🔗 Cross Reference"):
                gr.Markdown("""
                **Intelligent cross-referencing and relationship analysis**
                *Document correlation and case relationship mapping*
                """)
                create_cross_reference_agent_tab(webui_manager)

            with gr.TabItem("🔧 Database Maintenance"):
                gr.Markdown("""
                **System optimization and database health monitoring**
                *Automated maintenance and performance analytics*
                """)
                create_database_maintenance_agent_tab(webui_manager)

            # Configuration Management
            with gr.TabItem("⚙️ Config Management"):
                gr.Markdown("""
                **Load, save, and manage configurations**
                *Works with Global Settings above*
                """)
                create_load_save_config_tab(webui_manager)

            # Advanced Settings (kept for specialized configs)
            with gr.TabItem("🔧 Advanced Settings"):
                with gr.Accordion("Legacy Agent Settings", open=False):
                    gr.Markdown(
                        "⚠️ **Deprecated:** Use Global Settings panel above instead"
                    )
                    create_agent_settings_tab(webui_manager)

                with gr.Accordion("Browser Settings", open=True):
                    create_browser_settings_tab(webui_manager)

                with gr.Accordion("MCP Server Settings", open=False):
                    create_mcp_server_tab(webui_manager)

            # System Tools
            with gr.TabItem("🚀 System Tools"):
                gr.Markdown("""
                **System utilities and browser management**
                """)
                create_browser_launch_tab(webui_manager)

        # Status Footer
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("""
                **💡 Tips:**
                - **🎯 START HERE:** Use Legal Orchestrator tab for complete case workflows
                - Configure all LLM settings in the Global Settings panel above
                - Settings automatically sync to all agents
                - Use Config Management tab to save/load your preferred setups
                - **Phase 4 Agents:** Use Intake → Search → Cross Reference → Database Maintenance for complete workflows
                - Enhanced Legal Intake automates WCB case file organization and analysis
                """)

            with gr.Column(scale=1):
                global_status = gr.Textbox(
                    label="🌐 Global Status",
                    value="✅ Unified settings system active",
                    interactive=False,
                    elem_classes="status-indicator status-success",
                )

        # Store global status component for updates
        webui_manager.add_components("global_status", {"status": global_status})

    return demo
