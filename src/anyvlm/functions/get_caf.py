"""Perform search against variant(s) contained by an AnyVar node, and construct cohort allele frequency model(s)"""

from ga4gh.va_spec.base.core import CohortAlleleFrequencyStudyResult

from anyvlm.anyvar.base_client import BaseAnyVarClient


def get_caf(
    anyvar_client: BaseAnyVarClient, assembly_id: str, referenceName: str, start: int, referenceBases: str, alternateBases: str
) -> list[CohortAlleleFrequencyStudyResult]:
    """Retrieve Cohort Allele Frequency data for all known variants matching provided search params

    :param anyvar_client: AnyVar client
    :param assembly_id: The reference assembly to utilize - must be one of: "GRCh37", "GRCh38", "hg38", "hg19"
    :param referenceName: The chromosome to search on, with an optional "chr" prefix - e.g., "1", "chr22", "X", "chrY", etc.
    :param start: start of range search
    :param referenceBases: Genomic bases ('T', 'AC', etc.)
    :param alternateBases: Genomic bases ('T', 'AC', etc.)
    :return: list of CAFs contained in search interval
    """
    raise NotImplementedError #TODO: Implement this. See Issue #16.
