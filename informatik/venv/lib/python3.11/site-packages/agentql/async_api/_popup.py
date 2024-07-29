import asyncio
from typing import Any, Coroutine, Dict


class Popup:
    """Popup objects are dispatched by session via session.on("popup") event. For each popup window detected on the page, there will be corresponding event and popup objects emitted."""

    def __init__(
        self,
        page_url: str,
        popup_tree: dict,
        popup_name: str,
        on_popup_close: Coroutine[Dict[Any, Any], Any, None],
    ):
        self._page_url = page_url
        self._tree = popup_tree
        self._name = popup_name
        self._close_popup_callback = on_popup_close

    def __str__(self):
        return f"Popup {self._name} on page {self._page_url}"

    @property
    def accessibility_tree(self) -> dict:
        """
        Returns the part of accessibility tree where the popup node as the parent.

        Returns:
        --------
        dict: The part of accessibility tree wheree the popup no9de as the parent.
        """
        return self._tree

    @property
    def name(self) -> str:
        """
        Returns the name of the popup.

        Returns:
        --------
        str: The name of the popup.
        """
        return self._name

    @property
    def page_url(self) -> str:
        """
        Returns the URL of the page where the popup occurred.

        Returns:
        --------
        str: The URL of the page where the popup occurred.
        """
        return self._page_url

    async def close(self):
        """Close the popup by invoking the callback function passed into the Popup object when it is initialized."""
        if self._close_popup_callback is not None and self._tree is not None:
            await self._close_popup_callback(self._tree, self._page_url)
        else:
            raise ValueError("Popup object is not properly initialized.")


async def close_all_popups_handler(popups: list):
    """This is a asynchronous handler function for popups. Passing it as the callback function into session.on("popup") method will close all popups.

    Parameters:
    ----------
    popups(list): The list containing popup objects.
    """
    tasks = [popup.close() for popup in popups]
    await asyncio.gather(*tasks)
