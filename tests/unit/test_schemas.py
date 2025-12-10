"""Test schema validation functionality"""

import pytest

from anyvlm.schemas.vlm import (
    RESULT_ENTITY_TYPE,
    HandoverType,
    ResponseField,
    ResponseSummary,
    ResultSet,
    VlmResponse,
)
from anyvlm.utils.types import Zygosity


@pytest.fixture(scope="module")
def valid_handover_id() -> str:
    return HandoverType().id


@pytest.fixture(scope="module")
def response_summary() -> ResponseSummary:
    return ResponseSummary(exists=False, numTotalResults=0)


@pytest.fixture(scope="module")
def responses_with_invalid_resultset_ids(valid_handover_id) -> list[ResponseField]:
    return [
        ResponseField(
            resultSets=[
                ResultSet(
                    exists=True,
                    id=f"invalid_handover_id {Zygosity.HOMOZYGOUS}",
                    resultsCount=0,
                    setType=RESULT_ENTITY_TYPE,
                )
            ]
        ),
        ResponseField(
            resultSets=[
                ResultSet(
                    exists=True,
                    id=f"{valid_handover_id} invalid_zygosity",
                    resultsCount=0,
                    setType=RESULT_ENTITY_TYPE,
                )
            ]
        ),
        ResponseField(
            resultSets=[
                ResultSet(
                    exists=True,
                    id=f"{Zygosity.HOMOZYGOUS}-{valid_handover_id}",  # incorrect order/formatting
                    resultsCount=0,
                    setType=RESULT_ENTITY_TYPE,
                )
            ]
        ),
    ]


def test_valid_resultset_id(response_summary, valid_handover_id):
    response = ResponseField(
        resultSets=[
            ResultSet(
                exists=True,
                id=f"{valid_handover_id} {Zygosity.HOMOZYGOUS}",
                resultsCount=0,
                setType=RESULT_ENTITY_TYPE,
            )
        ]
    )

    # Should NOT raise an error
    vlm_response = VlmResponse(responseSummary=response_summary, response=response)

    assert (
        vlm_response.response.resultSets[0].id
        == f"{valid_handover_id} {Zygosity.HOMOZYGOUS}"
    )


def test_invalid_resultset_ids(response_summary, responses_with_invalid_resultset_ids):
    for response in responses_with_invalid_resultset_ids:
        with pytest.raises(
            ValueError,
            match=r"^Invalid ResultSet id - ids must be in form '<node_id> <zygosity>'",
        ):
            VlmResponse(responseSummary=response_summary, response=response)
