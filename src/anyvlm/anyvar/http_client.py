"""Provide abstraction for a VLM-to-AnyVar connection."""

import logging
from collections.abc import Iterable

import requests
from anyvar.utils.types import VrsVariation
from ga4gh.vrs import models

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
        self, expressions: Iterable[str], assembly: str = "GRCh38"
    ) -> list[str | None]:
        """Submit allele expressions to an AnyVar instance and retrieve corresponding VRS IDs

        :param expressions: variation expressions to register
        :param assembly: reference assembly used in expressions
        :return: list where the i'th item is either the VRS ID if translation succeeds,
            else `None`, for the i'th expression
        :raise AnyVarClientError: for unexpected errors relating to specifics of client interface
        """
        results = []
        for expression in expressions:
            url = f"{self.hostname}/variation"
            payload = {
                "definition": expression,
                "assembly_name": assembly,
                "input_type": "Allele",
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
                raise AnyVarClientError from e
            response_json = response.json()
            if messages := response_json.get("messages"):
                _logger.warning(
                    "Variant expression `%s` seems to have failed to translate: %s",
                    expression,
                    messages,
                )
                results.append(None)
            else:
                results.append(response_json["object_id"])
        return results

    def search_by_interval(
        self, accession: str, start: int, end: int
    ) -> list[VrsVariation]:
        """Get all variation IDs located within the specified range

        :param accession: sequence accession
        :param start: start position for genomic region
        :param end: end position for genomic region
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
