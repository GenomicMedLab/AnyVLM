"""Provide abstraction for a AnyVLM-to-AnyVar connection."""

import abc

from anyvar.utils.types import VrsVariation


class AnyVarClientError(Exception):
    """Generic client-related exception."""


class AnyVarConnectionError(AnyVarClientError):
    """Raise for network/communication failures when making calls to AnyVar instance"""


class BaseAnyVarClient(abc.ABC):
    """Interface elements for an AnyVar client"""

    @abc.abstractmethod
    def put_objects(self, objects: list[VrsVariation]) -> list[VrsVariation]:
        """Register objects with AnyVar

        :param objects: variation objects to register
        :return: completed VRS objects
        :raise AnyVarConnectionError: if connection is unsuccessful during registration request
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
        :raise AnyVarConnectionError: if connection is unsuccessful during search query
        """

    @abc.abstractmethod
    def close(self) -> None:
        """Clean up AnyVar connection."""
