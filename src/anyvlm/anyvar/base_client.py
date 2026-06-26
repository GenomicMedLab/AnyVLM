"""Provide abstraction for a AnyVLM-to-AnyVar connection."""

import abc
from collections.abc import Iterable, Sequence

from anyvar.core.objects import SupportedVrsVariation
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
    def retrieve_allele_by_id(self, vrs_id: str) -> SupportedVrsVariation | None:
        """Retrieve VRS Allele for given VRS ID

        :param vrs_id: The ID to dereference
        :return: The VRS Allele, or `None` if unable to retrieve the Allele.
        """

    @abc.abstractmethod
    def retrieve_allele_by_expression(
        self, expression: str, assembly: ReferenceAssembly = ReferenceAssembly.GRCH38
    ) -> Allele | None:
        """Retrieve VRS Allele for given allele expression

        Currently, only expressions supported by the VRS-Python translator are supported.
        This could change depending on the AnyVar implementation, though, and probably
        can't be validated on the AnyVLM side.

        :param expression: variation expression to get VRS Allele for
        :param assembly: reference assembly used in expression
        :return: VRS Allele if translation succeeds, else `None`
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
    def get_liftover_variation_id(
        self, vrs_id: str, starting_assembly: ReferenceAssembly
    ) -> str | None:
        """Get the VRS ID for the lifted-over equivalent of the variation specified by the provided VRS ID.

        :param vrs_id: The VRS ID of the variation to lift over
        :param starting_assembly: The assembly to liftover FROM (i.e., the assembly of the starting variant)
        :return: The VRS ID of the lifted-over variation, or `None` if liftover is unsuccessful
        """

    @abc.abstractmethod
    def close(self) -> None:
        """Clean up AnyVar connection."""
