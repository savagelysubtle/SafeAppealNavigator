import json
import logging
import os
from typing import Optional

import gradio as gr

from src.browser_use_web_ui.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


def validate_mcp_config(config_text: str) -> tuple[bool, str, Optional[dict]]:
    """Validate MCP configuration JSON and return status, message, and parsed config."""
    if not config_text.strip():
        return False, "⚠️ Configuration is empty", None

    try:
        mcp_config = json.loads(config_text)

        # Basic validation of MCP structure
        if not isinstance(mcp_config, dict):
            return False, "❌ Configuration must be a JSON object", None

        # Check for required sections (this is a basic check - adjust based on your MCP requirements)
        if "mcpServers" in mcp_config:
            servers = mcp_config["mcpServers"]
            if not isinstance(servers, dict):
                return False, "❌ mcpServers must be an object", None

            server_count = len(servers)
            return (
                True,
                f"✅ Valid MCP configuration with {server_count} server(s)",
                mcp_config,
            )
        else:
            # Assume it's a valid config even without mcpServers section
            return True, "✅ Valid JSON configuration", mcp_config

    except json.JSONDecodeError as e:
        return False, f"❌ Invalid JSON: {str(e)}", None
    except Exception as e:
        return False, f"❌ Validation error: {str(e)}", None


