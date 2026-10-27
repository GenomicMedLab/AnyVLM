from http import HTTPStatus
from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException

from anyvlm.auth.jwt_validator import JWTValidator


def _request(authorization: str | None) -> MagicMock:
    request = MagicMock()
    request.headers.get.return_value = authorization or ""
    return request


def test_decodes_valid_bearer_token():
    claims = {"client_id": "client-one", "azp": "client-one"}
    with (
        patch("anyvlm.auth.jwt_validator.get_config") as get_config,
        patch("anyvlm.auth.jwt_validator.jwt.decode", return_value=claims) as decode,
    ):
        get_config.return_value.base_vlm_network_url = "https://issuer.example"

        decoded_claims = JWTValidator().validate_and_decode_token(
            _request("Bearer encoded-token")
        )

    assert decoded_claims == claims
    decode.assert_called_once_with(
        jwt="encoded-token",
        algorithms=["RS256"],
        issuer="https://issuer.example",
        options={
            "verify_signature": False,
            "verify_iss": True,
            "verify_exp": True,
            "require": ["azp"],
        },
    )


@pytest.mark.parametrize(
    ("authorization", "detail"),
    [
        (None, "Invalid authorization header"),
        ("Bearer", "Invalid authorization header"),
        ("Basic encoded-token", "Invalid token scheme"),
    ],
)
def test_rejects_invalid_authorization_headers(authorization: str | None, detail: str):
    with pytest.raises(HTTPException) as error:
        JWTValidator().validate_and_decode_token(_request(authorization))

    assert error.value.status_code == HTTPStatus.FORBIDDEN
    assert error.value.detail == detail


def test_translates_jwt_errors_to_forbidden():
    with (
        patch(
            "anyvlm.auth.jwt_validator.jwt.decode",
            side_effect=jwt.InvalidTokenError("expired"),
        ),
        pytest.raises(HTTPException) as exc_info,
    ):
        JWTValidator().validate_and_decode_token(_request("Bearer token"))

    assert exc_info.value.status_code == HTTPStatus.FORBIDDEN
    assert exc_info.value.detail == "Invalid token: expired"
