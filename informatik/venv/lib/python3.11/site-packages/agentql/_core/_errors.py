import json
import logging
import textwrap
from typing import Union

from agentql import trail_logger
from agentql._core._syntax.node import Node

# pylint: disable-all
AGENTQL_1000_API_KEY_ERROR = 1000
AGENTQL_1001_ATTRIBUTE_NOT_FOUND_ERROR = 1001
AGENTQL_1002_NO_OPEN_BROWSER_ERROR = 1002
AGENTQL_1003_NO_OPEN_PAGE_ERROR = 1003
AGENTQL_1004_PAGE_TIMEOUT_ERROR = 1004
AGENTQL_1005_ACCESSIBILITY_TREE_ERROR = 1005
AGENTQL_1006_ELEMENT_NOT_FOUND_ERROR = 1006
AGENTQL_1007_OPEN_URL_ERROR = 1007
AGENTQL_1008_CLICK_ERROR = 1008
AGENTQL_1009_INPUT_ERROR = 1009
AGENTQL_1010_QUERY_SYNTAX_ERROR = 1010
AGENTQL_1011_UNABLE_TO_CLOSE_POPUP_ERROR = 1011
AGENTQL_1012_PAGE_MONITOR_NOT_INITIALIZED_ERROR = 1012
AGENTQL_2000_SERVER_ERROR = 2000
AGENTQL_2001_SERVER_TIMEOUT_ERROR = 2001

SUPPORT_MESSAGE = textwrap.dedent(
    """
    If the issue persists, please reach out for further assistance through support@tinyfish.io or Tiny Fish Discord channel https://discord.gg/agentql.
    """
)

log = logging.getLogger("agentql")


class BaseAgentQLError(Exception):
    def __init__(self, error, error_code):
        self.error = error + SUPPORT_MESSAGE
        self.error_code = error_code
        trail_logger.add_event(f"Error occurred: {error}")
        trail_logger.finalize()
        logger_store = trail_logger.TrailLoggerStore.get_loggers()
        if logger_store:
            log.debug(trail_logger.TrailLoggerStore.get_loggers()[-1])

    def __str__(self):
        return f"{self.error_code} {self.__class__.__name__}: {self.error}"


class APIKeyError(BaseAgentQLError):
    def __init__(
        self,
        message="Invalid or missing API key. Please set the environment variable 'AGENTQL_API_KEY' with a valid API key.",
    ):
        super().__init__(textwrap.dedent(message), AGENTQL_1000_API_KEY_ERROR)


class AttributeNotFoundError(BaseAgentQLError):
    def __init__(self, name: str, response_data: Union[dict, list], query_tree_node: Node):
        if query_tree_node.name:
            response_data = {query_tree_node.name: response_data}
        message = textwrap.dedent(
            f"""
            \"{name}\" not found in AgentQL response node:
            {json.dumps(response_data, indent=2)}
            There could be a few reasons for this:
            1. The element you are trying to access was not part of the original query. Make sure there are no typos in the name of the element you are trying to access. 

            Query:
            {query_tree_node.dump()}

            2. You may be trying to execute an action on a container node. I.e. the following would raise this error:
            Query:
            {{
                footer {{
                    some_link
                }}
            }}

            response.footer.click()

            In the above example, footer is a container node and you are trying to click on it. You should access the child node instead. I.e. response.footer.some_link.click()
            """
        )
        super().__init__(message, AGENTQL_1001_ATTRIBUTE_NOT_FOUND_ERROR)


class NoOpenBrowserError(BaseAgentQLError):
    def __init__(
        self,
        message=textwrap.dedent(
            """
            No open browser is detected.
            Before interacting with the web driver, please ensure that an AgentQL session is started using the "agentql.start_session()" method.
            """
        ),
    ):
        super().__init__(message, AGENTQL_1002_NO_OPEN_BROWSER_ERROR)


