from typing import Protocol, TypeVar, Union

from agentql.experimental.sync_api._protocol._page import Page

PageImplementation = TypeVar("PageImplementation", bound=Page)


class Browser(Protocol[PageImplementation]):
    """
    The Browser protocol represents a sync implementation of browser (session) which works with multiple pages.
    """

    @property
    def pages(self) -> list[PageImplementation]:
        """
        (AgentQL) A list of pages which browser has (in default context).

        Essentially just a convenient shortcut to default context's pages.

        Returns:
        --------
        list[PageImplementation]: A list of Page implementation objects which represent pages.
        """
        raise NotImplementedError()

    def open(self, url: Union[str, None] = None) -> PageImplementation:
        """
        (AgentQL) Creates a new page instance (in default context), and optionally opens a new url.

        Essentially just a shortcut for creating a new page in default context and opening a url.

        Returns:
        --------
        PageImplementation: A newly created page via Page implementation object.
        """
        raise NotImplementedError()
