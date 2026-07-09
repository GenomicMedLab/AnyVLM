"""Define route(s) for the variant-level matching (VLM) protocol"""

import logging
from http import HTTPStatus
from typing import Annotated

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
)

from anyvlm.anyvar.base_client import AnyVarClientConnectionError, BaseAnyVarClient
from anyvlm.functions.build_vlm_response import build_vlm_response
from anyvlm.functions.get_cafs import get_cafs
from anyvlm.schemas.vlm import VlmResponse
from anyvlm.storage.base_storage import Storage
from anyvlm.utils.exceptions import VariantLookupError
from anyvlm.utils.types import (
    AnyVlmCohortAlleleFrequencyResult,
    ChromosomeName,
    EndpointTag,
    GrcAssemblyId,
    Nucleotide,
    UcscAssemblyBuild,
)

_logger = logging.getLogger(__name__)

router = APIRouter()


# ====================
# Endpoints
# ====================

_allele_counts_description = """Search for a SNP and receive allele counts by zygosity, in accordance with the Variant-Level Matching protocol.

* Unrecognized variants will return a `200 OK` response with a `resultsCount` of 0
"""


@router.get(
    "/variant_counts",
    summary="Get allele counts of a single sequence variant, broken down by zygosity",
    description=_allele_counts_description,
    tags=[EndpointTag.SEARCH],
)
# ruff: noqa: N803, D103
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
        Nucleotide, Query(..., description="Single genomic base (A/C/T/G)")
    ],
    alternateBases: Annotated[
        Nucleotide, Query(..., description="Single genomic base (A/C/T/G)")
    ],
) -> VlmResponse:
    anyvar_client: BaseAnyVarClient = request.app.state.anyvar_client
    anyvlm_storage: Storage = request.app.state.anyvlm_storage

    try:
        caf_data: list[AnyVlmCohortAlleleFrequencyResult] = get_cafs(
            anyvar_client,
            anyvlm_storage,
            assemblyId,
            referenceName,
            start,
            referenceBases,
            alternateBases,
        )
    except VariantLookupError:
        caf_data = []
    except AnyVarClientConnectionError as e:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="Unable to establish AnyVar connection",
        ) from e
    return build_vlm_response(caf_data)
