# pylint: disable=protected-access

import copy
import logging
from typing import Callable, Generic, List, Literal, Optional, Union

from agentql import QueryParser, trail_logger
from agentql._core._utils import minify_query
from agentql.sync_api._debug_manager import DebugManager

from ._agentql_service import query_agentql_server
from ._popup import Popup
from ._response_proxy import AQLResponseProxy
from ._web_driver import BrowserTypeT, InteractiveItemTypeT, PageTypeT, WebDriver

log = logging.getLogger("agentql")

RESPONSE_ERROR_KEY = "detail"


class Session(Generic[InteractiveItemTypeT, PageTypeT, BrowserTypeT]):
    """A synchronous session with a AgentQL service. It is responsible for querying and managing session-related state (like authentication)."""

    def __init__(self, web_driver: WebDriver[InteractiveItemTypeT, PageTypeT, BrowserTypeT]):
        """Initialize the session.

        Parameters:
        ----------
        web_driver (WebDriver): The web driver that will be used in this session.
        """

        self._web_driver = web_driver
        self._event_listeners = {}
        self._check_popup = False
        self._last_query = None
        self._last_response = None
        self._last_accessibility_tree = None
        self._screenshot_counter = 1

    @property
    def current_page(self) -> PageTypeT:
        """Get the current page being processed by AgentQL.

        Returns:
        -------
        PageTypeT: A type variable representing the type of a page in a web driver session. If you did not pass a customized web driver when starting the session, then it will return [Playwright Page](https://playwright.dev/python/docs/api/class-page) object.
        """
        return self._web_driver.current_page

    @property
    def driver(self) -> WebDriver[InteractiveItemTypeT, PageTypeT, BrowserTypeT]:
        """Get the web driver.

        Returns:
        -------
        WebDriver: A protocol representing the web driver. If you did not pass a customized web driver when starting the session, default PlaywrightWebDriver will be returned.
        """
        return self._web_driver

    @property
    def last_query(self) -> Optional[str]:
        """Get the last query."""
        return self._last_query

    @property
    def last_response(self) -> Optional[dict]:
        """Get the last response."""
        return self._last_response

    @property
    def last_accessibility_tree(self) -> Optional[dict]:
        """Get the last captured accessibility tree"""
        return self._last_accessibility_tree

    def get_last_trail(self) -> Union[trail_logger.TrailLogger, None]:
        """
        Get the last trail recorded, if enable_history_log is True when starting the session.
        """
        logger_store = trail_logger.TrailLoggerStore.get_loggers()
        return logger_store[-1] if logger_store else None

    def get_user_auth_session(self):
        """Returns the user authentication session that contains the login session state of current browser. User could pass this information when starting the session to preserve previous login state.

        Returns:
        --------
        User auth session in Python dictionary format.
        """
        return self._web_driver._get_user_auth_session()

    def query_data(
        self,
        query: str,
        timeout: int = 500,
        lazy_load_pages_count: int = 0,
        wait_for_network_idle: bool = True,
        include_aria_hidden: bool = False,
    ) -> AQLResponseProxy[InteractiveItemTypeT]:
        """Query the web page tree for data, such as a block of texts or numbers.

        Returns:
        -------
        AQLResponseProxy: AgentQL Response (Data) of AQLResponseProxy type.
        """
        return self._query(
            query=query,
            timeout=timeout,
            lazy_load_pages_count=lazy_load_pages_count,
            wait_for_network_idle=wait_for_network_idle,
            include_aria_hidden=include_aria_hidden,
            query_data=True,
        )

    def query(
        self,
        query: str,
        timeout: int = 500,
        lazy_load_pages_count: int = 0,
        wait_for_network_idle: bool = True,
        include_aria_hidden: bool = False,
    ) -> AQLResponseProxy[InteractiveItemTypeT]:
        """Query the web page tree for elements that match the AgentQL query.

        Parameters:
        ----------
        query (str): The AgentQL query in String format.
        timeout (int) (optional): Optional timeout value for the connection with backend api service.
        lazy_load_pages_count (int) (optional): The number of pages to scroll down and up to load lazy loaded content.
        wait_for_network_idle (bool) (optional): Whether to wait for the network to be idle before querying the page.
        include_aria_hidden (bool) (optional): Whether to include elements with aria-hidden attribute in the accessibility tree.

        Returns:
        -------
        AQLResponseProxy: AgentQL Response (Elements that match the query) of AQLResponseProxy type.
        """

        return self._query(
            query=query,
            timeout=timeout,
            lazy_load_pages_count=lazy_load_pages_count,
            wait_for_network_idle=wait_for_network_idle,
            include_aria_hidden=include_aria_hidden,
            query_data=False,
        )

    def _query(
        self,
        query: str,
        timeout: int = 500,
        lazy_load_pages_count: int = 0,
        wait_for_network_idle: bool = True,
        include_aria_hidden: bool = False,
        query_data: bool = False,
    ) -> AQLResponseProxy[InteractiveItemTypeT]:
        trail_logger.add_event(f"Querying {minify_query(query)} on {self.current_page}")
        log.debug(f"querying {query}")

        self._last_query = query
        parser = QueryParser(query)
        query_tree = parser.parse()

        self._web_driver.wait_for_page_ready_state(wait_for_network_idle)

        if DebugManager.debug_mode_enabled:
            self._web_driver.take_screenshot(
                f"{DebugManager.debug_files_path}/screenshot_{self._screenshot_counter}.png"
            )
            self._screenshot_counter += 1

        accessibility_tree = self._web_driver._prepare_accessibility_tree(
            lazy_load_pages_count=lazy_load_pages_count, include_aria_hidden=include_aria_hidden
        )

        popup_list = []
        # Check if there is a popup in the page before sending the agentql query
        if self._check_popup:
            popup_list = self._detect_popup(accessibility_tree, [])
            if popup_list:
                self._handle_popup(popup_list)
                accessibility_tree = self._web_driver._prepare_accessibility_tree(
                    lazy_load_pages_count=lazy_load_pages_count,
                    include_aria_hidden=include_aria_hidden,
                )

        self._last_accessibility_tree = accessibility_tree

        response = query_agentql_server(
            query, accessibility_tree, timeout, self._web_driver.current_url, query_data
        )
        self._last_response = response

        # Check if there is a popup in the page after receiving the agentql response
        if self._check_popup:
            # Fetch the most up-to-date accessibility tree
            accessibility_tree = self._web_driver.accessibility_tree

            popup_list = self._detect_popup(accessibility_tree, popup_list)
            if popup_list:
                self._handle_popup(popup_list)

        return AQLResponseProxy[InteractiveItemTypeT](
            response, self._web_driver, query_tree, query_data
        )

    def stop(self):
        """Close the session."""
        log.debug("closing session")
        self._web_driver._stop_browser()
        trail_logger.finalize()

    def on(self, event: Literal["popup"], callback: Callable[[dict], None]):
        """Emitted when there is a popup (such as promotion window) on the page. The callback function will be invoked with the popup object as the argument. Passing None as the callback function will disable popup detections.

        Event Data:
        -----------
        popups (list): The list of popups captured on the page by AgentQL Popup Detection algorithm.
        """
        self._event_listeners[event] = callback
        if callback:
            self._check_popup = True
        else:
            self._check_popup = False

    def _detect_popup(self, tree: dict, known_popups: List[Popup]) -> List[Popup]:
        """Detect if there is a popup in the page. If so, create a Popup object and add it to the popup dict.

        Parameters:
        ----------
        tree (dict): The accessibility tree.
        known_popups (list): The list of known popups.

        Returns:
        --------
        popups (list): The list of popups.
        """
        tree_role = tree.get("role", "")
        tree_name = tree.get("name", "")
        popup_list = []
        if tree_role == "dialog":
            popup = Popup(
                self._web_driver.current_url,
                copy.deepcopy(tree),
                tree_name,
                self._web_driver._close_popup,
            )

            # Avoid adding existing popup to the dict and double handle the popup
            if known_popups:
                for popup_object in known_popups:
                    if popup_object.name != popup.name:
                        popup_list.append(popup)
            else:
                popup_list.append(popup)

            return popup_list

        if "children" in tree:
            for child in tree.get("children", []):
                popup_list = popup_list + self._detect_popup(child, known_popups)

        return popup_list

    def _handle_popup(self, popups: List[Popup]):
        """Handle the popup. If there is a popup in the list, and there is an event listener, emit the popup event by invoking the callback function.

        Parameters:
        ----------
        popups (list): The list of popups to handle."""
        if popups and "popup" in self._event_listeners and self._event_listeners["popup"]:
            self._event_listeners["popup"](popups)
