"""Module to handle authentication of incoming match requests"""

import logging
import os
from datetime import UTC, datetime
from http import HTTPStatus
from logging import Logger
from typing import Any

import jwt
import requests
from fastapi import HTTPException, Request
from requests.models import Response

_logger: Logger = logging.getLogger(__name__)


class AuthManager:
    """Handles auth for incoming and outgoing requests"""

    BASE_VLM_AUTH_URL: str = "https://vlm-auth.us.auth0.com"
    TOKEN_REQUEST_URL: str = BASE_VLM_AUTH_URL + "/oauth/token"
    AUDIENCE: str = BASE_VLM_AUTH_URL + "/api/v2/"

    known_node_ids: list[str]
    _token: str = ""
    token_expiry: datetime

    def __init__(self) -> None:  # noqa: D107
        self.known_node_ids = self.get_known_nodes()

    def get_known_nodes(self) -> list[str]:
        """Retrieves a list of all known nodes on the VLM Network"""
        return []  # TODO

    def set_token(self) -> None:
        """Sets a new JWT token and updates the token expiry time"""
        response: Response = requests.post(
            url=self.TOKEN_REQUEST_URL,
            json={
                "client_id": os.getenv("VLM_CLIENT_ID"),
                "client_secret": os.getenv("VLM_CLIENT_SECRET"),
                "audience": self.AUDIENCE,
                "grant_type": "client_credentials",
            },
            timeout=10,
        )

        data = response.json()

        self._token = data["access_token"]
        self.token_expiry = datetime.now(tz=UTC) + data["expires_in"]

    def get_token(self) -> str:
        """Retrieve a current JWT token. Will set a new token if there
        isn't currently one set, or if the current on is expired.

        :return: a JWT token
        """
        if (not self._token) or (datetime.now(tz=UTC) >= self.token_expiry):
            self.set_token()
        return self._token

    def authenticate_request(self, request: Request) -> None:
        """Authenticate JWT token from incoming match requests

        :param request: The incoming request object
        :return: None
        :raises: HTTPException if unable to successfully decode the request's JWT token
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
            decoded: dict[str, Any] = jwt.decode(
                jwt=token,
                algorithms=["RS256"],
                issuer=self.BASE_VLM_AUTH_URL,
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
