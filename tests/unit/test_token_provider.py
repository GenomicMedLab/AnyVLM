from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from anyvlm.auth.token_provider import TokenProvider


def _token_response(token: str = "test-token", expires_in: int = 3600) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "access_token": token,
        "expires_in": expires_in,
    }
    return response


def test_fetches_token_on_initialization():
    with patch("anyvlm.auth.token_provider.requests.post") as mock_post:
        mock_post.return_value = _token_response()

        provider = TokenProvider()

        assert provider.get_token() == "test-token"
        mock_post.assert_called_once()


def test_fetches_new_token_when_current_token_is_expired():
    with patch("anyvlm.auth.token_provider.requests.post") as mock_post:
        mock_post.side_effect = [
            _token_response(token="initial-token"),
            _token_response(token="refreshed-token"),
        ]
        provider = TokenProvider()
        provider._token_expiry = datetime.now(tz=UTC) - timedelta(seconds=1)  # pyright: ignore[reportPrivateUsage]

        assert provider.get_token() == "refreshed-token"
        assert mock_post.call_count == 2


def test_does_not_fetch_new_token_when_current_token_is_not_expired():
    with patch("anyvlm.auth.token_provider.requests.post") as mock_post:
        mock_post.side_effect = [
            _token_response(token="initial-token"),
            _token_response(
                token="refreshed-token"
            ),  # this token should NOT be returned, since the call should only be made once
        ]
        provider = TokenProvider()

        assert provider.get_token() == "initial-token"
        assert (
            provider.get_token() == "initial-token"
        )  # a second call should still return the same token
        mock_post.assert_called_once()
