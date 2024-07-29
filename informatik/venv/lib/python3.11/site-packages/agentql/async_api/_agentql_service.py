import os

import httpx

from agentql import AgentQLServerError, AgentQLServerTimeoutError, APIKeyError
from agentql._core._api_constants import (
    CHECK_SERVER_STATUS_ENDPOINT,
    GET_AGENTQL_DATA_ENDPOINT,
    GET_AGENTQL_ELEMENT_ENDPOINT,
    SERVICE_URL,
    VALIDATE_API_KEY_ENDPOINT,
)
from agentql._core._utils import get_api_key_async

RESPONSE_ERROR_KEY = "detail"


async def query_agentql_server(
    query: str, accessibility_tree: dict, timeout: int, page_url: str, query_data: bool = False
) -> dict:
    """Make Request to AgentQL Server's query endpoint.

    Parameters:
    ----------
    query (str): The query string.
    accessibility_tree (dict): The accessibility tree.
    timeout (int): The timeout value for the connection with backend api service
    page_url (str): The URL of the active page.

    Returns:
    -------
    dict: AgentQL response in json format.
    """
    api_key = await get_api_key_async()
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
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=request_data, headers=headers, timeout=timeout, follow_redirects=True
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as e:
        raise AgentQLServerTimeoutError() from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise APIKeyError(
                """
                Invalid or expired API key provided.
                Please set a valid AgentQL API key by invoking `agentql init` command or by setting the environment variable 'AGENTQL_API_KEY'.
                You could refer to the documentation for more information: https://docs.agentql.com/docs/installation/sdk-installation.
                """
            ) from e
        error_code = e.response.status_code
        server_error = e.response.text
        if server_error:
            try:
                server_error_json = e.response.json()
                if isinstance(server_error_json, dict):
                    server_error = server_error_json.get(RESPONSE_ERROR_KEY)
            except ValueError:
                raise AgentQLServerError(server_error, error_code) from e
        raise AgentQLServerError(server_error, error_code) from e
    except httpx.RequestError as e:
        raise AgentQLServerError(str(e)) from e


async def validate_api_key(api_key: str, timeout: int = 30):
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
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return True
    except httpx.HTTPStatusError:
        return False


async def check_agentql_server_status(timeout: int = 15) -> bool:
    """Check the status of the AgentQL server.

    Parameters:
    ----------
    timeout (int): The timeout value for the connection with backend API service.

    Returns:
    -------
    bool: True if the server is up and running, False otherwise.
    """
    try:
        url = os.getenv("AGENTQL_API_HOST", SERVICE_URL) + CHECK_SERVER_STATUS_ENDPOINT
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)
            response.raise_for_status()
            return True
    except httpx.HTTPStatusError:
        return False
