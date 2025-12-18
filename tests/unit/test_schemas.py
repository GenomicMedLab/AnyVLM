"""Test schema validation functionality"""

import re

import pytest

from anyvlm.schemas.vlm import (
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
                    id=f"invalid_handover_id {Zygosity.HOMOZYGOUS}",
                    resultsCount=0,
                )
            ]
        ),
        ResponseField(
            resultSets=[
                ResultSet(
                    id=f"{valid_handover_id} invalid_zygosity",
                    resultsCount=0,
                )
            ]
        ),
        ResponseField(
            resultSets=[
                ResultSet(
                    id=f"{Zygosity.HOMOZYGOUS}-{valid_handover_id}",  # incorrect order/formatting
                    resultsCount=0,
                )
            ]
        ),
    ]


def test_valid_resultset_id(response_summary, valid_handover_id):
    response = ResponseField(
        resultSets=[
            ResultSet(
                id=f"{valid_handover_id} {Zygosity.HOMOZYGOUS}",
                resultsCount=0,
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
            match=re.escape(VlmResponse.resultset_id_error_message_base),
        ):
            VlmResponse(responseSummary=response_summary, response=response)
