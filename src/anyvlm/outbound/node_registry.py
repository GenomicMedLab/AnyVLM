"""Retrieves information about other nodes on the VLM Network"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http import HTTPMethod, HTTPStatus

from anyvlm.config import Settings, get_config
from anyvlm.outbound.client import VlmClient
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

    _nodes: list[VlmNode]
    _nodes_expiry: datetime
    _vlm_client: VlmClient

    def __init__(self) -> None:  # noqa: D107
        self._vlm_client = VlmClient()

        settings: Settings = get_config()
        self.NODES_REQUEST_URL: str = settings.base_vlm_network_url + "/api/v2/clients"

        self._refresh_nodes()

    def get_nodes(self) -> list[VlmNode]:
        """Get a list of known nodes on the VLM network. Uses the cached list if cache is set & unexpired."""
        now: datetime = datetime.now(tz=UTC)
        if (not self._nodes) or (now >= self._nodes_expiry):
            self._refresh_nodes()
        return self._nodes

    def _refresh_nodes(self) -> None:
        """Retrieve an updated list of known nodes on the VLM Network + reset the expiry time for the next check"""
        response = self._vlm_client.request(
            method_type=HTTPMethod.GET, url=self.NODES_REQUEST_URL
        )

        if response.status_code == HTTPStatus.OK:
            self._known_nodes = []
        else:
            error_message: str = "Unable to fetch VLM Network nodes from Auth0"
            raise NodeRetrievalError(error_message)

        data = response.json()
        for entry in data:
            self._known_nodes.append(
                VlmNode(
                    client_id=entry.get("client_id", ""),
                    client_name=entry.get("name", ""),
                    match_url=entry.get("client_metadata", {}).get("match_url"),
                )
            )

        self._known_nodes_expiry: datetime = (
            datetime.now(tz=UTC) + self.NODES_REFRESH_INTERVAL
        )
