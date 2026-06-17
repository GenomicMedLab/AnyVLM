"""Implement AnyVar client interface for direct Python-based access."""

import logging
from collections.abc import Iterable, Sequence

from anyvar import AnyVar
from anyvar.core.metadata import VariationMapping, VariationMappingType
from anyvar.core.objects import SupportedVrsVariation
from anyvar.mapping.liftover import ReferenceAssembly
from anyvar.restapi.schema import SupportedVariationType
from anyvar.storage.base import Storage
from anyvar.translate.base import TranslationError, Translator
from ga4gh.vrs.dataproxy import DataProxyValidationError
from ga4gh.vrs.models import Allele

from anyvlm.anyvar.base_client import BaseAnyVarClient

_logger = logging.getLogger(__name__)


class PythonAnyVarClient(BaseAnyVarClient):
    """A Python-based AnyVar client."""

    def __init__(self, translator: Translator, storage: Storage) -> None:
        """Initialize directly-connected AnyVar client

        :param translator: AnyVar translator instance
        :param storage: AnyVar storage instance
        """
        self.av = AnyVar(translator, storage)

    def _translate_allele_expression(
        self, expression: str, assembly: ReferenceAssembly = ReferenceAssembly.GRCH38
    ) -> Allele | None:
        """Translate a single allele expression to a VRS Allele

        Currently, only expressions supported by the VRS-Python translator are supported.
        This could change depending on the AnyVar implementation, though, and probably
        can't be validated on the AnyVLM side.

        :param expression: variation expression to translate
        :param assembly: reference assembly used in expression
        :return: VRS Allele if translation succeeds, else `None`
        """
        translated_variation = None
        try:
            translated_variation = self.av.translator.translate_variation(
                expression,
                assembly=assembly.value,
                input_type=SupportedVariationType.ALLELE,  # type: ignore
            )
        except DataProxyValidationError:
            _logger.exception("Found invalid base in expression %s", expression)
        except TranslationError:
            _logger.exception("Failed to translate expression: %s", expression)
        return translated_variation  # type: ignore

    def retrieve_allele_by_id(self, vrs_id: str) -> SupportedVrsVariation | None:
        """Retrieve VRS Allele for given VRS ID

        :param vrs_id: The ID to dereference
        :return: The VRS Allele, or `None` if unable to retrieve the Allele.
        """
        return self.av.get_object(object_id=vrs_id, object_type=Allele)

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
        translated_variation = self._translate_allele_expression(expression, assembly)
        if not translated_variation:
            return None

        try:
            return self.av.get_object(translated_variation.id, Allele)  # type: ignore
        except KeyError:
            _logger.exception(
                "VRS Allele with ID %s not found", translated_variation.id
            )

    def put_allele_expressions(
        self,
        expressions: Iterable[str],
        assembly: ReferenceAssembly = ReferenceAssembly.GRCH38,
    ) -> Sequence[str | None]:
        """Submit allele expressions to an AnyVar instance and retrieve corresponding VRS IDs

        Currently, only expressions supported by the VRS-Python translator are supported.
        What this means could change depending on the AnyVar implementation, though, and
        probably can't be validated on the AnyVLM side given current designs.

        :param expressions: variation expressions to register
        :param assembly: reference assembly used in expressions
        :return: list where the i'th item is either the VRS ID if translation succeeds,
            else `None`, for the i'th expression
        """
        translated_variations = []
        for expression in expressions:
            translated_variation = self._translate_allele_expression(
                expression, assembly
            )
            translated_variations.append(translated_variation)

        self.av.put_objects([v for v in translated_variations if v])
        results = []
        for variation in translated_variations:
            if variation:
                results.append(variation.id)
            else:
                results.append(None)
        return results

    def get_liftover_variation_id(
        self, vrs_id: str, starting_assembly: ReferenceAssembly
    ) -> str | None:
        """Get the VRS ID for the lifted-over equivalent of the variation specified by the provided VRS ID.

        :param vrs_id: The VRS ID of the variation to lift over
        :param starting_assembly: The assembly to liftover FROM (i.e., the assembly of the starting variant)
        :return: The VRS ID of the lifted-over variation, or `None` if liftover is unsuccessful
        """
        as_source: bool = starting_assembly == ReferenceAssembly.GRCH37
        liftover_mappings: Iterable[VariationMapping] = self.av.get_object_mappings(
            source_object_id=vrs_id, mapping_type=VariationMappingType.LIFTOVER
        )
        # liftover_mappings: VariationMapping = self.av.get_object_mappings(source_object_id=vrs_id, mapping_type=VariationMappingType.LIFTOVER, as_source=as_source)
        liftover_mapping: VariationMapping | None = next(
            iter(liftover_mappings), None
        )  # TODO: replace this line with the one above once AnyVar version is updated
        return (
            (liftover_mapping.dest_id if as_source else liftover_mapping.source_id)
            if liftover_mapping
            else None
        )

    def close(self) -> None:
        """Clean up AnyVar instance."""
        _logger.info("Closing AnyVar client.")
        self.av.object_store.close()
