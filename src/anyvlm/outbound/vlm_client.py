"""Handles sending authenticated outbound requests to the VLM Network"""

from http import HTTPMethod
from typing import Any

import requests
from requests import Response

from anyvlm.auth.token_provider import TokenProvider


class VlmClient:
    """Handles sending authenticated outbound requests to the VLM Network"""

    def __init__(self, token_provider: TokenProvider) -> None:
        """Initializes a VLM client to send outbound requests to the VLM Network

        :param token_provider: A TokenProvider instance; used to obtain JWT tokens for outbound HTTP requests to other nodes on the VLM network
        """
        self.token_provider: TokenProvider = token_provider

    def request(
        self,
        method_type: HTTPMethod,
        url: str,
        request_body: dict[Any, Any] | None = None,
    ) -> Response:
        """Send an authenticated outbound request to the VLM Network"""
        return requests.request(
            method=method_type,
            url=url,
            headers={"Authorization": f"Bearer {self.token_provider.get_token()}"},
            json=request_body,
            timeout=10,
        )
