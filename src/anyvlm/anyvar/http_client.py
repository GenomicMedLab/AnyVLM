"""Provide abstraction for a VLM-to-AnyVar connection."""

import logging
from collections.abc import Iterable, Sequence
from http import HTTPMethod, HTTPStatus
from typing import Literal

import requests
from anyvar.core.metadata import VariationMapping
from anyvar.core.objects import VrsObject
from anyvar.mapping.liftover import ReferenceAssembly
from anyvar.restapi.schema import (
    GetMappingResponse,
    GetObjectResponse,
    RegisterVariationResponse,
)
from ga4gh.vrs import VrsType, models
from requests.models import Response

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
        method: Literal[HTTPMethod.POST]
        | Literal[HTTPMethod.PUT]
        | Literal[HTTPMethod.GET],
        url: str,
        payload: dict | list | None = None,
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

    def retrieve_allele_by_id(self, vrs_id: str) -> VrsObject | None:
        """Retrieve VRS Allele for given VRS ID

        :param vrs_id: The ID to dereference
        :return: The VRS Allele, or `None` if unable to retrieve the Allele.
        """
        url = f"{self.hostname}/object/{vrs_id}"
        try:
            response = self._make_http_request(method=HTTPMethod.GET, url=url)
        except requests.HTTPError:
            return None  # TODO: add logging

        validated_response: GetObjectResponse = GetObjectResponse(**response.json())
        return validated_response.data

    def retrieve_allele_by_expression(
        self, expression: str, assembly: ReferenceAssembly = ReferenceAssembly.GRCH38
    ) -> models.Allele | None:
        """Retrieve VRS Allele for given allele expression

        Currently, only expressions supported by the VRS-Python translator are supported.
        This could change depending on the AnyVar implementation, though, and probably
        can't be validated on the AnyVLM side.

        :param expression: variation expression to get VRS Allele for
        :param assembly: reference assembly used in expression
        :return: VRS Allele if translation succeeds, else `None`
        """
        url = f"{self.hostname}/variation"
        payload = {
            "definition": expression,
            "assembly_name": assembly.value,
            "input_type": VrsType.ALLELE.value,
        }
        try:
            response: Response = self._make_http_request(HTTPMethod.PUT, url, payload)
        except requests.HTTPError as e:
            if e.response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY:
                _logger.debug(
                    "Translation failed for variant expression '%s'", expression
                )
            return None

        validated_response = RegisterVariationResponse(**response.json())  # type ignore
        return validated_response.object  # type: ignore (input_type=Allele guarantees return type)

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

    def get_liftover_variation_id(
        self, vrs_id: str, starting_assembly: ReferenceAssembly
    ) -> str | None:
        """Get the VRS ID for the lifted-over equivalent of the variation specified by the provided VRS ID.

        :param vrs_id: The VRS ID of the variation to lift over
        :param starting_assembly: The assembly to liftover FROM (i.e., the assembly of the starting variant)
        :return: The VRS ID of the lifted-over variation, or `None` if liftover is unsuccessful
        """
        as_source: bool = starting_assembly == ReferenceAssembly.GRCH37
        url: str = f"{self.hostname}/object/{vrs_id}/mappings/liftover_to?as_source={as_source}"
        try:
            response = self._make_http_request(HTTPMethod.GET, url)
        except requests.HTTPError:
            return None
            # TODO - handle this (raise exception or return qqch)

        validated_response: GetMappingResponse = GetMappingResponse(**response.json())
        if len(validated_response.mappings) > 1:
            pass
            # raise Exception  # TODO - use more specific exception

        mapping_result: VariationMapping = validated_response.mappings[0]

        return mapping_result.dest_id if as_source else mapping_result.source_id

    def close(self) -> None:
        """Clean up AnyVar connection.

        This is a no-op for this class.
        """
        _logger.info(
            "Closing HTTP-based AnyVar client class. This requires no further action."
        )
