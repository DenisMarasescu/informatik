from typing import Any, Optional

from typing_extensions import Protocol

from agentql.async_api import BrowserTypeT, InteractiveItemTypeT, PageTypeT, ScrollDirection


class WebDriver(Protocol[InteractiveItemTypeT, PageTypeT, BrowserTypeT]):
    def get_text_content(self, web_element: InteractiveItemTypeT) -> Optional[str]:
        """
        Gets the text content of the web element.

        Parameters:
        -----------
        web_element (InteractiveItemTypeT): The web element to get text from.

        Returns:
        --------
        str: The text content of the web element."""

    def open_url(self, url: str, new_page: bool = False):
        """Open URL in the browser.

        Parameters:
        ----------
        url (str): The URL to open.
        new_page (bool): Whether to open the URL in a new page.
        """

    def wait_for_page_ready_state(self, wait_for_network_idle: bool = True):
        """Wait for the page to reach the "Page Ready" state (i.e. page has entered a relatively stable state and most main content is loaded).

        Parameters:
        -----------
        wait_for_network_idle (bool) (optional): This acts as a switch to determine whether to use default chekcing mechanism. If set to `False`, this method will only check for whether page has emitted `load` [event](https://developer.mozilla.org/en-US/docs/Web/API/Window/load_event) and provide a less costly checking mechanism for fast-loading pages.
        """

    def scroll_page(self, scroll_direction: ScrollDirection, pixels: int = 720):
        """Scrolls the page up or down by given pixels. By default, it will scroll 720 pixels.

        Parameters:
        -----------
        scroll_direction (ScrollDirection): An enumeration class that represents the direction in which a scroll action can occur. Currently, it has `UP` and `DOWN` member.
        scroll_direction (ScrollDirection): An enumeration class that represents the direction in which a scroll action can occur. Currently, it has `UP` and `DOWN` member.
        pixels (int) (optional): The number of pixels to scroll. 720 by default.
        """

    def scroll_to_bottom(self):
        """Scrolls to the bottom of the current page."""

    def scroll_to_top(self):
        """Scrolls to the top of the current page."""

    def take_screenshot(self, path: str):
        """Takes a screenshot of the current page.

        Parameters:
        -----------
        path (str): The path to save the screenshot.
        """

    @property
    def current_url(self) -> str:
        """Get the URL of the current page being processed by AgentQL.

        Returns:
        --------
        str: The URL of the current page.
        """

    @property
    def accessibility_tree(self) -> dict:
        """Returns the up-to-date accessibility tree of the page.

        Returns:
        --------
        dict: The accessibility tree of the page in Python Dict format.
        """

    @property
    def html(self) -> Optional[str]:
        """Returns the original HTML (i.e. without any AgentQL modifications) fetched from the most recently loaded page.".

        Returns:
        --------
        dict: The HTML content of the web page.
        """

    @property
    def browser(self) -> BrowserTypeT:
        """Returns the current browser being used.

        Returns:
        --------
        BrowserTypeT: The current browser objects.
        """

    @property
    def current_page(self) -> PageTypeT:
        """Returns the page object that represents the current page. Users should be able to do more fine grained interaction using this page object, such as navigating to a different url or take screenshot of the page.

        Returns:
        --------
        PageTypeT: The current page object.
        """

    def _close_popup(self, popup_tree: dict, page_url: str, timeout: int = 500):
        """Close the popup on the page.

        Parameters:
        -----------
        popup_tree (dict): The accessibility tree that has the popup node as the parent.
        page_url (str): The URL of the active page.
        timeout (int) (optional): The timeout value for the connection with AgentQL server service.
        """

    def _get_user_auth_session(self) -> Any:
        """Returns the user authentication session that contains the login session state of current browser. User could pass this information when starting the session to preserve previous login state.

        Returns:
        --------
        The user session state.
        """

    def _locate_interactive_element(self, response_data: dict) -> InteractiveItemTypeT:
        """
        Locates an interactive element in the web page.

        Parameters:
        -----------
        response_data (dict): The data of the interactive element from the AgentQL response.

        Returns:
        --------
        InteractiveItemTypeT: The interactive element.
        """

    def _prepare_accessibility_tree(
        self, lazy_load_pages_count: int, include_aria_hidden: bool
    ) -> dict:
        """Prepare the AT by modifing the dom. It will return the accessibility tree after preparation.

        Parameters:
        lazy_load_pages_count: The number of times to scroll down and up the page.
        include_aria_hidden: Whether to include elements with aria-hidden attribute in the AT.

        Returns:
        --------
        dict: The accessibility tree of the page in Python Dict format.
        """

    def _start_browser(self, user_auth_session: Any = None):
        """Starts a new browser session and set user session state (if there is any).

        Parameters:
        -----------
        user_auth_session (optional): The user authentication session that contains previous login session.
        """

    def _stop_browser(self):
        """Closes the current browser session."""
