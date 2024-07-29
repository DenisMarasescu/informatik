# pylint: disable=protected-access

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

from ._web_driver import BrowserTypeT, InteractiveItemTypeT, PageTypeT, WebDriver

log = logging.getLogger(__name__)


class AQLResponseProxy(Generic[InteractiveItemTypeT]):
    """
    AQLResponseProxy class acts as a dynamic proxy to the response received from AgentQL server. It allows users to interact with resulting web elements and to retrieve their text contents. This class is designed to work with the web driver to fetch and process query results.
    """

    if TYPE_CHECKING:
        # needed to make the type checker happy
        def __call__(self, *args, **kwargs): ...

    def __init__(
        self,
        data: Union[dict, list],
        web_driver: "WebDriver[InteractiveItemTypeT, PageTypeT, BrowserTypeT]",
        query_tree: ContainerNode,
        query_data: bool = False,
    ):
        self._response_data = data
        self._web_driver = web_driver
        self._query_tree_node = query_tree
        self._query_data = query_data

    def __getattr__(
        self, name
    ) -> Union["AQLResponseProxy[InteractiveItemTypeT]", InteractiveItemTypeT]:
        if self._response_data is None:
            raise AttributeError("Response data is None")

        if name not in self._response_data:
            raise AttributeNotFoundError(name, self._response_data, self._query_tree_node)
        trail_logger.add_event(f"Resolving element {name} on {self._web_driver.current_url}")

        return self._resolve_item(
            self._response_data[name], query_tree_node=self._query_tree_node.get_child_by_name(name)
        )  # type: ignore # returned value could be None, but to make static checker happy we ignore it

    def __getitem__(
        self, index: int
    ) -> Union[InteractiveItemTypeT, "AQLResponseProxy[InteractiveItemTypeT]"]:
        if not isinstance(self._response_data, list):
            raise ValueError("This node is not a list")

        return self._resolve_item(self._response_data[index], self._query_tree_node)  # type: ignore # returned value could be None, but to make static checker happy we ignore it

    def __iter__(self):
        if not isinstance(self._response_data, list):
            raise ValueError("This node is not a list")

        for item in self._response_data:
            yield self._resolve_item(item, self._query_tree_node)

    def _resolve_item(
        self, item, query_tree_node
    ) -> Union[InteractiveItemTypeT, "AQLResponseProxy[InteractiveItemTypeT]", None]:
        if item is None:
            return None

        if isinstance(item, list):
            return AQLResponseProxy[InteractiveItemTypeT](
                item, self._web_driver, query_tree_node, self._query_data
            )

        if isinstance(query_tree_node, IdNode) or isinstance(query_tree_node, IdListNode):
            # If query_data() was called, return the data directly without resolving it into a web element locator
            if self._query_data:
                return item

            interactive_element = self._web_driver._locate_interactive_element(item)
            trail_logger.add_event(f"Resolved to {interactive_element}")

            return interactive_element

        return AQLResponseProxy[InteractiveItemTypeT](
            item, self._web_driver, query_tree_node, self._query_data
        )

    def __len__(self):
        if self._response_data is None:
            return 0
        return len(self._response_data)

    def __str__(self):
        return json.dumps(self._response_data, indent=2)

    def to_data(self) -> dict:
        """Converts the response data into a structured dictionary based on the query tree.

        Returns:
        --------
        dict: A structured dictionary representing the processed response data, with fact nodes replaced by name (values) from the response data. It will have the following structure:

        ```py
        {
        "query_field": "text content of the corresponding web element"
        }
        ```
        """
        if self._query_data:
            return self._response_data

        res = self._to_data_node(self._response_data, self._query_tree_node)
        if not isinstance(res, dict):
            raise TypeError("Root node must be a container node")
        return res

    def _to_data_node(self, response_data, query_tree_node) -> Union[dict, list, str, None]:
        if isinstance(query_tree_node, ContainerListNode):
            return self._to_data_container_list_node(response_data, query_tree_node)
        elif isinstance(query_tree_node, ContainerNode):
            return self._to_data_container_node(response_data, query_tree_node)
        elif isinstance(query_tree_node, IdListNode):
            return self._to_data_id_list_node(response_data)
        elif isinstance(query_tree_node, IdNode):
            return self._to_data_id_node(response_data)
        else:
            raise TypeError("Unsupported query tree node type")

    def _to_data_container_node(self, response_data: dict, query_tree_node: ContainerNode) -> dict:
        data_dict = {}
        for child_name, child_data in response_data.items():
            child_query_tree = query_tree_node.get_child_by_name(child_name)
            data_dict[child_name] = self._to_data_node(child_data, child_query_tree)
        return data_dict

    def _to_data_container_list_node(
        self, response_data: dict, query_tree_node: ContainerListNode
    ) -> list:
        return [self._to_data_container_node(item, query_tree_node) for item in response_data]

    def _to_data_id_node(self, response_data: dict) -> Union[dict, str, None]:
        if response_data is None:
            return None
        name = response_data.get("name")
        if not name or not name.strip():
            web_element = self._web_driver._locate_interactive_element(response_data)
            if not web_element:
                log.warning(f"Could not locate web element for item {response_data}")
                return None
            name = self._web_driver.get_text_content(web_element)
        return name

    def _to_data_id_list_node(self, response_data: list) -> list:
        return [node for item in response_data if (node := self._to_data_id_node(item)) is not None]
