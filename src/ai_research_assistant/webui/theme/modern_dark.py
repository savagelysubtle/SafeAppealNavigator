import gradio as gr


class ModernDarkTheme(gr.Theme):
    """Custom dark theme with vertical navigation support, using direct attribute setting."""

    def __init__(self):
        super().__init__()
        # Theme customizations based on DESIGN_TOKENS from AllBeAllUIPlan.md

        # Colors
        self.body_background_fill = "#1E1E1E"  # DESIGN_TOKENS.colors.background
        self.panel_background_fill = "#2D2D2D"  # DESIGN_TOKENS.colors.surface
        self.color_accent = (
            "#1ABC9C"  # DESIGN_TOKENS.colors.accent_primary (used for general accent)
        )
        self.color_accent_soft = "#76D7C4"  # Softer primary accent

        self.button_primary_background_fill = (
            "#1ABC9C"  # DESIGN_TOKENS.colors.accent_primary
        )
        self.button_primary_background_fill_hover = "#16A085"  # Darker shade for hover
        self.button_primary_text_color = "#FFFFFF"

        self.button_secondary_background_fill = (
            "#3AA0FF"  # DESIGN_TOKENS.colors.accent_secondary
        )
        self.button_secondary_background_fill_hover = (
            "#2980B9"  # Darker shade for hover
        )
        self.button_secondary_text_color = "#FFFFFF"

        # Spacing (Directly setting available Gradio theme spacing properties)
        self.spacing_sm = "8px"  # DESIGN_TOKENS.spacing.sm
        self.spacing_md = "16px"  # DESIGN_TOKENS.spacing.md
        self.spacing_lg = "24px"  # DESIGN_TOKENS.spacing.lg
        self.layout_gap = self.spacing_md
        self.panel_spacing = self.spacing_lg
        self.block_spacing = self.spacing_lg

        # Radii (Directly setting available Gradio theme radius properties)
        self.radius_sm = "0.25rem"  # DESIGN_TOKENS.radii.small
        self.radius_md = "0.5rem"  # DESIGN_TOKENS.radii.default
        self.radius_lg = "0.75rem"  # DESIGN_TOKENS.radii.large
        self.block_radius = self.radius_md
        self.button_radius = (
            self.radius_sm
        )  # Smaller radius for buttons generally looks good

        # Shadows
        self.shadow_drop = "0 2px 6px rgba(0,0,0,0.35)"  # DESIGN_TOKENS.shadows.default
        self.block_shadow = self.shadow_drop
        self.shadow_drop_lg = (
            "0 4px 12px rgba(0,0,0,0.5)"  # DESIGN_TOKENS.shadows.elevated
        )

        # Text & Font
        self.text_color = "#EAEAEA"
        self.body_text_color = self.text_color
        self.text_size_sm = "0.875rem"  # Approx DESIGN_TOKENS text size (sm)
        self.text_size_md = "1rem"  # Approx DESIGN_TOKENS text size (md)
        self.text_size_lg = "1.125rem"  # Approx DESIGN_TOKENS text size (lg)
        self.font = ["Inter", "ui-sans-serif", "system-ui", "sans-serif"]
        self.header_text_weight = "600"
        self.body_text_weight = "400"

        # Commenting out problematic hue definitions as they are not strictly necessary
        # when direct color properties are set.
        # self.primary_hue = ...
        # self.secondary_hue = ...
        # self.neutral_hue = ...


# To use this theme:
# theme = ModernDarkTheme()
# gr.Interface(..., theme=theme).launch()
