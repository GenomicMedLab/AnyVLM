"""Perform search against variant(s) contained by an AnyVar node, and construct cohort allele frequency model(s)"""

import logging

from anyvar.core.objects import SupportedVrsVariation
from ga4gh.core.models import iriReference
from ga4gh.vrs.models import Allele, VrsType

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


class VariantLookupError(Exception):
    """Raised when a variant cannot be retrieved from AnyVar"""


class IncompleteVariantError(Exception):
    """Raised when a variant is missing one or more properties required by AnyVLM"""


class UnexpectedVariantTypeError(Exception):
    """Raised when <vrs_variant>.type is not of the type expected by AnyVLM"""


def _validate_allele(variant: SupportedVrsVariation | None) -> Allele:
    if not variant:
        raise VariantLookupError

    variant_id: str | None = variant.id
    if not variant_id:
        raise IncompleteVariantError

    if not variant.type == str(VrsType.ALLELE):
        raise UnexpectedVariantTypeError

    return variant


def _retrieve_caf_with_resolved_alleles(
    variation: Allele, anyvlm_storage: Storage
) -> list[AnyVlmCohortAlleleFrequencyResult]:
    """Retrieve CAF data for a resolved allele.

    :param variation: The allele to retrieve CAF data for
    :param anyvlm_storage: The storage for this AnyVLM instance
    :return: A list of AnyVlmCohortAlleleFrequencyResult objects
    """
    if not variation.id:
        error_message: str = "Variants must include an 'id'"
        raise IncompleteVariantError(error_message)

    cafs: list[AnyVlmCohortAlleleFrequencyResult] = (
        anyvlm_storage.get_caf_by_vrs_allele_id(vrs_allele_id=variation.id)
    )

    for caf in cafs:
        if isinstance(caf.focusAllele, iriReference):
            caf.focusAllele = variation

    return cafs


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
    :raises VariantLookupError: if variant is not registered in AnyVar
    :return: list of AnyVlmCohortAlleleFrequencyResult objects for the provided variant
    """
    gnomad_vcf: str = f"{reference_name}-{start}-{reference_base}-{alternate_base}"
    try:
        assembly = ASSEMBLY_MAP[assembly_id]
    except KeyError as e:
        msg = "Unsupported assembly ID: {assembly_id}"
        raise ValueError(msg) from e

    vrs_variation: Allele = _validate_allele(
        variant=anyvar_client.retrieve_allele_by_expression(gnomad_vcf, assembly)
    )

    cafs: list[AnyVlmCohortAlleleFrequencyResult] = _retrieve_caf_with_resolved_alleles(
        variation=vrs_variation, anyvlm_storage=anyvlm_storage
    )

    liftover_vrs_id: str | None = anyvar_client.get_liftover_variation_id(
        vrs_id=vrs_variation.id,  # type: ignore
        starting_assembly=assembly,
    )

    if liftover_vrs_id:
        liftover_variation: Allele | None = _validate_allele(
            variant=anyvar_client.retrieve_allele_by_id(vrs_id=liftover_vrs_id)
        )

        liftover_cafs: list[AnyVlmCohortAlleleFrequencyResult] = (
            _retrieve_caf_with_resolved_alleles(
                variation=liftover_variation, anyvlm_storage=anyvlm_storage
            )
        )

        cafs.extend(liftover_cafs)

    return cafs
