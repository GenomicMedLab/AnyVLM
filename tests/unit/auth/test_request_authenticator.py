from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from anyvlm.auth.request_authenticator import RequestAuthenticator
from anyvlm.utils.exceptions import AuthError, AuthErrorReason


def _authenticator(
    claims: dict[Any, Any], node_ids: list[str]
) -> tuple[RequestAuthenticator, MagicMock, MagicMock]:
    jwt_validator: MagicMock = MagicMock()
    jwt_validator.validate_and_decode_token.return_value = claims

    node_registry: MagicMock = MagicMock()
    node_registry.get_node_ids.return_value = node_ids

    return (
        RequestAuthenticator(jwt_validator=jwt_validator, node_registry=node_registry),
        jwt_validator,
        node_registry,
    )


def test_authenticates_known_node_without_refreshing_registry() -> None:
    request_authenticator, jwt_validator, node_registry = _authenticator(
        claims={"azp": "client-one"}, node_ids=["client-one"]
    )

    request_authenticator.authenticate(request=MagicMock())

    jwt_validator.validate_and_decode_token.assert_called_once()
    node_registry.refresh_nodes.assert_not_called()
    node_registry.get_node_ids.assert_called_once()


def test_refreshes_registry_when_node_is_not_cached() -> None:
    request_authenticator, _, node_registry = _authenticator(
        claims={"azp": "client-one"}, node_ids=[]
    )
    node_registry.get_node_ids.side_effect = [[], ["client-one"]]

    request_authenticator.authenticate(request=MagicMock())

    node_registry.refresh_nodes.assert_called_once()
    assert node_registry.get_node_ids.call_count == 2


def test_rejects_unknown_node_after_refresh() -> None:
    request_, _, node_registry = _authenticator(claims={"azp": "unknown"}, node_ids=[])

    with pytest.raises(
        AuthError,
        match=AuthErrorReason.UNRECOGNIZED_NODE,
    ):
        request_.authenticate(request=MagicMock())

    node_registry.refresh_nodes.assert_called_once()


def test_rejects_unknown_clients_without_refreshing_during_cooldown() -> None:
    request_authenticator, jwt_validator, node_registry = _authenticator(
        claims={"azp": "client-one"}, node_ids=[]
    )
    request_authenticator.last_node_refresh = datetime.now(tz=UTC) - timedelta(
        seconds=request_authenticator.NODE_REGISTRY_REFRESH_COOLDOWN_SECONDS + 1
    )
    jwt_validator.validate_and_decode_token.side_effect = [
        {"azp": "client-one"},
        {"azp": "client-two"},
    ]

    for _ in range(2):
        with pytest.raises(
            AuthError,
            match=AuthErrorReason.UNRECOGNIZED_NODE,
        ):
            request_authenticator.authenticate(request=MagicMock())

    node_registry.refresh_nodes.assert_called_once()


def test_refreshes_registry_again_after_cooldown() -> None:
    request_authenticator, _, node_registry = _authenticator(
        claims={"azp": "unknown"}, node_ids=[]
    )
    request = MagicMock()

    with pytest.raises(
        AuthError,
        match=AuthErrorReason.UNRECOGNIZED_NODE,
    ):
        request_authenticator.authenticate(request=request)

    request_authenticator.last_node_refresh = datetime.now(tz=UTC) - timedelta(
        seconds=request_authenticator.NODE_REGISTRY_REFRESH_COOLDOWN_SECONDS + 1
    )

    with pytest.raises(
        AuthError,
        match=AuthErrorReason.UNRECOGNIZED_NODE,
    ):
        request_authenticator.authenticate(request=request)

    assert node_registry.refresh_nodes.call_count == 2


@pytest.mark.parametrize(argnames="claims", argvalues=[{}, {"azp": ""}, {"azp": None}])
def test_rejects_missing_client_identity(claims: dict[Any, Any]) -> None:
    request_, _, node_registry = _authenticator(claims, node_ids=[])

    with pytest.raises(AuthError, match=AuthErrorReason.MISSING_CLIENT_ID):
        request_.authenticate(request=MagicMock())

    node_registry.get_node_ids.assert_not_called()
    node_registry.refresh_nodes.assert_not_called()
