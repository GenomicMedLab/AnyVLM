"""Provide abstraction for a AnyVLM-to-AnyVar connection."""

import abc
from collections.abc import Iterable, Sequence

from anyvar.utils.liftover_utils import ReferenceAssembly
from anyvar.utils.types import VrsVariation


class AnyVarClientError(Exception):
    """Generic client-related exception."""


class AnyVarClientConnectionError(AnyVarClientError):
    """Raise for failure to connect to AnyVar client.

    Likely relevant only for HTTP-based implementation.
    """


class BaseAnyVarClient(abc.ABC):
    """Interface elements for an AnyVar client"""

    @abc.abstractmethod
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
        :param assembly: reference assembly used in variation expressions
        :return: list where the i'th item is either the VRS ID if translation succeeds,
            else `None`, for the i'th expression
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
        :raise AnyVarClientConnectionError: if connection is unsuccessful during search query
        """

    @abc.abstractmethod
    def close(self) -> None:
        """Clean up AnyVar connection."""
