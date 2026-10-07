"""Module to handle authentication of incoming match requests"""

import logging
import os
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from logging import Logger
from typing import Any

import jwt
import requests
from fastapi import HTTPException, Request
from requests.models import Response

from anyvlm.utils.exceptions import Auth0Error

_logger: Logger = logging.getLogger(__name__)


class AuthManager:
    """Handles auth for incoming and outgoing requests"""

    BASE_VLM_AUTH_URL: str = "https://vlm-auth.us.auth0.com"
    TOKEN_REQUEST_URL: str = BASE_VLM_AUTH_URL + "/oauth/token"
    AUDIENCE: str = BASE_VLM_AUTH_URL + "/api/v2/"
    KNOWN_NODES_REQUEST_URL: str = BASE_VLM_AUTH_URL + "/api/v2/clients"

    KNOWN_NODES_REFRESH_INTERVAL: timedelta = timedelta(hours=24)

    _known_nodes: dict[str, dict[str, str | None]]
    _known_nodes_expiry: datetime

    _token: str = ""
    _token_expiry: datetime

    def __init__(self) -> None:  # noqa: D107
        self.refresh_known_nodes()

    def _get_or_refresh_value(
        self, value_name: str, refresh_value: Callable[[], None]
    ) -> Any:  # noqa: ANN401
        """Get the specified value. If it has expired, refresh the value first.
        NOTE: This function expects `value_name` to have a corresponding variable called `self.{value_name}_expiry`
        that will be checked to determine if the value has expired.

        :param value_name: The variable name of the value to get.
        :param refresh_value: The function to refresh the value + reset the expiry datetime, to use if the value is expired.
        """
        if (not getattr(self, value_name)) or (
            datetime.now(tz=UTC) >= getattr(self, f"{value_name})_expiry")
        ):
            refresh_value()
        return getattr(self, value_name)

    def refresh_known_nodes(self) -> None:
        """Retrieve an updated list of known nodes on the VLM Network + reset the expiry time for the next check"""
        response: Response = requests.get(url=self.KNOWN_NODES_REQUEST_URL, timeout=10)

        if response.status_code == HTTPStatus.OK:
            self._known_nodes = {}
        else:
            error_message: str = "Unable to fetch known VLM Network nodes"
            raise Auth0Error(error_message)

        data = response.json()
        for entry in data:
            self._known_nodes[entry.get("client_id")] = {
                "name": entry.get("name"),
                "match_url": entry.get("client_metadata", {}).get("match_url"),
            }

        self._known_nodes_expiry = (
            datetime.now(tz=UTC) + self.KNOWN_NODES_REFRESH_INTERVAL
        )

    def get_known_nodes(self) -> dict[str, list[str]]:
        """Retrieves a list of all known nodes on the VLM Network"""
        return self._get_or_refresh_value(
            value_name="known_nodes", refresh_value=self.refresh_known_nodes
        )

    def refresh_token(self) -> None:
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
        self._token_expiry = datetime.now(tz=UTC) + data["expires_in"]

    def get_token(self) -> str:
        """Retrieve a current JWT token. Will set a new token if there
        isn't currently one set, or if the current on is expired.

        :return: a JWT token
        """
        return self._get_or_refresh_value(
            value_name="token", refresh_value=self.refresh_token
        )

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

        if client_id not in self._known_nodes:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN, detail="Unknown client ID"
            )
