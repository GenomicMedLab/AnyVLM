"""Module to handle authentication of incoming match requests"""

import logging
from http import HTTPStatus
from logging import Logger
from typing import Any

import jwt
from fastapi import HTTPException, Request

_logger: Logger = logging.getLogger(__name__)

VLM_AUTH_API = "https://vlm-auth.us.auth0.com/"


async def authenticate(request: Request) -> None:
    """Authenticate JWT token from incoming match requests

    :param request: The incoming request object
    :return: None
    :raises: HTTPException if unable to successfully decode the request's JWT token
    """
    try:
        scheme, token = request.headers.get("Authorization", "").strip().split(sep=" ")
    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Invalid authorization header"
        ) from e
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Invalid token scheme"
        )

    try:
        decoded: dict[str, Any] = jwt.decode(
            jwt=token,
            algorithms=["RS256"],
            issuer=VLM_AUTH_API,
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

    client_id = decoded["azp"]
    message: str = f"Received match request from client_id '{client_id}'"
    _logger.info(msg=message)
