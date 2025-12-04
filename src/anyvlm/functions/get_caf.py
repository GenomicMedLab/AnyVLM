"""Perform search against variant(s) contained by an AnyVar node, and construct cohort allele frequency model(s)"""

from ga4gh.va_spec.base.core import CohortAlleleFrequencyStudyResult

from anyvlm.anyvar.base_client import BaseAnyVarClient


def get_caf(
    av: BaseAnyVarClient, accession_id: str, start: int, end: int
) -> list[CohortAlleleFrequencyStudyResult]:
    """Retrieve Cohort Allele Frequency data for all known variants matching provided search params

    :param av: AnyVar client
    :param accession_id: ID for sequence to search upon
    :param start: start of range search
    :param end: end of range to search
    :return: list of CAFs contained in search interval
    """
    raise NotImplementedError
