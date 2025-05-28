import asyncio
import logging
import os
import threading
import uuid
from typing import Any, Dict, List, Optional

from playwright.async_api import Page

# Try to import PyPDF2, handle gracefully if not available
try:
    from PyPDF2 import PdfReader

    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    PdfReader = None

from src.ai_research_assistant.browser.custom_browser import CustomBrowser
from src.ai_research_assistant.browser.custom_context import CustomBrowserContext

logger = logging.getLogger(__name__)

# Global registries for tracking agent instances and stop flags
_PDF_AGENT_STOP_FLAGS = {}
_PDF_AGENT_INSTANCES = {}


class PDFResearchAgent:
    """
    Agent that uses browser automation to perform searches, download PDFs, extract metadata,
    and enter results into Google Sheets via browser tab automation.
    """

    def __init__(
        self,
        browser: CustomBrowser,
        context: CustomBrowserContext,
        download_dir: str = "./downloads",
        task_id: Optional[str] = None,
    ):
        self.browser = browser
        self.context = context
        self.download_dir = download_dir
        self.task_id = task_id or str(uuid.uuid4())
        os.makedirs(self.download_dir, exist_ok=True)
        self.research_page: Optional[Page] = None
        self.sheets_page: Optional[Page] = None
        self.stopped = False

    async def run(
        self, search_queries: List[str], sheets_url: str
    ) -> List[Dict[str, Any]]:
        """
        Main entry point. Opens research and Google Sheets tabs, collects data, and enters it into the sheet.
        """
        all_results = []
        stop_event = _PDF_AGENT_STOP_FLAGS.get(self.task_id)

        try:
            # Store this instance for potential stop calls
            _PDF_AGENT_INSTANCES[self.task_id] = self

            # Create new pages using the custom context
            # 1. Open research tab
            self.research_page = await self.context.create_new_page()
            # 2. Open Google Sheets tab
            self.sheets_page = await self.context.create_new_page()

            await self.sheets_page.goto(sheets_url)
            logger.info(
                f"[PDFAgent {self.task_id}] Opened Google Sheets at {sheets_url}"
            )

            # TODO: Wait for login if needed
            # await self._wait_for_sheets_login()

            for query in search_queries:
                if stop_event and stop_event.is_set():
                    logger.info(
                        f"[PDFAgent {self.task_id}] Stop requested, breaking out of search loop"
                    )
                    break

                logger.info(f"[PDFAgent {self.task_id}] Processing query: {query}")
                search_results = await self.perform_search(query)

                for result in search_results:
                    if stop_event and stop_event.is_set():
                        logger.info(
                            f"[PDFAgent {self.task_id}] Stop requested, breaking out of results loop"
                        )
                        break

                    page_metadata = await self.extract_page_metadata(result["url"])
                    pdf_links = await self.find_pdf_links(result["url"])

                    for pdf_url in pdf_links:
                        if stop_event and stop_event.is_set():
                            logger.info(
                                f"[PDFAgent {self.task_id}] Stop requested, breaking out of PDF loop"
                            )
                            break

                        pdf_path = await self.download_pdf(pdf_url)
                        pdf_metadata = self.extract_pdf_metadata(pdf_path)
                        record = {
                            "search_query": query,
                            "result_url": result["url"],
                            "page_metadata": page_metadata,
                            "pdf_url": pdf_url,
                            "pdf_path": pdf_path,
                            "pdf_metadata": pdf_metadata,
                        }
                        all_results.append(record)
                        await self.enter_record_to_sheet(record)

                if stop_event and stop_event.is_set():
                    break

        except Exception as e:
            logger.error(
                f"[PDFAgent {self.task_id}] Error during execution: {e}", exc_info=True
            )

        finally:
            # Cleanup pages
            if self.research_page:
                try:
                    await self.research_page.close()
                except Exception as e:
                    logger.error(
                        f"[PDFAgent {self.task_id}] Error closing research page: {e}"
                    )

            if self.sheets_page:
                try:
                    await self.sheets_page.close()
                except Exception as e:
                    logger.error(
                        f"[PDFAgent {self.task_id}] Error closing sheets page: {e}"
                    )

            # Cleanup
            if self.task_id in _PDF_AGENT_INSTANCES:
                del _PDF_AGENT_INSTANCES[self.task_id]

        return all_results

    async def perform_search(self, query: str) -> List[Dict[str, str]]:
        """
        Use the research tab to perform the search and return a list of result dicts.
        """
        if not self.research_page:
            logger.error("Research page not available")
            return []

        # TODO: Implement browser automation for search
        # Example placeholder:
        # await self.research_page.goto(f"https://example.com/search?q={query}")
        # results = await self.research_page.query_selector_all('.search-result')
        # return [{"url": await r.get_attribute("href"), "title": await r.text_content()} for r in results]

        logger.info(
            f"[PDFAgent {self.task_id}] TODO: Implement search for query: {query}"
        )
        return []

    async def extract_page_metadata(self, url: str) -> Dict[str, Any]:
        """
        Extract metadata from the given page URL using the research tab.
        """
        if not self.research_page:
            logger.error("Research page not available")
            return {}

        try:
            await self.research_page.goto(url)
            # TODO: Implement browser automation to extract metadata
            # Example:
            # title = await self.research_page.title()
            # meta_desc = await self.research_page.get_attribute('meta[name="description"]', 'content')
            # return {"title": title, "description": meta_desc, "url": url}

            logger.info(
                f"[PDFAgent {self.task_id}] TODO: Implement metadata extraction for: {url}"
            )
            return {"url": url}
        except Exception as e:
            logger.error(
                f"[PDFAgent {self.task_id}] Error extracting metadata from {url}: {e}"
            )
            return {"url": url, "error": str(e)}

    async def find_pdf_links(self, url: str) -> List[str]:
        """
        Find all PDF links on the given page using the research tab.
        """
        if not self.research_page:
            logger.error("Research page not available")
            return []

        try:
            # Page should already be loaded from extract_page_metadata
            # TODO: Implement browser automation to find PDF links
            # Example:
            # pdf_links = await self.research_page.query_selector_all('a[href$=".pdf"]')
            # return [await link.get_attribute("href") for link in pdf_links]

            logger.info(
                f"[PDFAgent {self.task_id}] TODO: Implement PDF link finding for: {url}"
            )
            return []
        except Exception as e:
            logger.error(
                f"[PDFAgent {self.task_id}] Error finding PDF links on {url}: {e}"
            )
            return []

    async def download_pdf(self, pdf_url: str) -> str:
        """
        Download the PDF using the browser and return the local file path.
        """
        try:
            # TODO: Implement browser-based PDF download
            # Option 1: Use Playwright's download functionality
            # Option 2: Use requests/aiohttp to download the file

            filename = os.path.basename(pdf_url) or f"pdf_{uuid.uuid4().hex[:8]}.pdf"
            if not filename.endswith(".pdf"):
                filename += ".pdf"
            file_path = os.path.join(self.download_dir, filename)

            logger.info(
                f"[PDFAgent {self.task_id}] TODO: Implement PDF download for: {pdf_url}"
            )
            # For now, create an empty file as placeholder
            with open(file_path, "w") as f:
                f.write("")

            return file_path
        except Exception as e:
            logger.error(
                f"[PDFAgent {self.task_id}] Error downloading PDF {pdf_url}: {e}"
            )
            return ""

    def extract_pdf_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Use PyPDF2 or similar to extract PDF metadata.
        """
        if not pdf_path or not os.path.exists(pdf_path):
            return {"error": "PDF file not found or empty path"}

        if not HAS_PYPDF2 or PdfReader is None:
            return {"error": "PyPDF2 not available. Install with: pip install PyPDF2"}

        try:
            reader = PdfReader(pdf_path)
            info = reader.metadata

            result = {
                "num_pages": len(reader.pages),
                "file_path": pdf_path,
                "file_size": os.path.getsize(pdf_path),
            }

            # Safely extract metadata (info can be None)
            if info:
                result.update(
                    {
                        "title": getattr(info, "title", None),
                        "author": getattr(info, "author", None),
                        "subject": getattr(info, "subject", None),
                        "producer": getattr(info, "producer", None),
                        "creation_date": getattr(info, "creation_date", None),
                    }
                )
            else:
                result["metadata_error"] = "No metadata available in PDF"

            return result
        except Exception as e:
            logger.error(
                f"[PDFAgent {self.task_id}] Error extracting PDF metadata from {pdf_path}: {e}"
            )
            return {"error": str(e), "file_path": pdf_path}

    async def enter_record_to_sheet(self, record: dict):
        """
        Use browser automation to enter the record into the Google Sheet tab.
        """
        if not self.sheets_page:
            logger.error("Google Sheets page not available")
            return

        try:
            # TODO: Implement tab switch and data entry logic
            # Example:
            # await self.sheets_page.bring_to_front()
            # await self.sheets_page.click('A1')  # Click first empty cell
            # await self.sheets_page.keyboard.type(record['search_query'])
            # await self.sheets_page.keyboard.press('Tab')
            # await self.sheets_page.keyboard.type(record['result_url'])
            # await self.sheets_page.keyboard.press('Enter')

            logger.info(
                f"[PDFAgent {self.task_id}] TODO: Implement sheet entry for record: {record.get('search_query', 'unknown')}"
            )
        except Exception as e:
            logger.error(
                f"[PDFAgent {self.task_id}] Error entering record to sheet: {e}"
            )

    async def stop(self):
        """Stop the agent execution."""
        logger.info(f"[PDFAgent {self.task_id}] Stop requested")
        self.stopped = True


async def run_single_pdf_research_task(
    search_query: str,
    sheets_url: str,
    task_id: str,
    browser_config: Dict[str, Any],
    stop_event: threading.Event,
    download_dir: str = "./tmp/downloads",
) -> Dict[str, Any]:
    """
    Runs a single PDFResearchAgent task with proper browser management.
    """
    browser = None
    context = None

    try:
        logger.info(
            f"[PDFTask {task_id}] Starting PDF research for query: {search_query}"
        )

        # Create browser and context
        # TODO: Use the browser_config to configure the browser properly
        browser = CustomBrowser()  # You'll need to pass proper config here
        context = await browser.new_context()

        agent = PDFResearchAgent(
            browser=browser,
            context=context,
            download_dir=download_dir,
            task_id=task_id,
        )

        # Store agent instance for potential stop
        _PDF_AGENT_INSTANCES[task_id] = agent

        if stop_event.is_set():
            logger.info(f"[PDFTask {task_id}] Cancelled before start")
            return {"task_id": task_id, "query": search_query, "status": "cancelled"}

        results = await agent.run([search_query], sheets_url)

        if stop_event.is_set():
            logger.info(f"[PDFTask {task_id}] Stopped during execution")
            return {
                "task_id": task_id,
                "query": search_query,
                "results": results,
                "status": "stopped",
            }
        else:
            logger.info(f"[PDFTask {task_id}] Completed successfully")
            return {
                "task_id": task_id,
                "query": search_query,
                "results": results,
                "status": "completed",
            }

    except Exception as e:
        logger.error(f"[PDFTask {task_id}] Error during execution: {e}", exc_info=True)
        return {
            "task_id": task_id,
            "query": search_query,
            "error": str(e),
            "status": "failed",
        }

    finally:
        # Cleanup
        if task_id in _PDF_AGENT_INSTANCES:
            del _PDF_AGENT_INSTANCES[task_id]

        if context:
            try:
                await context.close()
                logger.info(f"[PDFTask {task_id}] Closed browser context")
            except Exception as e:
                logger.error(f"[PDFTask {task_id}] Error closing context: {e}")

        if browser:
            try:
                await browser.close()
                logger.info(f"[PDFTask {task_id}] Closed browser")
            except Exception as e:
                logger.error(f"[PDFTask {task_id}] Error closing browser: {e}")


async def run_parallel_pdf_research_agents(
    search_queries: List[str],
    sheets_url: str,
    browser_config: Dict[str, Any],
    max_parallel: int = 2,
    download_dir: str = "./tmp/downloads",
    main_task_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Runs multiple PDFResearchAgent instances in parallel, each with its own browser/context.
    """
    if not main_task_id:
        main_task_id = str(uuid.uuid4())

    # Create stop event for this batch
    stop_event = threading.Event()
    _PDF_AGENT_STOP_FLAGS[main_task_id] = stop_event

    semaphore = asyncio.Semaphore(max_parallel)

    async def run_agent_for_query(query: str) -> Dict[str, Any]:
        task_id = f"{main_task_id}_{uuid.uuid4().hex[:8]}"
        async with semaphore:
            # Each task gets its own stop event derived from the main one
            task_stop_event = threading.Event()
            _PDF_AGENT_STOP_FLAGS[task_id] = task_stop_event

            # Copy stop state from main event
            if stop_event.is_set():
                task_stop_event.set()

            try:
                return await run_single_pdf_research_task(
                    search_query=query,
                    sheets_url=sheets_url,
                    task_id=task_id,
                    browser_config=browser_config,
                    stop_event=task_stop_event,
                    download_dir=download_dir,
                )
            finally:
                if task_id in _PDF_AGENT_STOP_FLAGS:
                    del _PDF_AGENT_STOP_FLAGS[task_id]

    try:
        logger.info(
            f"[PDFParallel {main_task_id}] Starting {len(search_queries)} parallel PDF research tasks"
        )

        tasks = [run_agent_for_query(query) for query in search_queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"[PDFParallel {main_task_id}] Task {i} failed with exception: {result}"
                )
                processed_results.append(
                    {
                        "query": search_queries[i],
                        "error": str(result),
                        "status": "failed",
                    }
                )
            else:
                processed_results.append(result)

        logger.info(f"[PDFParallel {main_task_id}] Completed parallel execution")
        return processed_results

    finally:
        # Cleanup main stop event
        if main_task_id in _PDF_AGENT_STOP_FLAGS:
            del _PDF_AGENT_STOP_FLAGS[main_task_id]


async def stop_pdf_research_agents(main_task_id: str):
    """Stop all PDF research agents associated with a main task ID."""
    logger.info(f"[PDFParallel {main_task_id}] Stop requested for all agents")

    # Set stop event for main task
    if main_task_id in _PDF_AGENT_STOP_FLAGS:
        _PDF_AGENT_STOP_FLAGS[main_task_id].set()

    # Stop all sub-agents
    keys_to_stop = [
        key
        for key in _PDF_AGENT_INSTANCES.keys()
        if key.startswith(f"{main_task_id}_") or key == main_task_id
    ]

    if keys_to_stop:
        logger.info(
            f"[PDFParallel {main_task_id}] Stopping {len(keys_to_stop)} agent instances"
        )
        for key in keys_to_stop:
            agent = _PDF_AGENT_INSTANCES.get(key)
            if agent:
                try:
                    await agent.stop()
                except Exception as e:
                    logger.error(
                        f"[PDFParallel {main_task_id}] Error stopping agent {key}: {e}"
                    )
