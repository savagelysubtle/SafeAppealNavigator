import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import gradio as gr

from src.ai_research_assistant.config.mcp_client_config import (
    mcp_config,
    validate_agent_mcp_setup,
)
from src.ai_research_assistant.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


def load_current_mcp_config() -> tuple[dict, str]:
    """Load the current MCP configuration from the dev config system."""
    try:
        config = mcp_config.load_mcp_config()
        enabled_servers = mcp_config.get_enabled_servers()

        status_msg = f"✅ Loaded configuration with {len(config.get('mcp_servers', {}))} servers\n"
        status_msg += f"📡 Enabled servers: {len(enabled_servers)}\n"

        if enabled_servers:
            status_msg += f"🔗 Active: {', '.join(enabled_servers)}"
        else:
            status_msg += "⚠️ No servers are currently enabled"

        return config, status_msg
    except Exception as e:
        logger.error(f"Failed to load MCP config: {e}")
        return {}, f"❌ Failed to load configuration: {str(e)}"


def validate_mcp_config(config_text: str) -> tuple[bool, str, Optional[dict]]:
    """Validate MCP configuration JSON and return status, message, and parsed config."""
    if not config_text.strip():
        return False, "⚠️ Configuration is empty", None

    try:
        mcp_config_data = json.loads(config_text)

        # Basic validation of MCP structure
        if not isinstance(mcp_config_data, dict):
            return False, "❌ Configuration must be a JSON object", None

        # Check for the new structured format
        if "mcp_servers" in mcp_config_data:
            servers = mcp_config_data["mcp_servers"]
            if not isinstance(servers, dict):
                return False, "❌ mcp_servers must be an object", None

            server_count = len(servers)
            enabled_count = sum(
                1 for server in servers.values() if server.get("enabled", False)
            )
            return (
                True,
                f"✅ Valid MCP configuration with {server_count} server(s), {enabled_count} enabled",
                mcp_config_data,
            )
        else:
            # Legacy format support
            return True, "✅ Valid JSON configuration (legacy format)", mcp_config_data

    except json.JSONDecodeError as e:
        return False, f"❌ Invalid JSON: {str(e)}", None
    except Exception as e:
        return False, f"❌ Validation error: {str(e)}", None


