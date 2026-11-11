"""Handles retrieving/caching valid bearer tokens"""

import os
from datetime import UTC, datetime, timedelta
from http import HTTPStatus

import requests
from requests.models import Response

from anyvlm.utils.constants import (
    VLM_NETWORK_AUDIENCE_URL,
    VLM_NETWORK_TOKEN_REQUEST_URL,
)
from anyvlm.utils.exceptions import TokenRetrievalError


class TokenProvider:
    """Handles retrieving/caching valid bearer tokens"""

    # used to add margin to the token expiry time, to account for the time
    # it takes for the token provider to send its response back to AnyVLM
    TOKEN_EXPIRY_MARGIN_SECONDS = 30

    _token: str = ""
    _token_expiry: datetime

    def __init__(self) -> None:
        """Initializes a TokenProvider to obtain JWT tokens for outbound HTTP requests to other nodes on the VLM Network"""
        client_id: str | None = os.getenv("VLM_CLIENT_ID")
        client_secret: str | None = os.getenv("VLM_CLIENT_SECRET")

        if not client_id or not client_secret:
            error_message: str = "Unable to retrieve token - missing 'VLM_CLIENT_ID' and/or 'VLM_CLIENT_SECRET' environment variables"
            raise TokenRetrievalError(error_message)

        self.client_id: str = client_id
        self.client_secret: str = client_secret

        self.get_token()

    def get_token(self) -> str:
        """Retrieves a valid JWT token. Will obtain a new token if
        one is not currently set or if the current one is expired.

        :return: a JWT token
        :raises: a `TokenRetrievalError`, if unable to obtain a token
        """
        now: datetime = datetime.now(tz=UTC)
        if (not self._token) or (now >= self._token_expiry):
            self._refresh_token()
        return self._token

    def _refresh_token(self) -> None:
        """Retrieves and sets a new JWT token and updates the token expiry time"""
        now: datetime = datetime.now(tz=UTC)
        response: Response = requests.post(
            url=VLM_NETWORK_TOKEN_REQUEST_URL,
            json={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "audience": VLM_NETWORK_AUDIENCE_URL,
                "grant_type": "client_credentials",
            },
            timeout=10,
        )

        if response.status_code != HTTPStatus.OK:
            error_message: str = f"Unable to fetch bearer token from Auth0 - {response.status_code} response received"
            raise TokenRetrievalError(error_message)

        data = response.json()

        self._token = data["access_token"]
        self._token_expiry = now + timedelta(
            seconds=(data["expires_in"] - self.TOKEN_EXPIRY_MARGIN_SECONDS)
        )
