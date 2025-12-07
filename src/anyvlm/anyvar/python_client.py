"""Implement AnyVar client interface for direct Python-based access."""

from anyvar import AnyVar
from anyvar.storage.base_storage import IncompleteVrsObjectError, Storage
from anyvar.translate.translate import Translator
from anyvar.utils.types import VrsVariation, recursive_identify

from anyvlm.anyvar.base_client import BaseAnyVarClient


class PythonAnyVarClient(BaseAnyVarClient):
    """A Python-based AnyVar client."""

    def __init__(self, translator: Translator, storage: Storage) -> None:  # noqa: D107
        self.av = AnyVar(translator, storage)

    def put_objects(self, objects: list[VrsVariation]) -> list[VrsVariation]:
        """Register objects with AnyVar

        :param objects: variation objects to register
        :return: completed VRS objects
        """
        complete_variations = []
        for variation in objects:
            try:
                self.av.put_objects([variation])
            except IncompleteVrsObjectError:
                variation = recursive_identify(variation)  # noqa: PLW2901
                self.av.put_objects([variation])
            complete_variations.append(variation)
        return complete_variations

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
