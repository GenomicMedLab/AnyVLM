"""Provide abstraction for a VLM-to-AnyVar connection."""

import abc

from anyvar.utils.types import VrsObject

from vlm.schemas.domain import AlleleFrequencyAnnotation


class BaseAnyVarClient(abc.ABC):
    """Interface elements for an AnyVar client"""

    @abc.abstractmethod
    def put_objects(self, objects: list[VrsObject]) -> None:
        """Register objects with AnyVar

        :param objects: variation objects to register
        """

    @abc.abstractmethod
    def put_af_annotation(self, key: str, af: AlleleFrequencyAnnotation) -> None:
        """Add an allele frequency annotation to a variation


        :param key: VRS ID for variation being annotated
        :param af: frequency data for for annotation
        """

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

    @abc.abstractmethod
    def close(self) -> None:
        """Clean up AnyVar connection."""
