from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from anyvlm.main import authenticate_inbound_request
from anyvlm.utils.exceptions import AuthenticationError


def test_authenticate_inbound_request_delegates_to_app_authenticator():
    request = MagicMock()
    request.app.state.request_authenticator = MagicMock()

    authenticate_inbound_request(request)

    request.app.state.request_authenticator.authenticate.assert_called_once_with(
        request
    )


def test_authenticate_inbound_request_maps_authentication_errors_to_401():
    request = MagicMock()
    request.app.state.request_authenticator.authenticate.side_effect = (
        AuthenticationError("not a known node")
    )

    with pytest.raises(HTTPException) as error:
        authenticate_inbound_request(request)

    assert error.value.status_code == 401
    assert error.value.detail == "not a known node"
