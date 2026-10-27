from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from anyvlm.main import authenticate_inbound_request
from anyvlm.utils.exceptions import AuthError, AuthErrorReason


def test_authenticate_inbound_request_delegates_to_app_authenticator() -> None:
    request = MagicMock()
    request.app.state.request_authenticator = MagicMock()

    authenticate_inbound_request(request)

    request.app.state.request_authenticator.authenticate.assert_called_once_with(
        request
    )


def test_authenticate_inbound_request_maps_authentication_errors_to_http_exceptions() -> (
    None
):
    request = MagicMock()
    request.app.state.request_authenticator.authenticate.side_effect = AuthError(
        AuthErrorReason.UNRECOGNIZED_NODE
    )

    with pytest.raises(HTTPException) as error:
        authenticate_inbound_request(request)

    assert error.value.status_code == 403
    assert error.value.detail == AuthErrorReason.UNRECOGNIZED_NODE
    assert error.value.headers is None
