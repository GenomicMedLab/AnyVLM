"""Provide abstraction for a AnyVLM-to-AnyVar connection."""

import abc

from anyvar.utils.types import VrsVariation


class AnyVarClientError(Exception):
    """Generic client-related exception."""


class UnidentifiedObjectError(AnyVarClientError):
    """Raise if input object lacks an ID property"""


class BaseAnyVarClient(abc.ABC):
    """Interface elements for an AnyVar client"""

    @abc.abstractmethod
    def put_objects(self, objects: list[VrsVariation]) -> None:
        """Register objects with AnyVar

        All input objects must have a populated ID field. A validation check for this is
        performed before any variants are registered.

        :param objects: variation objects to register
        :raise AnyVarClientError: for errors relating to specifics of client interface
        :raise UnidentifiedObjectError: if *any* provided object lacks a VRS ID
        """

    @abc.abstractmethod
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

    @abc.abstractmethod
    def close(self) -> None:
        """Clean up AnyVar connection."""
