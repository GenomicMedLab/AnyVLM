"""Test AuthManager behavior."""

from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import Any

import pytest
from fastapi import HTTPException, Request

from anyvlm.restapi import auth_manager
from anyvlm.restapi.auth_manager import AuthManager, VlmNetworkNodeMetadata
from anyvlm.utils.exceptions import Auth0Error


class MockResponse:
    """Minimal requests.Response stand-in for AuthManager tests."""

    def __init__(self, status_code: int, data: object) -> None:
        self.status_code = status_code
        self._data = data

    def json(self) -> object:
        return self._data


@pytest.fixture
def auth0_success(monkeypatch: pytest.MonkeyPatch) -> tuple[list[Any], list[Any]]:
    """Patch successful Auth0 token and client-list responses."""
    post_calls: list[Any] = []
    get_calls: list[Any] = []
    nodes: list[dict[str, str | dict[str, str]] | dict[str, str | dict[Any, Any]]] = [
        {
            "client_id": "client-1",
            "name": "Node One",
            "client_metadata": {"match_url": "https://node-one.example/match"},
        },
        {
            "client_id": "client-2",
            "name": "Node Two",
            "client_metadata": {},
        },
    ]

    monkeypatch.setenv(name="VLM_CLIENT_ID", value="test-client")
    monkeypatch.setenv(name="VLM_CLIENT_SECRET", value="test-secret")

    def post(*, url: str, json: dict[str, str], timeout: int) -> MockResponse:
        post_calls.append({"url": url, "json": json, "timeout": timeout})
        return MockResponse(
            status_code=HTTPStatus.OK,
            data={"access_token": f"token-{len(post_calls)}", "expires_in": 60},
        )

    def get(*, url: str, headers: dict[str, str], timeout: int) -> MockResponse:
        get_calls.append({"url": url, "headers": headers, "timeout": timeout})
        return MockResponse(status_code=HTTPStatus.OK, data=nodes)

    monkeypatch.setattr(auth_manager.requests, "post", post)
    monkeypatch.setattr(auth_manager.requests, "get", get)

    return post_calls, get_calls


def build_auth_manager() -> AuthManager:
    """Build AuthManager instance without calling __init__."""
    return object.__new__(AuthManager)


def build_request(authorization: str) -> Request:
    """Build a Request with an Authorization header."""
    return Request(
        scope={
            "type": "http",
            "method": "GET",
            "path": "/anyvlm/variant_counts",
            "headers": [(b"authorization", authorization.encode())],
        }
    )


def test_init_fetches_token_and_known_nodes(auth0_success: tuple[list[Any], list[Any]]):
    post_calls, get_calls = auth0_success

    manager: AuthManager = AuthManager()

    assert manager.get_token() == "token-1"
    assert manager.get_known_nodes() == [
        VlmNetworkNodeMetadata(
            client_id="client-1",
            client_name="Node One",
            match_url="https://node-one.example/match",
        ),
        VlmNetworkNodeMetadata(
            client_id="client-2", client_name="Node Two", match_url=None
        ),
    ]
    assert post_calls == [
        {
            "url": AuthManager.TOKEN_REQUEST_URL,
            "json": {
                "client_id": "test-client",
                "client_secret": "test-secret",
                "audience": AuthManager.AUDIENCE,
                "grant_type": "client_credentials",
            },
            "timeout": 10,
        }
    ]
    assert get_calls == [
        {
            "url": AuthManager.KNOWN_NODES_REQUEST_URL,
            "headers": {"Authorization": "Bearer token-1"},
            "timeout": 10,
        }
    ]


def test_get_token_uses_cached_token_before_expiry(
    auth0_success: tuple[list[Any], list[Any]],
) -> None:
    post_calls, _ = auth0_success
    manager: AuthManager = AuthManager()

    assert manager.get_token() == "token-1"

    assert len(post_calls) == 1


