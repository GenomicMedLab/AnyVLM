"""Provide abstraction for a VLM-to-AnyVar connection."""

import logging
from collections.abc import Iterable, Sequence
from http import HTTPMethod, HTTPStatus

import requests
from anyvar.restapi.schema import RegisterVariationResponse
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

    def _make_allele_expression_request(
        self, expression: str, assembly: ReferenceAssembly, method: HTTPMethod
    ) -> requests.Response | None:
        """Make a request to the AnyVar variation endpoint for an allele expression

        :param expression: variation expression to translate
        :param assembly: reference assembly used in expression
        :param method: HTTP method to use for the request. Only POST and PUT are
            supported.
            POST is used for retrieving a registered variation, while PUT is used for
            registering a new variation.
        :raises ValueError: if unsupported HTTP method is provided
        :raise AnyVarClientConnectionError: if connection to AnyVar service is
            unsuccessful
        :raise AnyVarClientError: if HTTP request fails for other reasons
        :return: HTTP response object if request is successful, else `None`
        """
        if method not in {HTTPMethod.POST, HTTPMethod.PUT}:
            msg = (
                f"HTTP method {method} is not supported for allele expression requests"
            )
            raise ValueError(msg)

        url = f"{self.hostname}/variation"
        payload = {
            "definition": expression,
            "assembly_name": assembly.value,
            "input_type": VrsType.ALLELE.value,
        }
        try:
            response = requests.request(
                method=method,
                url=url,
                json=payload,
                timeout=self.request_timeout,
            )
        except requests.ConnectionError as e:
            _logger.exception(
                "Unable to establish connection using AnyVar configured at %s",
                self.hostname,
            )
            raise AnyVarClientConnectionError from e

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            _logger.exception(
                "Encountered HTTP exception submitting payload %s to %s",
                payload,
                url,
            )
            if response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
                _logger.debug(
                    "Translation failed for variant expression '%s'", expression
                )
                return None

            if response.status_code == HTTPStatus.NOT_FOUND:
                _logger.debug("No variation found for expression '%s'", expression)
                return None

            raise AnyVarClientError from e
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
        response = self._make_allele_expression_request(
            expression, assembly, HTTPMethod.POST
        )
        if not response:
            return None

        return models.Allele(**response.json()["data"])

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
            response = requests.put(
                url=url,
                json=payload,
                timeout=self.request_timeout,
            )
        except requests.ConnectionError as e:
            _logger.exception(
                "Unable to establish connection using AnyVar configured at %s",
                self.hostname,
            )
            raise AnyVarClientConnectionError from e

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            _logger.exception(
                "Encountered HTTP exception submitting payload %s to %s",
                payload,
                url,
            )
            raise AnyVarClientError from e
        return [RegisterVariationResponse(**r).object_id for r in response.json()]

    def close(self) -> None:
        """Clean up AnyVar connection.

        This is a no-op for this class.
        """
        _logger.info(
            "Closing HTTP-based AnyVar client class. This requires no further action."
        )
