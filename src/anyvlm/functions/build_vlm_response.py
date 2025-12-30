"""Craft a VlmResponse object from a list of CohortAlleleFrequencyStudyResults"""

import os

from anyvlm.schemas.vlm import (
    BeaconHandover,
    HandoverType,
    ResponseField,
    ResponseSummary,
    VlmResponse,
)
from anyvlm.utils.types import AnyVlmCohortAlleleFrequencyResult


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
    raise NotImplementedError  # TODO: Remove this and finish implementing this function in Issue #35

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

    num_results = len(caf_data)
    response_summary = ResponseSummary(
        exists=num_results > 0, numTotalResults=num_results
    )

    # TODO - create this field in Issue #35
    response_field = ResponseField()

    return VlmResponse(
        beaconHandovers=beacon_handovers,
        responseSummary=response_summary,
        response=response_field,
    )
