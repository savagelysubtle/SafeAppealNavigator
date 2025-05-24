import logging
from typing import Optional

from browser_use.browser.browser import Browser
from browser_use.browser.context import (
    BrowserContext,
    BrowserContextConfig,
    BrowserContextState,
)
from playwright.async_api import BrowserContext as PlaywrightBrowserContext
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class CustomBrowserContext(BrowserContext):
    """
    Custom browser context that provides additional functionality
    for managing multiple tabs and pages.
    """

    def __init__(
        self,
        browser: "Browser",
        config: BrowserContextConfig | None = None,
        state: Optional[BrowserContextState] = None,
    ):
        super(CustomBrowserContext, self).__init__(
            browser=browser, config=config, state=state
        )

    async def get_playwright_context(self) -> PlaywrightBrowserContext:
        """
        Get the underlying Playwright browser context.

        Returns:
            PlaywrightBrowserContext: The underlying Playwright context
        """
        session = await self.get_session()
        return session.context

    async def create_new_page(self) -> Page:
        """
        Create a new page in this browser context.

        Returns:
            Page: A new Playwright page
        """
        playwright_context = await self.get_playwright_context()
        return await playwright_context.new_page()

    async def get_all_pages(self) -> list[Page]:
        """
        Get all pages in this browser context.

        Returns:
            list[Page]: List of all pages
        """
        playwright_context = await self.get_playwright_context()
        return playwright_context.pages
