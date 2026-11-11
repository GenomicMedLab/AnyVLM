from datetime import UTC, datetime, timedelta
from http import HTTPMethod
from unittest.mock import MagicMock, patch

import pytest

from anyvlm.auth.token_provider import TokenProvider
from anyvlm.outbound.vlm_client import VLMClient
from anyvlm.utils.exceptions import TokenRetrievalError


def _token_response(token: str) -> MagicMock:
    response: MagicMock = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "access_token": token,
        "expires_in": 3600,
    }
    return response


def test_request_includes_cached_token_in_authorization_header() -> None:
    with patch("anyvlm.auth.token_provider.requests.post") as mock_post:
        mock_post.return_value = _token_response(token="cached-token")
        token_provider: TokenProvider = TokenProvider()

        with patch("anyvlm.outbound.vlm_client.requests.request") as mock_request:
            VLMClient(token_provider).request(
                method_type=HTTPMethod.GET,
                url="https://example.com/variants",
                request_body={"variant": "test"},
            )

    mock_request.assert_called_once_with(
        method=HTTPMethod.GET,
        url="https://example.com/variants",
        headers={"Authorization": "Bearer cached-token"},
        json={"variant": "test"},
        timeout=10,
    )
    mock_post.assert_called_once()


def test_request_includes_refreshed_token_in_authorization_header() -> None:
    with patch("anyvlm.auth.token_provider.requests.post") as mock_post:
        mock_post.side_effect = [
            _token_response(token="cached-token"),
            _token_response(token="refreshed-token"),
        ]
        token_provider: TokenProvider = TokenProvider()
        token_provider._token_expiry = datetime.now(tz=UTC) - timedelta(seconds=1)  # pyright: ignore[reportPrivateUsage]

        with patch("anyvlm.outbound.vlm_client.requests.request") as mock_request:
            VLMClient(token_provider).request(
                method_type=HTTPMethod.POST, url="https://example.com/variants"
            )

    mock_request.assert_called_once_with(
        method=HTTPMethod.POST,
        url="https://example.com/variants",
        headers={"Authorization": "Bearer refreshed-token"},
        json=None,
        timeout=10,
    )
    assert mock_post.call_count == 2


def test_request_does_not_send_request_when_token_retrieval_fails() -> None:
    token_provider: MagicMock = MagicMock(spec=TokenProvider)
    token_provider.get_token.side_effect = TokenRetrievalError(
        "Unable to fetch bearer token from Auth0"
    )
    client: VLMClient = VLMClient(token_provider)

    with (
        patch("anyvlm.outbound.vlm_client.requests.request") as mock_request,
        pytest.raises(TokenRetrievalError),
    ):
        client.request(method_type=HTTPMethod.GET, url="https://example.com/variants")

    mock_request.assert_not_called()
