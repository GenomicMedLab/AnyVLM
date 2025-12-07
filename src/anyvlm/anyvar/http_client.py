"""Provide abstraction for a VLM-to-AnyVar connection."""

import requests
from anyvar.utils.types import VrsVariation
from ga4gh.vrs import models

from anyvlm.anyvar.base_client import AnyVarConnectionError, BaseAnyVarClient


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

    def put_objects(self, objects: list[VrsVariation]) -> list[VrsVariation]:
        """Register objects with AnyVar

        This method is intentionally naive. Future improvements could include
        * A better way to batch requests together to mitigate HTTP latency
        * A smarter dispatch for reconstructing variation model instances

        :param objects: variation objects to register
        :return: completed VRS objects
        :raise AnyVarConnectionError: if connection is unsuccessful during registration request
        """
        results = []
        url = f"{self.hostname}/vrs_variation"
        for vrs_object in objects:
            response = requests.put(
                url,
                json=vrs_object.model_dump(exclude_none=True, mode="json"),
                timeout=self.request_timeout,
            )
            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                raise AnyVarConnectionError from e
            result_object = response.json()["object"]
            if result_object.get("type") == "Allele":
                results.append(models.Allele(**result_object))
            else:
                raise NotImplementedError(
                    f"Unsupported object type: {result_object.get('type')}"
                )
        return results

    def search_by_interval(
        self, accession: str, start: int, end: int
    ) -> list[VrsVariation]:
        """Get all variation IDs located within the specified range

        :param accession: sequence accession
        :param start: start position for genomic region
        :param end: end position for genomic region
        :return: list of matching variant objects
        :raise AnyVarConnectionError: if connection is unsuccessful during search query
        """
        response = requests.get(
            f"{self.hostname}/search?accession={accession}&start={start}&end={end}",
            timeout=self.request_timeout,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise AnyVarConnectionError from e
        return [models.Allele(**v) for v in response.json()["variations"]]

    def close(self) -> None:
        """Clean up AnyVar connection.

        This is a no-op for this class.
        """
