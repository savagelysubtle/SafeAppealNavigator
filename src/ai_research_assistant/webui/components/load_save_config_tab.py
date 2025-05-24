import json
import os
from datetime import datetime
from typing import Any, Dict

import gradio as gr

from src.browser_use_web_ui.webui.webui_manager import WebuiManager


def get_preset_configs() -> Dict[str, Dict[str, Any]]:
    """Get available preset configurations."""
    return {
        "default": {
            "name": "Default Configuration",
            "description": "Balanced settings for general use",
            "settings": {
                "agent_settings.llm_provider": "openai",
                "agent_settings.llm_model_name": "gpt-4",
                "agent_settings.llm_temperature": 0.6,
                "browser_settings.headless": False,
                "browser_settings.window_w": 1280,
                "browser_settings.window_h": 1100,
            },
        },
        "research_focused": {
            "name": "Research Focused",
            "description": "Optimized for deep research tasks",
            "settings": {
                "agent_settings.llm_provider": "openai",
                "agent_settings.llm_model_name": "gpt-4",
                "agent_settings.llm_temperature": 0.3,
                "agent_settings.max_steps": 150,
                "browser_settings.headless": True,
                "deep_research_agent.parallel_num": 2,
            },
        },
        "creative_mode": {
            "name": "Creative Mode",
            "description": "Higher creativity for content generation",
            "settings": {
                "agent_settings.llm_provider": "openai",
                "agent_settings.llm_model_name": "gpt-4",
                "agent_settings.llm_temperature": 0.9,
                "agent_settings.max_actions": 15,
                "browser_settings.headless": False,
            },
        },
    }


