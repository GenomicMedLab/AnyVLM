"""Handles sending authenticated outbound requests to the VLM Network"""

from http import HTTPMethod
from typing import Any

import requests

from anyvlm.auth.token_provider import TokenProvider


class VlmClient:
    """Handles sending authenticated outbound requests to the VLM Network"""

    def __init__(self) -> None:  # noqa: D107
        self.token_provider: TokenProvider = TokenProvider()

    def request(
        self,
        method_type: HTTPMethod,
        url: str,
        request_body: dict[Any, Any] | None = None,
    ) -> Any:  # noqa: ANN401
        """Send an authenticated outbound request to the VLM Network"""
        return requests.request(
            method=method_type,
            url=url,
            headers={"Authorization": f"Bearer {self.token_provider.get_token()}"},
            data=request_body,
            timeout=10,
        )
