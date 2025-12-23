"""Perform search against variant(s) contained by an AnyVar node, and construct cohort allele frequency model(s)"""

from ga4gh.core.models import iriReference
from ga4gh.va_spec.base import CohortAlleleFrequencyStudyResult

from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.storage.base_storage import Storage
from anyvlm.utils.types import (
    ASSEMBLY_MAP,
    ChromosomeName,
    GrcAssemblyId,
    NucleotideSequence,
    UcscAssemblyBuild,
)


def get_caf(
    anyvar_client: BaseAnyVarClient,
    anyvlm_storage: Storage,
    assembly_id: GrcAssemblyId | UcscAssemblyBuild,
    reference_name: ChromosomeName,
    start: int,
    reference_bases: NucleotideSequence,
    alternate_bases: NucleotideSequence,
) -> list[CohortAlleleFrequencyStudyResult]:
    """Retrieve Cohort Allele Frequency data for all known variants matching provided
    search params

    :param anyvar_client: AnyVar client (variant lookup)
    :param anyvlm_storage: AnyVLM Storage (CAF storage and retrieval)
    :param assembly_id: The reference assembly to utilize - must be one of: "GRCh37",
        "GRCh38", "hg38", "hg19"
    :param reference_name: The chromosome to search on, with an optional "chr" prefix
        - e.g., "1", "chr22", "X", "chrY", etc.
    :param start: start of range search. Uses residue coordinates (1-based)
    :param reference_bases: Genomic bases ('T', 'AC', etc.)
    :param alternate_bases: Genomic bases ('T', 'AC', etc.)
    :raises ValueError: if unsupported assembly ID is provided
    :return: list of CAFs contained in search interval
    """
    gnomad_vcf: str = f"{reference_name}-{start}-{reference_bases}-{alternate_bases}"
    try:
        assembly = ASSEMBLY_MAP[assembly_id]
    except KeyError as e:
        msg = "Unsupported assembly ID: {assembly_id}"
        raise ValueError(msg) from e
    vrs_variation = anyvar_client.get_registered_allele_expression(gnomad_vcf, assembly)
    if not vrs_variation:
        return []

    cafs: list[CohortAlleleFrequencyStudyResult] = (
        anyvlm_storage.get_caf_by_vrs_allele_id(vrs_variation.id)  # type: ignore
    )

    for caf in cafs:
        if isinstance(caf.focusAllele, iriReference):
            caf.focusAllele = vrs_variation

    return cafs
