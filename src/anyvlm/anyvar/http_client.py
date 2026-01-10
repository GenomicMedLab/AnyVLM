"""Provide abstraction for a VLM-to-AnyVar connection."""

import logging
from collections.abc import Iterable, Sequence
from http import HTTPMethod, HTTPStatus
from typing import Literal

import requests
from anyvar.restapi.schema import GetObjectResponse, RegisterVariationResponse
from anyvar.utils.liftover_utils import ReferenceAssembly
from ga4gh.vrs import VrsType, models

from anyvlm.anyvar.base_client import (
    AnyVarClientConnectionError,
    AnyVarClientError,
    BaseAnyVarClient,
)

_logger = logging.getLogger(__name__)


class HttpAnyVarClient(BaseAnyVarClient):
    """AnyVar HTTP-based client"""

    def __init__(
        self, hostname: str = "http://localhost:8000", request_timeout: int = 30
    ) -> None:
        """Initialize client instance

        :param hostname: service API root
        :param request_timeout: timeout value, in seconds, for HTTP requests
        """
        _logger.info("Initializing HTTP-based AnyVar client with hostname %s", hostname)
        self.hostname = hostname
        self.request_timeout = request_timeout

    def _make_http_request(
        self,
        method: Literal[HTTPMethod.POST] | Literal[HTTPMethod.PUT],
        url: str,
        payload: dict | list,
    ) -> requests.Response:
        """Issue an HTTP request to an AnyVar server.

        :param method: type of request to make
        :param url: target URL
        :param payload: request data to provide as JSON
        :return: literal response object
        :raise AnyVarClientConnectionError: if server fails to respond
        :raise requests.HTTPError: if response status code != 200 OK
        """
        try:
            response = requests.request(
                method=method, url=url, json=payload, timeout=self.request_timeout
            )
        except requests.ConnectionError as e:
            _logger.exception(
                "Unable to establish connection using AnyVar configured at %s",
                self.hostname,
            )
            raise AnyVarClientConnectionError from e
        try:
            response.raise_for_status()
        except requests.HTTPError:
            # log it, then let callers handle specific failures their own way
            _logger.exception(
                "Encountered HTTP exception submitting payload %s to %s",
                payload,
                url,
            )
            raise
        return response

    def get_registered_allele(
        self, expression: str, assembly: ReferenceAssembly = ReferenceAssembly.GRCH38
    ) -> models.Allele | None:
        """Retrieve registered VRS Allele for given allele expression

        Currently, only expressions supported by the VRS-Python translator are supported.
        This could change depending on the AnyVar implementation, though, and probably
        can't be validated on the AnyVLM side.

        :param expression: variation expression to get VRS Allele for
        :param assembly: reference assembly used in expression
        :return: VRS Allele if translation succeeds and VRS Allele has already been registered, else `None`
        """
        url = f"{self.hostname}/variation"
        payload = {
            "definition": expression,
            "assembly_name": assembly.value,
            "input_type": VrsType.ALLELE.value,
        }
        try:
            response = self._make_http_request(HTTPMethod.POST, url, payload)
        except requests.HTTPError as e:
            if e.response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
                _logger.debug(
                    "Translation failed for variant expression '%s'", expression
                )
                return None

            if e.response.status_code == HTTPStatus.NOT_FOUND:
                _logger.debug("No variation found for expression '%s'", expression)
                return None
            raise AnyVarClientError from e

        validated_response = GetObjectResponse(**response.json())
        return validated_response.data  # type: ignore (input_type=Allele guarantees return type)

    def put_allele_expressions(
        self,
        expressions: Iterable[str],
        assembly: ReferenceAssembly = ReferenceAssembly.GRCH38,
    ) -> Sequence[str | None]:
        """Submit allele expressions to an AnyVar instance and retrieve corresponding VRS IDs

        Currently, only expressions supported by the VRS-Python translator are supported.
        This could change depending on the AnyVar implementation, though, and probably
        can't be validated on the AnyVLM side.

        :param expressions: variation expressions to register
        :param assembly: reference assembly used in expressions
        :return: list where the i'th item is either the VRS ID if translation succeeds,
            else `None`, for the i'th expression
        :raise AnyVarClientError: for unexpected errors relating to specifics of client interface
        """
        payload = [
            {
                "definition": expression,
                "assembly_name": assembly.value,
                "input_type": VrsType.ALLELE.value,
            }
            for expression in expressions
        ]
        url = f"{self.hostname}/variations"
        try:
            response = self._make_http_request(HTTPMethod.PUT, url, payload)
        except requests.HTTPError as e:
            raise AnyVarClientError from e
        return [RegisterVariationResponse(**r).object_id for r in response.json()]

    def close(self) -> None:
        """Clean up AnyVar connection.

        This is a no-op for this class.
        """
        _logger.info(
            "Closing HTTP-based AnyVar client class. This requires no further action."
        )
