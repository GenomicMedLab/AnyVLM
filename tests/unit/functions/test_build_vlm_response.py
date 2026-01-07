import pytest
from ga4gh.core.models import iriReference
from ga4gh.va_spec.base import StudyGroup

from anyvlm.functions.build_vlm_response import (
    _get_environment_var,
    build_vlm_response,
)
from anyvlm.schemas.vlm import ResponseSummary, ResultSet, VlmResponse
from anyvlm.utils.funcs import sum_nullables
from anyvlm.utils.types import (
    AncillaryResults,
    AnyVlmCohortAlleleFrequencyResult,
    QualityMeasures,
    Zygosity,
)


@pytest.fixture(scope="module")
def caf_data() -> list[AnyVlmCohortAlleleFrequencyResult]:
    return [
        AnyVlmCohortAlleleFrequencyResult(
            focusAllele=iriReference("ga4gh:VA.J3Hi64dkKFKdnKIwB2419Qz3STDB2sJq"),
            focusAlleleCount=211787,
            locusAlleleCount=500000000,
            focusAlleleFrequency=0.00042357,
            qualityMeasures=QualityMeasures(qcFilters=["LowQual", "NO_HQ_GENOTYPES"]),
            ancillaryResults=AncillaryResults(
                homozygotes=177,
                heterozygotes=211608,
                hemizygotes=2,
            ),
            cohort=StudyGroup(name="rare disease"),  # type: ignore
        ),
        AnyVlmCohortAlleleFrequencyResult(
            focusAllele=iriReference("ga4gh:VA.J3Hi64dkKFKdnKIwB2419Qz3STDB2sJq"),
            focusAlleleCount=0,
            locusAlleleCount=0,
            focusAlleleFrequency=0,
            qualityMeasures=None,
            ancillaryResults=None,
            cohort=StudyGroup(name="rare disease"),  # type: ignore
        ),
        AnyVlmCohortAlleleFrequencyResult(
            focusAllele=iriReference("ga4gh:VA.J3Hi64dkKFKdnKIwB2419Qz3STDB2sJq"),
            focusAlleleCount=300300,
            locusAlleleCount=600000000,
            focusAlleleFrequency=0.00045005,
            qualityMeasures=None,
            ancillaryResults=AncillaryResults(
                homozygotes=300,
                heterozygotes=300000,
                hemizygotes=None,
            ),
            cohort=StudyGroup(name="rare disease"),  # type: ignore
        ),
        AnyVlmCohortAlleleFrequencyResult(
            focusAllele=iriReference("ga4gh:VA.J3Hi64dkKFKdnKIwB2419Qz3STDB2sJq"),
            focusAlleleCount=150000,
            locusAlleleCount=400000000,
            focusAlleleFrequency=0.000375,
            qualityMeasures=None,
            ancillaryResults=None,
            cohort=StudyGroup(name="rare disease"),  # type: ignore
        ),
    ]


def test_build_vlm_response(
    caf_data: list[AnyVlmCohortAlleleFrequencyResult],
):
    vlm_response: VlmResponse = build_vlm_response(caf_data)

    # VlmResponse.responseSummary
    response_summary: ResponseSummary = vlm_response.responseSummary
    assert response_summary.exists  # should be `True`
    assert response_summary.numTotalResults == sum(
        [entry.focusAlleleCount for entry in caf_data]
    )

    # VlmResponse.response
    result_sets: list[ResultSet] = vlm_response.response.resultSets
    assert (
        len(result_sets)
        == 4  # one entry for each type of Zygosity encountered (includes "Unknown")
    )

    result_sets_by_id: dict[str, ResultSet] = {
        result_set.id: result_set for result_set in result_sets
    }
    node_id: str = _get_environment_var("HANDOVER_TYPE_ID")

    homozygous_result_id: str = f"{node_id} {Zygosity.HOMOZYGOUS}"
    assert result_sets_by_id[homozygous_result_id].resultsCount == sum_nullables(
        [
            entry.ancillaryResults.homozygotes if entry.ancillaryResults else 0
            for entry in caf_data
        ]
    )

    heterozygous_result_id: str = f"{node_id} {Zygosity.HETEROZYGOUS}"
    assert result_sets_by_id[heterozygous_result_id].resultsCount == sum_nullables(
        [
            entry.ancillaryResults.heterozygotes if entry.ancillaryResults else 0
            for entry in caf_data
        ]
    )

    hemizygous_result_id: str = f"{node_id} {Zygosity.HEMIZYGOUS}"
    assert result_sets_by_id[hemizygous_result_id].resultsCount == sum_nullables(
        [
            entry.ancillaryResults.hemizygotes if entry.ancillaryResults else 0
            for entry in caf_data
        ]
    )

    unknown_result_id: str = f"{node_id} {Zygosity.UNKNOWN}"
    assert result_sets_by_id[unknown_result_id].resultsCount == sum_nullables(
        [
            entry.focusAlleleCount if entry.ancillaryResults is None else 0
            for entry in caf_data
        ]
    )


def test_build_vlm_response_no_data():
    vlm_response: VlmResponse = build_vlm_response([])

    # VlmResponse.responseSummary
    response_summary: ResponseSummary = vlm_response.responseSummary
    assert not response_summary.exists
    assert response_summary.numTotalResults == 0

    # VlmResponse.response
    result_sets: list[ResultSet] = vlm_response.response.resultSets
    assert len(result_sets) == 0
