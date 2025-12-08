"""Implement AnyVar client interface for direct Python-based access."""

import logging

from anyvar import AnyVar
from anyvar.storage.base_storage import Storage
from anyvar.translate.translate import Translator
from anyvar.utils.types import VrsVariation

from anyvlm.anyvar.base_client import BaseAnyVarClient, UnidentifiedObjectError

_logger = logging.getLogger(__name__)


class PythonAnyVarClient(BaseAnyVarClient):
    """A Python-based AnyVar client."""

    def __init__(self, translator: Translator, storage: Storage) -> None:
        """Initialize directly-connected AnyVar client

        :param translator: AnyVar translator instance
        :param storage: AnyVar storage instance
        """
        self.av = AnyVar(translator, storage)

    def put_objects(self, objects: list[VrsVariation]) -> None:
        """Register objects with AnyVar

        All input objects must have a populated ID field. A validation check for this is
        performed before any variants are registered.

        :param objects: variation objects to register
        :raise UnidentifiedObjectError: if *any* provided object lacks a VRS ID
        """
        for variant in objects:
            if not variant.id:
                _logger.error("Provided variant %s has no VRS ID: %s")
                raise UnidentifiedObjectError
        self.av.put_objects(objects)  # type: ignore[reportArgumentType]

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