def test_get_token_refreshes_expired_token(
    auth0_success: tuple[list[Any], list[Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    post_calls, _ = auth0_success
    manager: AuthManager = AuthManager()
    monkeypatch.setattr(
        manager, "_token_expiry", datetime.now(tz=UTC) - timedelta(seconds=1)
    )

    assert manager.get_token() == "token-2"

    assert len(post_calls) == 2


def test_get_known_nodes_refreshes_expired_known_nodes(
    auth0_success: tuple[list[Any], list[Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    _, get_calls = auth0_success
    manager: AuthManager = AuthManager()
    monkeypatch.setattr(
        manager,
        "_known_nodes_expiry",
        datetime.now(tz=UTC) - timedelta(seconds=1),
    )

    assert manager.get_known_nodes()[0].client_name == "Node One"

    assert len(get_calls) == 2


def test_refresh_token_raises_auth0_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        auth_manager.requests,
        "post",
        lambda **_: MockResponse(status_code=HTTPStatus.UNAUTHORIZED, data={}),
    )
    manager = build_auth_manager()

    with pytest.raises(Auth0Error, match="Unable to fetch bearer token from Auth0"):
        manager.get_token()


def test_refresh_known_nodes_raises_auth0_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        auth_manager.requests,
        "post",
        lambda **_: MockResponse(
            status_code=HTTPStatus.OK,
            data={"access_token": "token", "expires_in": 60},
        ),
    )
    monkeypatch.setattr(
        auth_manager.requests,
        "get",
        lambda **_: MockResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, data={}),
    )

    with pytest.raises(
        Auth0Error, match="Unable to fetch known VLM Network nodes from Auth0"
    ):
        AuthManager()


def test_authenticate_request_accepts_known_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager: AuthManager = build_auth_manager()
    monkeypatch.setattr(
        manager,
        "_known_nodes",
        {"client-1": {"name": "Node One", "match_url": None}},
        raising=False,
    )

    def decode(**kwargs) -> dict[str, str]:
        assert kwargs["jwt"] == "test-token"
        assert kwargs["algorithms"] == ["RS256"]
        assert kwargs["issuer"] == AuthManager.BASE_VLM_AUTH_URL
        assert kwargs["options"] == {
            "verify_signature": False,
            "verify_iss": True,
            "verify_exp": True,
            "require": ["azp"],
        }
        return {"azp": "client-1"}

    monkeypatch.setattr(auth_manager.jwt, "decode", decode)

    assert (
        manager.authenticate_request(
            request=build_request(authorization="Bearer test-token")
        )
        is None
    )


@pytest.mark.parametrize(
    argnames=("authorization", "detail"),
    argvalues=[
        ("", "Invalid authorization header"),
        ("Bearer", "Invalid authorization header"),
        ("Basic test-token", "Invalid token scheme"),
    ],
)
def test_authenticate_request_rejects_invalid_authorization_header(
    authorization: str, detail: str
) -> None:
    manager: AuthManager = build_auth_manager()

    with pytest.raises(HTTPException) as exc_info:
        manager.authenticate_request(request=build_request(authorization))

    assert exc_info.value.status_code == HTTPStatus.FORBIDDEN
    assert exc_info.value.detail == detail


def test_authenticate_request_rejects_invalid_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager: AuthManager = build_auth_manager()

    def decode(**kwargs) -> dict[str, str]:
        raise auth_manager.jwt.InvalidTokenError("bad token")

    monkeypatch.setattr(auth_manager.jwt, "decode", decode)

    with pytest.raises(HTTPException) as exc_info:
        manager.authenticate_request(
            request=build_request(authorization="Bearer test-token")
        )

    assert exc_info.value.status_code == HTTPStatus.FORBIDDEN
    assert exc_info.value.detail == "Invalid token: bad token"


def test_authenticate_request_rejects_unknown_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager: AuthManager = build_auth_manager()
    monkeypatch.setattr(
        manager,
        "_known_nodes",
        {"client-1": {"name": "Node One", "match_url": None}},
        raising=False,
    )
    monkeypatch.setattr(
        auth_manager.jwt,
        "decode",
        lambda **_: {"azp": "unknown-client"},
    )

    with pytest.raises(HTTPException) as exc_info:
        manager.authenticate_request(
            request=build_request(authorization="Bearer test-token")
        )

    assert exc_info.value.status_code == HTTPStatus.FORBIDDEN
    assert exc_info.value.detail == "Unknown client ID"
