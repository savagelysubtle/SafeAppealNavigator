"""
Reusable Rate Limit Slider Component for Gradio interfaces.
"""

from typing import TYPE_CHECKING, Optional, Tuple

import gradio as gr

if TYPE_CHECKING:
    from src.ai_research_assistant.webui.webui_manager import WebuiManager


class RateLimitSlider(gr.Column):
    """
    A Gradio component that provides an enhanced slider for rate limiting,
    including a visual timer and status indicator.
    """

    def __init__(
        self,
        provider_name: str,
        default_rpm: int = 60,
        min_rpm: int = 1,
        max_rpm: int = 300,  # Requests per minute
        webui_manager: Optional["WebuiManager"] = None,
        elem_id: Optional[str] = None,
        elem_classes: Optional[list[str]] = None,
        **kwargs,
    ):
        """
        Initializes the RateLimitSlider component.

        Args:
            provider_name (str): Name of the API provider for this rate limiter.
            default_rpm (int, optional): Default requests per minute. Defaults to 60.
            min_rpm (int, optional): Minimum configurable RPM. Defaults to 1.
            max_rpm (int, optional): Maximum configurable RPM. Defaults to 300.
            webui_manager (Optional[WebuiManager], optional): Reference to WebUI manager. Defaults to None.
            elem_id (Optional[str], optional): HTML ID for the Gradio component. Defaults to None.
            elem_classes (Optional[list[str]], optional): CSS classes. Defaults to None.
            **kwargs: Additional keyword arguments for gr.Column.
        """
        super().__init__(**kwargs)

        self.provider_name = provider_name
        self.webui_manager = webui_manager
        self._elem_id_base = (
            elem_id or f"rate-limit-slider-{provider_name.lower().replace(' ', '-')}"
        )
        self._elem_classes = elem_classes or []
        self._default_rpm = default_rpm
        self._min_rpm = min_rpm
        self._max_rpm = max_rpm

        # Convert RPM to seconds per request for the timer
        self._default_seconds_per_request = 60.0 / default_rpm

        with self:
            gr.Markdown(
                f"**Rate Limit: {self.provider_name}**",
                elem_classes=self._elem_classes + ["rate-limit-provider-label"],
            )
            with gr.Row(elem_classes=self._elem_classes + ["rate-limit-controls"]):
                self.rpm_slider = gr.Slider(
                    minimum=self._min_rpm,
                    maximum=self._max_rpm,
                    value=self._default_rpm,
                    step=1,
                    label="Requests per Minute (RPM)",
                    elem_id=f"{self._elem_id_base}-rpm-slider",
                    interactive=True,
                )
                self.timer_display = gr.HTML(
                    value=self._format_timer_html(
                        self._default_seconds_per_request, self._default_rpm
                    ),
                    elem_id=f"{self._elem_id_base}-timer-display",
                    elem_classes=self._elem_classes + ["rate-limit-timer-display"],
                )

            self.status_label = gr.Label(
                value=self._get_status_text(self._default_seconds_for_timer, True),
                elem_id=f"{self._elem_id_base}-status-label",
                elem_classes=self._elem_classes + ["rate-limit-status-label"],
            )

            # State for managing the countdown timer if we implement it in Python
            self.current_timer_value = gr.State(
                self._default_seconds_for_timer
            )  # seconds
            self.is_limited = gr.State(False)
            self.rpm_value_state = gr.State(self._default_rpm)

            # Event handling for slider changes
            self.rpm_slider.release(
                self._update_display_on_slider_change,
                inputs=[self.rpm_slider, self.is_limited],
                outputs=[
                    self.timer_display,
                    self.status_label,
                    self.current_timer_value,
                    self.rpm_value_state,
                ],
            )

            # Placeholder for real-time timer updates (would require gr.every or JS)
            # For a Python-driven timer, you might use demo.load with gr.every:
            # self.load(self._update_timer_periodically, inputs=[self.current_timer_value, self.is_limited, self.rpm_slider], outputs=[...], every=1)

    @property
    def _default_seconds_for_timer(self) -> float:
        return 60.0 / self._default_rpm

    def _format_timer_html(self, seconds_remaining: float, current_rpm: int) -> str:
        """Formats the HTML for the timer display."""
        # Basic display, JS would enhance this for a live countdown bar
        return (
            f"<div style='padding: 10px; text-align: center; background-color: #f0f0f0; border-radius: 5px;'>"
            f"  <div>Current: {current_rpm} RPM</div>"
            f"  <div>Next request in: ~{seconds_remaining:.1f}s</div>"
            f"</div>"
        )

    def _get_status_text(self, seconds_per_request: float, is_ready: bool) -> str:
        """Returns the status text based on whether the provider is rate-limited."""
        status = (
            "🟢 Ready"
            if is_ready
            else f"🔴 Limited (Next in ~{seconds_per_request:.1f}s)"
        )
        return f"Status: {status} for {self.provider_name}"

    def _update_display_on_slider_change(
        self, rpm_value: int, current_is_limited: bool
    ) -> Tuple[str, str, float, int]:
        """
        Called when the slider value is released. Updates the timer display and status.
        Also resets the current_timer_value state for a Python-driven timer.
        """
        seconds_per_request = 60.0 / rpm_value
        # If a Python timer is active, this change should reset it.
        # For now, we assume it's ready unless an external mechanism sets current_is_limited.
        new_timer_html = self._format_timer_html(seconds_per_request, rpm_value)
        new_status_text = self._get_status_text(
            seconds_per_request, not current_is_limited
        )
        return new_timer_html, new_status_text, seconds_per_request, rpm_value

    def _update_ui_from_state(
        self, is_limited_val: bool, timer_val: float, rpm_val: int
    ) -> Tuple[str, str]:
        """Callback for gr.every() to update UI based on internal state."""
        seconds_for_display = (
            timer_val
            if is_limited_val
            else (60.0 / rpm_val if rpm_val > 0 else float("inf"))
        )
        timer_html = self._format_timer_html(seconds_for_display, rpm_val)
        status_text = self._get_status_text(seconds_for_display, not is_limited_val)
        return timer_html, status_text

    # --- Methods for external control (e.g., by WebuiManager) ---
    def set_rate_limited_externally(
        self, is_limited_val: bool, countdown_seconds: float = 0.0
    ):
        """
        Allows an external system to set the rate-limited state.
        The UI will reflect this on the next gr.every() update if configured.
        """
        self.is_limited.value = is_limited_val  # Directly set the gr.State value
        if is_limited_val:
            self.current_timer_value.value = countdown_seconds
        else:
            # If becoming ready, timer value should reflect current RPM
            current_rpm = (
                self.rpm_value_state.value
                if hasattr(self.rpm_value_state, "value")
                else self._default_rpm
            )
            self.current_timer_value.value = (
                60.0 / current_rpm if current_rpm > 0 else float("inf")
            )
        # Note: This method itself does not trigger a UI update.
        # The UI update relies on a gr.every() mechanism polling these gr.State values.


