import time
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from anyvlm.auth.token_provider import TokenProvider


def _token_response(
    token: str = "test-token", expires_in: int = 3600, delay: bool = False
) -> MagicMock:
    if delay:
        time.sleep(3)

    response: MagicMock = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "access_token": token,
        "expires_in": expires_in,
    }
    return response


def test_fetches_token_on_initialization() -> None:
    with patch("anyvlm.auth.token_provider.requests.post") as mock_post:
        mock_post.return_value = _token_response()

        provider: TokenProvider = TokenProvider()

        assert provider.get_token() == "test-token"
        mock_post.assert_called_once()


def test_fetches_new_token_when_current_token_is_expired() -> None:
    with patch("anyvlm.auth.token_provider.requests.post") as mock_post:
        mock_post.side_effect = [
            _token_response(token="initial-token"),
            _token_response(token="refreshed-token"),
        ]
        provider: TokenProvider = TokenProvider()
        provider._token_expiry = datetime.now(tz=UTC) - timedelta(seconds=1)  # pyright: ignore[reportPrivateUsage]

        assert provider.get_token() == "refreshed-token"
        assert mock_post.call_count == 2


def test_does_not_fetch_new_token_when_current_token_is_not_expired() -> None:
    with patch("anyvlm.auth.token_provider.requests.post") as mock_post:
        mock_post.side_effect = [
            _token_response(token="initial-token"),
            _token_response(
                token="refreshed-token"
            ),  # this token should NOT be returned, since the call should only be made once
        ]
        provider: TokenProvider = TokenProvider()

        assert provider.get_token() == "initial-token"
        assert (
            provider.get_token() == "initial-token"
        )  # a second call should still return the same initial token
        mock_post.assert_called_once()


def test_token_provider_does_not_extend_token_validity_after_delayed_response() -> None:
    with patch("anyvlm.auth.token_provider.requests.post") as mock_post:
        mock_post.side_effect = [
            # Initial token will arrive already expired due to response delay
            _token_response(token="initial-token", expires_in=1, delay=True),
            _token_response(token="refreshed-token"),
        ]

        # TokenProvider is unknowingly initialized w/ expired token
        provider: TokenProvider = TokenProvider()

        # Call to 'get_token' should trigger token refresh
        assert provider.get_token() == "refreshed-token"
        assert mock_post.call_count == 2
