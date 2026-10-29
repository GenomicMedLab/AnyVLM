"""Handles retrieving/caching valid bearer tokens"""

import os
from datetime import UTC, datetime, timedelta
from http import HTTPStatus

import requests
from requests.models import Response

from anyvlm.utils.exceptions import TokenRetrievalError


class TokenProvider:
    """Handles retrieving/caching valid bearer tokens"""

    BASE_VLM_AUTH_URL: str = "https://vlm-auth.us.auth0.com"
    AUDIENCE_URL: str = BASE_VLM_AUTH_URL + "/api/v2/"
    TOKEN_REQUEST_URL: str = BASE_VLM_AUTH_URL + "/oauth/token"

    # used to add margin to the token expiry time, to account for the time
    # it takes for the token provider to send its response back to AnyVLM
    TOKEN_EXPIRY_MARGIN_SECONDS = 30

    _token: str = ""
    _token_expiry: datetime

    def __init__(self) -> None:
        """Initializes a TokenProvider to obtain JWT tokens for outbound HTTP requests to other nodes on the VLM Network"""
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
            url=self.TOKEN_REQUEST_URL,
            json={
                "client_id": os.getenv("VLM_CLIENT_ID"),
                "client_secret": os.getenv("VLM_CLIENT_SECRET"),
                "audience": self.AUDIENCE_URL,
                "grant_type": "client_credentials",
            },
            timeout=10,
        )

        if response.status_code != HTTPStatus.OK:
            error_message: str = "Unable to fetch bearer token from Auth0"
            raise TokenRetrievalError(error_message)

        data = response.json()

        self._token = data["access_token"]
        self._token_expiry = now + timedelta(
            seconds=(data["expires_in"] - self.TOKEN_EXPIRY_MARGIN_SECONDS)
        )
