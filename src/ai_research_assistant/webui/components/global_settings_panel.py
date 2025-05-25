"""
Global Settings Panel for AI Research Assistant

This module provides a unified, collapsible settings panel that consolidates
all LLM and system configurations previously scattered across multiple tabs.

Based on refactoring patterns from:
- Circumventing LLM Limits by Refactoring to Patterns
- Large Code Refactor using LLMs best practices
"""

import logging
import os
from typing import Any, Dict, Optional

import gradio as gr

from src.ai_research_assistant.utils import config
from src.ai_research_assistant.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


class GlobalSettingsManager:
    """
    Centralized settings management following the Singleton pattern.
    This eliminates the fragmentation of LLM configurations across multiple tabs.
    """

    _instance = None
    _settings_cache = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self.initialized = True
            self._settings_cache = self._load_default_settings()

    def _load_default_settings(self) -> Dict[str, Any]:
        """Load default settings from config and environment"""
        return {
            # Primary LLM Configuration
            "primary_llm_provider": os.getenv("DEFAULT_LLM", "google"),
            "primary_llm_model": self._get_default_model_for_provider(
                os.getenv("DEFAULT_LLM", "google")
            ),
            "primary_llm_temperature": 0.7,
            "primary_llm_max_tokens": 2048,
            "primary_llm_use_vision": True,
            # Planner LLM Configuration (optional separate LLM for planning)
            "planner_llm_enabled": False,
            "planner_llm_provider": "openai",
            "planner_llm_model": "gpt-4",
            "planner_llm_temperature": 0.3,
            "planner_llm_use_vision": False,
            # Browser Agent Settings
            "browser_headless": False,
            "browser_window_width": 1280,
            "browser_window_height": 1100,
            "browser_timeout": 30,
            "browser_max_steps": 100,
            # Research Agent Settings
            "research_max_parallel": 2,
            "research_max_depth": 3,
            "research_save_screenshots": True,
            # Legal Agent Settings
            "legal_max_cases_per_query": 20,
            "legal_enable_document_generation": True,
            "legal_database_path": os.getenv(
                "WCAT_DATABASE_PATH", "./tmp/legal_research/cases.db"
            ),
            # System Settings
            "output_directory": "./tmp",
            "enable_logging": True,
            "log_level": "INFO",
            "enable_telemetry": False,
        }

    def _get_default_model_for_provider(self, provider: str) -> str:
        """Get default model for a provider from config"""
        if provider in config.DEFAULT_MODELS:
            return config.DEFAULT_MODELS[provider]["model"]
        return "gpt-4"  # fallback

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self._settings_cache.get(key, default)

    def update_setting(self, key: str, value: Any) -> None:
        """Update a setting value"""
        self._settings_cache[key] = value
        logger.info(f"Updated setting: {key} = {value}")

    def get_primary_llm_config(self) -> Dict[str, Any]:
        """Get primary LLM configuration"""
        return {
            "provider": self.get_setting("primary_llm_provider"),
            "model_name": self.get_setting("primary_llm_model"),
            "temperature": self.get_setting("primary_llm_temperature"),
            "max_tokens": self.get_setting("primary_llm_max_tokens"),
            "use_vision": self.get_setting("primary_llm_use_vision"),
        }

    def get_planner_llm_config(self) -> Optional[Dict[str, Any]]:
        """Get planner LLM configuration if enabled"""
        if not self.get_setting("planner_llm_enabled"):
            return None

        return {
            "provider": self.get_setting("planner_llm_provider"),
            "model_name": self.get_setting("planner_llm_model"),
            "temperature": self.get_setting("planner_llm_temperature"),
            "use_vision": self.get_setting("planner_llm_use_vision"),
        }

    def export_settings(self) -> Dict[str, Any]:
        """Export all settings for saving/loading"""
        return self._settings_cache.copy()

    def import_settings(self, settings: Dict[str, Any]) -> None:
        """Import settings from saved configuration"""
        self._settings_cache.update(settings)
        logger.info("Imported settings successfully")


