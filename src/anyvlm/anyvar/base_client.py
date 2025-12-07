"""Provide abstraction for a AnyVLM-to-AnyVar connection."""

import abc

from anyvar.utils.types import VrsVariation


class AnyVarClientError(Exception):
    """Generic client-related exception."""


class BaseAnyVarClient(abc.ABC):
    """Interface elements for an AnyVar client"""

    @abc.abstractmethod
    def put_objects(self, objects: list[VrsVariation]) -> list[VrsVariation]:
        """Register objects with AnyVar

        :param objects: variation objects to register
        :return: completed VRS objects
        :raise AnyVarClientError: for errors relating to specifics of client interface
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
        :raise AnyVarClientError: if connection is unsuccessful during search query
        """

    @abc.abstractmethod
    def close(self) -> None:
        """Clean up AnyVar connection."""
