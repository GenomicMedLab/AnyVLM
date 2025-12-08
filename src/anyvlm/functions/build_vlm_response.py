"""Craft a VlmResponse object from a list of CohortAlleleFrequencyStudyResults"""

from ga4gh.va_spec.base.core import CohortAlleleFrequencyStudyResult

from anyvlm.schemas.vlm import (
    VlmResponse,
)


def build_vlm_response_from_caf_data(
    caf_data: list[CohortAlleleFrequencyStudyResult],
) -> VlmResponse:
    """Craft a VlmResponse object from a list of CohortAlleleFrequencyStudyResults.

    :param caf_data: A list of `CohortAlleleFrequencyStudyResult` objects that will be used to build the VlmResponse
    :return: A `VlmResponse` object.
    """
    raise NotImplementedError  # TODO: Implement this during/after Issue #16
