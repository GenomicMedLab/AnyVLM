from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import Any
from unittest.mock import MagicMock, patch

import jwt
import pytest

from anyvlm.auth.jwt_validator import JWTValidator
from anyvlm.utils.exceptions import AuthError, AuthErrorReason


def _request(authorization: str | None) -> MagicMock:
    request: MagicMock = MagicMock()
    request.headers.get.return_value = authorization or ""
    return request


def test_decodes_valid_bearer_token() -> None:
    claims: dict[str, Any] = {
        "client_id": "client-one",
        "azp": "client-one",
        "iss": "https://issuer.example",
        "exp": 2_000_000_000,
    }
    with (
        patch("anyvlm.auth.jwt_validator.get_config") as get_config,
        patch("anyvlm.auth.jwt_validator.jwt.decode", return_value=claims) as decode,
    ):
        get_config.return_value.base_vlm_network_url = "https://issuer.example/"

        decoded_claims: dict[str, Any] = JWTValidator().validate_and_decode_token(
            request=_request(authorization="Bearer encoded-token")
        )

    assert decoded_claims == claims
    decode.assert_called_once_with(
        jwt="encoded-token",
        algorithms=["RS256"],
        issuer="https://issuer.example/",
        options={
            "verify_signature": False,
            "verify_iss": True,
            "verify_exp": True,
            "require": ["iss", "exp", "azp"],
        },
    )


@pytest.mark.parametrize(
    argnames=("authorization", "reason"),
    argvalues=[
        (None, AuthErrorReason.MISSING_AUTH_HEADER),
        ("Bearer", AuthErrorReason.MALFORMED_AUTH_HEADER),
        ("Basic encoded-token", AuthErrorReason.INVALID_SCHEMA),
    ],
)
def test_rejects_invalid_authorization_headers(
    authorization: str | None, reason: AuthErrorReason
) -> None:
    with pytest.raises(AuthError) as error:
        JWTValidator().validate_and_decode_token(request=_request(authorization))

    assert error.value.error_reason == reason
    assert error.value.code == (
        HTTPStatus.UNAUTHORIZED
        if reason == AuthErrorReason.INVALID_SCHEMA
        else HTTPStatus.BAD_REQUEST
    )
    assert error.value.header == {"WWW-Authenticate": 'Bearer realm="AnyVLM"'}


def test_rejects_an_expired_token() -> None:
    issuer = "https://issuer.example/"
    expired_token = jwt.encode(
        {
            "azp": "client-one",
            "iss": issuer,
            "exp": datetime.now(tz=UTC) - timedelta(seconds=1),
        },
        key="unused-signing-key",
        algorithm="HS256",
    )

    get_config_patch = patch("anyvlm.auth.jwt_validator.get_config")
    get_config = get_config_patch.start()
    try:
        get_config.return_value.base_vlm_network_url = issuer

        with pytest.raises(AuthError) as error:
            JWTValidator().validate_and_decode_token(
                request=_request(authorization=f"Bearer {expired_token}")
            )
    finally:
        get_config_patch.stop()

    assert error.value.error_reason == AuthErrorReason.INVALID_TOKEN
    assert error.value.code == HTTPStatus.UNAUTHORIZED
    assert error.value.header == {"WWW-Authenticate": 'Bearer error="invalid_token"'}
