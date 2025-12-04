"""Schemas relating to VLM API."""

from pydantic import BaseModel, Field

from anyvlm import __version__

# ruff: noqa: N815

RESULT_ENTITY_TYPE = "genomicVariant"


class HandoverType(BaseModel):
    """The type of handover the parent `BeaconHandover` represents."""

    id: str = Field(
        default="gregor", description="Node-specific identifier"
    )  # TODO: verify what to use here
    label: str = Field(
        default="GREGor", description="Node-specific label"
    )  # TODO: verify what to use here


class BeaconHandover(BaseModel):
    """Describes how users can get more information about the results provided in the parent `VlmResponse`"""

    handoverType: HandoverType = HandoverType()
    url: str = "https://anvil.terra.bio/#workspaces?filter=GREGoR"  # TODO: verify what to use here


class Meta(BaseModel):
    """Relevant metadata about the results provided in the parent `VlmResponse`"""

    apiVersion: str = __version__
    beaconId: str = "org.gregor"  # TODO: verify what to use here
    returnedSchemas: list[dict[str, str]] = [
        {"entityType": RESULT_ENTITY_TYPE, "schema": "ga4gh-beacon-variant-v2.0.0"}
    ]


class ResponseSummary(BaseModel):
    """A high-level summary of the results provided in the parent `VlmResponse"""

    exists: bool
    total: int


class ResultSet(BaseModel):
    """A set of cohort allele frequency results. The zygosity of the ResultSet is identified in the `id` field"""

    exists: bool
    id: str = Field(
        ...,
        description="id should be constructed of the `HandoverType.id` + the result set's zygosity",
        examples=["Geno2MP Homozygous", "MyGene2 Heterozygous"],
    )
    results: list = Field(
        default=[],
        min_length=0,
        max_length=0,
        description="This must always be set to an empty array",
    )
    resultsCount: int
    setType: str = RESULT_ENTITY_TYPE


class ResponseField(BaseModel):
    """A list of ResultSets"""

    resultSets: list[ResultSet]


class VlmResponse(BaseModel):
    """Defines response structure for the vlm-query endpoint."""

    beaconHandovers: list[BeaconHandover] = [BeaconHandover()]
    meta: Meta = Meta()
    responseSummary: ResponseSummary
    response: ResponseField
