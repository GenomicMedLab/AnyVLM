"""Schemas relating to VLM API."""

from typing import ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from anyvlm.utils.types import Zygosity

# ruff: noqa: N815, D107 (allow camelCase instead of snake_case to align with expected VLM protocol response + don't require init docstrings)

RESULT_ENTITY_TYPE = "genomicVariant"


class HandoverType(BaseModel):
    """The type of handover the parent `BeaconHandover` represents."""

    id: str = Field(
        default="gregor",  # TODO fix
        description="Definition of an identifier in the CURIE `prefix:local-part` format which is the default type of e.g. ontology term `id` values (used e.g. for filters or external identifiers).",
        pattern="^\\w[^:]+:.+$",
        examples=[
            "ga4gh:GA.01234abcde",
            "DUO:0000004",
            "orcid:0000-0003-3463-0775",
            "PMID:15254584",
        ],
    )
    label: str = Field(
        description="The text that describes the term. By default it could be the preferred text of the term, but is it acceptable to customize it for a clearer description and understanding of the term in an specific context."
    )


class BeaconHandover(BaseModel):
    """Describes how users can get more information about the results provided in the parent `VlmResponse`"""

    handoverType: HandoverType = Field(
        ...,
        description='Handover type, as an Ontology_term object with CURIE syntax for the `id` value. Use "CUSTOM:123455" CURIE-style `id` when no ontology is available',
        examples=[  # TODO update these with better examples
            {"id": "EDAM:2572", "label": "BAM"},
            {"id": "EDAM:3016", "label": "VCF"},
            {"id": "CUSTOM:pgxseg", "label": "genomic variants in .pgxseg file format"},
        ],
    )
    url: str = Field(
        ...,
        pattern=r"^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?",
        description="URL endpoint to where the handover process could progress, in RFC3986 format",
    )
    note: str = Field(
        default="",
        description="An optional text including considerations on the handover link provided.",
        examples=["This handover link provides access to a summarized VCF."],
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
        # But VLM protocol expects a field named 'schema'
        alias="schema",
    )

    model_config = ConfigDict(populate_by_name=True)


class MetaSettings(BaseSettings):
    """Settings for 'Meta' class"""

    beaconId: str = Field(..., alias="BEACON_NODE_ID")

    model_config = SettingsConfigDict(env_prefix="", extra="ignore", env_file=".env")


meta_settings = MetaSettings()  # type: ignore


class Meta(BaseModel):
    """Relevant metadata about the results provided in the parent `VlmResponse`"""

    apiVersion: Literal["v1.0"] = "v1.0"
    beaconId: str = Field(
        default="",
        description=(
            "The Id of a Beacon. Usually a reversed domain string, but any URI is acceptable. "
            "The purpose of this attribute is,in the context of a Beacon network, to disambiguate "
            "responses coming from different Beacons. See the beacon documentation "
            "[here](https://github.com/ga4gh-beacon/beacon-v2/blob/c6558bf2e6494df3905f7b2df66e903dfe509500/framework/src/common/beaconCommonComponents.yaml#L26)"
        ),
    )
    returnedSchemas: list[ReturnedSchema] = [ReturnedSchema()]

    # custom __init__ to prevent overriding attributes that are static or set via environment variables
    def __init__(self) -> None:
        super().__init__(beaconId=meta_settings.beaconId)


class ResponseSummary(BaseModel):
    """A high-level summary of the results provided in the parent `VlmResponse"""

    exists: bool = Field(..., description="Whether the variant exists in the database.")
    numTotalResults: int = Field(
        ..., description="The total number of results found for the given query"
    )


class ResultSet(BaseModel):
    """A set of cohort allele frequency results. The zygosity of the ResultSet is identified in the `id` field"""

    exists: bool = Field(
        ...,
        description="Indicates whether this ResultSet exists.",
    )
    # ResultSet.id should be "<HandoverType.id> <the ResultSet's zygosity>"
    # See `validate_resultset_ids` validator in `VlmResponse` class
    id: str = Field(
        ...,
        description="Indicate result set + zygosity combination",
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
        pattern=RESULT_ENTITY_TYPE,
        description=f"The type of entity relevant to these results. Must always be set to '{RESULT_ENTITY_TYPE}'",
    )


class ResponseField(BaseModel):
    """A list of ResultSets"""

    resultSets: list[ResultSet] = Field(
        ..., description="A list of ResultSets for the given query."
    )


class VlmResponse(BaseModel):
    """Define response structure for the variant_counts endpoint."""

    beaconHandovers: list[BeaconHandover]
    meta: Meta = Meta()
    responseSummary: ResponseSummary
    response: ResponseField

    resultset_id_error_message_base: ClassVar[str] = (
        "Invalid ResultSet id - ids must be in form '<node_id> <zygosity>'"
    )

    @model_validator(mode="after")
    def validate_resultset_ids(self) -> Self:
        """Ensure each ResultSet.id is correctly constructed."""
        handover_ids: list[str] = [
            beaconHandover.handoverType.id for beaconHandover in self.beaconHandovers
        ]

        for result_set in self.response.resultSets:
            node_id, zygosity = None, None
            try:
                node_id, zygosity = result_set.id.split(" ", 1)
            except ValueError as e:
                error_message = f"{self.resultset_id_error_message_base}, but provided id of '{result_set.id}' contains invalid formatting"
                raise ValueError(error_message) from e

            if node_id not in handover_ids:
                error_message = f"{self.resultset_id_error_message_base}, but provided node_id of '{node_id}' does not match any `handoverType.id` provided in `self.beaconHandovers`"
                raise ValueError(error_message)

            try:
                Zygosity(zygosity)
            except ValueError as e:
                valid_zygosity_values = {zygosity.value for zygosity in Zygosity}
                error_message = f"{self.resultset_id_error_message_base}, but provided zygosity of '{zygosity}' is not found in allowable value set of: {', '.join(valid_zygosity_values)}"
                raise ValueError(error_message) from e

        return self
