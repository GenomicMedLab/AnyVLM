"""Craft a VlmResponse object from a list of CohortAlleleFrequencyStudyResults"""

from anyvlm.schemas.vlm import (
    VlmResponse,
)
from anyvlm.utils.types import AnyVlmCohortAlleleFrequencyResult


def build_vlm_response_from_caf_data(
    caf_data: list[AnyVlmCohortAlleleFrequencyResult],
) -> VlmResponse:
    """Craft a VlmResponse object from a list of CohortAlleleFrequencyStudyResults.

    :param caf_data: A list of `AnyVlmCohortAlleleFrequencyResult` objects that will be used to build the VlmResponse
    :return: A `VlmResponse` object.
    """
    raise NotImplementedError  # TODO: Implement this during/after Issue #16
