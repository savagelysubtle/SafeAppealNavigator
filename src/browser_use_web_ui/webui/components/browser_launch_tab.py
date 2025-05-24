import logging
import os
import traceback

import gradio as gr
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextConfig

from src.browser_use_web_ui.browser.custom_browser import CustomBrowser
from src.browser_use_web_ui.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


def create_browser_launch_tab(webui_manager: WebuiManager):
    """
    Tab for launching the browser directly to debug browser startup issues.
    Reads settings from the Browser Settings tab and allows specifying a Chrome profile.
    Logs all relevant info to help debug browser startup issues.
    """
    with gr.Group():
        launch_button = gr.Button("🚀 Launch Browser", variant="primary")
        profile_box = gr.Textbox(
            label="Chrome Profile Directory (e.g. 'Default', 'Profile 1')",
            placeholder="Leave blank for default profile",
            lines=1,
            interactive=True,
        )
        status_box = gr.Textbox(label="Status / Log", lines=10, interactive=False)

    async def handle_launch(profile_dir):
        """Attempt to launch the browser and report status/logs."""
        logs = []

        def log(msg):
            logger.info(msg)
            logs.append(str(msg))

        log("=== Browser Launch Debug Log ===")

        # Get settings from browser_settings tab or .env
        def get_browser_setting(key, default=None):
            comp = webui_manager.id_to_component.get(f"browser_settings.{key}")
            return comp.value if comp else default

        browser_binary_path = get_browser_setting("browser_binary_path") or os.getenv(
            "BROWSER_PATH"
        )
        browser_user_data_dir = get_browser_setting(
            "browser_user_data_dir"
        ) or os.getenv("BROWSER_USER_DATA")
        headless = get_browser_setting("headless", False)
        disable_security = get_browser_setting("disable_security", False)
        window_w = int(get_browser_setting("window_w", 1280))
        window_h = int(get_browser_setting("window_h", 1100))
        wss_url = get_browser_setting("wss_url") or os.getenv("BROWSER_WSS")
        cdp_url = get_browser_setting("cdp_url") or os.getenv("BROWSER_CDP")
        log(f"browser_binary_path: {browser_binary_path}")
        log(f"browser_user_data_dir: {browser_user_data_dir}")
        log(f"headless: {headless}")
        log(f"disable_security: {disable_security}")
        log(f"window_w: {window_w}, window_h: {window_h}")
        log(f"wss_url: {wss_url}")
        log(f"cdp_url: {cdp_url}")
        log(f"profile_dir: {profile_dir}")
        # Build extra args
        extra_args = []
        if browser_user_data_dir:
            extra_args.append(f"--user-data-dir={browser_user_data_dir}")
        if profile_dir and profile_dir.strip():
            extra_args.append(f"--profile-directory={profile_dir.strip()}")
            log(f"Using Chrome profile: {profile_dir.strip()}")
        else:
            log("No profile specified, using default Chrome profile.")
        log(f"extra_args: {extra_args}")
        # Log environment variables
        log(f"ENV BROWSER_PATH: {os.getenv('BROWSER_PATH')}")
        log(f"ENV BROWSER_USER_DATA: {os.getenv('BROWSER_USER_DATA')}")
        # Try launching browser
        try:
            # Pass a valid BrowserContextConfig for new_context_config
            context_config = BrowserContextConfig(
                window_width=window_w,
                window_height=window_h,
            )
            browser = CustomBrowser(
                config=BrowserConfig(
                    headless=False,
                    disable_security=False,
                    browser_binary_path=browser_binary_path,
                    extra_browser_args=extra_args,
                    wss_url=wss_url,
                    cdp_url=cdp_url,
                    new_context_config=context_config,
                )
            )
            log("Instantiated CustomBrowser. Attempting to launch browser...")
            await browser.launch_and_hold(10)
            log("Browser closed successfully.")
            return gr.update(value="\n".join(logs))
        except Exception as e:
            tb = traceback.format_exc()
            log(f"❌ Failed to launch browser: {e}")
            log(tb)
            return gr.update(value="\n".join(logs))

    launch_button.click(
        fn=handle_launch,
        inputs=profile_box,
        outputs=status_box,
    )

    webui_manager.add_components(
        "browser_launch",
        dict(
            launch_button=launch_button,
            profile_box=profile_box,
            status_box=status_box,
        ),
    )