def create_mcp_server_tab(webui_manager: WebuiManager):
    """
    Creates an enhanced MCP Server tab integrated with the new configuration system.
    """
    with gr.Column():
        # Header
        gr.Markdown(
            "# 🔌 MCP Server Configuration\n*Model Context Protocol server setup and management*"
        )

        with gr.Group():
            gr.Markdown("## 📋 Current Configuration Status")

            with gr.Row():
                refresh_config_btn = gr.Button(
                    "🔄 Refresh Configuration", variant="secondary", scale=1
                )
                validate_agents_btn = gr.Button(
                    "🧪 Validate Agent Requirements", variant="secondary", scale=1
                )

            config_overview = gr.Markdown(
                value="🔄 Loading configuration...",
                container=True,
            )

        with gr.Group():
            gr.Markdown("## 🔧 Server Management")

            # Server list with enable/disable toggles
            with gr.Accordion("📡 Available MCP Servers", open=True):
                server_controls = gr.HTML(
                    value="<p>Loading server controls...</p>", label="Server Controls"
                )

        with gr.Group():
            gr.Markdown("## ✏️ Advanced Configuration Editor")

            # Load current config
            current_config, status_text = load_current_mcp_config()

            gr.Markdown("### 📝 Direct Configuration Editing")
            gr.Markdown(
                "*⚠️ Advanced users only. Changes here will modify the actual configuration files.*"
            )

            mcp_server_config = gr.Textbox(
                label="MCP Server Configuration (JSON)",
                lines=15,
                interactive=True,
                visible=True,
                value=json.dumps(current_config, indent=2) if current_config else "",
                placeholder="Loading configuration...",
                info="💡 This shows the actual configuration from src/ai_research_assistant/config/mcp/mcp_servers.json",
                container=True,
            )

            with gr.Row():
                validate_button = gr.Button(
                    "🔍 Validate Configuration", variant="secondary", scale=2
                )
                reload_button = gr.Button(
                    "🔄 Reload from File", variant="secondary", scale=1
                )
                save_button = gr.Button("💾 Save to File", variant="primary", scale=2)

        with gr.Group():
            gr.Markdown("## 🎯 Agent-Server Mappings")

            agent_mappings_display = gr.Markdown(
                value="🔄 Loading agent mappings...",
                container=True,
            )

        with gr.Group():
            gr.Markdown("## 📊 Configuration Status & Validation")

            config_status = gr.Textbox(
                label="🔍 Status & Validation Results",
                lines=6,
                interactive=False,
                value=status_text,
                container=True,
            )

    def refresh_configuration():
        """Refresh the configuration display."""
        try:
            config, status_msg = load_current_mcp_config()

            # Generate server overview
            overview_text = "## 🔍 **Configuration Overview**\n\n"

            if config and "mcp_servers" in config:
                servers = config["mcp_servers"]
                enabled_servers = [
                    name
                    for name, server in servers.items()
                    if server.get("enabled", False)
                ]

                overview_text += f"📡 **Total Servers:** {len(servers)}\n"
                overview_text += f"✅ **Enabled Servers:** {len(enabled_servers)}\n"
                overview_text += f"❌ **Disabled Servers:** {len(servers) - len(enabled_servers)}\n\n"

                if enabled_servers:
                    overview_text += "### 🟢 Active Servers:\n"
                    for server_name in enabled_servers:
                        server_config = servers[server_name]
                        tools = server_config.get("tools", [])
                        overview_text += f"- **{server_name}**: {len(tools)} tools\n"

                disabled_servers = [
                    name
                    for name, server in servers.items()
                    if not server.get("enabled", False)
                ]
                if disabled_servers:
                    overview_text += "\n### 🔴 Disabled Servers:\n"
                    for server_name in disabled_servers:
                        overview_text += f"- {server_name}\n"
            else:
                overview_text += "⚠️ No MCP servers configured\n"

            # Generate server controls HTML
            controls_html = generate_server_controls_html(config)

            # Generate agent mappings display
            mappings_text = generate_agent_mappings_display()

            return (
                gr.update(value=json.dumps(config, indent=2) if config else "{}"),
                gr.update(value=status_msg),
                gr.update(value=overview_text),
                gr.update(value=controls_html),
                gr.update(value=mappings_text),
            )

        except Exception as e:
            logger.error(f"Error refreshing configuration: {e}")
            error_msg = f"❌ Error refreshing configuration: {str(e)}"
            return (
                gr.update(value="{}"),
                gr.update(value=error_msg),
                gr.update(value="❌ **Configuration Error**"),
                gr.update(value="<p>Error loading server controls</p>"),
                gr.update(value="❌ Error loading agent mappings"),
            )

    def generate_server_controls_html(config: dict) -> str:
        """Generate HTML for server enable/disable controls."""
        if not config or "mcp_servers" not in config:
            return "<p>No servers configured</p>"

        servers = config["mcp_servers"]
        html = "<div style='padding: 10px;'>"

        for server_name, server_config in servers.items():
            enabled = server_config.get("enabled", False)
            status_color = "#28a745" if enabled else "#6c757d"
            status_text = "ENABLED" if enabled else "DISABLED"

            tools = server_config.get("tools", [])
            description = server_config.get("description", "No description")

            html += f"""
            <div style='border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 8px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <h4 style='margin: 0; color: {status_color};'>{server_name}</h4>
                    <span style='background: {status_color}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;'>{status_text}</span>
                </div>
                <p style='margin: 5px 0; color: #666;'>{description}</p>
                <p style='margin: 5px 0;'><strong>Tools:</strong> {", ".join(tools) if tools else "None"}</p>
            </div>
            """

        html += "</div>"
        return html

    def generate_agent_mappings_display() -> str:
        """Generate agent-to-server mappings display."""
        try:
            mappings = mcp_config.load_agent_mappings()
            agent_mappings = mappings.get("agent_mcp_mappings", {})

            display_text = "## 🤖 **Agent-Server Mappings**\n\n"

            if not agent_mappings:
                display_text += "⚠️ No agent mappings configured\n"
                return display_text

            for agent_name, agent_config in agent_mappings.items():
                display_text += f"### 🔧 **{agent_name}**\n"

                required_servers = agent_config.get("required_servers", [])
                optional_servers = agent_config.get("optional_servers", [])
                primary_tools = agent_config.get("primary_tools", [])

                display_text += f"**Required Servers:** {', '.join(required_servers) if required_servers else 'None'}\n"
                display_text += f"**Optional Servers:** {', '.join(optional_servers) if optional_servers else 'None'}\n"
                display_text += f"**Primary Tools:** {', '.join(primary_tools) if primary_tools else 'None'}\n\n"

            return display_text

        except Exception as e:
            logger.error(f"Error generating agent mappings: {e}")
            return f"❌ Error loading agent mappings: {str(e)}"

    def validate_agent_requirements():
        """Validate all agent MCP requirements."""
        try:
            mappings = mcp_config.load_agent_mappings()
            agent_mappings = mappings.get("agent_mcp_mappings", {})

            if not agent_mappings:
                return gr.update(value="⚠️ No agent mappings found to validate")

            validation_results = []
            all_valid = True

            for agent_name in agent_mappings.keys():
                is_valid = validate_agent_mcp_setup(agent_name)
                validation = mcp_config.validate_agent_requirements(agent_name)

                if is_valid:
                    validation_results.append(
                        f"✅ **{agent_name}**: All requirements met"
                    )
                else:
                    all_valid = False
                    missing = validation.get("missing_required", [])
                    validation_results.append(
                        f"❌ **{agent_name}**: Missing required servers: {', '.join(missing)}"
                    )

            summary = "🎯 **Agent Validation Summary**\n\n"
            if all_valid:
                summary += "✅ All agents have their MCP requirements satisfied!\n\n"
            else:
                summary += "⚠️ Some agents have missing MCP server requirements\n\n"

            summary += "\n".join(validation_results)

            return gr.update(value=summary)

        except Exception as e:
            logger.error(f"Error validating agent requirements: {e}")
            return gr.update(value=f"❌ Error during validation: {str(e)}")

    def handle_mcp_textbox_edit(mcp_text):
        """Handle direct edits to the MCP server config textbox with validation."""
        if not mcp_text.strip():
            return gr.update(value="📝 Configuration cleared")

        is_valid, message, mcp_server = validate_mcp_config(mcp_text)

        if is_valid and mcp_server:
            # Store in webui manager for immediate use
            webui_manager.mcp_server_config = mcp_server
            return gr.update(value=message)
        else:
            webui_manager.mcp_server_config = None
            return gr.update(value=message)

    def handle_reload_click():
        """Handle reload button click to refresh from file."""
        return refresh_configuration()

    def handle_save_click(mcp_text):
        """Handle save button click to save configuration to file."""
        is_valid, message, mcp_server = validate_mcp_config(mcp_text)

        if not is_valid or not mcp_server:
            return gr.update(value=f"❌ Cannot save invalid configuration: {message}")

        try:
            # Save to the actual configuration file
            config_file = Path("dev/config/mcp/mcp_servers.json")

            # Create backup first
            if config_file.exists():
                backup_file = config_file.with_suffix(
                    f".backup.{int(time.time())}.json"
                )
                config_file.rename(backup_file)
                logger.info(f"Created backup: {backup_file}")

            # Write new configuration
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(mcp_server, f, indent=2)

            # Clear the cached config to force reload
            mcp_config._mcp_config = None
            webui_manager.mcp_server_config = mcp_server

            save_message = f"✅ Configuration saved successfully!\n📁 File: {config_file}\n🕒 Saved at: {os.path.basename(backup_file) if 'backup_file' in locals() else 'No backup needed'}"
            return gr.update(value=save_message)

        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return gr.update(value=f"❌ Save failed: {str(e)}")

    # Initialize with current configuration
    initial_refresh = refresh_configuration()

    # Connect event handlers
    refresh_config_btn.click(
        refresh_configuration,
        inputs=None,
        outputs=[
            mcp_server_config,
            config_status,
            config_overview,
            server_controls,
            agent_mappings_display,
        ],
    )

    validate_agents_btn.click(
        validate_agent_requirements,
        inputs=None,
        outputs=[config_status],
    )

    mcp_server_config.change(
        handle_mcp_textbox_edit,
        inputs=[mcp_server_config],
        outputs=[config_status],
    )

    validate_button.click(
        handle_mcp_textbox_edit,
        inputs=[mcp_server_config],
        outputs=[config_status],
    )

    reload_button.click(
        handle_reload_click,
        inputs=None,
        outputs=[
            mcp_server_config,
            config_status,
            config_overview,
            server_controls,
            agent_mappings_display,
        ],
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
            mcp_server_config=mcp_server_config,
            config_status=config_status,
            config_overview=config_overview,
            server_controls=server_controls,
            agent_mappings_display=agent_mappings_display,
            refresh_config_btn=refresh_config_btn,
            validate_agents_btn=validate_agents_btn,
            validate_button=validate_button,
            reload_button=reload_button,
            save_button=save_button,
        ),
    )
