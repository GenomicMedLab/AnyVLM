"""Craft a VlmResponse object from a list of CohortAlleleFrequencyStudyResults"""

from ga4gh.va_spec.base.core import CohortAlleleFrequencyStudyResult

from anyvlm.schemas.vlm import (
    HandoverType,
    ResponseField,
    ResponseSummary,
    ResultSet,
    VlmResponse,
)
from anyvlm.utils.types import Zygosity


def _get_caf_zygosity() -> Zygosity:
    """Extracts a zygosity from a CohortAlleleFrequencyStudyResult.
    #TODO: We will need to implement this function during or after Issue #16 based on how we choose to
    store CAF data/implement the CAF data pull.

    :param caf_study_result: The CohortAlleleFrequencyStudyResult whose zygosity we wish to determine.
    :return: The `Zygosity` of the study result.
    """
    raise NotImplementedError


def build_vlm_response(caf_data: list[CohortAlleleFrequencyStudyResult]) -> VlmResponse:
    """Craft a VlmResponse object from a list of CohortAlleleFrequencyStudyResults.

    :param caf_data: A list of `CohortAlleleFrequencyStudyResult` objects that will be used to build the VlmResponse
    :return: A `VlmResponse` object.
    """
    result_sets: list[ResultSet] = []
    if caf_data:
        total: int = sum(
            [caf_study_result.focusAlleleCount for caf_study_result in caf_data]
        )  # TODO: I'm not sure this is the right field? Will need to verify during/after Issue #16.
        response_summary = ResponseSummary(exists=True, total=total)

        for caf_study_result in caf_data:
            result_sets.extend(
                [
                    ResultSet(
                        exists=True,
                        # TODO - HandoverType.id represents the ID of the node from which the dataset was pulled.
                        # In the future, this ID should be set dynamically.
                        id=f"{HandoverType.id} {_get_caf_zygosity()}",
                        resultsCount=caf_study_result.focusAlleleCount,
                    )
                ]
            )
    else:
        response_summary = ResponseSummary(exists=False, total=0)

    return VlmResponse(
        responseSummary=response_summary, response=ResponseField(resultSets=result_sets)
    )
