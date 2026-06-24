"""Perform search against variant(s) contained by an AnyVar node, and construct cohort allele frequency model(s)"""

import logging

from ga4gh.core.models import iriReference
from ga4gh.vrs.models import Allele

from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.storage.base_storage import Storage
from anyvlm.utils.functions import validate_allele
from anyvlm.utils.types import (
    ASSEMBLY_MAP,
    AnyVlmCohortAlleleFrequencyResult,
    ChromosomeName,
    GrcAssemblyId,
    Nucleotide,
    UcscAssemblyBuild,
)

_logger = logging.getLogger(__name__)


def _retrieve_cafs_with_resolved_alleles(
    variation: Allele, anyvlm_storage: Storage
) -> list[AnyVlmCohortAlleleFrequencyResult]:
    """Retrieve CAF data for a resolved allele.

    :param variation: The allele to retrieve CAF data for
    :param anyvlm_storage: The storage for this AnyVLM instance
    :return: A list of AnyVlmCohortAlleleFrequencyResult objects
    """
    cafs: list[AnyVlmCohortAlleleFrequencyResult] = (
        anyvlm_storage.get_cafs_by_vrs_allele_id(vrs_allele_id=variation.id)  # pyright: ignore[reportArgumentType]
    )

    for caf in cafs:
        if isinstance(caf.focusAllele, iriReference):
            caf.focusAllele = variation

    return cafs


def get_cafs(
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
    :raises VariantLookupError: if variant is not registered in AnyVar
    :return: list of AnyVlmCohortAlleleFrequencyResult objects for the provided variant
    """
    gnomad_vcf: str = f"{reference_name}-{start}-{reference_base}-{alternate_base}"
    try:
        assembly = ASSEMBLY_MAP[assembly_id]
    except KeyError as e:
        msg = "Unsupported assembly ID: {assembly_id}"
        raise ValueError(msg) from e

    vrs_variation: Allele = validate_allele(
        allele=anyvar_client.retrieve_allele_by_expression(gnomad_vcf, assembly)
    )

    cafs: list[AnyVlmCohortAlleleFrequencyResult] = (
        _retrieve_cafs_with_resolved_alleles(
            variation=vrs_variation, anyvlm_storage=anyvlm_storage
        )
    )

    liftover_vrs_id: str | None = anyvar_client.get_liftover_variation_id(
        vrs_id=vrs_variation.id,  # type: ignore
        starting_assembly=assembly,
    )

    if liftover_vrs_id:
        liftover_variation: Allele = validate_allele(
            allele=anyvar_client.retrieve_allele_by_id(vrs_id=liftover_vrs_id)
        )

        liftover_cafs: list[AnyVlmCohortAlleleFrequencyResult] = (
            _retrieve_cafs_with_resolved_alleles(
                variation=liftover_variation, anyvlm_storage=anyvlm_storage
            )
        )

        cafs.extend(liftover_cafs)

    return cafs
