"""Perform search against variant(s) contained by an AnyVar node, and construct cohort allele frequency model(s)"""

import logging

from ga4gh.core.models import iriReference

from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.storage.base_storage import Storage
from anyvlm.utils.types import (
    ASSEMBLY_MAP,
    AnyVlmCohortAlleleFrequencyResult,
    ChromosomeName,
    GrcAssemblyId,
    Nucleotide,
    UcscAssemblyBuild,
)

_logger = logging.getLogger(__name__)


class VariantNotRegisteredError(Exception):
    """Raised when a variant is not registered in the AnyVar client"""


def get_caf(
    anyvar_client: BaseAnyVarClient,
    anyvlm_storage: Storage,
    assembly_id: GrcAssemblyId | UcscAssemblyBuild,
    reference_name: ChromosomeName,
    start: int,
    reference_base: Nucleotide,
    alternate_base: Nucleotide,
) -> list[AnyVlmCohortAlleleFrequencyResult]:
    """Retrieve Cohort Allele Frequency data for all known registered variants matching
    provided search params

    :param anyvar_client: AnyVar client (variant lookup)
    :param anyvlm_storage: AnyVLM Storage (CAF storage and retrieval)
    :param assembly_id: The reference assembly to utilize
    :param reference_name: The chromosome to search on, with an optional "chr" prefix
        - e.g., "1", "chr22", "X", "chrY", etc.
    :param start: start of range search. Uses residue coordinates (1-based)
    :param reference_bases: Single genomic base (A/G/C/T)
    :param alternate_bases: Single genomic base (A/G/C/T)
    :raises ValueError: if unsupported assembly ID is provided
    :raises VariantNotRegisteredError: if variant is not registered in AnyVar
    :return: list of AnyVlmCohortAlleleFrequencyResult objects for the provided variant
    """
    gnomad_vcf: str = f"{reference_name}-{start}-{reference_base}-{alternate_base}"
    try:
        assembly = ASSEMBLY_MAP[assembly_id]
    except KeyError as e:
        msg = "Unsupported assembly ID: {assembly_id}"
        raise ValueError(msg) from e

    vrs_variation = anyvar_client.get_registered_allele(gnomad_vcf, assembly)
    _logger.debug(
        "Variant %s %s is not registered in AnyVar", assembly.value, gnomad_vcf
    )

    cafs: list[AnyVlmCohortAlleleFrequencyResult] = (
        anyvlm_storage.get_caf_by_vrs_allele_id(vrs_variation.id)  # type: ignore
    )

    for caf in cafs:
        if isinstance(caf.focusAllele, iriReference):
            caf.focusAllele = vrs_variation

    return cafs
