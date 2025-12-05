"""Craft a VlmResponse object from a list of CohortAlleleFrequencyStudyResults"""

from ga4gh.va_spec.base.core import CohortAlleleFrequencyStudyResult

from anyvlm.schemas.vlm import (
    HandoverType,
    ResponseField,
    ResponseSummary,
    ResultSet,
    VlmResponse,
)


def build_vlm_response(caf_data: list[CohortAlleleFrequencyStudyResult]) -> VlmResponse:
    """Craft a VlmResponse object from a list of CohortAlleleFrequencyStudyResults.

    :param caf_data: A list of `CohortAlleleFrequencyStudyResult` objects that will be used to build the VlmResponse
    :return: A `VlmResponse` object.
    """
    result_sets: list[ResultSet] = []
    if caf_data:
        total: int = sum(
            [caf_study_result.focusAlleleCount for caf_study_result in caf_data]
        )  # TODO: I'm not sure this is the right field?
        response_summary = ResponseSummary(exists=True, total=total)

        for caf_study_result in caf_data:
            result_sets.extend(
                [
                    ResultSet(
                        exists=True,
                        id=f"{HandoverType.id} {caf_study_result.cohort}",  # TODO - not sure that caf_study_result.cohort is the right field
                        resultsCount=caf_study_result.focusAlleleCount,
                    )
                ]
            )
    else:
        response_summary = ResponseSummary(exists=False, total=0)

    return VlmResponse(
        responseSummary=response_summary, response=ResponseField(resultSets=result_sets)
    )
