from typing import Any, Protocol, Union

from agentql.experimental import InteractiveItemTypeT


class Page(Protocol[InteractiveItemTypeT]):
    """
    The Page protocol represents an async implementation of browser page (tab) which can be queried and interacted with.
    """

    _event_listeners: dict
    _page_monitor: Any
    _last_accessibility_tree: Any

    @property
    def _url(self) -> str:
        """
        (AgentQL) Internal proxy to '.url' method of original driver class.
        """
        raise NotImplementedError()

    @property
    async def _accessibility_tree(self) -> dict:
        """
        (AgentQL) Internal property used to access accessibility tree.
        """
        raise NotImplementedError()

    async def _prepare_accessibility_tree(self, include_aria_hidden: bool) -> dict:
        """
        (AgentQL) Prepare the accessibility tree by modifing the dom. It will return the accessibility tree after waiting for page to load and dom modification.

        Parameters:
        -----------
        include_aria_hidden: Whether to include elements with aria-hidden attribute in the AT.

        Returns:
        --------
        dict: The accessibility tree of the page in Python Dict format.
        """
        raise NotImplementedError()

    async def wait_for_page_ready_state(self, wait_for_network_idle: bool = True):
        """
        (AgentQL) Wait for the page to reach the "Page Ready" state (i.e. page has entered a relatively stable state and most main content is loaded).

        Parameters:
        -----------
        wait_for_network_idle (bool) (optional): This acts as a switch to determine whether to use default chekcing mechanism. If set to `False`, this method will only check for whether page has emitted `load` [event](https://developer.mozilla.org/en-US/docs/Web/API/Window/load_event) and provide a less costly checking mechanism for fast-loading pages.
        """
        raise NotImplementedError()

    def _locate_interactive_element(self, response_data: dict) -> InteractiveItemTypeT:
        """
        (AgentQL) Locates an interactive element in the web page.

        Parameters:
        -----------
        response_data (dict): The data of the interactive element from the AgentQL response.

        Returns:
        --------
        InteractiveItemTypeT: The interactive element.
        """
        raise NotImplementedError()

    async def _get_text_content(self, web_element: InteractiveItemTypeT) -> Union[str, None]:
        """
        (AgentQL) Gets the text content of the web element.

        Parameters:
        -----------
        web_element (InteractiveItemTypeT): The web element to get text from.

        Returns:
        --------
        str: The text content of the web element.
        """
        raise NotImplementedError()
