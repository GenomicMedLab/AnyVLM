"""Handles validating and decoding JWT tokens"""

from typing import Any

import jwt
from fastapi import Request

from anyvlm.config import get_config
from anyvlm.utils.exceptions import AuthError, AuthErrorReason


class JWTValidator:
    """Handles validating and decoding JWT tokens"""

    def validate_and_decode_token(self, request: Request) -> dict[str, Any]:
        """Validate and decode tokens from inbound requests.

        :param request: The inbound request containing the token to be validated/decoded
        :return: The decoded token claims
        :raises: `AuthError`, if unable to validate or decode the request's token
        """
        try:
            scheme, token = (
                request.headers.get("Authorization", "").strip().split(sep=" ")
            )
        except ValueError as e:
            raise AuthError(error_reason=AuthErrorReason.INVALID_HEADER) from e
        if scheme.lower() != "bearer":
            raise AuthError(error_reason=AuthErrorReason.INVALID_SCHEMA)

        try:
            decoded_claims: dict[str, Any] = jwt.decode(
                jwt=token,
                algorithms=["RS256"],
                issuer=get_config().base_vlm_network_url,
                options={
                    "verify_signature": False,  # See PR comment for more details: https://github.com/GenomicMedLab/AnyVLM/pull/120
                    "verify_iss": True,
                    "verify_exp": True,
                    "require": ["iss", "exp", "azp"],
                },
            )
        except jwt.InvalidTokenError as e:
            raise AuthError(error_reason=AuthErrorReason.INVALID_TOKEN) from e

        return decoded_claims
