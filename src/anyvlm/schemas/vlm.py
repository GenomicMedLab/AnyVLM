"""Schemas relating to VLM API."""

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

from anyvlm.utils.types import Zygosity

# ruff: noqa: N815 (allows camelCase vars instead of snake_case to align with expected VLM protocol response)

RESULT_ENTITY_TYPE = "genomicVariant"


class HandoverType(BaseModel):
    """The type of handover the parent `BeaconHandover` represents."""

    id: str = Field(
        default="gregor", description="Node-specific identifier"
    )  # TODO: enable configuration of this field. See Issue #27.
    label: str = Field(
        default="GREGoR AnVIL browser", description="Node-specific label"
    )  # TODO: enable configuration of this field. See Issue #27.


class BeaconHandover(BaseModel):
    """Describes how users can get more information about the results provided in the parent `VlmResponse`"""

    handoverType: HandoverType = HandoverType()
    url: str = Field(
        default="https://anvil.terra.bio/#workspaces?filter=GREGoR",  # TODO: enable configuration of this field. See Issue #27.
        description="A url which directs users to more detailed information about the results tabulated by the API (ideally human-readable)",
    )


class ReturnedSchema(BaseModel):
    """Fixed [Beacon Schema](https://github.com/ga4gh-beacon/beacon-v2/blob/c6558bf2e6494df3905f7b2df66e903dfe509500/framework/json/common/beaconCommonComponents.json#L241)"""

    entityType: str = Field(
        default=RESULT_ENTITY_TYPE,
        description=f"The type of entity this response describes. Must always be set to '{RESULT_ENTITY_TYPE}'",
    )
    schema_: str = Field(
        default="ga4gh-beacon-variant-v2.0.0",
        # Alias is required because 'schema' is reserved by Pydantic's BaseModel class,
        # But VLM expects a field named 'schema'
        alias="schema",
    )

    model_config = {"populate_by_name": True}


class Meta(BaseModel):
    """Relevant metadata about the results provided in the parent `VlmResponse`"""

    apiVersion: str = Field(
        default="v1.0",
        description="The version of the VLM API that this response conforms to",
    )
    beaconId: str = Field(
        default="org.gregor.beacon",  # TODO: enable configuration of this field. See Issue #27.
        description="""
            The Id of a Beacon. Usually a reversed domain string, but any URI is acceptable. The purpose of this attribute is,
            in the context of a Beacon network, to disambiguate responses coming from different Beacons. See the beacon documentation
            [here](https://github.com/ga4gh-beacon/beacon-v2/blob/c6558bf2e6494df3905f7b2df66e903dfe509500/framework/src/common/beaconCommonComponents.yaml#L26)
        """,
    )
    returnedSchemas: list[ReturnedSchema] = [ReturnedSchema()]


class ResponseSummary(BaseModel):
    """A high-level summary of the results provided in the parent `VlmResponse"""

    exists: bool = Field(
        ..., description="Indicates whether the response contains any results."
    )
    numTotalResults: int = Field(
        ..., description="The total number of results found for the given query"
    )


class ResultSet(BaseModel):
    """A set of cohort allele frequency results. The zygosity of the ResultSet is identified in the `id` field"""

    exists: Literal[True] = Field(
        default=True,
        description="Indicates whether this ResultSet exists. This must always be `True`, even if `resultsCount` = `0`",
    )
    id: str = Field(
        ...,
        description="id should be constructed of the `HandoverType.id` + the ResultSet's zygosity. See `validate_resultset_ids` validator in `VlmResponse` class.",
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
    setType: str = Field(
        default=RESULT_ENTITY_TYPE,
        description=f"The type of entity relevant to these results. Must always be set to '{RESULT_ENTITY_TYPE}'",
    )


class ResponseField(BaseModel):
    """A list of ResultSets"""

    resultSets: list[ResultSet] = Field(
        ..., description="A list of ResultSets for the given query."
    )


class VlmResponse(BaseModel):
    """Define response structure for the variant_counts endpoint."""

    beaconHandovers: list[BeaconHandover] = [BeaconHandover()]
    meta: Meta = Meta()
    responseSummary: ResponseSummary
    response: ResponseField

    @model_validator(mode="after")
    def validate_resultset_ids(self) -> Self:
        """Ensure each ResultSet.id is correctly constructed."""
        handover_ids: list[str] = [
            beaconHandover.handoverType.id for beaconHandover in self.beaconHandovers
        ]

        for result_set in self.response.resultSets:
            node_id, zygosity = result_set.id.split(" ")

            if node_id not in handover_ids:
                error_message = f"Invalid ResultSet id - ids must be in form '<node_id> <zygosity>', but provided node_id of {node_id} does not match any `handoverType.id` provided in `self.beaconHandovers`"
                raise ValueError(error_message)

            try:
                Zygosity(zygosity)
            except ValueError as e:
                valid_zygosity_values = {zygosity.value for zygosity in Zygosity}
                error_message = f"Invalid ResultSet id - ids must be in form '<node_id> <zygosity>', but provided zygosity of {zygosity} is not found in allowable value set of: {', '.join(valid_zygosity_values)}"
                raise ValueError(error_message) from e

        return self
