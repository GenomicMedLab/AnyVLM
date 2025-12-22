"""Provide abstraction for a VLM-to-AnyVar connection."""

import logging
from collections.abc import Iterable, Sequence
from http import HTTPStatus

import requests
from anyvar.utils.liftover_utils import ReferenceAssembly
from anyvar.utils.types import VrsVariation
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
        results = []
        url = f"{self.hostname}/variation"
        for expression in expressions:
            payload = {
                "definition": expression,
                "assembly_name": assembly.value,
                "input_type": VrsType.ALLELE.value,
            }
            try:
                response = requests.put(
                    url,
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
                    results.append(None)
                else:
                    raise AnyVarClientError from e
            else:
                results.append(response.json()["object_id"])
        return results

    def search_by_interval(
        self, accession: str, start: int, end: int
    ) -> list[VrsVariation]:
        """Get all variation IDs located within the specified range

        :param accession: sequence accession
        :param start: Inclusive, inter-residue genomic start position of the interval
            to search
        :param end: Inclusive, inter-residue genomic end position of the interval to
            search
        :return: list of matching variant objects
        :raise AnyVarClientError: if connection is unsuccessful during search query
        """
        response = requests.get(
            f"{self.hostname}/search?accession={accession}&start={start}&end={end}",
            timeout=self.request_timeout,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            if response.json() == {
                "detail": "Unable to dereference provided accession ID"
            }:
                return []
            raise AnyVarClientError from e
        return [models.Allele(**v) for v in response.json()["variations"]]

    def close(self) -> None:
        """Clean up AnyVar connection.

        This is a no-op for this class.
        """
        _logger.info(
            "Closing HTTP-based AnyVar client class. This requires no further action."
        )
