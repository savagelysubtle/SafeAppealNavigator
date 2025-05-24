import gradio as gr
import gradio.themes as themes

from src.browser_use_web_ui.webui.components.agent_settings_tab import (
    create_agent_settings_tab,
)
from src.browser_use_web_ui.webui.components.browser_launch_tab import (
    create_browser_launch_tab,
)
from src.browser_use_web_ui.webui.components.browser_settings_tab import (
    create_browser_settings_tab,
)
from src.browser_use_web_ui.webui.components.browser_use_agent_tab import (
    create_browser_use_agent_tab,
)
from src.browser_use_web_ui.webui.components.collector_agent_tab import (
    create_collector_agent_tab,
)
from src.browser_use_web_ui.webui.components.deep_research_agent_tab import (
    create_deep_research_agent_tab,
)
from src.browser_use_web_ui.webui.components.legal_research_tab import (
    create_legal_research_tab,
)
from src.browser_use_web_ui.webui.components.load_save_config_tab import (
    create_load_save_config_tab,
)
from src.browser_use_web_ui.webui.components.mcp_server_tab import (
    create_mcp_server_tab,
)
from src.browser_use_web_ui.webui.webui_manager import WebuiManager

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
    css = """
    .gradio-container {
        width: 70vw !important;
        max-width: 70% !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: 10px !important;
    }
    .header-text {
        text-align: center;
        margin-bottom: 20px;
    }
    .tab-header-text {
        text-align: center;
    }
    .theme-section {
        margin-bottom: 10px;
        padding: 15px;
        border-radius: 10px;
    }
    """

    # dark mode in default
    js_func = """
    function refresh() {
        const url = new URL(window.location);

        if (url.searchParams.get('__theme') !== 'dark') {
            url.searchParams.set('__theme', 'dark');
            window.location.href = url.href;
        }
    }
    """

    ui_manager = WebuiManager()

    with gr.Blocks(
        title="Browser Use WebUI",
        theme=theme_map[theme_name],
        css=css,
        js=js_func,
    ) as demo:
        with gr.Row():
            gr.Markdown(
                """
                # 🌐 Browser Use WebUI
                ### Control your browser with AI assistance
                """,
                elem_classes=["header-text"],
            )

        with gr.Tabs():
            with gr.TabItem("⚙️ Agent Settings"):
                create_agent_settings_tab(ui_manager)

            with gr.TabItem("🌐 Browser Settings"):
                create_browser_settings_tab(ui_manager)

            with gr.TabItem("🧪 Browser Launch"):
                create_browser_launch_tab(ui_manager)

            with gr.TabItem("🤖 Run Agent"):
                create_browser_use_agent_tab(ui_manager)

            with gr.TabItem("🗄️ MCP Server"):
                create_mcp_server_tab(ui_manager)

            with gr.TabItem("🔍 Deep Research"):
                create_deep_research_agent_tab(ui_manager)

            with gr.TabItem("⚖️ Legal Research"):
                create_legal_research_tab(ui_manager)

            with gr.TabItem("📊 PDF Collector"):
                create_collector_agent_tab(ui_manager)

            with gr.TabItem("📁 Load & Save Config"):
                create_load_save_config_tab(ui_manager)

    return demo