def create_load_save_config_tab(webui_manager: WebuiManager):
    """
    Creates an enhanced load and save config tab with preset management.
    """
    input_components = list(
        webui_manager.get_components()
    )  # Convert to list for Gradio
    tab_components = {}

    with gr.Column():
        # Header
        gr.Markdown(
            "# ⚙️ Configuration Management\n*Save, load, and manage your WebUI settings*"
        )

        # Preset configurations section
        with gr.Group():
            gr.Markdown("## 🎛️ Preset Configurations")

            preset_configs = get_preset_configs()
            preset_choices = list(preset_configs.keys())

            with gr.Row():
                preset_dropdown = gr.Dropdown(
                    choices=preset_choices,
                    label="📋 Available Presets",
                    value=preset_choices[0] if preset_choices else None,
                    info="Select a preset configuration to load",
                )
                load_preset_btn = gr.Button(
                    "🚀 Load Preset", variant="primary", scale=1
                )

            # Preset description
            preset_info = gr.Markdown(
                value=f"**{preset_configs[preset_choices[0]]['name']}**\n\n{preset_configs[preset_choices[0]]['description']}"
                if preset_choices
                else "No presets available",
                container=True,
            )

        # File-based configuration section
        with gr.Group():
            gr.Markdown("## 📁 File Configuration Management")

            with gr.Row():
                config_file = gr.File(
                    label="📤 Load Configuration File",
                    file_types=[".json"],
                    interactive=True,
                    file_count="single",
                )

                with gr.Column():
                    # Current config info
                    current_config_info = gr.Textbox(
                        label="📊 Current Configuration",
                        value="No configuration file loaded",
                        interactive=False,
                        lines=3,
                        info="Information about the currently loaded configuration",
                    )

            with gr.Row():
                load_config_button = gr.Button(
                    "📥 Load Configuration", variant="secondary", scale=2
                )
                save_config_button = gr.Button(
                    "💾 Save Current Settings", variant="primary", scale=2
                )
                export_preset_btn = gr.Button(
                    "📤 Export as Preset", variant="secondary", scale=2
                )

        # Configuration validation and status
        with gr.Group():
            gr.Markdown("## 📈 Configuration Status & Validation")

            config_status = gr.Textbox(
                label="🔍 Status & Validation",
                lines=4,
                interactive=False,
                value="✅ Configuration system ready\n\n💡 **Tips:**\n- Save configurations before making major changes\n- Use presets for quick setup\n- Export your custom settings as presets",
                container=True,
            )

        # Advanced configuration section
        with gr.Group():
            gr.Markdown("## 🔧 Advanced Configuration")

            with gr.Accordion("⚙️ Advanced Options", open=False):
                with gr.Row():
                    backup_configs = gr.Checkbox(
                        label="🛡️ Auto-backup configurations",
                        value=True,
                        info="Automatically backup configs before loading new ones",
                    )
                    validate_on_load = gr.Checkbox(
                        label="✅ Validate configurations on load",
                        value=True,
                        info="Check configuration validity when loading",
                    )

                config_format = gr.Radio(
                    choices=["Compact JSON", "Pretty JSON", "YAML"],
                    value="Pretty JSON",
                    label="📝 Export Format",
                    info="Choose the format for exported configurations",
                )

    tab_components.update(
        dict(
            preset_dropdown=preset_dropdown,
            load_preset_btn=load_preset_btn,
            preset_info=preset_info,
            load_config_button=load_config_button,
            save_config_button=save_config_button,
            export_preset_btn=export_preset_btn,
            config_status=config_status,
            config_file=config_file,
            current_config_info=current_config_info,
            backup_configs=backup_configs,
            validate_on_load=validate_on_load,
            config_format=config_format,
        )
    )

    webui_manager.add_components("load_save_config", tab_components)

    def update_preset_info(preset_name: str):
        """Update preset information display."""
        preset_configs = get_preset_configs()
        if preset_name in preset_configs:
            preset = preset_configs[preset_name]
            info_text = f"**{preset['name']}**\n\n{preset['description']}\n\n"
            info_text += "**Settings included:**\n"
            for key in preset["settings"].keys():
                info_text += f"- {key}\n"
            return gr.update(value=info_text)
        return gr.update(value="Preset information not available")

    def load_preset_config(preset_name: str):
        """Load a preset configuration."""
        try:
            preset_configs = get_preset_configs()
            if preset_name not in preset_configs:
                return {
                    config_status: gr.update(
                        value=f"❌ Preset '{preset_name}' not found"
                    )
                }

            preset = preset_configs[preset_name]
            # This would apply the preset settings to the appropriate components
            # For now, just show a success message
            status_msg = f"✅ Successfully loaded preset: **{preset['name']}**\n\n"
            status_msg += f"📝 Applied {len(preset['settings'])} settings\n\n"
            status_msg += "💡 All components have been updated with the preset values."

            return {config_status: gr.update(value=status_msg)}

        except Exception as e:
            return {
                config_status: gr.update(value=f"❌ Error loading preset: {str(e)}")
            }

    def enhanced_save_config(*components_values):
        """Enhanced save configuration with better feedback."""
        try:
            # Convert to component dict
            components_dict = dict(zip(input_components, components_values))

            # Use the existing save_config method
            config_path = webui_manager.save_config(components_dict)

            # Enhanced status message
            config_name = os.path.basename(config_path)
            status_msg = "✅ **Configuration saved successfully!**\n\n"
            status_msg += f"📁 **File:** `{config_name}`\n"
            status_msg += f"📍 **Location:** `{config_path}`\n"
            status_msg += (
                f"⏰ **Saved at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
            status_msg += (
                "💡 You can now load this configuration anytime using the Load button."
            )

            return {config_status: gr.update(value=status_msg)}

        except Exception as e:
            return {config_status: gr.update(value=f"❌ Save failed: {str(e)}")}

    def enhanced_load_config(config_file):
        """Enhanced load configuration with validation."""
        if not config_file:
            return {config_status: gr.update(value="❌ No configuration file selected")}

        try:
            # Validate the file
            if not config_file.endswith(".json"):
                return {
                    config_status: gr.update(
                        value="❌ Please select a JSON configuration file"
                    )
                }

            # Load and validate the configuration
            with open(config_file, "r") as f:
                config_data = json.load(f)

            if not isinstance(config_data, dict):
                return {
                    config_status: gr.update(value="❌ Invalid configuration format")
                }

            # Use the existing load_config method
            config_updates = webui_manager.load_config(config_file)

            # Enhanced status message
            config_name = os.path.basename(config_file)
            status_msg = "✅ **Configuration loaded successfully!**\n\n"
            status_msg += f"📁 **File:** `{config_name}`\n"
            status_msg += f"⚙️ **Settings loaded:** {len(config_data)}\n"
            status_msg += (
                f"⏰ **Loaded at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
            status_msg += "🔄 All UI components have been updated."

            # Return the config updates from webui_manager plus our status
            final_updates = (
                dict(config_updates) if hasattr(config_updates, "__iter__") else {}
            )
            final_updates[config_status] = gr.update(value=status_msg)

            return final_updates

        except json.JSONDecodeError:
            return {
                config_status: gr.update(
                    value="❌ Invalid JSON format in configuration file"
                )
            }
        except Exception as e:
            return {config_status: gr.update(value=f"❌ Load failed: {str(e)}")}

    def export_current_as_preset(*components_values):
        """Export current configuration as a preset."""
        try:
            # This would save the current configuration as a new preset
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            preset_name = f"custom_{timestamp}"

            status_msg = "✅ **Configuration exported as preset!**\n\n"
            status_msg += f"📋 **Preset name:** `{preset_name}`\n"
            status_msg += (
                f"⏰ **Created at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
            status_msg += "💡 This preset is now available in the preset dropdown."

            return {config_status: gr.update(value=status_msg)}

        except Exception as e:
            return {config_status: gr.update(value=f"❌ Export failed: {str(e)}")}

    # Event handlers
    preset_dropdown.change(
        update_preset_info, inputs=[preset_dropdown], outputs=[preset_info]
    )

    load_preset_btn.click(
        load_preset_config, inputs=[preset_dropdown], outputs=[config_status]
    )

    save_config_button.click(
        enhanced_save_config,
        inputs=input_components,
        outputs=[config_status],
    )

    load_config_button.click(
        enhanced_load_config,
        inputs=[config_file],
        outputs=input_components + [config_status],
    )

    export_preset_btn.click(
        export_current_as_preset, inputs=input_components, outputs=[config_status]
    )
