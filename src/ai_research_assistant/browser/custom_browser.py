import asyncio
import logging
import socket
from typing import Optional

from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContextConfig
from browser_use.browser.utils.screen_resolution import (
    get_screen_resolution,
    get_window_adjustments,
)
from playwright.async_api import Browser as PlaywrightBrowser
from playwright.async_api import Playwright, async_playwright

from .custom_context import CustomBrowserContext

logger = logging.getLogger(__name__)

CHROME_ARGS = [
    "--disable-gpu",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--disable-background-networking",
    "--disable-sync",
    "--metrics-recording-only",
    "--disable-default-apps",
    "--mute-audio",
    "--no-first-run",
    "--disable-popup-blocking",
    "--disable-background-timer-throttling",
    "--disable-renderer-backgrounding",
    "--disable-device-discovery-notifications",
]


class CustomBrowser(Browser):
    """
    Custom browser class for launching and managing browser instances with Playwright.

    Supports launching a system Chrome binary if specified, with detailed logging and
    anti-detection measures. Used by the web UI agent for browser automation and debugging.
    """

    async def new_context(
        self, config: Optional[BrowserContextConfig] = None
    ) -> CustomBrowserContext:
        """
        Create a new browser context with merged configuration.

        Parameters
        ----------
        config : Optional[BrowserContextConfig]
            Additional context configuration to merge with the browser's config.

        Returns
        -------
        CustomBrowserContext
            The created browser context instance.
        """
        browser_config = self.config.model_dump() if self.config else {}
        context_config = config.model_dump() if config else {}
        merged_config = {**browser_config, **context_config}
        logger.debug(
            f"[CustomBrowser] Creating new browser context with config: {merged_config}"
        )
        return CustomBrowserContext(
            config=BrowserContextConfig(**merged_config), browser=self
        )

    async def _setup_builtin_browser(self, playwright: Playwright) -> PlaywrightBrowser:
        """
        Set up and return a Playwright Browser instance with anti-detection measures.

        If a custom Chrome binary is specified in the config, it will be used.
        Otherwise, Playwright's managed browser will be launched.

        If a user data directory is specified, uses launch_persistent_context as required by Playwright.

        Parameters
        ----------
        playwright : Playwright
            The Playwright instance to use for launching the browser.

        Returns
        -------
        PlaywrightBrowser
            The launched Playwright browser instance.
        """
        logger.info("[CustomBrowser] Starting browser launch process...")
        logger.info(f"[CustomBrowser] Config: {self.config}")
        logger.info(
            f"[CustomBrowser] browser_binary_path: {getattr(self.config, 'browser_binary_path', None)}"
        )
        logger.info(
            f"[CustomBrowser] extra_browser_args: {getattr(self.config, 'extra_browser_args', None)}"
        )
        logger.info(
            f"[CustomBrowser] headless: {getattr(self.config, 'headless', None)}"
        )
        logger.info(
            f"[CustomBrowser] disable_security: {getattr(self.config, 'disable_security', None)}"
        )
        logger.info(
            f"[CustomBrowser] deterministic_rendering: {getattr(self.config, 'deterministic_rendering', None)}"
        )
        logger.info(
            f"[CustomBrowser] chrome_remote_debugging_port: {getattr(self.config, 'chrome_remote_debugging_port', None)}"
        )
        logger.info(
            f"[CustomBrowser] browser_class: {getattr(self.config, 'browser_class', None)}"
        )
        logger.info(f"[CustomBrowser] proxy: {getattr(self.config, 'proxy', None)}")
        logger.info(
            f"[CustomBrowser] new_context_config: {getattr(self.config, 'new_context_config', None)}"
        )

        # Determine window size and position
        try:
            if (
                not self.config.headless
                and hasattr(self.config, "new_context_config")
                and hasattr(self.config.new_context_config, "window_width")
                and hasattr(self.config.new_context_config, "window_height")
            ):
                screen_size = {
                    "width": self.config.new_context_config.window_width,
                    "height": self.config.new_context_config.window_height,
                }
                offset_x, offset_y = get_window_adjustments()
                logger.info(
                    f"[CustomBrowser] Using window size from config: {screen_size}, position: ({offset_x},{offset_y})"
                )
            elif self.config.headless:
                screen_size = {"width": 1920, "height": 1080}
                offset_x, offset_y = 0, 0
                logger.info(
                    f"[CustomBrowser] Headless mode: using default size {screen_size}"
                )
            else:
                screen_size = get_screen_resolution()
                offset_x, offset_y = get_window_adjustments()
                logger.info(
                    f"[CustomBrowser] Using detected screen size: {screen_size}, position: ({offset_x},{offset_y})"
                )
        except Exception as e:
            logger.error(f"[CustomBrowser] Error determining window size/position: {e}")
            raise

        # Extract user_data_dir from extra_browser_args, remove it from args
        user_data_dir = None
        filtered_args = []
        for arg in self.config.extra_browser_args:
            if arg.startswith("--user-data-dir="):
                user_data_dir = arg.split("=", 1)[1]
                logger.info(f"[CustomBrowser] Detected user_data_dir: {user_data_dir}")
            else:
                filtered_args.append(arg)

        # Build Chrome arguments (without --user-data-dir)
        try:
            # For debugging: use only minimal essential Chrome args
            chrome_args = [
                f"--remote-debugging-port={self.config.chrome_remote_debugging_port}",
                *CHROME_ARGS,  # Now correctly unpacked into a list
                # *(CHROME_HEADLESS_ARGS if self.config.headless else []),  # Commented out for minimal debug
                # *(CHROME_DISABLE_SECURITY_ARGS if self.config.disable_security else []),  # Commented out for minimal debug
                # *(
                #     CHROME_DETERMINISTIC_RENDERING_ARGS
                #     if self.config.deterministic_rendering
                #     else []
                # ),  # Commented out for minimal debug
                f"--window-position={offset_x},{offset_y}",
                f"--window-size={screen_size['width']},{screen_size['height']}",
                *filtered_args,
            ]
            logger.info(
                f"[CustomBrowser] Chrome args (minimal for debug): {chrome_args}"
            )
        except Exception as e:
            logger.error(f"[CustomBrowser] Error building Chrome args: {e}")
            raise

        # Check if the remote debugging port is already taken
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if (
                    s.connect_ex(
                        ("localhost", self.config.chrome_remote_debugging_port)
                    )
                    == 0
                ):
                    chrome_args.remove(
                        f"--remote-debugging-port={self.config.chrome_remote_debugging_port}"
                    )
                    logger.warning(
                        f"[CustomBrowser] Remote debugging port {self.config.chrome_remote_debugging_port} already in use. Removed from args."
                    )
        except Exception as e:
            logger.error(f"[CustomBrowser] Error checking remote debugging port: {e}")
            raise

        try:
            browser_class = getattr(playwright, self.config.browser_class)
            logger.info(f"[CustomBrowser] Using browser_class: {browser_class}")
        except Exception as e:
            logger.error(f"[CustomBrowser] Error getting browser_class: {e}")
            raise

        try:
            args = {
                "chromium": list(chrome_args),
                "firefox": [
                    *{
                        "-no-remote",
                        *filtered_args,
                    }
                ],
                "webkit": [
                    *{
                        "--no-startup-window",
                        *filtered_args,
                    }
                ],
            }
            logger.info(
                f"[CustomBrowser] Launch args for {self.config.browser_class}: {args[self.config.browser_class]}"
            )
        except Exception as e:
            logger.error(f"[CustomBrowser] Error building launch args: {e}")
            raise

        # Prepare launch arguments
        launch_args = {
            "headless": self.config.headless,
            "args": args[self.config.browser_class],
            "proxy": self.config.proxy.model_dump() if self.config.proxy else None,
            "handle_sigterm": False,
            "handle_sigint": False,
        }

        if getattr(self.config, "browser_binary_path", None):
            launch_args["executable_path"] = self.config.browser_binary_path
            logger.info(
                f"[CustomBrowser] Launching system Chrome: {self.config.browser_binary_path}"
            )
        else:
            launch_args["channel"] = "chromium"
            logger.info(
                "[CustomBrowser] Launching Playwright-managed Chromium browser."
            )

        logger.info(f"[CustomBrowser] Final browser launch arguments: {launch_args}")
        logger.debug(f"[CustomBrowser] Full browser config: {self.config}")

        try:
            if user_data_dir:
                logger.info(
                    f"[CustomBrowser] Launching with persistent context, user_data_dir={user_data_dir}"
                )
                browser = await browser_class.launch_persistent_context(
                    user_data_dir, **launch_args
                )
            else:
                logger.info("[CustomBrowser] Launching with normal context")
                browser = await browser_class.launch(**launch_args)
            logger.info("[CustomBrowser] Browser launched successfully.")
            return browser
        except Exception as e:
            logger.error(f"[CustomBrowser] Failed to launch browser: {e}")
            raise

    async def launch_and_hold(self, hold_seconds=10):
        """
        Launch the browser and keep it open for a specified number of seconds.

        Parameters
        ----------
        hold_seconds : int
            Number of seconds to keep the browser open for debugging.
        """
        async with async_playwright() as playwright:
            browser = await self._setup_builtin_browser(playwright)
            logger.info(
                f"[CustomBrowser] Browser launched and will be held open for {hold_seconds} seconds."
            )
            await asyncio.sleep(hold_seconds)
            await browser.close()
            logger.info("[CustomBrowser] Browser closed after hold.")
