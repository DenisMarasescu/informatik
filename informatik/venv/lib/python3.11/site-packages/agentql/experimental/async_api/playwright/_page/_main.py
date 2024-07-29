from typing import Any
import asyncio
import logging
import time

from playwright.async_api import Error, Page

from agentql import QueryParser, trail_logger
from agentql._core._errors import (
    PageMonitorNotInitializedError,
    AccessibilityTreeError,
    ElementNotFoundError,
)

from agentql.experimental.async_api._protocol._page import Page as PageProtocol
from agentql.experimental.async_api._response_proxy import AQLResponseProxy
from agentql.ext.playwright._utils import post_process_accessibility_tree
from agentql.ext.playwright._network_monitor import PageActivityMonitor
from agentql.async_api._agentql_service import query_agentql_server
from agentql._core._js_snippets.snippet_loader import load_js

from agentql.ext.playwright.async_api.playwright_driver_async import (
    get_page_accessibility_tree,
    find_element_by_id,
    process_iframes,
    Locator,
)


log = logging.getLogger("agentql")


class PlaywrightPage(Page, PageProtocol[Locator]):

    def __init__(self, impl_obj: Any):
        super().__init__(impl_obj)

        self._event_listeners = {}
        self._page_monitor = None
        self._original_html = None
        self._last_accessibility_tree = None

    def __str__(self) -> str:
        return f"<Page url={self.url}>"

    def __repr__(self) -> str:
        return f"<Page url={self.url}>"

    @property
    async def _accessibility_tree(self) -> dict:
        try:
            accessibility_tree = await get_page_accessibility_tree(self)
            await process_iframes(self, accessibility_tree)
            return accessibility_tree

        except Exception as e:
            raise AccessibilityTreeError() from e

    @property
    def _url(self) -> str:
        return self.url

    async def query(
        self,
        query: str,
        timeout: int = 500,
        wait_for_network_idle: bool = True,
        include_aria_hidden: bool = False,
    ) -> AQLResponseProxy[Locator]:
        """
        (AgentQL) Query the web page tree for elements that match the AgentQL query.

        Parameters:
        ----------
        query (str): The AgentQL query in String format.
        timeout (int) (optional): Optional timeout value for the connection with backend api service.
        wait_for_network_idle (bool) (optional): Whether to wait for the network to be idle before querying the page.
        include_aria_hidden (bool) (optional): Whether to include elements with aria-hidden attribute in the accessibility tree.

        Returns:
        -------
        AQLResponseProxy: AgentQL Response (Elements that match the query) of AQLResponseProxy type.
        """
        parser = QueryParser(query)
        query_tree = parser.parse()

        await self.wait_for_page_ready_state(wait_for_network_idle=wait_for_network_idle)

        accessibility_tree = await self._prepare_accessibility_tree(
            include_aria_hidden=include_aria_hidden
        )

        response = await query_agentql_server(query, accessibility_tree, timeout, self.url)

        self._last_accessibility_tree = accessibility_tree

        return AQLResponseProxy[Locator](response, self, query_tree)

    async def _prepare_accessibility_tree(self, include_aria_hidden: bool) -> dict:
        self._original_html = await self.content()

        try:
            accessibility_tree = await get_page_accessibility_tree(
                self, include_aria_hidden=include_aria_hidden
            )
            await process_iframes(self, accessibility_tree)
            post_process_accessibility_tree(accessibility_tree)
            return accessibility_tree

        except Exception as e:
            raise AccessibilityTreeError() from e

    async def wait_for_page_ready_state(self, wait_for_network_idle: bool = True):
        trail_logger.add_event(f"Waiting for {self} to reach 'Page Ready' state")

        if not self._page_monitor:
            self._page_monitor = PageActivityMonitor()
        else:
            # Reset the network monitor to clear the logs
            self._page_monitor.reset()

        # Add event listeners to track DOM changes and network activities
        await self._add_event_listeners_for_page_monitor(self)

        # Wait for the page to reach the "Page Ready" state
        await self._determine_load_state(
            self, self._page_monitor, wait_for_network_idle=wait_for_network_idle
        )

        # Remove the event listeners to prevent overwhelming the async event loop
        await self._remove_event_listeners_for_page_monitor(self)

        trail_logger.add_event(f"Finished waiting for {self} to reach 'Page Ready' state")

    def _locate_interactive_element(self, response_data: dict) -> Locator:
        tf623_id = response_data.get("tf623_id")
        if not tf623_id:
            raise ElementNotFoundError(self.url, "tf623_id")
        iframe_path = response_data.get("attributes", {}).get("iframe_path")
        interactive_element = find_element_by_id(
            page=self, tf623_id=tf623_id, iframe_path=iframe_path
        )
        trail_logger.spy_on_object(interactive_element)
        return interactive_element

    async def _determine_load_state(
        self,
        page: Page,
        monitor: PageActivityMonitor,
        timeout_seconds: int = 14,
        wait_for_network_idle: bool = True,
    ):
        if not self._page_monitor:
            raise PageMonitorNotInitializedError()

        start_time = time.time()

        while True:
            if wait_for_network_idle:
                try:
                    last_updated_timestamp = await page.evaluate(load_js("get_last_dom_change"))
                # If the page is navigating, the evaluate function will raise an error. In this case, we wait for the page to load.
                except Error:
                    while True:
                        if self._page_monitor.get_load_status() or time.time() - start_time > 6:
                            break
                        await asyncio.sleep(0.2)
                    # monitor.check_conditions() is expecting milliseconds
                    last_updated_timestamp = time.time() * 1000

                if monitor.is_page_ready(last_active_dom_time=last_updated_timestamp):
                    break
            else:
                if self._page_monitor.get_load_status():
                    trail_logger.add_event("Page ready: Page emitted 'load' event.")
                    break

            if time.time() - start_time > timeout_seconds:
                trail_logger.add_event("Page ready: Timeout while waiting for page to settle.")
                break
            await asyncio.sleep(0.1)

    async def _add_event_listeners_for_page_monitor(self, page: Page):
        if not self._page_monitor:
            raise PageMonitorNotInitializedError()

        try:
            page.on("request", self._page_monitor.track_network_request)
            page.on("requestfinished", self._page_monitor.track_network_response)
            page.on("requestfailed", self._page_monitor.track_network_response)
            page.on("load", self._page_monitor.track_load)
            await page.evaluate(load_js("add_dom_change_listener"))
        # If the page is navigating, the evaluate function will raise an error. In this case, we wait for the page to load.
        except Error:
            start_time = time.time()
            while True:
                if self._page_monitor.get_load_status() or time.time() - start_time > 6:
                    break
                await asyncio.sleep(0.2)

    async def _remove_event_listeners_for_page_monitor(self, page: Page):
        if not self._page_monitor:
            raise PageMonitorNotInitializedError()

        try:
            page.remove_listener("request", self._page_monitor.track_network_request)
            page.remove_listener("requestfinished", self._page_monitor.track_network_response)
            page.remove_listener("requestfailed", self._page_monitor.track_network_response)
            page.remove_listener("load", self._page_monitor.track_load)
            await page.evaluate(load_js("remove_dom_change_listener"))
        except Error:
            log.warning("Unable to remove event listeners for page monitor.")

    async def _get_text_content(self, web_element: Locator) -> str | None:
        return await web_element.text_content()