# Example Usage
if __name__ == "__main__":
    from gradio.themes import Soft as SoftTheme  # Import Soft theme

    with gr.Blocks(theme=SoftTheme()) as demo:
        gr.Markdown("# Rate Limit Slider Demo")

        with gr.Row():
            google_slider = RateLimitSlider(
                provider_name="Google AI", default_rpm=50, elem_id="google_slider"
            )
            openai_slider = RateLimitSlider(
                provider_name="OpenAI API",
                default_rpm=20,
                min_rpm=5,
                max_rpm=100,
                elem_id="openai_slider",
            )

        # This demonstrates how the UI would react if state is changed and polled by gr.every
        demo.load(
            google_slider._update_ui_from_state,
            inputs=[
                google_slider.is_limited,
                google_slider.current_timer_value,
                google_slider.rpm_value_state,
            ],
            outputs=[google_slider.timer_display, google_slider.status_label],
            every=1,
        )
        demo.load(
            openai_slider._update_ui_from_state,
            inputs=[
                openai_slider.is_limited,
                openai_slider.current_timer_value,
                openai_slider.rpm_value_state,
            ],
            outputs=[openai_slider.timer_display, openai_slider.status_label],
            every=1,
        )

        def simulate_rate_limit_google_external():
            # Simulate Google API being rate limited for 5 seconds by an external event
            google_slider.set_rate_limited_externally(True, 5.0)
            gr.Info(
                "Google Slider state set to limited for 5s (UI will update via polling)."
            )
            return "Google API state set to rate-limited (simulated external event)."

        def simulate_google_ready_external():
            google_slider.set_rate_limited_externally(False)
            gr.Info("Google Slider state set to ready (UI will update via polling).")
            return "Google API state set to ready (simulated external event)."

        limit_btn = gr.Button("Simulate Google Rate Limit (External Update)")
        limit_btn.click(
            simulate_rate_limit_google_external, outputs=[gr.Textbox(label="Sim Log")]
        )

        ready_btn = gr.Button("Simulate Google Ready (External Update)")
        ready_btn.click(
            simulate_google_ready_external, outputs=[gr.Textbox(label="Sim Log")]
        )

    demo.launch()
