"""Provide abstraction for a VLM-to-AnyVar connection."""

import abc
from http import HTTPStatus

import requests
from anyvar.utils.types import VrsObject

from vlm.anyvar.base_client import AF_ANNOTATION_TYPE, AmbiguousAnnotationError
from vlm.schemas.domain import AlleleFrequencyAnnotation


class HttpAnyVarClient(abc.ABC):
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

    def put_objects(self, objects: list[VrsObject]) -> list[VrsObject]:
        """Register objects with AnyVar

        :param objects: variation objects to register
        :return: completed VRS objects
        """
        results = []
        url = f"{self.hostname}/vrs_variation"
        for vrs_object in objects:
            response = requests.put(
                url,
                json=vrs_object.model_dump(exclude_none=True, mode="json"),
                timeout=self.request_timeout,
            )
            response.raise_for_status()
            results.append(response.json()["object"])
        return results

    def put_af_annotation(self, key: str, af: AlleleFrequencyAnnotation) -> None:
        """Add an allele frequency annotation to a variation

        :param key: VRS ID for variation being annotated
        :param af: frequency data for for annotation
        """
        response = requests.post(
            f"{self.hostname}/variation/{key}/annotations",
            json={
                "annotation_type": AF_ANNOTATION_TYPE,
                "annotation_value": af.model_dump(mode="json", exclude_none=True),
            },
            timeout=self.request_timeout,
        )
        response.raise_for_status()

    @abc.abstractmethod
    def search_by_interval(
        self, accession: str, start: int, end: int
    ) -> list[VrsObject]:
        """Get all variation IDs located within the specified range

        :param accession: sequence accession
        :param start: start position for genomic region
        :param end: end position for genomic region
        :return: list of matching variant objects
        """

    def get_af_annotation(self, key: str) -> AlleleFrequencyAnnotation | None:
        """Get AF annotation for a key (object ID)

        :param key: object ID (presumably VRS ID)
        :return: AF object if available, `None` otherwise
        :raise KeyError: if object with given ID doesn't exist
        """
        response = requests.get(
            f"{self.hostname}/variation/{key}/annotations/{AF_ANNOTATION_TYPE}",
            timeout=self.request_timeout,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            if response.status_code == HTTPStatus.NOT_FOUND:
                raise KeyError from e
            raise
        data = response.json()
        if len(data["annotations"]) == 0:
            return None
        if len(data["annotations"]) > 1:
            raise AmbiguousAnnotationError
        return AlleleFrequencyAnnotation(**data["annotations"][0]["annotation_value"])

    def close(self) -> None:  # noqa: B027
        """Clean up AnyVar connection.

        This is a no-op for this class.
        """
