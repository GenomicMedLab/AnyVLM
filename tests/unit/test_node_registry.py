from datetime import UTC, datetime, timedelta
from http import HTTPMethod, HTTPStatus
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from anyvlm.outbound.node_registry import NodeRegistry
from anyvlm.utils.exceptions import NodeRetrievalError


def _response(
    status_code: HTTPStatus = HTTPStatus.OK, data: list[Any] | None = None
) -> MagicMock:
    response: MagicMock = MagicMock()
    response.status_code = status_code
    response.json.return_value = data or []
    return response


def test_loads_nodes_and_exposes_client_ids() -> None:
    client: MagicMock = MagicMock()
    client.request.return_value = _response(
        data=[
            {
                "client_id": "client-one",
                "name": "One",
                "client_metadata": {"match_url": "https://one.example"},
            },
            {"client_id": "client-two", "name": "Two"},
        ]
    )

    with patch("anyvlm.outbound.node_registry.get_config") as get_config:
        get_config.return_value.base_vlm_network_url = "https://network.example"
        registry: NodeRegistry = NodeRegistry(vlm_client=client)

    assert [node.client_id for node in registry.get_nodes()] == [
        "client-one",
        "client-two",
    ]
    assert registry.get_node_ids() == ["client-one", "client-two"]
    client.request.assert_called_once_with(
        method_type=HTTPMethod.GET,
        url="https://network.example/api/v2/clients",
    )


def test_refresh_nodes_replaces_cached_nodes() -> None:
    client: MagicMock = MagicMock()
    client.request.side_effect = [
        _response(data=[{"client_id": "old"}]),
        _response(data=[{"client_id": "new"}]),
    ]

    with patch("anyvlm.outbound.node_registry.get_config") as get_config:
        get_config.return_value.base_vlm_network_url = "https://network.example"
        registry: NodeRegistry = NodeRegistry(vlm_client=client)
        registry.refresh_nodes()

    assert registry.get_node_ids() == ["new"]


def test_refreshes_expired_cache_on_get_nodes() -> None:
    client: MagicMock = MagicMock()
    client.request.side_effect = [
        _response(data=[{"client_id": "initial"}]),
        _response(data=[{"client_id": "refreshed"}]),
    ]

    with patch("anyvlm.outbound.node_registry.get_config") as get_config:
        get_config.return_value.base_vlm_network_url = "https://network.example"
        registry: NodeRegistry = NodeRegistry(vlm_client=client)
        registry._nodes_expiry = datetime.now(tz=UTC) - timedelta(seconds=1)
        assert registry.get_node_ids() == ["refreshed"]

    assert client.request.call_count == 2


def test_raises_when_node_retrieval_fails() -> None:
    client: MagicMock = MagicMock()
    client.request.return_value = _response(status_code=HTTPStatus.SERVICE_UNAVAILABLE)

    with patch("anyvlm.outbound.node_registry.get_config") as get_config:
        get_config.return_value.base_vlm_network_url = "https://network.example"
        with pytest.raises(NodeRetrievalError, match="Unable to fetch"):
            NodeRegistry(vlm_client=client)
