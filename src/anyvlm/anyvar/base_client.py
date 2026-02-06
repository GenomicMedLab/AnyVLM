"""Provide abstraction for a AnyVLM-to-AnyVar connection."""

import abc
from collections.abc import Iterable, Sequence

from anyvar.mapping.liftover import ReferenceAssembly
from ga4gh.vrs.models import Allele


class AnyVarClientError(Exception):
    """Generic client-related exception."""


class AnyVarClientConnectionError(AnyVarClientError):
    """Raise for failure to connect to AnyVar client.

    Likely relevant only for HTTP-based implementation.
    """


class BaseAnyVarClient(abc.ABC):
    """Interface elements for an AnyVar client"""

    @abc.abstractmethod
    def get_registered_allele(
        self, expression: str, assembly: ReferenceAssembly = ReferenceAssembly.GRCH38
    ) -> Allele | None:
        """Retrieve registered VRS Allele for given allele expression

        Currently, only expressions supported by the VRS-Python translator are supported.
        This could change depending on the AnyVar implementation, though, and probably
        can't be validated on the AnyVLM side.

        :param expression: variation expression to get VRS Allele for
        :param assembly: reference assembly used in expression
        :return: VRS Allele if translation succeeds and VRS Allele has already been registered, else `None`
        """

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
    def close(self) -> None:
        """Clean up AnyVar connection."""
