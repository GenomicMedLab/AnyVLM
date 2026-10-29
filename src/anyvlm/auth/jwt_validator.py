"""Handles validating and decoding JWT tokens"""

from typing import Any

import jwt
from fastapi import Request

from anyvlm.config import Settings, get_config
from anyvlm.utils.exceptions import AuthError, AuthErrorReason


class JWTValidator:
    """Handles validating and decoding JWT tokens"""

    def validate_and_decode_token(self, request: Request) -> dict[str, Any]:
        """Validate and decode tokens from inbound requests.

        :param request: The inbound request containing the token to be validated/decoded
        :return: The decoded token claims
        :raises: `AuthError`, if unable to validate or decode the request's token
        """
        configs: Settings = get_config()

        auth_header: str | None = request.headers.get("Authorization")
        if not auth_header:
            raise AuthError(error_reason=AuthErrorReason.MISSING_AUTH_HEADER)
        try:
            scheme, token = auth_header.strip().split(sep=" ")
        except ValueError as e:
            raise AuthError(error_reason=AuthErrorReason.MALFORMED_AUTH_HEADER) from e
        if scheme.lower() != "bearer":
            raise AuthError(error_reason=AuthErrorReason.INVALID_SCHEMA)

        try:
            decoded_claims: dict[str, Any] = jwt.decode(
                jwt=token,
                algorithms=["RS256"],
                issuer=configs.base_vlm_network_url,
                audience=configs.vlm_network_audience_url,
                options={
                    "verify_signature": False,  # See PR comment for more details: https://github.com/GenomicMedLab/AnyVLM/pull/120
                    "verify_iss": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "require": ["iss", "exp", "azp", "aud"],
                },
            )
        except jwt.InvalidTokenError as e:
            raise AuthError(error_reason=AuthErrorReason.INVALID_TOKEN) from e

        try:
            int(decoded_claims["exp"])  # catch malformed/empty 'exp' values
        except TypeError as e:
            raise AuthError(error_reason=AuthErrorReason.INVALID_TOKEN) from e

        return decoded_claims
