"""Craft a VlmResponse object from a list of CohortAlleleFrequencyStudyResults"""

from ga4gh.core.models import MappableConcept
from ga4gh.va_spec.base.core import CohortAlleleFrequencyStudyResult

from anyvlm.schemas.vlm import (
    HandoverType,
    ResponseField,
    ResponseSummary,
    ResultSet,
    VlmResponse,
)
from anyvlm.utils.types import Zygosity


def _extract_zygosity(caf_study_result: CohortAlleleFrequencyStudyResult) -> Zygosity:
    """Extracts a zygosity from a CohortAlleleFrequencyStudyResult.
    #TODO: This is my best guess at how we'll want to represent zygosity in our CAF results. We may need
    to update this function during or after Issue #16 based on how we choose to implement our CAF data pull.

    :param caf_study_result: The CohortAlleleFrequencyStudyResult whose zygosity we wish to determine.
    :return: The `Zygosity` of the study result.
    """
    cohort_characteristics: list[MappableConcept] | None = (
        caf_study_result.cohort.characteristics
    )
    if not (cohort_characteristics):
        error_message: str = "Each CohortAlleleFrequencyStudyResult's 'cohort' field must have 'characteristics' set"
        raise ValueError(error_message)

    zygosity: str | None = next(
        (
            concept.name
            for concept in cohort_characteristics
            if getattr(concept, "conceptType", None) == "Zygosity"
        ),
        None,
    )
    if not zygosity:
        error_message: str = "'CohortAlleleFrequencyStudyResult.cohort.characteristics' must contain a 'Zygosity' entry"
        raise ValueError(error_message)

    try:
        return Zygosity(zygosity)
    except ValueError as e:
        error_message: str = f"Invalid zygosity provided: {zygosity}"
        raise ValueError(error_message) from e


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
                        id=f"{HandoverType.id} {_extract_zygosity(caf_study_result)}",
                        resultsCount=caf_study_result.focusAlleleCount,
                    )
                ]
            )
    else:
        response_summary = ResponseSummary(exists=False, total=0)

    return VlmResponse(
        responseSummary=response_summary, response=ResponseField(resultSets=result_sets)
    )
