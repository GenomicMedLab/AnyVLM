"""Define core FastAPI app"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from enum import Enum
from http import HTTPStatus
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request

from anyvlm import __version__
from anyvlm.anyvar.base_client import BaseAnyVarClient
from anyvlm.config import get_config
from anyvlm.functions.get_caf import get_caf
from anyvlm.schemas.common import (
    SERVICE_DESCRIPTION,
    ServiceInfo,
    ServiceOrganization,
    ServiceType,
)
from anyvlm.schemas.vlm import VlmResponse


def create_anyvar_client(
    connection_string: str = "http://localhost:8000",
) -> BaseAnyVarClient:
    """Construct new AnyVar client instance

    :param connection_string: description of connection param
    :return: client instance
    """
    raise NotImplementedError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Configure FastAPI instance lifespan.

    :param app: FastAPI app instance
    :return: async context handler
    """
    app.state.anyvar_client = create_anyvar_client()
    yield
    app.state.anyvar_client.close()


app = FastAPI(
    title="AnyVLM",
    description=SERVICE_DESCRIPTION,
    version=__version__,
    license={
        "name": "Apache 2.0",
        "url": "https://github.com/genomicmedlab/anyvlm/blob/main/LICENSE",
    },
    contact={
        "name": "Alex H. Wagner",
        "email": "Alex.Wagner@nationwidechildrens.org",
        "url": "https://www.nationwidechildrens.org/specialties/institute-for-genomic-medicine/research-labs/wagner-lab",
    },
    swagger_ui_parameters={"tryItOutEnabled": True},
    lifespan=lifespan,
)


class _Tag(str, Enum):
    """Define tag names for endpoints."""

    META = "Meta"
    SEARCH = "Search"


@app.get(
    "/service-info",
    summary="Get basic service information",
    description="Retrieve service metadata, such as versioning and contact info. Structured in conformance with the [GA4GH service info API specification](https://www.ga4gh.org/product/service-info/)",
    tags=[_Tag.META],
)
def service_info() -> ServiceInfo:
    """Provide service info per GA4GH Service Info spec"""
    return ServiceInfo(
        organization=ServiceOrganization(),
        type=ServiceType(),
        environment=get_config().env,
    )


@app.get(
    "/vlm-query",
    summary="Provides counts of occurrences of a single sequence variant, broken down by zygosity",
    description="Provides counts of occurrences of a single sequence variant, broken down by zygosity",
    tags=[_Tag.SEARCH]
)
def vlm_query(
    request: Request,
    assemblyId: Annotated[str, Query(..., description="Genome reference assembly")],
    referenceName: Annotated[str, Query(..., description="Chromosome with optional 'chr' prefix")],
    start: Annotated[int, Query(..., description="Variant position")],
    referenceBases: Annotated[str, Query(..., description="Genomic bases ('T', 'AC', etc.)")],
    alternateBases: Annotated[str, Query(..., description="Genomic bases ('T', 'AC', etc.)")]
) -> VlmResponse
    if not assemblyId or referenceName or start or referenceBases or alternateBases:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail="'assemblyId', 'referenceName', 'start', 'referenceBase', and 'alternateBases' are required",
        )
    
    valid_assembly_ids = [
        "GRCh37",
        "GRCh38",
        "hg38",
        "hg19"
    ]
    if assemblyId not in (valid_assembly_ids):
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail="assemblyId must be one of: " + ", ".join(valid_assembly_ids),
        )

    anyvar_client: BaseAnyVarClient = request.app.state.anyvar_client
    
    caf_data = get_caf(
        anyvar_client,
        assemblyId,
        referenceName,
        start,
        referenceBases,
        alternateBases
    )