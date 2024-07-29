from typing import TYPE_CHECKING, Union

from playwright.sync_api import Page as _Page

from agentql import AccessibilityTreeError, QueryParser
from agentql.sync_api._agentql_service import query_agentql_server

from .._utils import post_process_accessibility_tree
from .playwright_driver_sync import (
    Locator,
    find_element_by_id,
    get_page_accessibility_tree,
    process_iframes,
)


class Page(_Page):
    if TYPE_CHECKING:

        def get_by_ai(
            self, query: str, include_aria_hidden: bool = False  # pylint: disable=unused-argument
        ) -> Union[Locator, None]:
            """Get an web element by AI.
            Parameters:
            -----------
            query (str): The query to locate the element.

            Returns:
            --------
            [Playwright Locator](https://playwright.dev/python/docs/api/class-locator) | None: The located element.
            """


def _get_by_ai(self, query: str, include_aria_hidden: bool = False) -> Union[Locator, None]:

    page: Page = self

    query = f"""
{{
    page_element({query})
}}
"""

    # make sure the query is valid
    QueryParser(query).parse()

    try:
        accessibility_tree = get_page_accessibility_tree(
            page, include_aria_hidden=include_aria_hidden
        )
        process_iframes(page, accessibility_tree)
        post_process_accessibility_tree(accessibility_tree)

    except Exception as e:
        raise AccessibilityTreeError() from e

    response = query_agentql_server(query, accessibility_tree, 300, page.url)
    response_data = response.get("page_element")
    if not response_data:
        return None

    tf623_id = response_data.get("tf623_id")
    iframe_path = response_data.get("attributes", {}).get("iframe_path")
    web_element = find_element_by_id(page=page, tf623_id=tf623_id, iframe_path=iframe_path)

    return web_element


# Add the get_by_ai method to the Page class
setattr(_Page, "get_by_ai", _get_by_ai)
