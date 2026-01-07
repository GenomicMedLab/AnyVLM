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
from anyvlm.utils.funcs import sum_nullables
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

    results: dict[Zygosity, int | None] = {
        Zygosity.HOMOZYGOUS: None,
        Zygosity.HETEROZYGOUS: None,
        Zygosity.HEMIZYGOUS: None,
        Zygosity.UNKNOWN: None,
    }

    for entry in caf_data:
        ancillary_results: AncillaryResults | None = entry.ancillaryResults
        if ancillary_results is not None:
            results[Zygosity.HOMOZYGOUS] = sum_nullables(
                results[Zygosity.HOMOZYGOUS], ancillary_results.homozygotes
            )
            results[Zygosity.HETEROZYGOUS] = sum_nullables(
                results[Zygosity.HETEROZYGOUS], ancillary_results.heterozygotes
            )
            results[Zygosity.HEMIZYGOUS] = sum_nullables(
                results[Zygosity.HEMIZYGOUS], ancillary_results.hemizygotes
            )
        else:
            results[Zygosity.UNKNOWN] = sum_nullables(results[Zygosity.UNKNOWN], 1)

    result_sets: list[ResultSet] = []
    total_num_results = 0
    for zygosity_type, num_results in results.items():
        if num_results is not None:
            total_num_results += num_results
            result_sets.append(
                ResultSet(
                    resultset_id=f"{_get_environment_var('HANDOVER_TYPE_ID')} {zygosity_type}",
                    resultsCount=num_results,
                )
            )

    return VlmResponse(
        beaconHandovers=beacon_handovers,
        responseSummary=ResponseSummary(
            exists=total_num_results > 0, numTotalResults=total_num_results
        ),
        response=ResponseField(resultSets=result_sets),
    )
