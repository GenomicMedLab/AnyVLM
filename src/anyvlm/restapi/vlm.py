"""Define route(s) for the variant-level matching (VLM) protocol"""

from pathlib import Path
from typing import Annotated

from fastapi import Query, Request
from ga4gh.va_spec.base.core import CohortAlleleFrequencyStudyResult

from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.functions.build_vlm_response import build_vlm_response
from anyvlm.functions.get_caf import get_caf
from anyvlm.main import app
from anyvlm.schemas.vlm import (
    VlmResponse,
)
from anyvlm.utils.types import (
    ChromosomeName,
    EndpointTag,
    GenomicSequence,
    GrcAssemblyId,
    UscsAssemblyBuild,
)


def ingest_vcf(vcf_path: Path) -> None:
    """Ingest variants and cohort allele frequency data from an input VCF

    :param vcf_path: VCF file location
    """
    raise NotImplementedError


@app.get(
    "/vlm-query",
    summary="Provides counts of occurrences of a single sequence variant, broken down by zygosity",
    description="Search for a single sequence variant and receive a count of its observed occurrences broken down by zygosity, in accordance with the Variant-Level Matching protocol",
    tags=[EndpointTag.SEARCH],
)
def vlm_query(
    request: Request,
    assemblyId: Annotated[  # noqa: N803
        GrcAssemblyId | UscsAssemblyBuild,
        Query(..., description="Genome reference assembly"),
    ],
    referenceName: Annotated[  # noqa: N803
        ChromosomeName, Query(..., description="Chromosome with optional 'chr' prefix")
    ],
    start: Annotated[int, Query(..., description="Variant position")],
    referenceBases: Annotated[  # noqa: N803
        GenomicSequence, Query(..., description="Genomic bases ('T', 'AC', etc.)")
    ],
    alternateBases: Annotated[  # noqa: N803
        GenomicSequence, Query(..., description="Genomic bases ('T', 'AC', etc.)")
    ],
) -> VlmResponse:
    """Accept a Variant-Level Matching network request and return a count of occurrences of a single sequence variant, broken down by zygosity.

    :param request: FastAPI `Request` object
    :param assemblyId: The genome reference assembly. Must be a GRC assembly identifier (e.g., "GRCh38) or a USCS assembly build (e.g., "hg38")
    :param referenceName: The name of the reference chromosome, with optional 'chr' prefix
    :param start: The start of the variant's position
    :param referenceBases: Genomic bases ('T', 'AC', etc.)
    :param alternateBases: Genomic bases ('T', 'AC', etc.)
    :return: A VlmResponse object containing cohort allele frequency data. If no matches are found, endpoint will return a status code of 200 with an empty set of results.
    """
    anyvar_client: BaseAnyVarClient = request.app.state.anyvar_client
    caf_data: list[CohortAlleleFrequencyStudyResult] = get_caf(
        anyvar_client, assemblyId, referenceName, start, referenceBases, alternateBases
    )
    return build_vlm_response(caf_data)