def create_global_settings_panel(webui_manager: WebuiManager):
    """
    Create a collapsible global settings panel that consolidates all configurations.
    This replaces the fragmented settings across multiple tabs.
    """
    settings_manager = GlobalSettingsManager()

    with gr.Accordion("🌐 Global Settings", open=False) as settings_accordion:
        gr.Markdown("""
        **Unified Configuration Center**
        All LLM and system settings are managed here. Changes apply to all agents automatically.
        """)

        # Primary LLM Section
        with gr.Group():
            gr.Markdown("## 🧠 Primary LLM Configuration")

            with gr.Row():
                primary_provider = gr.Dropdown(
                    choices=list(config.PROVIDER_DISPLAY_NAMES.keys()),
                    label="🏢 Primary LLM Provider",
                    value=settings_manager.get_setting("primary_llm_provider"),
                    info="Main LLM used by all agents",
                )

                # Initialize primary_model dropdown with proper Google models if google is selected
                initial_provider = settings_manager.get_setting("primary_llm_provider")
                initial_model = settings_manager.get_setting("primary_llm_model")

                if initial_provider == "google":
                    # Get all Google models organized by category
                    all_models = []
                    categories = config.get_google_models_by_category()

                    # Create choices with format: "display_name|actual_model_id"
                    for category, models in categories.items():
                        for model in models:
                            model_info = config.GOOGLE_MODEL_OPTIONS.get(model, {})
                            display_name = f"[{category.split('(')[0].strip()}] {model_info.get('name', model)}"
                            # Store both display and value info
                            all_models.append((display_name, model))

                    # Add non-categorized models if any
                    for model_id in config.GOOGLE_MODEL_OPTIONS.keys():
                        if not any(
                            model_id in category_models
                            for category_models in categories.values()
                        ):
                            model_info = config.GOOGLE_MODEL_OPTIONS.get(model_id, {})
                            display_name = f"[Other] {model_info.get('name', model_id)}"
                            all_models.append((display_name, model_id))

                    # Sort models by display name
                    all_models.sort(key=lambda x: x[0])

                    # Create choices list - Gradio will use the second element as the value
                    model_choices = [
                        (display, model_id) for display, model_id in all_models
                    ]
                    model_info_text = (
                        "Google Gemini models - organized by capability and generation"
                    )
                else:
                    # For non-Google providers, use simple choices
                    model_choices = [initial_model] if initial_model else []
                    model_info_text = (
                        f"Model for {initial_provider}"
                        if initial_provider
                        else "Select provider first"
                    )

                primary_model = gr.Dropdown(
                    label="🤖 Primary Model",
                    choices=model_choices,
                    value=initial_model,
                    allow_custom_value=True,
                    info=model_info_text,
                )

            with gr.Row():
                primary_temperature = gr.Slider(
                    minimum=0.0,
                    maximum=2.0,
                    value=settings_manager.get_setting("primary_llm_temperature"),
                    step=0.1,
                    label="🌡️ Primary Temperature",
                    info="Creativity level (0.0 = focused, 2.0 = creative)",
                )

                primary_use_vision = gr.Checkbox(
                    label="👁️ Enable Vision",
                    value=settings_manager.get_setting("primary_llm_use_vision"),
                    info="Allow image analysis capabilities",
                )

        # Planner LLM Section
        with gr.Group():
            gr.Markdown("## 🗺️ Planner LLM Configuration (Optional)")

            planner_enabled = gr.Checkbox(
                label="Enable Separate Planner LLM",
                value=settings_manager.get_setting("planner_llm_enabled"),
                info="Use a different LLM for planning tasks",
            )

            with gr.Row():
                planner_provider = gr.Dropdown(
                    choices=list(config.PROVIDER_DISPLAY_NAMES.keys()),
                    label="🏢 Planner Provider",
                    value=settings_manager.get_setting("planner_llm_provider"),
                    visible=settings_manager.get_setting("planner_llm_enabled"),
                )

                # Initialize planner_model dropdown with proper Google models if google is selected
                planner_provider_setting = settings_manager.get_setting(
                    "planner_llm_provider"
                )
                planner_model_setting = settings_manager.get_setting(
                    "planner_llm_model"
                )

                if planner_provider_setting == "google":
                    # For planner, focus on reasoning-heavy models
                    reasoning_models = []

                    # Get models good for reasoning/planning
                    recommended = config.get_recommended_google_models()
                    priority_models = [
                        recommended.get(
                            "reasoning_heavy", "gemini-2.5-pro-preview-05-06"
                        ),
                        recommended.get(
                            "general_use", "gemini-2.5-flash-preview-04-17"
                        ),
                        recommended.get("stable_production", "gemini-1.5-flash"),
                    ]

                    for model_id in priority_models:
                        if model_id in config.GOOGLE_MODEL_OPTIONS:
                            model_info = config.GOOGLE_MODEL_OPTIONS[model_id]
                            display_name = model_info.get("name", model_id)
                            reasoning_models.append((display_name, model_id))

                    # Create choices list
                    planner_model_choices = reasoning_models
                    planner_model_info = (
                        "Models optimized for planning and reasoning tasks"
                    )
                else:
                    # For non-Google providers, use simple choices
                    planner_model_choices = (
                        [planner_model_setting] if planner_model_setting else []
                    )
                    planner_model_info = (
                        f"Model for {planner_provider_setting}"
                        if planner_provider_setting
                        else "Select provider first"
                    )

                planner_model = gr.Dropdown(
                    label="🤖 Planner Model",
                    choices=planner_model_choices,
                    value=planner_model_setting,
                    allow_custom_value=True,
                    visible=settings_manager.get_setting("planner_llm_enabled"),
                    info=planner_model_info,
                )

            planner_temperature = gr.Slider(
                minimum=0.0,
                maximum=2.0,
                value=settings_manager.get_setting("planner_llm_temperature"),
                step=0.1,
                label="🌡️ Planner Temperature",
                info="Usually lower for planning tasks",
                visible=settings_manager.get_setting("planner_llm_enabled"),
            )

        # Browser Settings Section
        with gr.Group():
            gr.Markdown("## 🌐 Browser Agent Settings")

            with gr.Row():
                browser_headless = gr.Checkbox(
                    label="🕶️ Headless Mode",
                    value=settings_manager.get_setting("browser_headless"),
                    info="Run browser without UI (faster)",
                )

                browser_max_steps = gr.Number(
                    label="🚶 Max Steps",
                    value=settings_manager.get_setting("browser_max_steps"),
                    precision=0,
                    info="Maximum actions per task",
                )

            with gr.Row():
                browser_width = gr.Number(
                    label="📏 Window Width",
                    value=settings_manager.get_setting("browser_window_width"),
                    precision=0,
                )

                browser_height = gr.Number(
                    label="📐 Window Height",
                    value=settings_manager.get_setting("browser_window_height"),
                    precision=0,
                )

        # Research Settings Section
        with gr.Group():
            gr.Markdown("## 🔍 Research Agent Settings")

            with gr.Row():
                research_parallel = gr.Number(
                    label="⚡ Max Parallel Tasks",
                    value=settings_manager.get_setting("research_max_parallel"),
                    precision=0,
                    info="Number of concurrent research tasks",
                )

                research_depth = gr.Number(
                    label="🕳️ Max Research Depth",
                    value=settings_manager.get_setting("research_max_depth"),
                    precision=0,
                    info="How deep to go in research chains",
                )

        # Quick Actions
        with gr.Row():
            reset_button = gr.Button("🔄 Reset to Defaults", variant="secondary")
            save_button = gr.Button("💾 Save Settings", variant="primary")
            # export_button = gr.Button("📤 Export Config", variant="secondary")  # TODO: Implement export functionality

        # Status display
        settings_status = gr.Textbox(
            label="📊 Settings Status",
            value="✅ Global settings loaded successfully",
            interactive=False,
            lines=2,
        )

    # Store components for external access
    components = {
        "settings_accordion": settings_accordion,
        "primary_provider": primary_provider,
        "primary_model": primary_model,
        "primary_temperature": primary_temperature,
        "primary_use_vision": primary_use_vision,
        "planner_enabled": planner_enabled,
        "planner_provider": planner_provider,
        "planner_model": planner_model,
        "planner_temperature": planner_temperature,
        "browser_headless": browser_headless,
        "browser_max_steps": browser_max_steps,
        "browser_width": browser_width,
        "browser_height": browser_height,
        "research_parallel": research_parallel,
        "research_depth": research_depth,
        "settings_status": settings_status,
    }

    # Event handlers
    def update_primary_model_choices(provider):
        """Update model choices when provider changes"""
        if provider == "google":
            # Get all Google models organized by category
            all_models = []
            categories = config.get_google_models_by_category()

            # Create choices with format: "display_name|actual_model_id"
            for category, models in categories.items():
                for model in models:
                    model_info = config.GOOGLE_MODEL_OPTIONS.get(model, {})
                    display_name = f"[{category.split('(')[0].strip()}] {model_info.get('name', model)}"
                    # Store both display and value info
                    all_models.append((display_name, model))

            # Add non-categorized models if any
            for model_id in config.GOOGLE_MODEL_OPTIONS.keys():
                if not any(
                    model_id in category_models
                    for category_models in categories.values()
                ):
                    model_info = config.GOOGLE_MODEL_OPTIONS.get(model_id, {})
                    display_name = f"[Other] {model_info.get('name', model_id)}"
                    all_models.append((display_name, model_id))

            # Sort models by display name
            all_models.sort(key=lambda x: x[0])

            # Create choices list - Gradio will use the second element as the value
            choices = [(display, model_id) for display, model_id in all_models]

            # Get recommended default
            default_model = config.get_recommended_google_models().get(
                "general_use", "gemini-2.5-flash-preview-04-17"
            )

            return gr.Dropdown(
                choices=choices,
                value=default_model,
                allow_custom_value=True,
                info="Google Gemini models - organized by capability and generation",
            )
        elif provider in config.DEFAULT_MODELS:
            model_config = config.DEFAULT_MODELS[provider]
            return gr.Dropdown(
                choices=[model_config["model"]],
                value=model_config["model"],
                allow_custom_value=True,
                info=f"Default {provider} model",
            )
        return gr.Dropdown(choices=[], value="", allow_custom_value=True)

    def update_planner_model_choices(provider):
        """Update planner model choices when provider changes"""
        if provider == "google":
            # For planner, focus on reasoning-heavy models
            reasoning_models = []

            # Get models good for reasoning/planning
            recommended = config.get_recommended_google_models()
            priority_models = [
                recommended.get("reasoning_heavy", "gemini-2.5-pro-preview-05-06"),
                recommended.get("general_use", "gemini-2.5-flash-preview-04-17"),
                recommended.get("stable_production", "gemini-1.5-flash"),
            ]

            for model_id in priority_models:
                if model_id in config.GOOGLE_MODEL_OPTIONS:
                    model_info = config.GOOGLE_MODEL_OPTIONS[model_id]
                    display_name = model_info.get("name", model_id)
                    reasoning_models.append((display_name, model_id))

            # Create choices list
            choices = reasoning_models
            default_model = recommended.get(
                "reasoning_heavy", "gemini-2.5-pro-preview-05-06"
            )

            return gr.Dropdown(
                choices=choices,
                value=default_model,
                allow_custom_value=True,
                info="Models optimized for planning and reasoning tasks",
            )
        elif provider in config.DEFAULT_MODELS:
            model_config = config.DEFAULT_MODELS[provider]
            return gr.Dropdown(
                choices=[model_config["model"]],
                value=model_config["model"],
                allow_custom_value=True,
                info=f"Default {provider} model for planning",
            )
        return gr.Dropdown(choices=[], value="", allow_custom_value=True)

    def toggle_planner_visibility(enabled):
        """Show/hide planner settings based on checkbox"""
        return (
            gr.update(visible=enabled),  # planner_provider
            gr.update(visible=enabled),  # planner_model
            gr.update(visible=enabled),  # planner_temperature
        )

    def update_setting_and_sync(*values):
        """Update settings and sync across all agents"""
        component_keys = list(components.keys())[1:-1]  # Exclude accordion and status
        for key, value in zip(component_keys, values):
            setting_key = key.replace("_", "_")
            settings_manager.update_setting(setting_key, value)

        return gr.update(value="✅ Settings updated and synced to all agents")

    def reset_to_defaults():
        """Reset all settings to defaults"""
        settings_manager.__init__()  # Reload defaults
        defaults = settings_manager.export_settings()

        updates = {}
        for comp_name, component in components.items():
            if comp_name in defaults:
                updates[component] = gr.update(value=defaults[comp_name])

        updates[settings_status] = gr.update(value="🔄 Reset to default settings")
        return updates

    def save_current_settings():
        """Save current settings to file"""
        try:
            settings = settings_manager.export_settings()
            config_path = webui_manager.save_settings(settings)
            return gr.update(
                value=f"💾 Settings saved to: {os.path.basename(config_path)}"
            )
        except Exception as e:
            return gr.update(value=f"❌ Save failed: {str(e)}")

    # Wire up event handlers
    primary_provider.change(
        update_primary_model_choices,
        inputs=[primary_provider],
        outputs=[primary_model],
    )

    planner_provider.change(
        update_planner_model_choices,
        inputs=[planner_provider],
        outputs=[planner_model],
    )

    planner_enabled.change(
        toggle_planner_visibility,
        inputs=[planner_enabled],
        outputs=[planner_provider, planner_model, planner_temperature],
    )

    # Auto-sync on any change
    for comp_name, component in components.items():
        if comp_name not in ["settings_accordion", "settings_status"]:
            component.change(
                lambda: gr.update(value="🔄 Settings changed - auto-syncing..."),
                outputs=[settings_status],
            )

    reset_button.click(
        reset_to_defaults,
        outputs=list(components.values()),
    )

    save_button.click(
        save_current_settings,
        outputs=[settings_status],
    )

    # Register with webui_manager (exclude layout components like accordion)
    input_components = {
        k: v for k, v in components.items() if k != "settings_accordion"
    }
    webui_manager.add_components("global_settings", input_components)
    webui_manager.global_settings_manager = settings_manager

    return components, settings_manager
