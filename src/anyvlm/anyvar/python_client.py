"""Implement AnyVar client interface for direct Python-based access."""

import logging
from collections.abc import Iterable

from anyvar import AnyVar
from anyvar.storage.base_storage import Storage
from anyvar.translate.translate import TranslationError, Translator
from anyvar.utils.types import VrsVariation

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

    def put_allele_expressions(
        self, expressions: Iterable[str], assembly: str = "GRCh38"
    ) -> list[str | None]:
        """Submit allele expressions to an AnyVar instance and retrieve corresponding VRS IDs

        :param expressions: variation expressions to register
        :param assembly: reference assembly used in expressions
        :return: list where the i'th item is either the VRS ID if translation succeeds,
            else `None`, for the i'th expression
        """
        results = []
        for expression in expressions:
            translated_variation = None
            try:
                translated_variation = self.av.translator.translate_variation(
                    expression, assembly=assembly
                )
            except TranslationError:
                _logger.exception("Failed to translate expression: %s", expression)
            self.av.put_objects([translated_variation])  # type: ignore
            results.append(translated_variation.id)  # type: ignore
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
        self.av.object_store.close()
