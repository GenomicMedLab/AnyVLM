from datetime import UTC, datetime, timedelta
from http import HTTPMethod, HTTPStatus
from typing import Any
from unittest.mock import MagicMock, call

import pytest

from anyvlm.outbound.node_registry import NodeRegistry
from anyvlm.utils.constants import VLM_NETWORK_NODES_REQUEST_URL
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

    registry: NodeRegistry = NodeRegistry(vlm_client=client)

    assert [node.client_id for node in registry.get_nodes()] == [
        "client-one",
        "client-two",
    ]
    client.request.assert_called_once_with(
        method_type=HTTPMethod.GET,
        url=VLM_NETWORK_NODES_REQUEST_URL + "?page=0&per_page=100",
    )


def test_loads_nodes_from_multiple_pages() -> None:
    client: MagicMock = MagicMock()
    client.request.side_effect = [
        _response(data=[{"client_id": "client-one"}] * 100),
        _response(data=[{"client_id": "client-two"}]),
    ]

    registry: NodeRegistry = NodeRegistry(vlm_client=client)

    assert [node.client_id for node in registry.get_nodes()] == [
        "client-one",
    ] * 100 + ["client-two"]
    assert client.request.call_args_list == [
        call(
            method_type=HTTPMethod.GET,
            url=VLM_NETWORK_NODES_REQUEST_URL + "?page=0&per_page=100",
        ),
        call(
            method_type=HTTPMethod.GET,
            url=VLM_NETWORK_NODES_REQUEST_URL + "?page=1&per_page=100",
        ),
    ]


def test_refresh_nodes_replaces_cached_nodes() -> None:
    client: MagicMock = MagicMock()
    client.request.side_effect = [
        _response(data=[{"client_id": "old"}]),
        _response(data=[{"client_id": "new"}]),
    ]

    registry: NodeRegistry = NodeRegistry(vlm_client=client)
    registry.refresh_nodes()

    assert [node.client_id for node in registry.get_nodes()] == ["new"]


def test_refreshes_expired_cache_on_get_nodes() -> None:
    client: MagicMock = MagicMock()
    client.request.side_effect = [
        _response(data=[{"client_id": "initial"}]),
        _response(data=[{"client_id": "refreshed"}]),
    ]

    registry: NodeRegistry = NodeRegistry(vlm_client=client)
    registry._nodes_expiry = datetime.now(tz=UTC) - timedelta(seconds=1)  # pyright: ignore[reportPrivateUsage]
    assert [node.client_id for node in registry.get_nodes()] == ["refreshed"]

    assert client.request.call_count == 2


def test_raises_when_node_retrieval_fails() -> None:
    client: MagicMock = MagicMock()
    client.request.return_value = _response(status_code=HTTPStatus.SERVICE_UNAVAILABLE)

    with pytest.raises(NodeRetrievalError, match="Unable to fetch"):
        NodeRegistry(vlm_client=client)


def test_registry_excludes_self_when_other_nodes_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # this is our own node's client_id
    self_vlm_client_id = "self-client"
    monkeypatch.setenv("VLM_CLIENT_ID", self_vlm_client_id)

    client: MagicMock = MagicMock()
    client.request.return_value = _response(
        data=[
            {
                "client_id": "client-one",
                "name": "One",
                "client_metadata": {"match_url": "https://one.example"},
            },
            {
                "client_id": self_vlm_client_id,
                "name": "GenomicMedLabs' AnyVLM instance",
            },
        ]
    )

    registry: NodeRegistry = NodeRegistry(vlm_client=client)

    assert [node.client_id for node in registry.get_nodes()] == [
        "client-one",
    ]
    client.request.assert_called_once_with(
        method_type=HTTPMethod.GET,
        url=VLM_NETWORK_NODES_REQUEST_URL + "?page=0&per_page=100",
    )


def test_registry_returns_empty_list_when_only_self_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # this is our own node's client_id
    self_vlm_client_id = "self-client"
    monkeypatch.setenv("VLM_CLIENT_ID", self_vlm_client_id)

    client: MagicMock = MagicMock()
    client.request.return_value = _response(
        data=[
            {
                "client_id": self_vlm_client_id,
                "name": "GenomicMedLabs' AnyVLM instance",
            },
        ]
    )

    registry: NodeRegistry = NodeRegistry(vlm_client=client)

    assert [node.client_id for node in registry.get_nodes()] == []
    client.request.assert_called_once_with(
        method_type=HTTPMethod.GET,
        url=VLM_NETWORK_NODES_REQUEST_URL + "?page=0&per_page=100",
    )
