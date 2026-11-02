from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import Any
from unittest.mock import MagicMock, patch

import jwt
import pytest

from anyvlm.auth.jwt_validator import JWTValidator
from anyvlm.utils.constants import VLM_NETWORK_AUDIENCE_URL, VLM_NETWORK_ROOT_URL
from anyvlm.utils.exceptions import AuthError, AuthErrorReason


def _request(authorization: str | None) -> MagicMock:
    request: MagicMock = MagicMock()
    request.headers.get.return_value = authorization or ""
    return request


def test_decodes_valid_bearer_token() -> None:
    issuer: str = "https://issuer.example/"
    audience: str = issuer + "api"
    claims: dict[str, Any] = {
        "client_id": "client-one",
        "azp": "client-one",
        "iss": issuer,
        "aud": audience,
        "exp": 2_000_000_000,
    }
    with (
        patch("anyvlm.auth.jwt_validator.jwt.decode", return_value=claims) as decode,
    ):
        decoded_claims: dict[str, Any] = JWTValidator().validate_and_decode_token(
            request=_request(authorization="Bearer encoded-token")
        )

    assert decoded_claims == claims
    decode.assert_called_once_with(
        jwt="encoded-token",
        algorithms=["RS256"],
        issuer=VLM_NETWORK_ROOT_URL,
        audience=VLM_NETWORK_AUDIENCE_URL,
        options={
            "verify_signature": False,
            "verify_iss": True,
            "verify_exp": True,
            "verify_aud": True,
            "require": ["iss", "exp", "azp", "aud"],
        },
    )


@pytest.mark.parametrize(
    argnames=("authorization", "reason"),
    argvalues=[
        (None, AuthErrorReason.MISSING_AUTH_HEADER),  # no header
        (
            "Bearer",
            AuthErrorReason.MALFORMED_AUTH_HEADER,
        ),  # header that's missing the token
        (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIi",
            AuthErrorReason.MALFORMED_AUTH_HEADER,
        ),  # header that's missing the schema
        (
            "Basic encoded-token",
            AuthErrorReason.INVALID_SCHEMA,
        ),  # header w/ incorrect schema
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
    expired_token: str = jwt.encode(
        payload={
            "azp": "client-one",
            "iss": VLM_NETWORK_ROOT_URL,
            "aud": VLM_NETWORK_AUDIENCE_URL,
            "exp": datetime.now(tz=UTC) - timedelta(seconds=1),
        },
        key="unused-signing-key",
        algorithm="HS256",
    )

    with pytest.raises(AuthError) as error:
        JWTValidator().validate_and_decode_token(
            request=_request(authorization=f"Bearer {expired_token}")
        )

    assert error.value.error_reason == AuthErrorReason.INVALID_TOKEN
    assert error.value.code == HTTPStatus.UNAUTHORIZED
    assert error.value.header == {"WWW-Authenticate": 'Bearer error="invalid_token"'}


def test_rejects_incorrect_audience() -> None:
    token_with_wrong_audience: str = jwt.encode(
        payload={
            "azp": "client-one",
            "iss": VLM_NETWORK_ROOT_URL,
            "aud": VLM_NETWORK_ROOT_URL + "wrong-audience/",
            "exp": datetime.now(tz=UTC) - timedelta(seconds=1),
        },
        key="unused-signing-key",
        algorithm="HS256",
    )

    with pytest.raises(AuthError) as error:
        JWTValidator().validate_and_decode_token(
            request=_request(authorization=f"Bearer {token_with_wrong_audience}")
        )

    assert error.value.error_reason == AuthErrorReason.INVALID_TOKEN
    assert error.value.code == HTTPStatus.UNAUTHORIZED
    assert error.value.header == {"WWW-Authenticate": 'Bearer error="invalid_token"'}