def create_mcp_server_tab(webui_manager: WebuiManager):
    """
    Creates an enhanced MCP Server tab with better UI and validation features.
    """
    with gr.Column():
        # Header
        gr.Markdown(
            "# 🔌 MCP Server Configuration\n*Model Context Protocol server setup and management*"
        )

        with gr.Group():
            gr.Markdown("## 📁 Configuration File Upload")

            with gr.Row():
                mcp_json_file = gr.File(
                    label="Upload MCP Server JSON",
                    interactive=True,
                    file_types=[".json"],
                    file_count="single",
                )

                with gr.Column():
                    config_status = gr.Textbox(
                        label="📊 Configuration Status",
                        value="📝 No configuration loaded",
                        interactive=False,
                        lines=2,
                        container=True,
                    )

        with gr.Group():
            gr.Markdown("## ✏️ Manual Configuration Editor")

            # Example configuration for reference
            example_config = {
                "mcpServers": {
                    "filesystem": {
                        "command": "npx",
                        "args": [
                            "-y",
                            "@modelcontextprotocol/server-filesystem",
                            "/path/to/allowed/files",
                        ],
                        "env": {},
                    },
                    "brave-search": {
                        "command": "npx",
                        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                        "env": {"BRAVE_API_KEY": "your-api-key-here"},
                    },
                }
            }

            gr.Markdown("### 📝 Configuration Template")
            with gr.Accordion("💡 Click to see example configuration", open=False):
                gr.Code(
                    value=json.dumps(example_config, indent=2),
                    language="json",
                    label="Example MCP Configuration",
                    interactive=False,
                )

            mcp_server_config = gr.Textbox(
                label="MCP Server Configuration (JSON)",
                lines=12,
                interactive=True,
                visible=True,
                placeholder="Paste your MCP configuration JSON here or upload a file above...",
                info="💡 Edit the JSON configuration directly here. Changes are validated in real-time.",
                container=True,
            )

            with gr.Row():
                validate_button = gr.Button(
                    "🔍 Validate Configuration", variant="secondary", scale=2
                )
                clear_button = gr.Button("🗑️ Clear", variant="secondary", scale=1)
                save_button = gr.Button("💾 Save & Apply", variant="primary", scale=2)

        with gr.Group():
            gr.Markdown("## 📊 Server Information")

            server_info = gr.Markdown(
                value="🔍 **Server Status:** Not configured\n\n📋 **Available Servers:** None",
                container=True,
            )

    def handle_mcp_file_upload(mcp_file):
        """Handle MCP server JSON file upload with enhanced validation."""
        if not mcp_file or not os.path.exists(mcp_file):
            return (
                None,
                gr.update(visible=True),
                gr.update(value="❌ No file uploaded or file not found"),
                gr.update(value="🔍 **Server Status:** File upload failed"),
            )

        if not mcp_file.endswith(".json"):
            return (
                None,
                gr.update(visible=True),
                gr.update(value="❌ Please upload a JSON file"),
                gr.update(value="🔍 **Server Status:** Invalid file type"),
            )

        try:
            with open(mcp_file, "r", encoding="utf-8") as f:
                config_text = f.read()

            is_valid, message, mcp_server = validate_mcp_config(config_text)

            if is_valid and mcp_server:
                # Store in shared state
                webui_manager.mcp_server_config = mcp_server

                # Generate server info
                server_info_text = (
                    "🔍 **Server Status:** Configuration loaded from file\n\n"
                )
                if "mcpServers" in mcp_server:
                    servers = mcp_server["mcpServers"]
                    server_info_text += f"📋 **Available Servers:** {len(servers)}\n\n"
                    for name, config in servers.items():
                        command = config.get("command", "Unknown")
                        server_info_text += f"- **{name}**: `{command}`\n"
                else:
                    server_info_text += (
                        "📋 **Available Servers:** Custom configuration\n"
                    )

                return (
                    config_text,
                    gr.update(visible=True),
                    gr.update(value=message),
                    gr.update(value=server_info_text),
                )
            else:
                return (
                    config_text,
                    gr.update(visible=True),
                    gr.update(value=message),
                    gr.update(value="🔍 **Server Status:** Configuration invalid"),
                )

        except Exception as e:
            logger.error(f"Error loading MCP file: {e}")
            return (
                None,
                gr.update(visible=True),
                gr.update(value=f"❌ Error reading file: {str(e)}"),
                gr.update(value="🔍 **Server Status:** File read error"),
            )

    def handle_mcp_textbox_edit(mcp_text):
        """Handle direct edits to the MCP server config textbox with validation."""
        if not mcp_text.strip():
            webui_manager.mcp_server_config = None
            return (
                gr.update(value="📝 Configuration cleared"),
                gr.update(value="🔍 **Server Status:** No configuration"),
            )

        is_valid, message, mcp_server = validate_mcp_config(mcp_text)

        if is_valid and mcp_server:
            webui_manager.mcp_server_config = mcp_server

            # Generate server info
            server_info_text = "🔍 **Server Status:** Configuration valid\n\n"
            if "mcpServers" in mcp_server:
                servers = mcp_server["mcpServers"]
                server_info_text += f"📋 **Available Servers:** {len(servers)}\n\n"
                for name, config in servers.items():
                    command = config.get("command", "Unknown")
                    server_info_text += f"- **{name}**: `{command}`\n"
            else:
                server_info_text += "📋 **Available Servers:** Custom configuration\n"

            return (gr.update(value=message), gr.update(value=server_info_text))
        else:
            webui_manager.mcp_server_config = None
            return (
                gr.update(value=message),
                gr.update(value="🔍 **Server Status:** Configuration invalid"),
            )

    def handle_validate_click(mcp_text):
        """Handle validation button click."""
        return handle_mcp_textbox_edit(mcp_text)

    def handle_clear_click():
        """Handle clear button click."""
        webui_manager.mcp_server_config = None
        return (
            gr.update(value=""),
            gr.update(value="📝 Configuration cleared"),
            gr.update(value="🔍 **Server Status:** Configuration cleared"),
        )

    def handle_save_click(mcp_text):
        """Handle save button click."""
        is_valid, message, mcp_server = validate_mcp_config(mcp_text)

        if is_valid and mcp_server:
            webui_manager.mcp_server_config = mcp_server

            # Optionally save to file
            try:
                config_dir = "./tmp/mcp_configs"
                os.makedirs(config_dir, exist_ok=True)
                config_file = os.path.join(config_dir, "current_config.json")

                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(mcp_server, f, indent=2)

                save_message = (
                    f"✅ Configuration saved and applied! File saved to: {config_file}"
                )
            except Exception as e:
                save_message = (
                    f"✅ Configuration applied! (Save to file failed: {str(e)})"
                )

            return gr.update(value=save_message)
        else:
            return gr.update(value=f"❌ Cannot save invalid configuration: {message}")

    # Connect event handlers
    mcp_json_file.change(
        handle_mcp_file_upload,
        inputs=[mcp_json_file],
        outputs=[mcp_server_config, mcp_server_config, config_status, server_info],
    )

    mcp_server_config.change(
        handle_mcp_textbox_edit,
        inputs=[mcp_server_config],
        outputs=[config_status, server_info],
    )

    validate_button.click(
        handle_validate_click,
        inputs=[mcp_server_config],
        outputs=[config_status, server_info],
    )

    clear_button.click(
        handle_clear_click,
        inputs=None,
        outputs=[mcp_server_config, config_status, server_info],
    )

    save_button.click(
        handle_save_click,
        inputs=[mcp_server_config],
        outputs=[config_status],
    )

    # Store components for possible future use
    webui_manager.add_components(
        "mcp_server",
        dict(
            mcp_json_file=mcp_json_file,
            mcp_server_config=mcp_server_config,
            config_status=config_status,
            server_info=server_info,
            validate_button=validate_button,
            clear_button=clear_button,
            save_button=save_button,
        ),
    )
