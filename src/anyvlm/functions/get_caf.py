"""Perform search against variant(s) contained by an AnyVar node, and construct cohort allele frequency model(s)"""

from anyvar.utils.types import VrsVariation
from ga4gh.va_spec.base.core import CohortAlleleFrequencyStudyResult

from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.anyvlm import AnyVLM


def get_caf(
    anyvar: BaseAnyVarClient,
    anyvlm: AnyVLM,
    accession_id: str,
    start: int,
    end: int,
) -> list[CohortAlleleFrequencyStudyResult]:
    """Retrieve Cohort Allele Frequency data for all known variants matching provided search params

    :param anyvar: AnyVar client (variant lookup)
    :param anyvlm: AnyVLM client (caf lookup)
    :param accession_id: ID for sequence to search upon
    :param start: start of range search
    :param end: end of range to search
    :return: list of CAFs contained in search interval
    """
    vrs_variations: list[VrsVariation] = anyvar.search_by_interval(
        accession_id, start, end
    )
    return anyvlm.get_caf_for_variations(vrs_variations)
