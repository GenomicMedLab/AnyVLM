"""Perform search against variant(s) contained by an AnyVar node, and construct cohort allele frequency model(s)"""

from anyvar.utils.types import VrsVariation
from ga4gh.core.models import iriReference
from ga4gh.va_spec.base import CohortAlleleFrequencyStudyResult
from ga4gh.vrs.models import Allele

from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.storage.base_storage import Storage


def get_caf(
    anyvar: BaseAnyVarClient,
    anyvlm_storage: Storage,
    accession_id: str,
    start: int,
    end: int,
) -> list[CohortAlleleFrequencyStudyResult]:
    """Retrieve Cohort Allele Frequency data for all known variants matching provided search params

    :param anyvar: AnyVar client (variant lookup)
    :param anyvlm_storage: AnyVLM Storage (CAF storage and retrieval)
    :param accession_id: ID for sequence to search upon
    :param start: start of range search
    :param reference_bases: Genomic bases ('T', 'AC', etc.)
    :param alternate_bases: Genomic bases ('T', 'AC', etc.)
    :return: list of CAFs contained in search interval
    """
    vrs_variations: list[VrsVariation] = anyvar.search_by_interval(
        accession_id, start, end
    )
    vrs_variations_map: dict[str, Allele] = {
        vrs_variation.id: vrs_variation
        for vrs_variation in vrs_variations
        if vrs_variation.id and isinstance(vrs_variation, Allele)
    }

    cafs: list[CohortAlleleFrequencyStudyResult] = anyvlm_storage.get_caf_by_vrs_ids(
        list(vrs_variations_map)
    )

    for caf in cafs:
        if isinstance(caf.focusAllele, iriReference):
            caf.focusAllele = vrs_variations_map[caf.focusAllele.root]

    return cafs
