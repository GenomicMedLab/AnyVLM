"""Schemas relating to VLM API."""

from pydantic import BaseModel, Field

from anyvlm import __version__

# ruff: noqa: N815 (allows camelCase vars instead of snake_case)

RESULT_ENTITY_TYPE = "genomicVariant"


class HandoverType(BaseModel):
    """The type of handover the parent `BeaconHandover` represents."""

    id: str = Field(
        default="gregor", description="Node-specific identifier"
    )  # TODO: verify what to use here. In the future this should be set dynamically.
    label: str = Field(
        default="GREGor AnVIL browser", description="Node-specific label"
    )  # TODO: verify what to use here. In the future this should be set dynamically.


class BeaconHandover(BaseModel):
    """Describes how users can get more information about the results provided in the parent `VlmResponse`"""

    handoverType: HandoverType = HandoverType()
    url: str = Field(
        default="https://anvil.terra.bio/#workspaces?filter=GREGoR",  # TODO: verify what to use here. In the future this should be set dynamically.
        description="A url which directs users to more detailed information about the results tabulated by the API (ideally human-readable)",
    )


class Meta(BaseModel):
    """Relevant metadata about the results provided in the parent `VlmResponse`"""

    apiVersion: str = __version__
    beaconId: str = Field(
        default="org.gregor.beacon",  # TODO: verify what to use here. In the future this should be set dynamically.
        description="""
            The Id of a Beacon. Usually a reversed domain string, but any URI is acceptable. The purpose of this attribute is,
            in the context of a Beacon network, to disambiguate responses coming from different Beacons. See the beacon documentation
            [here](https://github.com/ga4gh-beacon/beacon-v2/blob/c6558bf2e6494df3905f7b2df66e903dfe509500/framework/src/common/beaconCommonComponents.yaml#L26)
        """,
    )
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
        description="id should be constructed of the `HandoverType.id` + the ResultSet's zygosity",
        examples=["Geno2MP Homozygous", "MyGene2 Heterozygous"],
    )
    results: list = Field(
        default=[],
        min_length=0,
        max_length=0,
        description="This must always be set to an empty array",
    )
    resultsCount: int = Field(
        ..., description="A count for the zygosity indicated by the ResultSet's `id`"
    )
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
