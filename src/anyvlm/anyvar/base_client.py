"""Provide abstraction for a AnyVLM-to-AnyVar connection."""

import abc
from collections.abc import Iterable

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
    ) -> list[str | None]:
        """Submit allele expressions to an AnyVar instance and retrieve corresponding VRS IDs

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
        :param start: start position for genomic region
        :param end: end position for genomic region
        :return: list of matching variant objects
        :raise AnyVarClientConnectionError: if connection is unsuccessful during search query
        """

    @abc.abstractmethod
    def close(self) -> None:
        """Clean up AnyVar connection."""
