"""Provide abstraction for a AnyVLM-to-AnyVar connection."""

import abc

from anyvar.utils.types import VrsVariation

# define constant to use as AnyVar annotation type
AF_ANNOTATION_TYPE = "cohort_allele_frequency"


class AmbiguousAnnotationError(Exception):
    """Raise if multiple candidate annotations exist on a variation"""


class BaseAnyVarClient(abc.ABC):
    """Interface elements for an AnyVar client"""

    @abc.abstractmethod
    def put_objects(self, objects: list[VrsVariation]) -> list[VrsVariation]:
        """Register objects with AnyVar

        :param objects: variation objects to register
        :return: completed VRS objects
        """

    @abc.abstractmethod
    def search_by_interval(
        self, accession: str, start: int, end: int
    ) -> list[VrsVariation]:
        """Get all variation IDs located within the specified range

        :param accession: sequence accession
        :param start: start position for genomic region
        :param end: end position for genomic region
        :return: list of matching variant objects
        """

    @abc.abstractmethod
    def close(self) -> None:
        """Clean up AnyVar connection."""
