"""Schemas relating to VLM API."""

from collections.abc import Callable
from typing import Any, ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from anyvlm.utils.types import Zygosity

# ruff: noqa: N815, D107 (allow camelCase vars instead of snake_case to align with expected VLM protocol response + don't require init docstrings)

RESULT_ENTITY_TYPE = "genomicVariant"


def forbid_env_override(field_name: str) -> Callable[..., Any]:
    """Returns a Pydantic field validator that forbids explicitly
    passing a value for `field_name`. The value must come from env.
    """

    @field_validator(field_name, mode="before")
    @classmethod
    def _forbid_override(cls, value: Any) -> Any:  # noqa: ARG001, ANN401, ANN001
        if value is not None:
            raise TypeError(f"{field_name} must be set via environment variable only")
        return value

    return _forbid_override


class HandoverType(BaseSettings):
    """The type of handover the parent `BeaconHandover` represents."""

    id: str = Field(..., description="Node-specific identifier")
    label: str = Field(..., description="Node-specific label")

    model_config = SettingsConfigDict(env_prefix="HANDOVER_TYPE_", extra="forbid")

    # These validators prevent instantiation of this class with values that would override `id` or `label`
    _forbid_id_override = forbid_env_override("id")
    _forbid_label_override = forbid_env_override("label")

    # Allows `HandoverType` to be instantiated without providing values for the
    # any required fields, since both are pulled from environment variables instead
    def __init__(self) -> None:
        super().__init__()


class BeaconHandover(BaseSettings):
    """Describes how users can get more information about the results provided in the parent `VlmResponse`"""

    handoverType: HandoverType = Field(default=HandoverType())
    url: str = Field(
        ...,
        description="""
            A url which directs users to more detailed information about the results tabulated by the API. Must be human-readable.
            Ideally links directly to the variant specified in the query, but can be a generic search page if necessary.
        """,
    )

    model_config = SettingsConfigDict(env_prefix="BEACON_HANDOVER_", extra="forbid")

    # These validators prevent instantiation of this class with values that would override `handoverType` or `url`
    _forbid_handoverType_override = forbid_env_override("handoverType")
    _forbid_url_override = forbid_env_override("url")

    # Allows `BeaconHandover` to be instantiated without providing values
    # for any required fields, since both are generated statically
    def __init__(self) -> None:
        super().__init__()


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


class Meta(BaseSettings):
    """Relevant metadata about the results provided in the parent `VlmResponse`"""

    apiVersion: str = Field(
        default="v1.0",
        description="The version of the VLM API that this response conforms to",
    )
    beaconId: str = Field(
        ...,
        alias="BEACON_NODE_ID",
        description="""
            The Id of a Beacon. Usually a reversed domain string, but any URI is acceptable. The purpose of this attribute is,
            in the context of a Beacon network, to disambiguate responses coming from different Beacons. See the beacon documentation
            [here](https://github.com/ga4gh-beacon/beacon-v2/blob/c6558bf2e6494df3905f7b2df66e903dfe509500/framework/src/common/beaconCommonComponents.yaml#L26)
        """,
    )
    returnedSchemas: list[ReturnedSchema] = [ReturnedSchema()]

    model_config = SettingsConfigDict(
        env_prefix="", populate_by_name=False, extra="forbid"
    )

    # This validator prevents instantiation of this class with values that would override `handoverType` or `url`
    _forbid_beaconId_override = forbid_env_override("beaconId")

    # Allows `Meta` to be instantiated without providing values
    # for any required fields, since all are generated statically
    def __init__(self) -> None:
        super().__init__()


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
                node_id, zygosity = result_set.id.split(" ")
            except ValueError as e:
                error_message = f"{self.resultset_id_error_message_base}, but provided id of {result_set.id} contains invalid formatting"
                raise ValueError(error_message) from e

            if node_id not in handover_ids:
                error_message = f"{self.resultset_id_error_message_base}, but provided node_id of {node_id} does not match any `handoverType.id` provided in `self.beaconHandovers`"
                raise ValueError(error_message)

            try:
                Zygosity(zygosity)
            except ValueError as e:
                valid_zygosity_values = {zygosity.value for zygosity in Zygosity}
                error_message = f"{self.resultset_id_error_message_base}, but provided zygosity of {zygosity} is not found in allowable value set of: {', '.join(valid_zygosity_values)}"
                raise ValueError(error_message) from e

        return self
