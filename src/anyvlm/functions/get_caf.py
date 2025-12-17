"""Perform search against variant(s) contained by an AnyVar node, and construct cohort allele frequency model(s)"""

from anyvar.utils.types import VrsVariation
from ga4gh.core.models import iriReference
from ga4gh.va_spec.base import CohortAlleleFrequencyStudyResult
from ga4gh.vrs.models import Allele

from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.storage.base_storage import Storage
from anyvlm.utils.types import ChromosomeName, GrcAssemblyId, UcscAssemblyBuild


def get_caf(
    anyvar_client: BaseAnyVarClient,
    anyvlm_storage: Storage,
    assembly_id: GrcAssemblyId | UcscAssemblyBuild,
    chromosome_name: ChromosomeName,
    start: int,
    end: int,
) -> list[CohortAlleleFrequencyStudyResult]:
    """Retrieve Cohort Allele Frequency data for all known variants matching provided
    search params

    :param anyvar_client: AnyVar client (variant lookup)
    :param anyvlm_storage: AnyVLM Storage (CAF storage and retrieval)
    :param assembly_id: The reference assembly to utilize - must be one of: "GRCh37",
        "GRCh38", "hg38", "hg19"
    :param chromosome_name: The chromosome to search on, with an optional "chr" prefix
        - e.g., "1", "chr22", "X", "chrY", etc.
    :param start: Inclusive, inter-residue genomic start position of the interval to
        search
    :param end: Inclusive, inter-residue genomic end position of the interval to search
    :param reference_bases: Genomic bases ('T', 'AC', etc.)
    :param alternate_bases: Genomic bases ('T', 'AC', etc.)
    :return: list of CAFs contained in search interval
    """
    vrs_variations: list[VrsVariation] = anyvar_client.search_by_interval(
        f"{assembly_id}:{chromosome_name}", start, end
    )
    vrs_variations_map: dict[str, Allele] = {
        vrs_variation.id: vrs_variation
        for vrs_variation in vrs_variations
        if vrs_variation.id and isinstance(vrs_variation, Allele)
    }

    cafs: list[CohortAlleleFrequencyStudyResult] = (
        anyvlm_storage.get_caf_by_vrs_allele_ids(list(vrs_variations_map))
    )

    for caf in cafs:
        if isinstance(caf.focusAllele, iriReference):
            caf.focusAllele = vrs_variations_map[caf.focusAllele.root]

    return cafs
