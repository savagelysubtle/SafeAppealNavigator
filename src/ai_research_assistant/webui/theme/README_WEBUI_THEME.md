# `webui/theme/` Module: Guide

This document explains the `theme/` subdirectory within the `src/ai_research_assistant/webui/` module, focusing on how to use, modify, and create custom Gradio themes.

## Purpose

The `theme/` directory contains custom Gradio theme definitions that control the overall look and feel of the AI Research Assistant's web interface. This includes colors, fonts, spacing, and other visual styling elements.

The primary goal is to achieve a modern, consistent, and accessible user interface, as outlined in the `[AllBeAllUIPlan.md](mdc:plans/WUI/AllBeAllUIPlan.md)` and the `[ui-design-system](cursor://rules/ui-design-system)` rule.

## Key Components

-   **`modern_dark.py` (Example)**: This file (or similarly named files) defines a custom theme class, typically inheriting from `gradio.themes.Base` or another Gradio base theme.
    -   It specifies design tokens for colors (primary, secondary, accent, background, text), typography (font families, sizes, weights), spacing, and other style properties.
    -   It may also include overrides for specific Gradio component styles.
-   **`__init__.py`**: Makes the theme modules importable.

## Applying a Theme

The application's main interface entry point (usually `src/ai_research_assistant/webui/interface.py` or `webui.py`) is responsible for instantiating and applying the desired theme to the Gradio Blocks layout.

```python
# Example in interface.py or webui.py
from src.ai_research_assistant.webui.theme.modern_dark import ModernDarkTheme

with gr.Blocks(theme=ModernDarkTheme()) as demo:
    # ... UI layout ...
```

## Modifying an Existing Theme

1.  **Locate Theme File**: Open the Python file for the theme you want to modify in the `theme/` directory (e.g., `modern_dark.py`).
2.  **Identify Design Tokens**: Refer to the `[ui-design-system](cursor://rules/ui-design-system)` rule and the `AllBeAllUIPlan.md` for the defined color palette, typography, and spacing scales.
3.  **Adjust Values**: Carefully change the values of the theme's attributes (e.g., `primary_hue`, `secondary_hue`, `font`, `spacing_size`) to match the design system or achieve the desired visual effect.
    ```python
    class ModernDarkTheme(gr.themes.Base):
        def __init__(self):
            super().__init__(
                primary_hue=gr.themes.colors.emerald, # Example color token
                secondary_hue=gr.themes.colors.blue,
                font=gr.themes.GoogleFont("Inter"),
                # ... other theme parameters
            )
    ```
4.  **Test Thoroughly**: After making changes, run the WebUI and check all pages and components to ensure the modifications have the intended effect and do not introduce visual regressions or accessibility issues.

## Creating a New Theme

1.  **Create Theme File**: Add a new Python file in `src/ai_research_assistant/webui/theme/` (e.g., `my_new_theme.py`).
2.  **Define Theme Class**: Create a new class that inherits from `gradio.themes.Base` or another suitable Gradio theme class.
    ```python
    import gradio as gr

    class MyNewTheme(gr.themes.Base):
        def __init__(self):
            super().__init__(
                # Define your theme's primary_hue, secondary_hue, neutral_hue,
                # font, spacing_size, radius_size, etc.
                # Refer to Gradio documentation for all available parameters.
            )
            # You can also override specific component styles here if needed.
    ```
3.  **Implement Design System**: Ensure your new theme aligns with the established design tokens and visual language (`[ui-design-system](cursor://rules/ui-design-system)`).
4.  **Apply and Test**: Modify the main interface file to use your new theme and test its appearance across the entire application.

## Interaction with Static CSS

While themes control the general styling, more specific or complex CSS rules that are not easily achievable through Gradio theme parameters can be placed in `src/ai_research_assistant/webui/static/modern-ui.css` (or other CSS files in `static/`).

-   Themes provide the foundation.
-   Static CSS files can provide targeted overrides or styles for custom HTML elements used within Gradio.

Refer to `README_WEBUI_OVERVIEW.md` for the overall WebUI structure and the `[ui-design-system](cursor://rules/ui-design-system)` rule for specific visual guidelines.