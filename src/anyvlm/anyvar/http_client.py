"""Provide abstraction for a VLM-to-AnyVar connection."""

import logging

import requests
from anyvar.utils.types import VrsVariation
from ga4gh.vrs import models

from anyvlm.anyvar.base_client import (
    AnyVarClientError,
    BaseAnyVarClient,
    UnidentifiedObjectError,
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
        self.hostname = hostname
        self.request_timeout = request_timeout

    def put_objects(self, objects: list[VrsVariation]) -> None:
        """Register objects with AnyVar

        All input objects must have a populated ID field. A validation check for this is
        performed before any variants are registered.

        :param objects: variation objects to register
        :return: completed VRS objects
        :raise AnyVarClientError: if connection is unsuccessful during registration request
        :raise UnidentifiedObjectError: if *any* provided object lacks a VRS ID
        """
        objects_to_submit = []
        for vrs_object in objects:
            if not vrs_object.id:
                _logger.error("Provided variant %s has no VRS ID: %s")
                raise UnidentifiedObjectError
            objects_to_submit.append(
                vrs_object.model_dump(exclude_none=True, mode="json")
            )
        for vrs_object in objects_to_submit:
            response = requests.put(
                f"{self.hostname}/vrs_variation",
                json=vrs_object,
                timeout=self.request_timeout,
            )
            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                raise AnyVarClientError from e

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
