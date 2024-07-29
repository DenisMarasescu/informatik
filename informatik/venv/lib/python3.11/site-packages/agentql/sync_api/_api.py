"""
This module is an entrypoint to AgentQL service
"""

import logging
from typing import Any

from agentql import trail_logger
from agentql.ext.playwright.sync_api import BrowserContext, Locator, Page, PlaywrightWebDriver
from agentql.sync_api._debug_manager import DebugManager

from ._session import Session
from ._web_driver import BrowserTypeT, InteractiveItemTypeT, PageTypeT, WebDriver

log = logging.getLogger("agentql")


class PlaywrightDriverTypeStub(WebDriver[Locator, Page, BrowserContext]):
    pass


def start_session(
    url: str = "",
    *,
    web_driver: WebDriver[
        InteractiveItemTypeT, PageTypeT, BrowserTypeT
    ] = PlaywrightDriverTypeStub(),
    user_auth_session: Any = None,
    enable_history_log: bool = False,
) -> Session[InteractiveItemTypeT, PageTypeT, BrowserTypeT]:
    """Start a new synchronous AgentQL session with the given URL, web driver and user authentication session. By default, session will use Playwright Web Driver.

    Parameters:
    ----------
    url (str): URL to navigate session to. To navigate after a session has already started, users could start session with an initialized web driver and invoke `driver.open_url()` method.
    web_driver (webDriver) (optional): Web driver is responsible for interacting with the browser and page. Defaults to Playwright web driver, which is built on top of the [Playwright framework](https://playwright.dev/python/).
    user_auth_session (dict) (optional): The user authentication session that contains previous login session. Users could retrieve authentication session by starting a session, logging into desired website, and calling `session.get_user_auth_session()`, which will return a `auth_session` object defined in web driver.
    enable_history_log (bool) (optional): Enable history log to record all the events during the session, retrieved via `session.get_last_trail()`.

    Returns:
    -------
    Session: An instance of AgentQL Session class for synchronous environment.
    """
    if enable_history_log or DebugManager.debug_mode_enabled:
        trail_logger.init()

    log.debug(f"Starting session with {url}")

    # this is a dirty hack to avoid instantiating PlaywrightWebDriver as a default value
    # which will be cached and reused across all sessions. This may cause problems when
    # start_session is called multiple times with default params. In this case driver will
    # be reused which is a problem since its stateful.
    if isinstance(web_driver, PlaywrightDriverTypeStub):
        web_driver = PlaywrightWebDriver()  # type: ignore

    try:
        # pylint: disable=protected-access
        web_driver._start_browser(user_auth_session=user_auth_session)
        if url:
            web_driver.open_url(url)
        session = Session[InteractiveItemTypeT, PageTypeT, BrowserTypeT](web_driver)
    except Exception as e:
        log.error(f"Failed to start session: {e}")
        web_driver._stop_browser()
        raise e

    if DebugManager.debug_mode_enabled:
        DebugManager.set_agentql_session(session)
    return session
