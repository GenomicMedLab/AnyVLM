"""Craft a VlmResponse object from a list of CohortAlleleFrequencyStudyResults"""

import os

from anyvlm.schemas.vlm import (
    BeaconHandover,
    HandoverType,
    ResponseField,
    ResponseSummary,
    ResultSet,
    VlmResponse,
)
from anyvlm.utils.types import (
    AncillaryResults,
    AnyVlmCohortAlleleFrequencyResult,
    Zygosity,
)


class MissingEnvironmentVariableError(Exception):
    """Raised when a required environment variable is not set."""


def _get_environment_var(key: str) -> str:
    """Retrieves an environment variable, raising an error if it is not set.

    :param key: The key for the environment variable
    :returns: The value for the environment variable of the provided `key`
    :raises: MissingEnvironmentVariableError if environment variable is not found.
    """
    value: str | None = os.environ.get(key)
    if not value:
        message = f"Missing required environment variable: {key}"
        raise MissingEnvironmentVariableError(message)
    return value


def build_vlm_response_from_caf_data(
    caf_data: list[AnyVlmCohortAlleleFrequencyResult],
) -> VlmResponse:
    """Craft a VlmResponse object from a list of CohortAlleleFrequencyStudyResults.

    :param caf_data: A list of `AnyVlmCohortAlleleFrequencyResult` objects that will be used to build the VlmResponse
    :return: A `VlmResponse` object.
    """
    # TODO - create `handover_type` and `beacon_handovers` dynamically,
    # instead of pulling from environment variables. See Issue #37.
    handover_type = HandoverType(
        id=_get_environment_var("HANDOVER_TYPE_ID"),
        label=_get_environment_var("HANDOVER_TYPE_LABEL"),
    )

    beacon_handovers: list[BeaconHandover] = [
        BeaconHandover(
            handoverType=handover_type, url=_get_environment_var("BEACON_HANDOVER_URL")
        )
    ]

    # TODO - is this the right way to count this?
    # Or is it the total of heterozygotes + homozygotes + hemizygotes + unknowns?
    num_results = len(caf_data)
    response_summary = ResponseSummary(
        exists=num_results > 0, numTotalResults=num_results
    )

    # Build Response Field
    results: dict[Zygosity, int | None] = {
        Zygosity.HOMOZYGOUS: None,
        Zygosity.HETEROZYGOUS: None,
        Zygosity.HEMIZYGOUS: None,
        Zygosity.UNKNOWN: None,
    }

    for entry in caf_data:
        ancillary_results: AncillaryResults | None = entry.ancillaryResults
        if ancillary_results is not None:
            results[Zygosity.HOMOZYGOUS] = (
                ancillary_results.homozygotes
                if results[Zygosity.HOMOZYGOUS] is None
                else results[Zygosity.HOMOZYGOUS] + ancillary_results.homozygotes  # type: ignore
            )
            results[Zygosity.HETEROZYGOUS] = (
                ancillary_results.heterozygotes
                if results[Zygosity.HETEROZYGOUS] is None
                else results[Zygosity.HETEROZYGOUS] + ancillary_results.heterozygotes  # type: ignore
            )
            results[Zygosity.HEMIZYGOUS] = (
                ancillary_results.hemizygotes
                if results[Zygosity.HEMIZYGOUS] is None
                else results[Zygosity.HEMIZYGOUS] + ancillary_results.hemizygotes  # type: ignore
            )
        else:
            results[Zygosity.UNKNOWN] = (
                1
                if results[Zygosity.UNKNOWN] is None
                else results[Zygosity.UNKNOWN] + 1  # type: ignore
            )

    result_sets = []
    for zygosity_type, num_results in results.items():
        if num_results is not None:
            result_sets.append(
                ResultSet(
                    resultset_id=f"{_get_environment_var('HANDOVER_TYPE_ID')} {zygosity_type}",
                    resultsCount=num_results,
                )
            )

    return VlmResponse(
        beaconHandovers=beacon_handovers,
        responseSummary=response_summary,
        response=ResponseField(resultSets=result_sets),
    )
