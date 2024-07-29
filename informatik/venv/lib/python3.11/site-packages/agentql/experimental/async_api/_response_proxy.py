# pylint: disable=protected-access

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Generic, Union

from agentql import (
    AttributeNotFoundError,
    ContainerListNode,
    ContainerNode,
    IdListNode,
    IdNode,
    trail_logger,
)
from agentql.experimental import InteractiveItemTypeT
from agentql.experimental.async_api._protocol._page import Page as PageProtocol

log = logging.getLogger("agentql")


class AQLResponseProxy(Generic[InteractiveItemTypeT]):
    """
    AQLResponseProxy class acts as a dynamic proxy to the response received from AgentQL server. It allows users to interact with resulting web elements and to retrieve their text contents. This class is designed to work with the web driver to fetch and process query results.
    """

    if TYPE_CHECKING:
        # needed to make the type checker happy
        async def __call__(self, *args, **kwargs): ...

    def __init__(
        self,
        data: Union[dict, list],
        page: PageProtocol[InteractiveItemTypeT],
        query_tree: ContainerNode,
    ):
        self._response_data = data
        self._page = page
        self._query_tree_node = query_tree

    def __getattr__(
        self, name
    ) -> Union["AQLResponseProxy[InteractiveItemTypeT]", InteractiveItemTypeT]:
        if self._response_data is None:
            raise AttributeError("Response data is None")
        if name not in self._response_data:
            raise AttributeNotFoundError(
                name, self._response_data, query_tree_node=self._query_tree_node
            )
        trail_logger.add_event(f"Resolving element {name}")
        return self._resolve_item(
            self._response_data[name], self._query_tree_node.get_child_by_name(name)
        )  # type: ignore # returned value could be None, but to make static checker happy we ignore it

    def __getitem__(
        self, index: int
    ) -> Union[InteractiveItemTypeT, "AQLResponseProxy[InteractiveItemTypeT]"]:
        if not isinstance(self._response_data, list):
            raise ValueError("This node is not a list")
        return self._resolve_item(self._response_data[index], self._query_tree_node)  # type: ignore # returned value could be None, but to make static checker happy we ignore it

    def _resolve_item(
        self, item, query_tree_node
    ) -> Union[InteractiveItemTypeT, "AQLResponseProxy[InteractiveItemTypeT]", None]:
        if item is None:
            return None

        if isinstance(item, list):
            return AQLResponseProxy[InteractiveItemTypeT](item, self._page, query_tree_node)

        if isinstance(query_tree_node, IdNode) or isinstance(query_tree_node, IdListNode):
            interactive_element = self._page._locate_interactive_element(item)
            trail_logger.add_event(f"Resolved to {interactive_element}")

            return interactive_element

        return AQLResponseProxy[InteractiveItemTypeT](item, self._page, query_tree_node)

    def __len__(self):
        if self._response_data is None:
            return 0
        return len(self._response_data)

    def __str__(self):
        return json.dumps(self._response_data, indent=2)

    async def to_data(self) -> dict:
        """
        (AgentQL) Converts the response data into a structured dictionary based on the query tree.

        Returns:
        --------
        dict: A structured dictionary representing the processed response data, with fact nodes replaced by name (values) from the response data. It will have the following structure:

        ```py
        {
        "query_field": "text content of the corresponding web element"
        }
        ```
        """
        return await self._to_data_node(self._response_data, self._query_tree_node)

    async def _to_data_node(
        self, response_data, query_tree_node
    ) -> dict:  # TODO Figure out what the f is going on here.
        if isinstance(query_tree_node, ContainerListNode):
            return await self._to_data_container_list_node(response_data, query_tree_node)  # type: ignore
        elif isinstance(query_tree_node, ContainerNode):
            return await self._to_data_container_node(response_data, query_tree_node)
        elif isinstance(query_tree_node, IdListNode):
            return await self._to_data_id_list_node(response_data)  # type: ignore
        elif isinstance(query_tree_node, IdNode):
            return await self._to_data_id_node(response_data)  # type: ignore
        else:
            raise TypeError("Unsupported query tree node type")

    async def _to_data_container_node(
        self, response_data: dict, query_tree_node: ContainerNode
    ) -> dict:
        tasks = []
        children = []

        for child_name, child_data in response_data.items():
            child_query_tree = query_tree_node.get_child_by_name(child_name)

            task = asyncio.create_task(self._to_data_node(child_data, child_query_tree))
            tasks.append(task)
            children.append(child_name)

        # run all tasks concurrently.
        results = await asyncio.gather(*tasks)

        return {child_name: result for result, child_name in zip(results, children)}

    async def _to_data_container_list_node(
        self, response_data: dict, query_tree_node: ContainerListNode
    ) -> list:
        tasks = [self._to_data_container_node(item, query_tree_node) for item in response_data]
        result_list = await asyncio.gather(*tasks)
        return result_list

    async def _to_data_id_node(self, response_data: dict) -> Union[dict, str, None]:
        if response_data is None:
            return None
        name = response_data.get("name")
        if not name or not name.strip():
            web_element = self._page._locate_interactive_element(response_data)
            if not web_element:
                log.warning(f"Could not locate web element for item {response_data}")
                return None
            element_text = await self._page._get_text_content(web_element)
            if not element_text:
                log.warning(f"Could not get text content for item {response_data}")
                return None
            name = element_text.strip()
        return name

    async def _to_data_id_list_node(self, response_data: list) -> list:
        tasks = [self._to_data_id_node(item) for item in response_data]
        res = await asyncio.gather(*tasks)
        return [node for node in res if node is not None]
