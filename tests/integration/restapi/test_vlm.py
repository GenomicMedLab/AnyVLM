import http

import pytest
from fastapi.testclient import TestClient

from anyvlm.main import app as vlm_restapi


@pytest.fixture
def restapi_client(anyvar_populated_python_client, postgres_storage):
    vlm_restapi.state.anyvar_client = anyvar_populated_python_client
    vlm_restapi.state.anyvlm_storage = postgres_storage
    return TestClient(app=vlm_restapi)


def test_variantcounts_handle_unrecognized(restapi_client: TestClient):
    response = restapi_client.get(
        "/variant_counts",
        params={
            "assemblyId": "GRCh38",
            "referenceName": "chr1",
            "start": 10,
            "referenceBases": "A",
            "alternateBases": "T",
        },
    )
    response.raise_for_status()
    response_data = response.json()
    assert response_data["responseSummary"] == {"exists": False, "numTotalResults": 0}
    expected_resultsets = [
        {
            "exists": False,
            "id": "CUSTOM:GREGoR-NCH Heterozygous",
            "results": [],
            "resultsCount": 0,
            "setType": "genomicVariant",
        },
        {
            "exists": False,
            "id": "CUSTOM:GREGoR-NCH Homozygous",
            "results": [],
            "resultsCount": 0,
            "setType": "genomicVariant",
        },
        {
            "exists": False,
            "id": "CUSTOM:GREGoR-NCH Hemizygous",
            "results": [],
            "resultsCount": 0,
            "setType": "genomicVariant",
        },
        {
            "exists": False,
            "id": "CUSTOM:GREGoR-NCH Unknown",
            "results": [],
            "resultsCount": 0,
            "setType": "genomicVariant",
        },
    ]
    assert len(response_data["response"]["resultSets"]) == len(expected_resultsets)
    for result_set in response_data["response"]["resultSets"]:
        assert result_set in expected_resultsets


def test_variantcounts_handle_invalid(restapi_client: TestClient):
    response = restapi_client.get(
        "/variant_counts",
        params={
            "assemblyId": "T2T-CHM13v2.0",
            "referenceName": "1",
            "start": 10,
            "referenceBases": "A",
            "alternateBases": "T",
        },
    )
    assert response.status_code == http.HTTPStatus.BAD_REQUEST
