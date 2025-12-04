"""Perform search against variant(s) contained by an AnyVar node, and construct cohort allele frequency model(s)"""

from ga4gh.va_spec.base.core import CohortAlleleFrequencyStudyResult

from anyvlm.anyvar.base_client import BaseAnyVarClient


def get_caf(
    anyvar_client: BaseAnyVarClient,
    assembly_id: str,
    reference_name: str,
    start: int,
    reference_bases: str,
    alternate_bases: str,
) -> list[CohortAlleleFrequencyStudyResult]:
    """Retrieve Cohort Allele Frequency data for all known variants matching provided search params

    :param anyvar_client: AnyVar client
    :param assembly_id: The reference assembly to utilize - must be one of: "GRCh37", "GRCh38", "hg38", "hg19"
    :param reference_name: The chromosome to search on, with an optional "chr" prefix - e.g., "1", "chr22", "X", "chrY", etc.
    :param start: start of range search
    :param reference_bases: Genomic bases ('T', 'AC', etc.)
    :param alternate_bases: Genomic bases ('T', 'AC', etc.)
    :return: list of CAFs contained in search interval
    """
    raise NotImplementedError  # TODO: Implement this. See Issue #16.
