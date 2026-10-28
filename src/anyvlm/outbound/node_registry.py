"""Retrieves information about other nodes on the VLM Network"""

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http import HTTPMethod, HTTPStatus

from requests import Response

from anyvlm.config import Settings, get_config
from anyvlm.outbound.vlm_client import VlmClient
from anyvlm.utils.exceptions import NodeRetrievalError


@dataclass
class VlmNode:
    """Houses metadata about a VLM Network node"""

    client_id: str
    client_name: str
    match_url: str | None


class NodeRegistry:
    """Manages the list of other known nodes on the VLM Network"""

    NODES_REFRESH_INTERVAL: timedelta = timedelta(hours=24)
    NODES_RESULTS_PAGE_SIZE: int = (
        100  # Auth0's node list is paginated w/ a max of 100 results per page
    )

    _nodes: list[VlmNode]
    _nodes_expiry: datetime
    _vlm_client: VlmClient

    def __init__(self, vlm_client: VlmClient) -> None:
        """Initializes a list of all other nodes currently on the VLM Network

        :param vlm_client: A 'VlmClient' instance used to send outbound HTTP requests to the VLM Network
        """
        self._vlm_client = vlm_client

        settings: Settings = get_config()
        self.NODES_REQUEST_URL: str = settings.base_vlm_network_url + "api/v2/clients"

        self.refresh_nodes()

    def get_nodes(self) -> list[VlmNode]:
        """Get a list of known nodes on the VLM network. Uses the cached list if cache is set & unexpired.
        See 'self.refresh_nodes()' for list of possible Exceptions that may be raised.
        """
        now: datetime = datetime.now(tz=UTC)
        if (not self._nodes_expiry) or (now >= self._nodes_expiry):
            self.refresh_nodes()
        return self._nodes

    def refresh_nodes(self) -> None:
        """Retrieve an updated list of known nodes on the VLM Network + reset the expiry time for the next check

        :raises: `NodeRetrievalError` if request to the VLM Network to obtain the list of registered nodes fails
        :raises: `TokenRetrievalError` if unable to obtain a JWT token to send the request to the VLM Network
        """
        refreshed_nodes: list[VlmNode] = []
        page = 0
        while True:
            response: Response = self._vlm_client.request(
                method_type=HTTPMethod.GET,
                url=(
                    f"{self.NODES_REQUEST_URL}?page={page}"
                    f"&per_page={self.NODES_RESULTS_PAGE_SIZE}"
                ),
            )

            if response.status_code != HTTPStatus.OK:
                error_message: str = "Unable to fetch VLM Network nodes from Auth0"
                raise NodeRetrievalError(error_message)

            data = response.json()
            refreshed_nodes.extend(
                VlmNode(
                    client_id=entry.get("client_id", ""),
                    client_name=entry.get("name", ""),
                    match_url=entry.get("client_metadata", {}).get("match_url"),
                )
                for entry in data
                if entry.get("client_id")
                != os.environ.get("VLM_CLIENT_ID")  # exclude our own node
            )

            # we know we've hit the last page if the number of results is less than our requested limit
            if len(data) < self.NODES_RESULTS_PAGE_SIZE:
                break
            page += 1

        # Update the cache only after all pages have been retrieved successfully.
        self._nodes = refreshed_nodes

        self._nodes_expiry = datetime.now(tz=UTC) + self.NODES_REFRESH_INTERVAL