class NoOpenPageError(BaseAgentQLError):
    def __init__(
        self,
        message=textwrap.dedent(
            """
            No open page is detected.
            Make sure to open a page by passing a URL into the "agentql.start_session()" method or by invoking the "session.driver.open_url()" method. 
            """
        ),
    ):
        super().__init__(message, AGENTQL_1003_NO_OPEN_PAGE_ERROR)


class PageTimeoutError(BaseAgentQLError):
    def __init__(self, message="The page took too long to respond"):
        super().__init__(message, AGENTQL_1004_PAGE_TIMEOUT_ERROR)


class AccessibilityTreeError(BaseAgentQLError):
    def __init__(
        self,
        message=textwrap.dedent(
            """
            An error occurred while generating accessibility tree.
            The page may no longer be available due to navigation or being closed. 
            """
        ),
    ):
        super().__init__(message, AGENTQL_1005_ACCESSIBILITY_TREE_ERROR)


class ElementNotFoundError(BaseAgentQLError):
    def __init__(self, page_url, element_id=None):
        if element_id:
            message = (
                f"The element with ID {element_id} could not be found on the current page anymore."
            )
        else:
            message = "The element could not be found on the current page anymore."

        message += textwrap.dedent(
            f"""
            The element may have been removed from the page or the page may have been navigated away from.
            The current page url is: {page_url}
            """
        )

        super().__init__(message, AGENTQL_1006_ELEMENT_NOT_FOUND_ERROR)


class OpenUrlError(BaseAgentQLError):
    def __init__(
        self,
        url: str,
    ):
        message = textwrap.dedent(
            f"""
            Unable to open the URL.
            There could be a few reasons for this:
            1. The web Driver could not navigate to the provided URL {url}. Please check the URL and try again.
            2. If you are running in stealth mode, there might be an issue with how Stealth Mode configuration. Please reach out to Tiny Fish team for further assistance.
            """
        )

        super().__init__(message, AGENTQL_1007_OPEN_URL_ERROR)


class ClickError(BaseAgentQLError):
    def __init__(self, message="Unable to click"):
        super().__init__(message, AGENTQL_1008_CLICK_ERROR)


class InputError(BaseAgentQLError):
    def __init__(self, message="Unable to input text"):
        super().__init__(message, AGENTQL_1009_INPUT_ERROR)


class QuerySyntaxError(BaseAgentQLError):
    def __init__(self, message=None, *, unexpected_token, row, column):
        if not message:
            message = f"Unexpected character {unexpected_token} at row {row}, column {column} in AgentQL query."
        super().__init__(message, AGENTQL_1010_QUERY_SYNTAX_ERROR)
        self.unexpected_token = unexpected_token
        self.row = row
        self.column = column


class UnableToClosePopupError(BaseAgentQLError):
    def __init__(
        self,
        message=textwrap.dedent(
            """
            Failed to automatically close popup. By default, the close function will query AgentQL server and click the close button in the popup with the following query:

            {
                popup_form {
                    close_btn
                }
            }

            You could analyze the popup by invoking popup.accessibility_tree and close it manually by querying the AgentQL server.
            """
        ),
    ):
        super().__init__(message, AGENTQL_1011_UNABLE_TO_CLOSE_POPUP_ERROR)


class PageMonitorNotInitializedError(BaseAgentQLError):
    def __init__(
        self,
    ):
        message = textwrap.dedent(
            """
            The page monitor is not initialized.
            Please use the 'session.driver.wait_for_page_ready_state()' method to wait for the page to reach a stable state.
            """
        )
        super().__init__(message, AGENTQL_1012_PAGE_MONITOR_NOT_INITIALIZED_ERROR)


class AgentQLServerError(BaseAgentQLError):
    def __init__(self, error=None, error_code=None):
        if error is None:
            error = "AgentQL Server Error. Please try again."
        if error_code is None:
            error_code = AGENTQL_2000_SERVER_ERROR

        super().__init__(error, error_code)


class AgentQLServerTimeoutError(AgentQLServerError):
    def __init__(
        self,
        message="Agentql Server Timed Out. Please try again.",
    ):
        super().__init__(message, AGENTQL_2001_SERVER_TIMEOUT_ERROR)
