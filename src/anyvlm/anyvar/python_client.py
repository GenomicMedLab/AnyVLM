"""Implement AnyVar client interface for direct Python-based access."""

import logging
from collections.abc import Iterable, Sequence

from anyvar import AnyVar
from anyvar.storage.base_storage import Storage
from anyvar.translate.translate import TranslationError, Translator
from anyvar.utils.liftover_utils import ReferenceAssembly
from anyvar.utils.types import SupportedVariationType, VrsVariation
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
        """Translate a single allele expression to a VRS Allele ID

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
        if isinstance(translated_variation, Allele):
            return translated_variation
        return None

    def get_registered_allele_expression(
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
        translated_variation = self._translate_allele_expression(expression, assembly)
        if translated_variation:
            try:
                return self.av.get_object(translated_variation.id, Allele)  # type: ignore
            except KeyError:
                _logger.exception(
                    "VRS Allele with ID %s not found", translated_variation.id
                )
        return None

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
        :param assembly: reference assembly used in expressions
        :return: list where the i'th item is either the VRS ID if translation succeeds,
            else `None`, for the i'th expression
        """
        results = []
        for expression in expressions:
            translated_variation = self._translate_allele_expression(
                expression, assembly
            )
            if translated_variation:
                self.av.put_objects([translated_variation])
                results.append(translated_variation.id)
            else:
                results.append(None)
        return results

    def search_by_interval(
        self, accession: str, start: int, end: int
    ) -> list[VrsVariation]:
        """Get all variation IDs located within the specified range

        :param accession: sequence accession
        :param start: start position for genomic region
        :param end: end position for genomic region
        :return: list of matching variant objects
        """
        try:
            if accession.startswith("ga4gh:"):
                ga4gh_id = accession
            else:
                ga4gh_id = self.av.translator.get_sequence_id(accession)
        except KeyError:
            return []

        alleles = []
        if ga4gh_id:
            refget_accession = ga4gh_id.split("ga4gh:")[-1]
            alleles = self.av.object_store.search_alleles(refget_accession, start, end)

        return alleles  # type: ignore[reportReturnType]

    def close(self) -> None:
        """Clean up AnyVar instance."""
        _logger.info("Closing AnyVar client.")
        self.av.object_store.close()
