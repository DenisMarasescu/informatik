import json
import os

import requests

from agentql import AgentQLServerError, AgentQLServerTimeoutError, APIKeyError
from agentql._core._api_constants import (
    CHECK_SERVER_STATUS_ENDPOINT,
    GET_AGENTQL_DATA_ENDPOINT,
    GET_AGENTQL_ELEMENT_ENDPOINT,
    SERVICE_URL,
    VALIDATE_API_KEY_ENDPOINT,
)
from agentql._core._utils import get_api_key

RESPONSE_ERROR_KEY = "detail"


def query_agentql_server(
    query: str, accessibility_tree: dict, timeout: int, page_url: str, query_data: bool = False
) -> dict:
    """Make Request to AgentQL Server's query endpoint.

    Parameters:
    ----------
    query (str): The query string.
    accessibility_tree (dict): The accessibility tree.
    timeout (int): The timeout value for the connection with backend api service
    page_url (str): The URL of the active page.
    query_data (bool): Whether to query for data. If false, this will query for locators.

    Returns:
    -------
    dict: AgentQL response in json format.
    """
    api_key = get_api_key()
    if not api_key:
        raise APIKeyError(
            """
            AgentQL API key not found.
            Please set the AgentQL API key by invoking `agentql init` command or by setting the environment variable 'AGENTQL_API_KEY'.
            You could refer to the documentation for more information: https://docs.agentql.com/docs/installation/sdk-installation.
            """
        )

    try:
        request_data = {
            "query": f"{query}",
            "accessibility_tree": accessibility_tree,
            "metadata": {"url": page_url},
        }
        if query_data:
            url = os.getenv("AGENTQL_API_HOST", SERVICE_URL) + GET_AGENTQL_DATA_ENDPOINT
        else:
            url = os.getenv("AGENTQL_API_HOST", SERVICE_URL) + GET_AGENTQL_ELEMENT_ENDPOINT

        headers = {"X-API-Key": api_key}
        response = requests.post(
            url, json=request_data, headers=headers, timeout=timeout, allow_redirects=True
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if isinstance(e, requests.exceptions.ReadTimeout):
            raise AgentQLServerTimeoutError() from e
        if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 401:
            raise APIKeyError(
                """
                Invalid or expired API key provided.
                Please set a valid AgentQL API key by invoking `agentql init` command or by setting the environment variable 'AGENTQL_API_KEY'.
                You could refer to the documentation for more information: https://docs.agentql.com/docs/installation/sdk-installation.
                """
            ) from e
        error_code = e.response.status_code if e.response is not None else None
        server_error = e.response.content.decode("utf-8") if e.response is not None else None
        if server_error:
            try:
                server_error_json = json.loads(server_error)
                if isinstance(server_error_json, dict):
                    server_error = server_error_json.get(RESPONSE_ERROR_KEY)
            except ValueError:
                raise AgentQLServerError(server_error, error_code) from e
        raise AgentQLServerError(server_error, error_code) from e


def validate_api_key(api_key: str, timeout: int = 30):
    """Validate the API key through the AgentQL service.

    Parameters:
    ----------
    api_key (str): The AGENTQL API key to validate.

    Returns:
    -------
    bool: True if the API key is valid, False otherwise.
    """
    try:
        url = os.getenv("AGENTQL_API_HOST", SERVICE_URL) + VALIDATE_API_KEY_ENDPOINT
        headers = {"X-API-Key": api_key}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        return False


def check_agentql_server_status(timeout: int = 15) -> bool:
    """Check the status of the AgentQL server.

    Parameters:
    ----------
    timeout (int): The timeout value for the connection with backend api service.

    Returns:
    -------
    bool: True if the server is up and running, False otherwise.
    """
    try:
        url = os.getenv("AGENTQL_API_HOST", SERVICE_URL) + CHECK_SERVER_STATUS_ENDPOINT
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        return False
