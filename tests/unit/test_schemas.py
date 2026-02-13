"""Test schema validation functionality"""

import os
import re

import pytest

from anyvlm.schemas.vlm import (
    BeaconHandover,
    HandoverType,
    ResponseField,
    ResponseSummary,
    ResultSet,
    VlmResponse,
)
from anyvlm.utils.types import Zygosity


@pytest.fixture(scope="module")
def valid_handover_id() -> str:
    return os.environ.get("HANDOVER_TYPE_ID")  # type: ignore


@pytest.fixture(scope="module")
def beacon_handovers(valid_handover_id: str) -> list[BeaconHandover]:
    handover_type = HandoverType(
        id=valid_handover_id,
        label=os.environ.get("HANDOVER_TYPE_LABEL"),  # type: ignore
    )

    return [
        BeaconHandover(
            handoverType=handover_type,
            url=os.environ.get("BEACON_HANDOVER_URL"),  # type: ignore
        )
    ]


@pytest.fixture(scope="module")
def response_summary() -> ResponseSummary:
    return ResponseSummary(exists=False, numTotalResults=0)


def test_valid_resultset_id(
    valid_handover_id: str,
    beacon_handovers: list[BeaconHandover],
    response_summary: ResponseSummary,
):
    response = ResponseField(
        resultSets=[
            ResultSet(
                id=f"{valid_handover_id} {Zygosity.HOMOZYGOUS}",
                resultsCount=0,
                exists=True,
            )
        ]
    )

    # Should NOT raise an error
    vlm_response = VlmResponse(
        beaconHandovers=beacon_handovers,
        responseSummary=response_summary,
        response=response,
    )

    assert (
        vlm_response.response.resultSets[0].id
        == f"{valid_handover_id} {Zygosity.HOMOZYGOUS}"
    )


def test_invalid_resultset_ids(
    response_summary: ResponseSummary,
    beacon_handovers: list[BeaconHandover],
):
    responses_with_invalid_resultset_ids: list[ResponseField] = [
        ResponseField(
            resultSets=[
                ResultSet(
                    exists=True,
                    id=f"invalid_handover_id {Zygosity.HOMOZYGOUS}",
                    resultsCount=0,
                )
            ]
        ),
        ResponseField(
            resultSets=[
                ResultSet(
                    exists=False,
                    id=f"{valid_handover_id} invalid_zygosity",
                    resultsCount=0,
                )
            ]
        ),
        ResponseField(
            resultSets=[
                ResultSet(
                    exists=True,
                    id=f"{Zygosity.HOMOZYGOUS}-{valid_handover_id}",  # incorrect order/formatting
                    resultsCount=0,
                )
            ]
        ),
    ]

    for response in responses_with_invalid_resultset_ids:
        with pytest.raises(
            ValueError,
            match=re.escape(VlmResponse.resultset_id_error_message_base),
        ):
            VlmResponse(
                beaconHandovers=beacon_handovers,
                responseSummary=response_summary,
                response=response,
            )
