"""Handles validating and decoding JWT tokens"""

from http import HTTPStatus
from typing import Any

import jwt
from fastapi import HTTPException, Request

from anyvlm.config import get_config


class JWTValidator:
    """Handles validating and decoding JWT tokens"""

    def validate_and_decode_token(self, request: Request) -> dict[str, Any]:
        """Validate and decode tokens from inbound requests.

        :param request: The inbound request containing the token to be validated/decoded
        :return: The decoded token claims
        :raises: `HTTPException`, if unable to validate or decode the request's token
        """
        try:
            scheme, token = (
                request.headers.get("Authorization", "").strip().split(sep=" ")
            )
        except ValueError as e:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN, detail="Invalid authorization header"
            ) from e
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN, detail="Invalid token scheme"
            )

        try:
            decoded_claims: dict[str, Any] = jwt.decode(
                jwt=token,
                algorithms=["RS256"],
                issuer=get_config().base_vlm_network_url,
                options={
                    "verify_signature": False,
                    "verify_iss": True,
                    "verify_exp": True,
                    "require": ["azp"],
                },
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN, detail=f"Invalid token: {e}"
            ) from e

        return decoded_claims
