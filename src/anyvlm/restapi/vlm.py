"""Define route(s) for the variant-level matching (VLM) protocol"""

from pathlib import Path
from typing import Annotated

from fastapi import Query, Request

from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.functions.build_vlm_response import build_vlm_response
from anyvlm.functions.get_caf import get_caf
from anyvlm.main import app
from anyvlm.schemas.vlm import (
    VlmResponse,
)
from anyvlm.storage.base_storage import Storage
from anyvlm.utils.types import (
    AnyVlmCohortAlleleFrequencyResult,
    ChromosomeName,
    EndpointTag,
    GrcAssemblyId,
    NucleotideSequence,
    UcscAssemblyBuild,
)


def ingest_vcf(vcf_path: Path) -> None:
    """Ingest variants and cohort allele frequency data from an input VCF

    :param vcf_path: VCF file location
    """
    raise NotImplementedError


@app.get(
    "/variant_counts",
    summary="Provides allele counts of a single sequence variant, broken down by zygosity",
    description="Search for a single sequence variant and receive allele counts by zygosity, in accordance with the Variant-Level Matching protocol",
    tags=[EndpointTag.SEARCH],
)
# ruff: noqa: D103, N803 (allow camelCase args and don't require docstrings)
def variant_counts(
    request: Request,
    assemblyId: Annotated[
        GrcAssemblyId | UcscAssemblyBuild,
        Query(..., description="Genome reference assembly"),
    ],
    referenceName: Annotated[
        ChromosomeName, Query(..., description="Chromosome with optional 'chr' prefix")
    ],
    start: Annotated[int, Query(..., description="Variant position")],
    referenceBases: Annotated[
        NucleotideSequence, Query(..., description="Genomic bases ('T', 'AC', etc.)")
    ],
    alternateBases: Annotated[
        NucleotideSequence, Query(..., description="Genomic bases ('T', 'AC', etc.)")
    ],
) -> VlmResponse:
    anyvar_client: BaseAnyVarClient = request.app.state.anyvar_client
    anyvlm_storage: Storage = request.app.state.anyvlm_storage
    caf_data: list[AnyVlmCohortAlleleFrequencyResult] = get_caf(
        anyvar_client,
        anyvlm_storage,
        assemblyId,
        referenceName,
        start,
        referenceBases,
        alternateBases,
    )
    return build_vlm_response(caf_data)
