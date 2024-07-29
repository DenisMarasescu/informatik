# pylint: disable=protected-access

from pathlib import Path
from typing import List, Union

from playwright.async_api import Browser, StorageState, async_playwright

from agentql._core._errors import OpenUrlError
from agentql.experimental.async_api._protocol._browser import Browser as BrowserProtocol
from agentql.experimental.async_api.playwright._page._main import PlaywrightPage


class Playwright(BrowserProtocol[PlaywrightPage], Browser):
    """
    An implementation of Browser protocol using Playwright SDK. Represents a browser which handles multiple pages.
    """

    @classmethod
    async def chromium(
        cls,
        headless: bool = False,
        user_auth_session: Union[StorageState, None] = None,
        user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    ) -> "Playwright":
        """
        (AgentQL) Initialize a standard Playwright chromium browser.

        Parameters:
        -----------
        headless (bool) (optional): Run browser in a headless mode.
        user_auth_session (StorageState) (optional): Specify a snapshot of user data such as cookies, auth sessions.
        user_agent (str) (optional): Specify a user-agent applied to the browser.
        """
        playwright = await async_playwright().start()

        browser = await playwright.chromium.launch(headless=headless)

        await browser.new_context(storage_state=user_auth_session, user_agent=user_agent)

        return cls(browser._impl_obj)

    @classmethod
    async def from_cdp(cls, url: str) -> "Playwright":
        """
        (AgentQL) Connect to an existing browser using Chrome DevTools Protocol.

        Parameters:
        -----------
        url (str): Url to connect.
        """
        playwright = await async_playwright().start()

        browser = await playwright.chromium.connect_over_cdp(url)

        return cls(browser._impl_obj)

    @property
    def pages(self) -> List[PlaywrightPage]:
        """
        (AgentQL) A list of pages which browser has (in default context).

        Essentially just a convenient shortcut to default context's pages.

        Returns:
        --------
        list[PageImplementation]: A list of Page implementation objects which represent pages.
        """
        return [PlaywrightPage(page._impl_obj) for page in self.contexts[0].pages]

    async def open(self, url: Union[str, None] = None) -> PlaywrightPage:
        """
        (AgentQL) Creates a new page instance (in default context), and optionally opens a new url.

        Essentially just a shortcut for creating a new page in default context and opening a url.

        Returns:
        --------
        PageImplementation: A newly created page via Page implementation object.
        """
        try:
            page = await self.contexts[0].new_page()

            if url:
                await page.goto(url)

        except Exception as exc:
            raise OpenUrlError(str(url)) from exc

        return PlaywrightPage(page._impl_obj)

    async def storage_state(self, path: Union[str, Path, None] = None) -> StorageState:
        """
        (AgentQL) Returns storage state of browser (in default context).
        """
        return await self.contexts[0].storage_state(path=path)
